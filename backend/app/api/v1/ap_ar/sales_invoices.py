"""Sales Invoice API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.ap_ar.sales_invoice_service import SalesInvoiceService
from app.schemas.ap_ar.sales_invoice import (
    SalesInvoiceCreate,
    SalesInvoiceUpdate,
    SalesInvoiceResponse,
    SalesInvoiceListResponse,
    SalesInvoiceLineResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _line_to_response(line) -> SalesInvoiceLineResponse:
    """Convert line model to response."""
    return SalesInvoiceLineResponse(
        id=line.id,
        invoice_id=line.invoice_id,
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
        revenue_account_id=line.revenue_account_id,
    )


def _to_response(invoice) -> SalesInvoiceResponse:
    """Convert model to response."""
    return SalesInvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        customer_id=invoice.customer_id,
        organization_id=invoice.organization_id,
        unit_id=invoice.unit_id,
        subtotal=invoice.subtotal,
        discount_amount=invoice.discount_amount,
        taxable_amount=invoice.taxable_amount,
        cgst_amount=invoice.cgst_amount,
        sgst_amount=invoice.sgst_amount,
        igst_amount=invoice.igst_amount,
        cess_amount=invoice.cess_amount,
        tcs_amount=invoice.tcs_amount,
        round_off=invoice.round_off,
        total_amount=invoice.total_amount,
        balance_amount=invoice.balance_amount,
        is_reverse_charge=invoice.is_reverse_charge,
        supply_type=invoice.supply_type.value if invoice.supply_type else None,
        customer_gstin=invoice.customer_gstin,
        place_of_supply=invoice.place_of_supply,
        e_invoice_required=invoice.e_invoice_required,
        irn=invoice.irn,
        e_invoice_status=invoice.e_invoice_status.value if invoice.e_invoice_status else None,
        status=invoice.status.value if invoice.status else None,
        receipt_status=invoice.receipt_status.value if invoice.receipt_status else None,
        voucher_id=invoice.voucher_id,
        is_posted=invoice.is_posted,
        narration=invoice.narration,
        reference_number=invoice.reference_number,
        po_number=invoice.po_number,
        po_date=invoice.po_date,
        shipping_address=invoice.shipping_address,
        transporter_name=invoice.transporter_name,
        vehicle_number=invoice.vehicle_number,
        eway_bill_number=invoice.eway_bill_number,
        eway_bill_date=invoice.eway_bill_date,
        lines=[_line_to_response(line) for line in invoice.lines] if invoice.lines else [],
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        is_active=invoice.is_active,
    )


def _to_list_response(invoice) -> SalesInvoiceListResponse:
    """Convert model to list response."""
    return SalesInvoiceListResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        customer_id=invoice.customer_id,
        customer_name=invoice.customer.name if invoice.customer else None,
        total_amount=invoice.total_amount,
        balance_amount=invoice.balance_amount,
        status=invoice.status.value if invoice.status else None,
        receipt_status=invoice.receipt_status.value if invoice.receipt_status else None,
        e_invoice_status=invoice.e_invoice_status.value if invoice.e_invoice_status else None,
        is_posted=invoice.is_posted,
    )


@router.get("", response_model=PaginatedResponse[SalesInvoiceListResponse])
async def list_sales_invoices(
    organization_id: UUID = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    status: Optional[str] = Query(None, description="Filter by status"),
    receipt_status: Optional[str] = Query(None, description="Filter by receipt status"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    from_date: Optional[date] = Query(None, description="From date"),
    to_date: Optional[date] = Query(None, description="To date"),
    search: Optional[str] = Query(None, description="Search in invoice number"),
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of sales invoices."""
    service = SalesInvoiceService(db)
    skip = (page - 1) * page_size
    invoices, total = await service.get_all(
        organization_id, skip, page_size, include_inactive,
        status, receipt_status, customer_id, from_date, to_date, search
    )
    items = [_to_list_response(inv) for inv in invoices]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/unreceived/{customer_id}", response_model=list[SalesInvoiceListResponse])
async def list_unreceived_invoices(
    customer_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID"),
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get unreceived invoices for a customer (for receipt allocation)."""
    service = SalesInvoiceService(db)
    invoices = await service.get_unreceived_for_customer(organization_id, customer_id)
    return [_to_list_response(inv) for inv in invoices]


@router.get("/generate-number")
async def generate_invoice_number(
    organization_id: UUID = Query(..., description="Organization ID"),
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Generate next invoice number."""
    service = SalesInvoiceService(db)
    number = await service.generate_number(organization_id)
    return {"invoice_number": number}


@router.post("", response_model=SalesInvoiceResponse)
async def create_sales_invoice(
    data: SalesInvoiceCreate,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sales invoice."""
    service = SalesInvoiceService(db)
    invoice = await service.create(data, current_user.id)
    return _to_response(invoice)


@router.get("/{invoice_id}", response_model=SalesInvoiceResponse)
async def get_sales_invoice(
    invoice_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get sales invoice by ID."""
    service = SalesInvoiceService(db)
    invoice = await service.get(invoice_id)
    return _to_response(invoice)


@router.put("/{invoice_id}", response_model=SalesInvoiceResponse)
async def update_sales_invoice(
    invoice_id: UUID,
    data: SalesInvoiceUpdate,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a sales invoice."""
    service = SalesInvoiceService(db)
    invoice = await service.update(invoice_id, data, current_user.id)
    return _to_response(invoice)


@router.post("/{invoice_id}/submit", response_model=SalesInvoiceResponse)
async def submit_sales_invoice(
    invoice_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Submit sales invoice for approval."""
    service = SalesInvoiceService(db)
    invoice = await service.submit(invoice_id, current_user.id)
    return _to_response(invoice)


@router.post("/{invoice_id}/approve", response_model=SalesInvoiceResponse)
async def approve_sales_invoice(
    invoice_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_APPROVE")),
    db: AsyncSession = Depends(get_db),
):
    """Approve a sales invoice."""
    service = SalesInvoiceService(db)
    invoice = await service.approve(invoice_id, current_user.id)
    return _to_response(invoice)


@router.post("/{invoice_id}/cancel")
async def cancel_sales_invoice(
    invoice_id: UUID,
    reason: str = Query(..., description="Cancellation reason"),
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a sales invoice."""
    service = SalesInvoiceService(db)
    invoice = await service.cancel(invoice_id, current_user.id, reason)
    return {"message": "Sales invoice cancelled successfully"}


@router.delete("/{invoice_id}")
async def delete_sales_invoice(
    invoice_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_INVOICE_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a sales invoice."""
    service = SalesInvoiceService(db)
    await service.delete(invoice_id, current_user.id)
    return {"message": "Sales invoice deleted successfully"}
