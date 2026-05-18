"""E-Way Bill API endpoints.

Provides endpoints for E-Way Bill operations:
- E-Way Bill generation
- E-Way Bill cancellation
- Vehicle update (Part B)
- Validity extension
- Statistics
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.gst.einvoice import EWayBillStatus
from app.services.gst.ewaybill_service import EWayBillService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/ewaybill", tags=["E-Way Bill"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class EWayBillItemCreate(BaseModel):
    """E-Way Bill item create schema."""
    product_name: str
    product_desc: Optional[str] = None
    hsn_code: str
    quantity: float
    unit: str = "NOS"
    taxable_amount: float
    cgst_rate: float = 0
    sgst_rate: float = 0
    igst_rate: float = 0
    cess_rate: float = 0


class GenerateEWayBillRequest(BaseModel):
    """Request to generate E-Way Bill."""
    gst_registration_id: UUID
    # Document details
    document_type: str = "INV"
    document_number: str
    document_date: str  # DD/MM/YYYY format
    # Supply details
    supply_type: str = "O"  # O=Outward, I=Inward
    sub_supply_type: str = "1"  # 1=Supply
    # Supplier details
    from_gstin: str
    from_trade_name: str
    from_address1: str
    from_address2: Optional[str] = ""
    from_place: str
    from_pincode: str
    from_state_code: str
    # Recipient details
    to_gstin: Optional[str] = "URP"
    to_trade_name: str
    to_address1: str
    to_address2: Optional[str] = ""
    to_place: str
    to_pincode: str
    to_state_code: str
    # Values
    total_value: float
    cgst_value: float = 0
    sgst_value: float = 0
    igst_value: float = 0
    cess_value: float = 0
    invoice_value: float
    # Transport
    transport_mode: str = "1"  # 1=Road
    distance: int
    transporter_id: Optional[str] = ""
    transporter_name: Optional[str] = ""
    transport_doc_no: Optional[str] = ""
    transport_doc_date: Optional[str] = ""
    vehicle_number: Optional[str] = ""
    vehicle_type: str = "R"  # R=Regular, O=ODC
    # Items
    items: List[EWayBillItemCreate]
    # Linked invoice
    sales_invoice_id: Optional[UUID] = None


class GenerateFromInvoiceRequest(BaseModel):
    """Request to generate E-Way Bill from invoice."""
    sales_invoice_id: UUID
    distance: int
    transporter_id: Optional[str] = None
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    transport_doc_no: Optional[str] = None
    transport_doc_date: Optional[date] = None


class CancelEWayBillRequest(BaseModel):
    """Request to cancel E-Way Bill."""
    cancel_reason: str  # 1-5
    cancel_remarks: str


class UpdateVehicleRequest(BaseModel):
    """Request to update vehicle details."""
    vehicle_number: str
    from_place: str
    from_state_code: str
    reason_code: str = "1"  # 1=First time, 2=Breakdown, etc.
    reason_remarks: str = ""


class ExtendValidityRequest(BaseModel):
    """Request to extend E-Way Bill validity."""
    remaining_distance: int
    extend_reason: str
    from_place: str
    from_state_code: str


class EWayBillItemResponse(BaseModel):
    """E-Way Bill item response."""
    line_number: int
    product_name: str
    hsn_code: str
    quantity: float
    unit: str
    taxable_value: float

    class Config:
        from_attributes = True


class EWayBillResponse(BaseModel):
    """E-Way Bill response."""
    id: UUID
    eway_bill_number: Optional[str] = None
    eway_bill_date: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    status: str
    document_type: str
    document_number: str
    document_date: str
    supplier_gstin: str
    supplier_name: str
    recipient_gstin: Optional[str] = None
    recipient_name: str
    taxable_value: float
    total_value: float
    transport_mode: str
    vehicle_number: Optional[str] = None
    transporter_name: Optional[str] = None
    approximate_distance: int
    is_cancelled: bool = False
    extension_count: int = 0
    error_message: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class EWayBillListResponse(BaseModel):
    """E-Way Bill list response."""
    items: List[EWayBillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EWayBillStatistics(BaseModel):
    """E-Way Bill statistics."""
    total: int
    active: int
    expired: int
    cancelled: int
    extended: int
    expiring_soon: int
    total_value: float


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Generate E-Way Bill",
    description="Generate E-Way Bill for goods movement.",
)
async def generate_eway_bill(
    organization_id: UUID,
    request: GenerateEWayBillRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_CREATE")),
):
    """Generate E-Way Bill."""
    service = EWayBillService(db)
    try:
        eway_bill_data = request.model_dump()
        result = await service.generate_eway_bill(
            organization_id=organization_id,
            gst_registration_id=request.gst_registration_id,
            eway_bill_data=eway_bill_data,
            sales_invoice_id=request.sales_invoice_id,
            created_by=current_user.id,
        )
        return _to_response(result)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/generate-from-invoice",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Generate E-Way Bill from Invoice",
    description="Generate E-Way Bill from an existing sales invoice.",
)
async def generate_from_invoice(
    request: GenerateFromInvoiceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_CREATE")),
):
    """Generate E-Way Bill from sales invoice."""
    service = EWayBillService(db)
    try:
        result = await service.generate_from_invoice(
            sales_invoice_id=request.sales_invoice_id,
            distance=request.distance,
            transporter_id=request.transporter_id,
            transporter_name=request.transporter_name,
            vehicle_number=request.vehicle_number,
            transport_doc_no=request.transport_doc_no,
            transport_doc_date=request.transport_doc_date,
            created_by=current_user.id,
        )
        return _to_response(result)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{eway_bill_id}/cancel",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Cancel E-Way Bill",
    description="Cancel an E-Way Bill.",
)
async def cancel_eway_bill(
    eway_bill_id: UUID,
    request: CancelEWayBillRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_CANCEL")),
):
    """Cancel E-Way Bill."""
    service = EWayBillService(db)
    try:
        result = await service.cancel_eway_bill(
            eway_bill_id=eway_bill_id,
            cancel_reason=request.cancel_reason,
            cancel_remarks=request.cancel_remarks,
            cancelled_by=current_user.id,
        )
        return _to_response(result)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{eway_bill_id}/update-vehicle",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Update Vehicle",
    description="Update vehicle details (Part B) of E-Way Bill.",
)
async def update_vehicle(
    eway_bill_id: UUID,
    request: UpdateVehicleRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_UPDATE")),
):
    """Update vehicle details."""
    service = EWayBillService(db)
    try:
        result = await service.update_vehicle(
            eway_bill_id=eway_bill_id,
            vehicle_number=request.vehicle_number,
            from_place=request.from_place,
            from_state_code=request.from_state_code,
            reason_code=request.reason_code,
            reason_remarks=request.reason_remarks,
            updated_by=current_user.id,
        )
        return _to_response(result)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{eway_bill_id}/extend",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Extend Validity",
    description="Extend E-Way Bill validity.",
)
async def extend_validity(
    eway_bill_id: UUID,
    request: ExtendValidityRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_UPDATE")),
):
    """Extend E-Way Bill validity."""
    service = EWayBillService(db)
    try:
        result = await service.extend_validity(
            eway_bill_id=eway_bill_id,
            remaining_distance=request.remaining_distance,
            extend_reason=request.extend_reason,
            from_place=request.from_place,
            from_state_code=request.from_state_code,
            extended_by=current_user.id,
        )
        return _to_response(result)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/{eway_bill_id}",
    response_model=EWayBillResponse, response_model_by_alias=True,
    summary="Get E-Way Bill",
    description="Get E-Way Bill details by ID.",
)
async def get_eway_bill(
    eway_bill_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_READ")),
):
    """Get E-Way Bill details."""
    service = EWayBillService(db)
    result = await service.get_eway_bill(eway_bill_id)
    if not result:
        raise NotFoundException(detail="E-Way Bill not found", error_code="E_WAY_BILL_NOT_FOUND")
    return _to_response(result)


@router.get(
    "",
    response_model=EWayBillListResponse, response_model_by_alias=True,
    summary="List E-Way Bills",
    description="List E-Way Bills with filtering.",
)
async def list_eway_bills(
    organization_id: UUID,
    eway_status: Optional[EWayBillStatus] = Query(None, alias="status"),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    expiring_soon: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_READ")),
):
    """List E-Way Bills."""
    service = EWayBillService(db)
    items, total = await service.list_eway_bills(
        organization_id=organization_id,
        status=eway_status,
        from_date=from_date,
        to_date=to_date,
        expiring_soon=expiring_soon,
        page=page,
        page_size=page_size,
    )

    return EWayBillListResponse(
        items=[_to_response(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/statistics",
    response_model=EWayBillStatistics, response_model_by_alias=True,
    summary="Get E-Way Bill Statistics",
    description="Get E-Way Bill statistics.",
)
async def get_statistics(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_READ")),
):
    """Get E-Way Bill statistics."""
    service = EWayBillService(db)
    stats = await service.get_statistics(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )
    return EWayBillStatistics(**{**stats, "total_value": float(stats.get("total_value", 0))})


@router.get(
    "/check-required",
    summary="Check E-Way Bill Required",
    description="Check if E-Way Bill is required based on invoice value.",
)
async def check_required(
    invoice_value: float,
    supply_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("EWAYBILL_READ")),
):
    """Check if E-Way Bill is required."""
    service = EWayBillService(db)
    is_required = service.check_eway_bill_required(
        invoice_value=Decimal(str(invoice_value)),
        supply_type=supply_type,
    )
    return {"required": is_required, "threshold": 50000}


def _to_response(e) -> EWayBillResponse:
    """Convert E-Way Bill model to response."""
    return EWayBillResponse(
        id=e.id,
        eway_bill_number=e.eway_bill_number,
        eway_bill_date=e.eway_bill_date.isoformat() if e.eway_bill_date else None,
        valid_from=e.valid_from.isoformat() if e.valid_from else None,
        valid_until=e.valid_until.isoformat() if e.valid_until else None,
        status=e.status.value,
        document_type=e.document_type,
        document_number=e.document_number,
        document_date=e.document_date.isoformat() if e.document_date else "",
        supplier_gstin=e.supplier_gstin,
        supplier_name=e.supplier_name,
        recipient_gstin=e.recipient_gstin,
        recipient_name=e.recipient_name,
        taxable_value=float(e.taxable_value),
        total_value=float(e.total_value),
        transport_mode=e.transport_mode.value,
        vehicle_number=e.vehicle_number,
        transporter_name=e.transporter_name,
        approximate_distance=e.approximate_distance,
        is_cancelled=e.is_cancelled,
        extension_count=e.extension_count,
        error_message=e.error_message,
        created_at=e.created_at.isoformat() if e.created_at else "",
    )
