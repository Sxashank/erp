"""E-Invoice API endpoints.

Provides endpoints for E-Invoice operations:
- IRN generation
- E-Invoice cancellation
- E-Invoice status checking
- Statistics
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.gst.einvoice import EInvoiceRequestStatus
from app.services.gst.einvoice_service import EInvoiceService

router = APIRouter(prefix="/einvoice", tags=["E-Invoice"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class GenerateEInvoiceRequest(BaseModel):
    """Request to generate E-Invoice."""
    sales_invoice_id: UUID


class CancelEInvoiceRequest(BaseModel):
    """Request to cancel E-Invoice."""
    cancel_reason: str  # 1=Duplicate, 2=Data Entry Error, 3=Order Cancelled, 4=Others
    cancel_remarks: str


class EInvoiceResponse(BaseModel):
    """E-Invoice response."""
    id: UUID
    sales_invoice_id: UUID
    provider: str
    status: str
    irn: Optional[str] = None
    ack_number: Optional[str] = None
    ack_date: Optional[str] = None
    signed_qr_code: Optional[str] = None
    eway_bill_number: Optional[str] = None
    eway_bill_date: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_cancelled: bool = False
    created_at: str

    class Config:
        from_attributes = True


class EInvoiceListResponse(BaseModel):
    """E-Invoice list response."""
    items: List[EInvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EInvoiceStatistics(BaseModel):
    """E-Invoice statistics."""
    total_requests: int
    successful: int
    failed: int
    cancelled: int
    pending: int
    with_eway_bill: int


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=EInvoiceResponse,
    summary="Generate E-Invoice",
    description="Generate E-Invoice (IRN) for a sales invoice.",
)
async def generate_einvoice(
    request: GenerateEInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.create")),
):
    """Generate E-Invoice for sales invoice."""
    service = EInvoiceService(db)
    try:
        result = await service.generate_einvoice(
            sales_invoice_id=request.sales_invoice_id,
            initiated_by=current_user.id,
        )
        return EInvoiceResponse(
            id=result.id,
            sales_invoice_id=result.sales_invoice_id,
            provider=result.provider.value,
            status=result.status.value,
            irn=result.irn,
            ack_number=result.ack_number,
            ack_date=result.ack_date.isoformat() if result.ack_date else None,
            signed_qr_code=result.signed_qr_code,
            eway_bill_number=result.eway_bill_number,
            eway_bill_date=result.eway_bill_date.isoformat() if result.eway_bill_date else None,
            error_code=result.error_code,
            error_message=result.error_message,
            is_cancelled=result.is_cancelled,
            created_at=result.created_at.isoformat() if result.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{request_id}/cancel",
    response_model=EInvoiceResponse,
    summary="Cancel E-Invoice",
    description="Cancel an E-Invoice by IRN.",
)
async def cancel_einvoice(
    request_id: UUID,
    request: CancelEInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.cancel")),
):
    """Cancel E-Invoice."""
    service = EInvoiceService(db)
    try:
        result = await service.cancel_einvoice(
            einvoice_request_id=request_id,
            cancel_reason=request.cancel_reason,
            cancel_remarks=request.cancel_remarks,
            cancelled_by=current_user.id,
        )
        return EInvoiceResponse(
            id=result.id,
            sales_invoice_id=result.sales_invoice_id,
            provider=result.provider.value,
            status=result.status.value,
            irn=result.irn,
            ack_number=result.ack_number,
            ack_date=result.ack_date.isoformat() if result.ack_date else None,
            signed_qr_code=result.signed_qr_code,
            is_cancelled=result.is_cancelled,
            created_at=result.created_at.isoformat() if result.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{request_id}",
    response_model=EInvoiceResponse,
    summary="Get E-Invoice",
    description="Get E-Invoice details by ID.",
)
async def get_einvoice(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.read")),
):
    """Get E-Invoice details."""
    service = EInvoiceService(db)
    result = await service.get_einvoice_request(request_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E-Invoice request not found",
        )
    return EInvoiceResponse(
        id=result.id,
        sales_invoice_id=result.sales_invoice_id,
        provider=result.provider.value,
        status=result.status.value,
        irn=result.irn,
        ack_number=result.ack_number,
        ack_date=result.ack_date.isoformat() if result.ack_date else None,
        signed_qr_code=result.signed_qr_code,
        eway_bill_number=result.eway_bill_number,
        eway_bill_date=result.eway_bill_date.isoformat() if result.eway_bill_date else None,
        error_code=result.error_code,
        error_message=result.error_message,
        is_cancelled=result.is_cancelled,
        created_at=result.created_at.isoformat() if result.created_at else "",
    )


@router.get(
    "/invoice/{sales_invoice_id}",
    response_model=Optional[EInvoiceResponse],
    summary="Get E-Invoice by Sales Invoice",
    description="Get E-Invoice for a sales invoice.",
)
async def get_einvoice_by_invoice(
    sales_invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.read")),
):
    """Get E-Invoice by sales invoice ID."""
    service = EInvoiceService(db)
    result = await service.get_einvoice_by_invoice(sales_invoice_id)
    if not result:
        return None
    return EInvoiceResponse(
        id=result.id,
        sales_invoice_id=result.sales_invoice_id,
        provider=result.provider.value,
        status=result.status.value,
        irn=result.irn,
        ack_number=result.ack_number,
        ack_date=result.ack_date.isoformat() if result.ack_date else None,
        signed_qr_code=result.signed_qr_code,
        eway_bill_number=result.eway_bill_number,
        eway_bill_date=result.eway_bill_date.isoformat() if result.eway_bill_date else None,
        error_code=result.error_code,
        error_message=result.error_message,
        is_cancelled=result.is_cancelled,
        created_at=result.created_at.isoformat() if result.created_at else "",
    )


@router.get(
    "",
    response_model=EInvoiceListResponse,
    summary="List E-Invoices",
    description="List E-Invoice requests with filtering.",
)
async def list_einvoices(
    organization_id: UUID,
    request_status: Optional[EInvoiceRequestStatus] = Query(None, alias="status"),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.read")),
):
    """List E-Invoice requests."""
    service = EInvoiceService(db)
    items, total = await service.list_einvoice_requests(
        organization_id=organization_id,
        status=request_status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    return EInvoiceListResponse(
        items=[
            EInvoiceResponse(
                id=r.id,
                sales_invoice_id=r.sales_invoice_id,
                provider=r.provider.value,
                status=r.status.value,
                irn=r.irn,
                ack_number=r.ack_number,
                ack_date=r.ack_date.isoformat() if r.ack_date else None,
                signed_qr_code=r.signed_qr_code,
                eway_bill_number=r.eway_bill_number,
                eway_bill_date=r.eway_bill_date.isoformat() if r.eway_bill_date else None,
                error_code=r.error_code,
                error_message=r.error_message,
                is_cancelled=r.is_cancelled,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/{request_id}/retry",
    response_model=EInvoiceResponse,
    summary="Retry Failed E-Invoice",
    description="Retry a failed E-Invoice generation.",
)
async def retry_einvoice(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.create")),
):
    """Retry failed E-Invoice generation."""
    service = EInvoiceService(db)
    try:
        result = await service.retry_failed_einvoice(
            request_id=request_id,
            initiated_by=current_user.id,
        )
        return EInvoiceResponse(
            id=result.id,
            sales_invoice_id=result.sales_invoice_id,
            provider=result.provider.value,
            status=result.status.value,
            irn=result.irn,
            ack_number=result.ack_number,
            ack_date=result.ack_date.isoformat() if result.ack_date else None,
            signed_qr_code=result.signed_qr_code,
            eway_bill_number=result.eway_bill_number,
            eway_bill_date=result.eway_bill_date.isoformat() if result.eway_bill_date else None,
            error_code=result.error_code,
            error_message=result.error_message,
            is_cancelled=result.is_cancelled,
            created_at=result.created_at.isoformat() if result.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/statistics",
    response_model=EInvoiceStatistics,
    summary="Get E-Invoice Statistics",
    description="Get E-Invoice generation statistics.",
)
async def get_statistics(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.read")),
):
    """Get E-Invoice statistics."""
    service = EInvoiceService(db)
    stats = await service.get_statistics(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )
    return EInvoiceStatistics(**stats)


@router.get(
    "/check-applicable",
    summary="Check E-Invoice Applicability",
    description="Check if E-Invoice is applicable for organization.",
)
async def check_applicable(
    organization_id: UUID,
    invoice_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("einvoice.read")),
):
    """Check E-Invoice applicability."""
    service = EInvoiceService(db)
    is_applicable = await service.check_einvoice_applicable(
        organization_id=organization_id,
        invoice_date=invoice_date,
    )
    return {"applicable": is_applicable}
