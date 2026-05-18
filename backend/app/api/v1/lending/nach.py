"""NACH API endpoints for batch management and EMI collection."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import NachBatchStatus
from app.schemas.base import CamelSchema
from app.schemas.lending.nach import (
    NachBatchDetailResponse,
    NachBatchGenerateRequest,
    NachBatchListItemResponse,
    NachBatchListResponse,
    NachBatchResponse,
    NachBatchStatistics,
    NachBounceAnalysis,
    NachFileGenerationResponse,
    NachRetryDueList,
    NachTransactionResponse,
)
from app.services.lending.nach_service import NachService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/nach", tags=["NACH"])


class NachProcessResponse(CamelSchema):
    """Response for uploaded NACH response-file processing."""

    success: bool
    success_count: int
    failure_count: int
    errors: list[str]


class RetryBatchRequest(CamelSchema):
    """Body for POST /retry-batch."""

    transaction_ids: list[UUID]
    new_debit_date: date


# =============================================================================
# Batch Endpoints
# =============================================================================


@router.post(
    "/batches/generate",
    response_model=NachBatchResponse,
    response_model_by_alias=True,
)
async def generate_batch(
    request: NachBatchGenerateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate a NACH batch from due EMIs.

    This endpoint scans for all due EMIs with active mandates and creates
    a batch for NACH presentation.
    """
    service = NachService(db)
    try:
        batch = await service.generate_batch_from_due_emis(
            request=request,
            created_by_id=current_user.id,
        )
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/batches",
    response_model=NachBatchListResponse,
    response_model_by_alias=True,
)
async def list_batches(
    status: NachBatchStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List NACH batches scoped to caller's org (camelCase wire)."""
    service = NachService(db)
    batches, total = await service.get_batches(
        organization_id=current_user.organization_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return NachBatchListResponse(
        items=[NachBatchListItemResponse.model_validate(b) for b in batches],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/batches/{batch_id}",
    response_model=NachBatchDetailResponse,
    response_model_by_alias=True,
)
async def get_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get batch details with transactions."""
    service = NachService(db)
    batch = await service.get_batch(batch_id)
    if not batch:
        raise NotFoundException(detail="Batch not found", error_code="BATCH_NOT_FOUND")

    # Build transaction summaries
    from app.schemas.lending.nach import NachTransactionSummary

    transactions = []
    for t in batch.transactions:
        transactions.append(
            NachTransactionSummary(
                id=t.id,
                transaction_reference=t.transaction_reference,
                loan_account_number=t.loan_account.loan_account_number if t.loan_account else "",
                borrower_name=t.account_holder_name,
                umrn=t.umrn,
                debit_amount=t.debit_amount,
                debit_date=t.debit_date,
                status=t.status,
                return_code=t.return_code,
                failure_reason=t.failure_reason,
            )
        )

    response = NachBatchDetailResponse.model_validate(batch)
    response.transactions = transactions
    return response


@router.post(
    "/batches/{batch_id}/generate-file",
    response_model=NachFileGenerationResponse,
    response_model_by_alias=True,
)
async def generate_batch_file(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate NACH ACH file for a batch."""
    service = NachService(db)
    try:
        file_name, file_path, checksum = await service.generate_batch_file(batch_id)
        batch = await service.get_batch(batch_id)
        return NachFileGenerationResponse(
            batch_id=batch_id,
            file_name=file_name,
            file_path=file_path,
            file_checksum=checksum,
            total_records=batch.total_transactions,
            total_amount=batch.total_amount,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/batches/{batch_id}/submit",
    response_model=NachBatchResponse,
    response_model_by_alias=True,
)
async def submit_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Submit batch to NACH provider."""
    service = NachService(db)
    try:
        batch = await service.submit_batch(
            batch_id=batch_id,
            submitted_by_id=current_user.id,
        )
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/batches/{batch_id}/process-response",
    response_model=NachProcessResponse,
    response_model_by_alias=True,
)
async def process_response_file(
    batch_id: UUID,
    response_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Process NACH response file.

    Upload the response file received from NPCI/provider to update
    transaction statuses.
    """
    import shutil
    import tempfile

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        shutil.copyfileobj(response_file.file, tmp)
        tmp_path = tmp.name

    service = NachService(db)
    try:
        success_count, failure_count, errors = await service.process_response_file(
            batch_id=batch_id,
            response_file_path=tmp_path,
        )
        return {
            "success": True,
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors,
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/batches/{batch_id}/cancel",
    response_model=NachBatchResponse,
    response_model_by_alias=True,
)
async def cancel_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Cancel a batch."""
    service = NachService(db)
    try:
        batch = await service.cancel_batch(batch_id)
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# Retry Endpoints
# =============================================================================


@router.get(
    "/retry-due",
    response_model=NachRetryDueList,
    response_model_by_alias=True,
)
async def get_retry_due_transactions(
    as_of_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get transactions due for retry (camelCase, scoped to caller's org)."""
    service = NachService(db)
    return await service.get_transactions_for_retry(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


@router.post(
    "/retry-batch",
    response_model=NachBatchResponse,
    response_model_by_alias=True,
)
async def create_retry_batch(
    body: RetryBatchRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a retry batch from failed transactions (scoped to caller's org)."""
    service = NachService(db)
    try:
        batch = await service.create_retry_batch(
            organization_id=current_user.organization_id,
            transaction_ids=body.transaction_ids,
            new_debit_date=body.new_debit_date,
            created_by_id=current_user.id,
        )
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# Statistics & Reporting
# =============================================================================


@router.get(
    "/statistics",
    response_model=NachBatchStatistics,
    response_model_by_alias=True,
)
async def get_batch_statistics(
    organization_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get NACH batch statistics."""
    service = NachService(db)
    return await service.get_batch_statistics(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/bounce-analysis",
    response_model=NachBounceAnalysis,
    response_model_by_alias=True,
)
async def get_bounce_analysis(
    organization_id: UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Analyze NACH bounces."""
    service = NachService(db)
    return await service.get_bounce_analysis(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )


# =============================================================================
# Transaction Endpoints
# =============================================================================


@router.get(
    "/transactions/{transaction_id}",
    response_model=NachTransactionResponse,
    response_model_by_alias=True,
)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get transaction details."""
    from app.models.lending.nach_batch import NachTransaction

    transaction = await db.get(NachTransaction, transaction_id)
    if not transaction:
        raise NotFoundException(detail="Transaction not found", error_code="TRANSACTION_NOT_FOUND")
    return NachTransactionResponse.model_validate(transaction)
