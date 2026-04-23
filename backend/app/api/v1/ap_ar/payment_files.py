"""Payment File API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
from app.schemas.ap_ar.payment_file import (
    PaymentFileFormat,
    PaymentFileStatus,
    PaymentFileGenerateRequest,
    PaymentFileResponse,
    PaymentFileDetailResponse,
    PaymentFileListResponse,
    PaymentFileSummary,
    PaymentFileTransactionResponse,
    PaymentFileProcessingUpdate,
)
from app.services.ap_ar.payment_file_service import PaymentFileService

router = APIRouter()


@router.get("", response_model=PaymentFileListResponse)
async def list_payment_files(
    organization_id: UUID,
    status: Optional[str] = None,
    file_format: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payment files for an organization."""
    service = PaymentFileService(db)
    items, total = await service.get_by_organization(
        organization_id=organization_id,
        status=status,
        file_format=file_format,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )

    return PaymentFileListResponse(
        items=[service.to_response(pf) for pf in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", response_model=PaymentFileSummary)
async def get_payment_summary(
    organization_id: UUID,
    payment_ids: List[UUID] = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary of payments for file generation."""
    service = PaymentFileService(db)
    return await service.get_payment_summary(organization_id, payment_ids)


@router.post("/generate", response_model=PaymentFileResponse, status_code=status.HTTP_201_CREATED)
async def generate_payment_file(
    data: PaymentFileGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a payment file from selected payments."""
    service = PaymentFileService(db)
    try:
        payment_file = await service.generate_file(data, current_user.id)
        return service.to_response(payment_file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{id}", response_model=PaymentFileDetailResponse)
async def get_payment_file(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment file details with transactions."""
    service = PaymentFileService(db)
    payment_file = await service.get(id)
    if not payment_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )

    response = service.to_response(payment_file)
    transactions = [
        PaymentFileTransactionResponse(
            id=t.id,
            payment_file_id=t.payment_file_id,
            payment_id=t.payment_id,
            sequence_number=t.sequence_number,
            beneficiary_name=t.beneficiary_name,
            beneficiary_account_number=t.beneficiary_account_number,
            beneficiary_ifsc=t.beneficiary_ifsc,
            beneficiary_bank_name=t.beneficiary_bank_name,
            amount=t.amount,
            narration=t.narration,
            status=t.status,
            bank_reference=t.bank_reference,
            failure_reason=t.failure_reason,
            processed_at=t.processed_at,
        )
        for t in payment_file.transactions
    ]

    return PaymentFileDetailResponse(
        **response.model_dump(),
        transactions=transactions,
    )


@router.get("/{id}/download")
async def download_payment_file(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the generated payment file."""
    service = PaymentFileService(db)
    payment_file = await service.get(id)
    if not payment_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )

    if not payment_file.file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has not been generated yet",
        )

    # Mark as downloaded
    await service.mark_downloaded(id)

    # Determine file extension
    ext = "txt"
    if payment_file.file_format in ["NEFT", "RTGS"]:
        ext = "txt"

    filename = f"{payment_file.file_reference}.{ext}"

    return PlainTextResponse(
        content=payment_file.file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Checksum": payment_file.checksum or "",
        },
    )


@router.get("/{id}/preview")
async def preview_payment_file(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview the generated payment file content."""
    service = PaymentFileService(db)
    content = await service.get_file_content(id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )

    return {"content": content}


@router.post("/{id}/mark-uploaded", response_model=PaymentFileResponse)
async def mark_file_uploaded(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark payment file as uploaded to bank."""
    service = PaymentFileService(db)
    payment_file = await service.mark_uploaded(id)
    if not payment_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )
    return service.to_response(payment_file)


@router.post("/{id}/start-processing", response_model=PaymentFileResponse)
async def start_file_processing(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark payment file as processing started."""
    service = PaymentFileService(db)
    payment_file = await service.start_processing(id)
    if not payment_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )
    return service.to_response(payment_file)


@router.post("/{id}/update-results", response_model=PaymentFileResponse)
async def update_processing_results(
    id: UUID,
    data: PaymentFileProcessingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update transaction statuses from bank response."""
    service = PaymentFileService(db)
    try:
        payment_file = await service.update_processing_results(id, data.transactions)
        return service.to_response(payment_file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/cancel", response_model=PaymentFileResponse)
async def cancel_payment_file(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a payment file (only if not yet uploaded)."""
    service = PaymentFileService(db)
    try:
        payment_file = await service.cancel_file(id)
        if not payment_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment file not found",
            )
        return service.to_response(payment_file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/by-reference/{reference}", response_model=PaymentFileResponse)
async def get_payment_file_by_reference(
    reference: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment file by reference number."""
    service = PaymentFileService(db)
    payment_file = await service.get_by_reference(reference)
    if not payment_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment file not found",
        )
    return service.to_response(payment_file)
