"""Loan Receipt API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.auth.user import User
from app.services.lending import ReceiptService

router = APIRouter()


# Request/Response Schemas
class ReceiptCreateRequest(BaseModel):
    """Request to create a receipt."""
    loan_account_id: UUID
    receipt_amount: Decimal = Field(..., gt=0)
    receipt_date: date
    value_date: Optional[date] = None
    receipt_type: str = Field(default="REGULAR")
    receipt_mode: str
    instrument_number: Optional[str] = None
    instrument_date: Optional[date] = None
    instrument_bank: Optional[str] = None
    mandate_id: Optional[UUID] = None
    remarks: Optional[str] = None


class ReceiptResponse(BaseModel):
    """Receipt response."""
    id: UUID
    receipt_number: str
    loan_account_id: UUID
    receipt_amount: Decimal
    receipt_date: date
    value_date: date
    receipt_type: str
    receipt_mode: str
    status: str
    allocated_amount: Decimal
    unallocated_amount: Decimal
    principal_allocated: Decimal
    interest_allocated: Decimal
    penal_interest_allocated: Decimal
    charges_allocated: Decimal


class AllocationRequest(BaseModel):
    """Request to allocate a receipt."""
    receipt_id: UUID
    allocation_method: str = Field(default="fifo", description="fifo, proportional, or specific")
    specific_allocations: Optional[List[dict]] = None


class AllocationResponse(BaseModel):
    """Allocation response."""
    id: UUID
    receipt_id: UUID
    installment_id: Optional[UUID]
    component: str
    amount: Decimal
    sequence: int


class ReceiptReversalRequest(BaseModel):
    """Request to reverse a receipt."""
    receipt_id: UUID
    reversal_reason: str
    reversal_date: Optional[date] = None


class BulkReceiptItem(BaseModel):
    """Single receipt in bulk upload."""
    loan_account_number: str
    receipt_amount: Decimal
    receipt_date: date
    receipt_mode: str
    instrument_number: Optional[str] = None
    remarks: Optional[str] = None


class BulkReceiptRequest(BaseModel):
    """Bulk receipt upload request."""
    receipts: List[BulkReceiptItem]
    auto_allocate: bool = Field(default=True)


class BulkReceiptResponse(BaseModel):
    """Bulk receipt response."""
    total_count: int
    success_count: int
    failed_count: int
    total_amount: Decimal
    failures: List[dict]


# Endpoints
@router.post("/", response_model=ReceiptResponse)
async def create_receipt(
    request: ReceiptCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new receipt."""
    service = ReceiptService(db)

    receipt = await service.create_receipt(
        loan_account_id=request.loan_account_id,
        receipt_amount=request.receipt_amount,
        receipt_date=request.receipt_date,
        value_date=request.value_date,
        receipt_type=request.receipt_type,
        receipt_mode=request.receipt_mode,
        instrument_number=request.instrument_number,
        instrument_date=request.instrument_date,
        instrument_bank=request.instrument_bank,
        mandate_id=request.mandate_id,
        remarks=request.remarks,
        user_id=current_user.id,
    )

    return ReceiptResponse(
        id=receipt.id,
        receipt_number=receipt.receipt_number,
        loan_account_id=receipt.loan_account_id,
        receipt_amount=receipt.receipt_amount,
        receipt_date=receipt.receipt_date,
        value_date=receipt.value_date,
        receipt_type=receipt.receipt_type.name,
        receipt_mode=receipt.receipt_mode.name,
        status=receipt.status.name,
        allocated_amount=receipt.allocated_amount,
        unallocated_amount=receipt.unallocated_amount,
        principal_allocated=receipt.principal_allocated,
        interest_allocated=receipt.interest_allocated,
        penal_interest_allocated=receipt.penal_interest_allocated,
        charges_allocated=receipt.charges_allocated,
    )


@router.post("/allocate")
async def allocate_receipt(
    request: AllocationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Allocate a receipt to installments."""
    service = ReceiptService(db)

    allocations = await service.allocate_receipt(
        receipt_id=request.receipt_id,
        allocation_method=request.allocation_method,
        specific_allocations=request.specific_allocations,
        user_id=current_user.id,
    )

    return {
        "receipt_id": str(request.receipt_id),
        "allocation_count": len(allocations),
        "allocations": [
            {
                "id": str(a.id),
                "installment_id": str(a.installment_id) if a.installment_id else None,
                "component": a.allocation_component.name,
                "amount": a.allocated_amount,
                "sequence": a.allocation_sequence,
            }
            for a in allocations
        ],
    }


@router.post("/reverse")
async def reverse_receipt(
    request: ReceiptReversalRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Reverse a receipt."""
    service = ReceiptService(db)

    receipt = await service.reverse_receipt(
        receipt_id=request.receipt_id,
        reversal_reason=request.reversal_reason,
        reversal_date=request.reversal_date,
        user_id=current_user.id,
    )

    return {
        "receipt_id": str(receipt.id),
        "receipt_number": receipt.receipt_number,
        "status": receipt.status.name,
        "message": "Receipt reversed successfully",
    }


@router.post("/bulk", response_model=BulkReceiptResponse)
async def process_bulk_receipts(
    request: BulkReceiptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process bulk receipt upload."""
    service = ReceiptService(db)

    # Convert to dict format expected by service
    receipts_data = [r.dict() for r in request.receipts]

    result = await service.process_bulk_receipts(
        receipts_data=receipts_data,
        organization_id=current_user.organization_id,
        auto_allocate=request.auto_allocate,
        user_id=current_user.id,
    )

    return BulkReceiptResponse(
        total_count=result["total_count"],
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        total_amount=result["total_amount"],
        failures=result.get("failures", []),
    )


@router.get("/loan/{loan_account_id}")
async def get_receipts_by_loan(
    loan_account_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get receipts for a loan account."""
    service = ReceiptService(db)

    receipts = await service.get_receipts(
        loan_account_id=loan_account_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
    )

    return {
        "loan_account_id": str(loan_account_id),
        "count": len(receipts),
        "receipts": [
            {
                "id": str(r.id),
                "receipt_number": r.receipt_number,
                "receipt_date": r.receipt_date,
                "receipt_amount": r.receipt_amount,
                "receipt_type": r.receipt_type.name,
                "receipt_mode": r.receipt_mode.name,
                "status": r.status.name,
                "allocated_amount": r.allocated_amount,
                "unallocated_amount": r.unallocated_amount,
            }
            for r in receipts
        ],
    }


@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get receipt details with allocations."""
    service = ReceiptService(db)

    receipt = await service.get_receipt(receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found",
        )

    allocations = await service.get_allocations(receipt_id)

    return {
        "id": str(receipt.id),
        "receipt_number": receipt.receipt_number,
        "loan_account_id": str(receipt.loan_account_id),
        "receipt_date": receipt.receipt_date,
        "value_date": receipt.value_date,
        "receipt_amount": receipt.receipt_amount,
        "receipt_type": receipt.receipt_type.name,
        "receipt_mode": receipt.receipt_mode.name,
        "instrument_number": receipt.instrument_number,
        "instrument_date": receipt.instrument_date,
        "instrument_bank": receipt.instrument_bank,
        "status": receipt.status.name,
        "allocated_amount": receipt.allocated_amount,
        "unallocated_amount": receipt.unallocated_amount,
        "principal_allocated": receipt.principal_allocated,
        "interest_allocated": receipt.interest_allocated,
        "penal_interest_allocated": receipt.penal_interest_allocated,
        "charges_allocated": receipt.charges_allocated,
        "bounced": receipt.bounced,
        "bounce_reason": receipt.bounce_reason,
        "remarks": receipt.remarks,
        "allocations": [
            {
                "id": str(a.id),
                "installment_id": str(a.installment_id) if a.installment_id else None,
                "component": a.allocation_component.name,
                "amount": a.allocated_amount,
                "sequence": a.allocation_sequence,
            }
            for a in allocations
        ],
    }


@router.get("/organization/{organization_id}/summary")
async def get_receipt_summary(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get receipt summary for organization."""
    service = ReceiptService(db)

    summary = await service.get_receipt_summary(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )

    return summary


@router.post("/{receipt_id}/bounce")
async def mark_receipt_bounced(
    receipt_id: UUID,
    bounce_reason: str = Query(..., description="Reason for bounce"),
    bounce_date: Optional[date] = None,
    bounce_charges: Decimal = Query(default=Decimal("0"), description="Bounce charges"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Mark a receipt as bounced."""
    service = ReceiptService(db)

    receipt = await service.mark_bounced(
        receipt_id=receipt_id,
        bounce_reason=bounce_reason,
        bounce_date=bounce_date,
        bounce_charges=bounce_charges,
        user_id=current_user.id,
    )

    return {
        "receipt_id": str(receipt.id),
        "receipt_number": receipt.receipt_number,
        "status": receipt.status.name,
        "bounced": receipt.bounced,
        "bounce_reason": receipt.bounce_reason,
        "bounce_charges": receipt.bounce_charges,
        "message": "Receipt marked as bounced",
    }
