"""NACH API endpoints for batch management and EMI collection."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.auth.user import User
from app.models.lending.enums import NachBatchStatus
from app.services.lending.nach_service import NachService
from app.schemas.lending.nach import (
    NachBatchCreate,
    NachBatchGenerateRequest,
    NachBatchUpdate,
    NachBatchSubmit,
    NachBatchResponse,
    NachBatchDetailResponse,
    NachBatchListResponse,
    NachTransactionResponse,
    NachTransactionListResponse,
    NachBatchStatistics,
    NachBounceAnalysis,
    NachRetryDueList,
    NachFileGenerationRequest,
    NachFileGenerationResponse,
)

router = APIRouter(prefix="/nach", tags=["NACH"])


# =============================================================================
# Batch Endpoints
# =============================================================================


@router.post("/batches/generate", response_model=NachBatchResponse)
async def generate_batch(
    request: NachBatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/batches", response_model=NachBatchListResponse)
async def list_batches(
    organization_id: UUID,
    status: Optional[NachBatchStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List NACH batches with filtering."""
    service = NachService(db)
    batches, total = await service.get_batches(
        organization_id=organization_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return NachBatchListResponse(
        items=[NachBatchResponse.model_validate(b) for b in batches],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/batches/{batch_id}", response_model=NachBatchDetailResponse)
async def get_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get batch details with transactions."""
    service = NachService(db)
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    # Build transaction summaries
    from app.schemas.lending.nach import NachTransactionSummary
    transactions = []
    for t in batch.transactions:
        transactions.append(NachTransactionSummary(
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
        ))

    response = NachBatchDetailResponse.model_validate(batch)
    response.transactions = transactions
    return response


@router.post("/batches/{batch_id}/generate-file", response_model=NachFileGenerationResponse)
async def generate_batch_file(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batches/{batch_id}/submit", response_model=NachBatchResponse)
async def submit_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batches/{batch_id}/process-response")
async def process_response_file(
    batch_id: UUID,
    response_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process NACH response file.

    Upload the response file received from NPCI/provider to update
    transaction statuses.
    """
    import tempfile
    import shutil

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batches/{batch_id}/cancel", response_model=NachBatchResponse)
async def cancel_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a batch."""
    service = NachService(db)
    try:
        batch = await service.cancel_batch(batch_id)
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Retry Endpoints
# =============================================================================


@router.get("/retry-due", response_model=NachRetryDueList)
async def get_retry_due_transactions(
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transactions due for retry."""
    service = NachService(db)
    return await service.get_transactions_for_retry(
        organization_id=organization_id,
        as_of_date=as_of_date,
    )


@router.post("/retry-batch", response_model=NachBatchResponse)
async def create_retry_batch(
    organization_id: UUID,
    transaction_ids: list[UUID],
    new_debit_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a retry batch from failed transactions."""
    service = NachService(db)
    try:
        batch = await service.create_retry_batch(
            organization_id=organization_id,
            transaction_ids=transaction_ids,
            new_debit_date=new_debit_date,
            created_by_id=current_user.id,
        )
        return NachBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Statistics & Reporting
# =============================================================================


@router.get("/statistics", response_model=NachBatchStatistics)
async def get_batch_statistics(
    organization_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get NACH batch statistics."""
    service = NachService(db)
    return await service.get_batch_statistics(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/bounce-analysis", response_model=NachBounceAnalysis)
async def get_bounce_analysis(
    organization_id: UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
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


@router.get("/transactions/{transaction_id}", response_model=NachTransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transaction details."""
    from app.models.lending.nach_batch import NachTransaction

    transaction = await db.get(NachTransaction, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return NachTransactionResponse.model_validate(transaction)
