"""Legal Notice API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.legal.enums import (
    NoticeType,
    DeliveryMode,
    DeliveryStatus,
)
from app.services.legal.notice_service import NoticeService

router = APIRouter(prefix="/notices", tags=["Legal Notices"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class NoticeTemplateCreate(BaseModel):
    """Create notice template request."""

    template_code: str = Field(..., max_length=50)
    template_name: str = Field(..., max_length=200)
    notice_type: NoticeType
    subject_template: str
    body_template: str
    statutory_period_days: int = Field(..., ge=0)
    legal_reference: Optional[str] = None
    default_language: str = "en"
    requires_acknowledgment: bool = True
    requires_witness: bool = False


class NoticeTemplateResponse(BaseModel):
    """Notice template response."""

    id: UUID
    template_code: str
    template_name: str
    notice_type: str
    statutory_period_days: int
    legal_reference: Optional[str] = None
    default_language: str
    is_active: bool

    class Config:
        from_attributes = True


class NoticeGenerateRequest(BaseModel):
    """Generate notice request."""

    legal_case_id: UUID
    loan_account_id: UUID
    customer_id: UUID
    notice_type: NoticeType
    template_id: Optional[UUID] = None
    amount_demanded: Decimal
    principal_outstanding: Optional[Decimal] = None
    interest_outstanding: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    notice_date: Optional[date] = None
    custom_content: Optional[str] = None
    language: str = "en"


class NoticeResponse(BaseModel):
    """Legal notice response."""

    id: UUID
    notice_number: str
    notice_type: str
    legal_case_id: UUID
    loan_account_id: UUID
    customer_id: UUID
    notice_date: date
    amount_demanded: float
    statutory_period_days: int
    response_due_date: date
    is_responded: bool
    response_date: Optional[date] = None
    is_complied: bool
    current_status: str

    class Config:
        from_attributes = True


class NoticeDispatchRequest(BaseModel):
    """Record notice dispatch request."""

    delivery_mode: DeliveryMode
    tracking_number: Optional[str] = None
    dispatch_date: Optional[date] = None
    recipient_name: str
    recipient_address: str
    recipient_pincode: Optional[str] = None
    dispatch_office: Optional[str] = None
    dispatch_cost: Optional[Decimal] = None


class NoticeDeliveryResponse(BaseModel):
    """Notice delivery response."""

    id: UUID
    notice_id: UUID
    delivery_mode: str
    tracking_number: Optional[str] = None
    dispatch_date: date
    delivery_status: str
    delivered_date: Optional[date] = None
    recipient_name: str
    pod_received: bool

    class Config:
        from_attributes = True


class DeliveryUpdateRequest(BaseModel):
    """Update delivery status request."""

    delivery_status: DeliveryStatus
    delivered_date: Optional[date] = None
    received_by: Optional[str] = None
    pod_document_id: Optional[UUID] = None
    remarks: Optional[str] = None


class NoticeResponseRequest(BaseModel):
    """Record notice response request."""

    response_date: date
    response_type: str = Field(..., description="OBJECTION, COMPLIANCE, PARTIAL_COMPLIANCE")
    response_content: Optional[str] = None
    amount_paid: Optional[Decimal] = None
    document_ids: Optional[List[UUID]] = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Notice Template Endpoints
# =============================================================================


@router.post(
    "/templates",
    response_model=NoticeTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Notice Template",
)
async def create_template(
    organization_id: UUID,
    request: NoticeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice_template.create")),
):
    """Create a new notice template."""
    service = NoticeService(db)
    template = await service.create_template(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return template


@router.get(
    "/templates",
    response_model=PaginatedResponse,
    summary="List Notice Templates",
)
async def list_templates(
    organization_id: UUID,
    notice_type: Optional[NoticeType] = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice_template.read")),
):
    """List notice templates."""
    service = NoticeService(db)
    items, total = await service.list_templates(
        organization_id=organization_id,
        notice_type=notice_type,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[NoticeTemplateResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


# =============================================================================
# Notice Generation Endpoints
# =============================================================================


@router.post(
    "",
    response_model=NoticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Legal Notice",
)
async def generate_notice(
    organization_id: UUID,
    request: NoticeGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.create")),
):
    """Generate a new legal notice."""
    service = NoticeService(db)
    notice = await service.generate_notice(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return notice


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List Legal Notices",
)
async def list_notices(
    organization_id: UUID,
    legal_case_id: Optional[UUID] = None,
    loan_account_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    notice_type: Optional[NoticeType] = None,
    is_responded: Optional[bool] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """List legal notices with filtering."""
    service = NoticeService(db)
    items, total = await service.list_notices(
        organization_id=organization_id,
        legal_case_id=legal_case_id,
        loan_account_id=loan_account_id,
        customer_id=customer_id,
        notice_type=notice_type,
        is_responded=is_responded,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[NoticeResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{notice_id}",
    response_model=NoticeResponse,
    summary="Get Notice Details",
)
async def get_notice(
    notice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """Get legal notice details."""
    service = NoticeService(db)
    notice = await service.get_notice(notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )
    return notice


@router.get(
    "/{notice_id}/pdf",
    summary="Download Notice PDF",
)
async def download_notice_pdf(
    notice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """Download notice as PDF."""
    service = NoticeService(db)
    notice = await service.get_notice(notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    pdf_content = await service.generate_notice_pdf(notice_id)

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=notice_{notice.notice_number}.pdf"
        },
    )


# =============================================================================
# Notice Dispatch & Delivery Endpoints
# =============================================================================


@router.post(
    "/{notice_id}/dispatch",
    response_model=NoticeDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Notice Dispatch",
)
async def record_dispatch(
    notice_id: UUID,
    request: NoticeDispatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.update")),
):
    """Record notice dispatch details."""
    service = NoticeService(db)
    delivery = await service.record_dispatch(
        notice_id=notice_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return delivery


@router.get(
    "/{notice_id}/deliveries",
    response_model=List[NoticeDeliveryResponse],
    summary="Get Notice Deliveries",
)
async def get_notice_deliveries(
    notice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """Get all delivery attempts for a notice."""
    service = NoticeService(db)
    deliveries = await service.get_notice_deliveries(notice_id)
    return [NoticeDeliveryResponse.model_validate(d) for d in deliveries]


@router.put(
    "/deliveries/{delivery_id}",
    response_model=NoticeDeliveryResponse,
    summary="Update Delivery Status",
)
async def update_delivery_status(
    delivery_id: UUID,
    request: DeliveryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.update")),
):
    """Update notice delivery status."""
    service = NoticeService(db)
    delivery = await service.update_delivery_status(
        delivery_id=delivery_id,
        updated_by=current_user.id,
        **request.model_dump(),
    )
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery record not found",
        )
    await db.commit()
    return delivery


# =============================================================================
# Notice Response Endpoints
# =============================================================================


@router.post(
    "/{notice_id}/response",
    response_model=NoticeResponse,
    summary="Record Notice Response",
)
async def record_response(
    notice_id: UUID,
    request: NoticeResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.update")),
):
    """Record borrower's response to notice."""
    service = NoticeService(db)
    notice = await service.record_response(
        notice_id=notice_id,
        updated_by=current_user.id,
        **request.model_dump(),
    )
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )
    await db.commit()
    return notice


# =============================================================================
# Overdue & Pending Notices
# =============================================================================


@router.get(
    "/overdue",
    response_model=PaginatedResponse,
    summary="Get Overdue Notices",
)
async def get_overdue_notices(
    organization_id: UUID,
    notice_type: Optional[NoticeType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """Get notices past their statutory response period without response."""
    service = NoticeService(db)
    items, total = await service.get_overdue_notices(
        organization_id=organization_id,
        notice_type=notice_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[NoticeResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/pending-delivery",
    response_model=PaginatedResponse,
    summary="Get Pending Delivery Notices",
)
async def get_pending_delivery_notices(
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.notice.read")),
):
    """Get notices dispatched but not yet delivered."""
    service = NoticeService(db)
    items, total = await service.get_pending_delivery_notices(
        organization_id=organization_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[NoticeResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
