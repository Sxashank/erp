"""SARFAESI Workflow API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.legal.enums import (
    AuctionStatus,
    PossessionType,
    PropertyType,
    SARFAESIStage,
)
from app.services.legal.sarfaesi_service import SARFAESIService
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/sarfaesi", tags=["SARFAESI"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class SARFAESIInitiateRequest(BaseModel):
    """Initiate SARFAESI request."""

    loan_account_id: UUID
    customer_id: UUID
    total_outstanding: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    other_charges: Decimal | None = None
    npa_date: date
    security_details: str | None = None
    property_description: str | None = None
    property_address: str | None = None
    property_value: Decimal | None = None


class SARFAESICaseResponse(BaseModel):
    """SARFAESI case response."""

    id: UUID
    case_number: str
    loan_account_id: UUID
    customer_id: UUID
    current_stage: str
    total_outstanding: float
    npa_date: date
    demand_notice_date: date | None = None
    demand_notice_expiry: date | None = None
    possession_date: date | None = None
    possession_type: str | None = None
    auction_scheduled: bool
    sale_completed: bool
    total_recovered: float

    class Config:
        from_attributes = True


class ObjectionRequest(BaseModel):
    """Record objection request."""

    objection_date: date
    objection_content: str
    objection_grounds: list[str] | None = None
    document_ids: list[UUID] | None = None


class ObjectionResponse(BaseModel):
    """Objection response."""

    id: UUID
    legal_case_id: UUID
    objection_date: date
    objection_content: str
    response_date: date | None = None
    response_content: str | None = None
    is_resolved: bool

    class Config:
        from_attributes = True


class PossessionRequest(BaseModel):
    """Take possession request."""

    possession_date: date
    possession_type: PossessionType
    property_type: PropertyType
    property_address: str
    property_description: str
    property_area: str | None = None
    property_value: Decimal
    panchnama_document_id: UUID | None = None
    inventory_document_id: UUID | None = None
    cersai_registration_number: str | None = None
    remarks: str | None = None


class PossessionResponse(BaseModel):
    """Possession details response."""

    id: UUID
    legal_case_id: UUID
    possession_date: date
    possession_type: str
    property_type: str
    property_address: str
    property_value: float
    is_possession_notice_published: bool
    cersai_registration_number: str | None = None

    class Config:
        from_attributes = True


class AuctionScheduleRequest(BaseModel):
    """Schedule auction request."""

    auction_date: date
    reserve_price: Decimal
    earnest_money_deposit: Decimal
    bid_increment: Decimal
    auction_venue: str | None = None
    auction_type: str = "E_AUCTION"  # E_AUCTION, PHYSICAL
    e_auction_portal: str | None = None
    publication_date: date | None = None
    publication_newspaper: str | None = None
    terms_and_conditions: str | None = None


class AuctionResponse(BaseModel):
    """Auction response."""

    id: UUID
    legal_case_id: UUID
    auction_number: str
    auction_date: date
    reserve_price: float
    highest_bid: float | None = None
    winning_bidder_name: str | None = None
    auction_status: str
    is_notice_published: bool
    publication_date: date | None = None
    sale_confirmed: bool
    sale_price: float | None = None

    class Config:
        from_attributes = True


class BidRecordRequest(BaseModel):
    """Record bid request."""

    bidder_name: str
    bidder_pan: str | None = None
    bidder_address: str | None = None
    bidder_phone: str | None = None
    bid_amount: Decimal
    bid_time: str | None = None
    emd_received: bool = False
    emd_amount: Decimal | None = None
    emd_reference: str | None = None


class SaleConfirmRequest(BaseModel):
    """Confirm sale request."""

    sale_price: Decimal
    sale_date: date
    buyer_name: str
    buyer_pan: str | None = None
    buyer_address: str | None = None
    payment_received: Decimal
    payment_date: date
    payment_reference: str
    sale_certificate_date: date | None = None
    remarks: str | None = None


class TimelineResponse(BaseModel):
    """SARFAESI timeline response."""

    stage: str
    stage_name: str
    target_date: date
    actual_date: date | None = None
    status: str  # COMPLETED, CURRENT, PENDING, OVERDUE
    days_remaining: int | None = None
    remarks: str | None = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# SARFAESI Initiation
# =============================================================================


@router.post(
    "/initiate",
    response_model=SARFAESICaseResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate SARFAESI Proceedings",
)
async def initiate_sarfaesi(
    request: SARFAESIInitiateRequest,
    organization_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """
    Initiate SARFAESI proceedings for an NPA account.

    This will:
    1. Create a legal case with SARFAESI type
    2. Generate Section 13(2) demand notice
    3. Set up statutory timeline tracking
    """
    service = SARFAESIService(db)
    result = await service.initiate_sarfaesi(
        organization_id=(organization_id or current_user.organization_id),
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return result["legal_case"]


@router.get(
    "",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="List SARFAESI Cases",
)
async def list_sarfaesi_cases(
    organization_id: UUID | None = Query(None),
    stage: SARFAESIStage | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """List SARFAESI cases with filtering."""
    service = SARFAESIService(db)
    items, total = await service.list_sarfaesi_cases(
        organization_id=(organization_id or current_user.organization_id),
        stage=stage,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[SARFAESICaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{case_id}",
    response_model=SARFAESICaseResponse, response_model_by_alias=True,
    summary="Get SARFAESI Case",
)
async def get_sarfaesi_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get SARFAESI case details."""
    service = SARFAESIService(db)
    case = await service.get_sarfaesi_case(case_id)
    if not case:
        raise NotFoundException(detail="SARFAESI case not found", error_code="SARFAESI_CASE_NOT_FOUND")
    return case


# =============================================================================
# Objection Handling
# =============================================================================


@router.post(
    "/{case_id}/objection",
    response_model=ObjectionResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Record Borrower Objection",
)
async def record_objection(
    case_id: UUID,
    request: ObjectionRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """
    Record borrower's objection under Section 13(3A).

    Bank must respond within 15 days of receiving objection.
    """
    service = SARFAESIService(db)
    objection = await service.record_objection(
        case_id=case_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return objection


@router.post(
    "/{case_id}/objection-response",
    response_model=ObjectionResponse, response_model_by_alias=True,
    summary="Respond to Objection",
)
async def respond_to_objection(
    case_id: UUID,
    response_content: str,
    response_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Record bank's response to borrower objection."""
    service = SARFAESIService(db)
    objection = await service.respond_to_objection(
        case_id=case_id,
        response_content=response_content,
        response_date=response_date,
        responded_by=current_user.id,
    )
    if not objection:
        raise NotFoundException(detail="Objection not found", error_code="OBJECTION_NOT_FOUND")
    await db.commit()
    return objection


# =============================================================================
# Possession
# =============================================================================


@router.post(
    "/{case_id}/possession",
    response_model=PossessionResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Take Possession Under 13(4)",
)
async def take_possession(
    case_id: UUID,
    request: PossessionRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """
    Record possession taken under Section 13(4).

    Possession can be taken after 60 days from demand notice
    if no response received or objection rejected.
    """
    service = SARFAESIService(db)
    possession = await service.take_possession(
        case_id=case_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return possession


@router.get(
    "/{case_id}/possession",
    response_model=PossessionResponse, response_model_by_alias=True,
    summary="Get Possession Details",
)
async def get_possession_details(
    case_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get possession details for a SARFAESI case."""
    service = SARFAESIService(db)
    possession = await service.get_possession_details(case_id)
    if not possession:
        raise NotFoundException(
            detail="Possession record not found",
            error_code="POSSESSION_RECORD_NOT_FOUND",
        )
    return possession


# =============================================================================
# Auction
# =============================================================================


@router.post(
    "/{case_id}/auction",
    response_model=AuctionResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule Property Auction",
)
async def schedule_auction(
    case_id: UUID,
    request: AuctionScheduleRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """
    Schedule property auction under Rule 8 & 9.

    Auction notice must be published 30 days before auction date.
    """
    service = SARFAESIService(db)
    auction = await service.schedule_auction(
        case_id=case_id,
        scheduled_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return auction


@router.get(
    "/{case_id}/auctions",
    response_model=list[AuctionResponse], response_model_by_alias=True,
    summary="Get Case Auctions",
)
async def get_case_auctions(
    case_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get all auctions for a SARFAESI case."""
    service = SARFAESIService(db)
    auctions = await service.get_case_auctions(case_id)
    return [AuctionResponse.model_validate(a) for a in auctions]


@router.post(
    "/auctions/{auction_id}/bid",
    summary="Record Auction Bid",
)
async def record_bid(
    auction_id: UUID,
    request: BidRecordRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Record a bid in the auction."""
    service = SARFAESIService(db)
    bid = await service.record_bid(
        auction_id=auction_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return {"message": "Bid recorded successfully", "bid_id": bid.id}


@router.put(
    "/auctions/{auction_id}/status",
    response_model=AuctionResponse, response_model_by_alias=True,
    summary="Update Auction Status",
)
async def update_auction_status(
    auction_id: UUID,
    auction_status: AuctionStatus,
    remarks: str | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Update auction status (CANCELLED, POSTPONED, etc.)."""
    service = SARFAESIService(db)
    auction = await service.update_auction_status(
        auction_id=auction_id,
        auction_status=auction_status,
        remarks=remarks,
        updated_by=current_user.id,
    )
    if not auction:
        raise NotFoundException(detail="Auction not found", error_code="AUCTION_NOT_FOUND")
    await db.commit()
    return auction


# =============================================================================
# Sale Confirmation
# =============================================================================


@router.post(
    "/auctions/{auction_id}/sale",
    response_model=AuctionResponse, response_model_by_alias=True,
    summary="Confirm Sale",
)
async def confirm_sale(
    auction_id: UUID,
    request: SaleConfirmRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """
    Confirm sale after successful auction.

    Issues sale certificate and updates recovery records.
    """
    service = SARFAESIService(db)
    auction = await service.confirm_sale(
        auction_id=auction_id,
        confirmed_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return auction


# =============================================================================
# Timeline & Dashboard
# =============================================================================


@router.get(
    "/{case_id}/timeline",
    response_model=list[TimelineResponse], response_model_by_alias=True,
    summary="Get SARFAESI Timeline",
)
async def get_sarfaesi_timeline(
    case_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """
    Get complete SARFAESI timeline with statutory deadlines.

    Shows all stages from demand notice to sale completion.
    """
    service = SARFAESIService(db)
    timeline = await service.get_sarfaesi_timeline(case_id)
    return timeline


@router.get(
    "/pending-actions",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Pending SARFAESI Actions",
)
async def get_pending_actions(
    organization_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get cases with pending statutory actions."""
    service = SARFAESIService(db)
    items, total = await service.get_pending_actions(
        organization_id=(organization_id or current_user.organization_id),
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/upcoming-auctions",
    response_model=list[AuctionResponse], response_model_by_alias=True,
    summary="Get Upcoming Auctions",
)
async def get_upcoming_auctions(
    organization_id: UUID | None = Query(None),
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get auctions scheduled in the next N days."""
    service = SARFAESIService(db)
    auctions = await service.get_upcoming_auctions(
        organization_id=(organization_id or current_user.organization_id),
        days=days,
    )
    return [AuctionResponse.model_validate(a) for a in auctions]
