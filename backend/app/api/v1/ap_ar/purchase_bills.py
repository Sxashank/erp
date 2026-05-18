"""Purchase Bill API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.ap_ar.purchase_bill_service import PurchaseBillService
from app.schemas.ap_ar.purchase_bill import (
    PurchaseBillCreate,
    PurchaseBillUpdate,
    PurchaseBillResponse,
    PurchaseBillListResponse,
    PurchaseBillLineResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _line_to_response(line) -> PurchaseBillLineResponse:
    """Convert line model to response."""
    return PurchaseBillLineResponse(
        id=line.id,
        bill_id=line.bill_id,
        line_number=line.line_number,
        description=line.description,
        hsn_sac_code=line.hsn_sac_code,
        quantity=line.quantity,
        unit_price=line.unit_price,
        discount_percent=line.discount_percent,
        discount_amount=line.discount_amount,
        taxable_amount=line.taxable_amount,
        gst_rate_id=line.gst_rate_id,
        cgst_rate=line.cgst_rate,
        cgst_amount=line.cgst_amount,
        sgst_rate=line.sgst_rate,
        sgst_amount=line.sgst_amount,
        igst_rate=line.igst_rate,
        igst_amount=line.igst_amount,
        cess_rate=line.cess_rate,
        cess_amount=line.cess_amount,
        total_amount=line.total_amount,
        expense_account_id=line.expense_account_id,
    )


def _to_response(bill) -> PurchaseBillResponse:
    """Convert model to response."""
    return PurchaseBillResponse(
        id=bill.id,
        bill_number=bill.bill_number,
        vendor_invoice_number=bill.vendor_invoice_number,
        vendor_invoice_date=bill.vendor_invoice_date,
        bill_date=bill.bill_date,
        due_date=bill.due_date,
        vendor_id=bill.vendor_id,
        organization_id=bill.organization_id,
        unit_id=bill.unit_id,
        subtotal=bill.subtotal,
        discount_amount=bill.discount_amount,
        taxable_amount=bill.taxable_amount,
        cgst_amount=bill.cgst_amount,
        sgst_amount=bill.sgst_amount,
        igst_amount=bill.igst_amount,
        cess_amount=bill.cess_amount,
        tds_amount=bill.tds_amount,
        round_off=bill.round_off,
        total_amount=bill.total_amount,
        balance_amount=bill.balance_amount,
        is_reverse_charge=bill.is_reverse_charge,
        supply_type=bill.supply_type.value if bill.supply_type else None,
        vendor_gstin=bill.vendor_gstin,
        place_of_supply=bill.place_of_supply,
        status=bill.status.value if bill.status else None,
        payment_status=bill.payment_status.value if bill.payment_status else None,
        voucher_id=bill.voucher_id,
        is_posted=bill.is_posted,
        narration=bill.narration,
        reference_number=bill.reference_number,
        lines=[_line_to_response(line) for line in bill.lines] if bill.lines else [],
        created_at=bill.created_at,
        updated_at=bill.updated_at,
        is_active=bill.is_active,
    )


def _to_list_response(bill) -> PurchaseBillListResponse:
    """Convert model to list response."""
    return PurchaseBillListResponse(
        id=bill.id,
        bill_number=bill.bill_number,
        vendor_invoice_number=bill.vendor_invoice_number,
        bill_date=bill.bill_date,
        due_date=bill.due_date,
        vendor_id=bill.vendor_id,
        vendor_name=bill.vendor.name if bill.vendor else None,
        total_amount=bill.total_amount,
        balance_amount=bill.balance_amount,
        status=bill.status.value if bill.status else None,
        payment_status=bill.payment_status.value if bill.payment_status else None,
        is_posted=bill.is_posted,
    )


@router.get("", response_model=PaginatedResponse[PurchaseBillListResponse], response_model_by_alias=True)
async def list_purchase_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    vendor_id: Optional[UUID] = Query(None, description="Filter by vendor"),
    from_date: Optional[date] = Query(None, description="From date"),
    to_date: Optional[date] = Query(None, description="To date"),
    search: Optional[str] = Query(None, description="Search in bill number"),
    current_user: User = Depends(RequirePermissions("APAR_BILL_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of purchase bills."""
    service = PurchaseBillService(db)
    skip = (page - 1) * page_size
    bills, total = await service.get_all(
        current_user.organization_id, skip, page_size, include_inactive,
        status, payment_status, vendor_id, from_date, to_date, search
    )
    items = [_to_list_response(b) for b in bills]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/unpaid/{vendor_id}", response_model=list[PurchaseBillListResponse], response_model_by_alias=True)
async def list_unpaid_bills(
    vendor_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_BILL_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get unpaid bills for a vendor (for payment allocation)."""
    service = PurchaseBillService(db)
    bills = await service.get_unpaid_for_vendor(current_user.organization_id, vendor_id)
    return [_to_list_response(b) for b in bills]


@router.get("/generate-number")
async def generate_bill_number(
    current_user: User = Depends(RequirePermissions("APAR_BILL_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Generate next bill number."""
    service = PurchaseBillService(db)
    number = await service.generate_number(current_user.organization_id)
    return {"bill_number": number}


@router.post("", response_model=PurchaseBillResponse, response_model_by_alias=True)
async def create_purchase_bill(
    data: PurchaseBillCreate,
    current_user: User = Depends(RequirePermissions("APAR_BILL_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new purchase bill."""
    service = PurchaseBillService(db)
    bill = await service.create(data, current_user.id)
    return _to_response(bill)


@router.get("/{bill_id}", response_model=PurchaseBillResponse, response_model_by_alias=True)
async def get_purchase_bill(
    bill_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_BILL_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get purchase bill by ID."""
    service = PurchaseBillService(db)
    bill = await service.get(bill_id)
    return _to_response(bill)


@router.put("/{bill_id}", response_model=PurchaseBillResponse, response_model_by_alias=True)
async def update_purchase_bill(
    bill_id: UUID,
    data: PurchaseBillUpdate,
    current_user: User = Depends(RequirePermissions("APAR_BILL_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a purchase bill."""
    service = PurchaseBillService(db)
    bill = await service.update(bill_id, data, current_user.id)
    return _to_response(bill)


@router.post("/{bill_id}/submit", response_model=PurchaseBillResponse, response_model_by_alias=True)
async def submit_purchase_bill(
    bill_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_BILL_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Submit purchase bill for approval."""
    service = PurchaseBillService(db)
    bill = await service.submit(bill_id, current_user.id)
    return _to_response(bill)


@router.post("/{bill_id}/approve", response_model=PurchaseBillResponse, response_model_by_alias=True)
async def approve_purchase_bill(
    bill_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_BILL_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Approve a purchase bill."""
    service = PurchaseBillService(db)
    bill = await service.approve(bill_id, current_user.id)
    return _to_response(bill)


@router.post("/{bill_id}/cancel")
async def cancel_purchase_bill(
    bill_id: UUID,
    reason: str = Query(..., description="Cancellation reason"),
    current_user: User = Depends(RequirePermissions("APAR_BILL_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Cancel a purchase bill."""
    service = PurchaseBillService(db)
    bill = await service.cancel(bill_id, current_user.id, reason)
    return {"message": "Purchase bill cancelled successfully"}


@router.delete("/{bill_id}")
async def delete_purchase_bill(
    bill_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_BILL_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a purchase bill."""
    service = PurchaseBillService(db)
    await service.delete(bill_id, current_user.id)
    return {"message": "Purchase bill deleted successfully"}
