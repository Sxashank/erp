"""Advocate & Law Firm API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.legal.enums import (
    AdvocateRole,
    BarCouncilState,
    FeeStructureType,
    SpecializationType,
)
from app.services.legal.advocate_service import AdvocateService
from app.core.exceptions import NotFoundException

router = APIRouter(tags=["Advocates & Law Firms"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class LawFirmCreate(BaseModel):
    """Create law firm request."""

    name: str = Field(..., max_length=200)
    registration_number: str | None = None
    bar_council_id: str | None = None
    pan: str | None = Field(None, max_length=10)
    gstin: str | None = Field(None, max_length=15)
    address_line1: str | None = None
    city: str | None = None
    state_code: str | None = Field(None, max_length=2)
    pincode: str | None = Field(None, max_length=10)
    phone: str | None = None
    email: str | None = None
    empanelment_date: date | None = None
    empanelment_category: str | None = None
    default_fee_structure: FeeStructureType | None = None
    retainer_amount: Decimal | None = None
    specializations: list[str] | None = None


class LawFirmResponse(BaseModel):
    """Law firm response."""

    id: UUID
    name: str
    registration_number: str | None = None
    bar_council_id: str | None = None
    pan: str | None = None
    gstin: str | None = None
    is_empaneled: bool
    empanelment_date: date | None = None
    empanelment_category: str | None = None
    total_cases_handled: int
    cases_won: int
    total_recovery_amount: float

    class Config:
        from_attributes = True


class AdvocateCreate(BaseModel):
    """Create advocate request."""

    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    enrollment_number: str = Field(..., max_length=50)
    bar_council_state: BarCouncilState
    law_firm_id: UUID | None = None
    middle_name: str | None = None
    salutation: str | None = None
    enrollment_date: date | None = None
    designation: str = "Advocate"
    pan: str | None = Field(None, max_length=10)
    phone: str | None = None
    mobile: str | None = None
    email: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state_code: str | None = Field(None, max_length=2)
    pincode: str | None = Field(None, max_length=10)
    default_fee_structure: FeeStructureType | None = None
    fee_per_appearance: Decimal | None = None
    years_of_experience: int | None = None
    specializations: list[SpecializationType] | None = None


class AdvocateResponse(BaseModel):
    """Advocate response."""

    id: UUID
    full_name: str
    enrollment_number: str
    bar_council_state: str
    designation: str
    is_empaneled: bool
    law_firm_id: UUID | None = None
    email: str | None = None
    mobile: str | None = None
    default_fee_structure: str | None = None
    fee_per_appearance: float | None = None
    years_of_experience: int | None = None

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    """Create advocate assignment request."""

    legal_case_id: UUID
    role: AdvocateRole = AdvocateRole.LEAD_COUNSEL
    assigned_date: date | None = None
    fee_structure: FeeStructureType | None = None
    agreed_fee: Decimal | None = None
    success_fee_percentage: Decimal | None = None
    assignment_reason: str | None = None


class AssignmentResponse(BaseModel):
    """Advocate assignment response."""

    id: UUID
    advocate_id: UUID
    legal_case_id: UUID
    role: str
    assigned_date: date
    is_active: bool
    fee_structure: str | None = None
    agreed_fee: float | None = None
    hearings_attended: int
    total_fee_paid: float

    class Config:
        from_attributes = True


class PerformanceResponse(BaseModel):
    """Advocate performance response."""

    advocate_id: UUID
    total_cases_assigned: int
    active_cases: int
    cases_won: int
    cases_lost: int
    cases_settled: int
    total_hearings: int
    hearings_attended: int
    total_claim_amount: float
    total_recovered_amount: float
    recovery_percentage: float | None = None
    success_rate: float | None = None
    internal_rating: float | None = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Law Firm Endpoints
# =============================================================================


@router.post(
    "/law-firms",
    response_model=LawFirmResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Register Law Firm",
)
async def create_law_firm(
    request: LawFirmCreate,
    organization_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Register a new law firm."""
    service = AdvocateService(db)
    law_firm = await service.create_law_firm(
        organization_id=(organization_id or current_user.organization_id),
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return law_firm


@router.get(
    "/law-firms",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="List Law Firms",
)
async def list_law_firms(
    organization_id: UUID | None = Query(None),
    is_empaneled: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """List law firms with filtering."""
    service = AdvocateService(db)
    items, total = await service.list_law_firms(
        organization_id=(organization_id or current_user.organization_id),
        is_empaneled=is_empaneled,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[LawFirmResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/law-firms/{law_firm_id}",
    response_model=LawFirmResponse, response_model_by_alias=True,
    summary="Get Law Firm",
)
async def get_law_firm(
    law_firm_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get law firm details."""
    service = AdvocateService(db)
    law_firm = await service.get_law_firm(law_firm_id)
    if not law_firm:
        raise NotFoundException(detail="Law firm not found", error_code="LAW_FIRM_NOT_FOUND")
    return law_firm


# =============================================================================
# Advocate Endpoints
# =============================================================================


@router.post(
    "/advocates",
    response_model=AdvocateResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Register Advocate",
)
async def create_advocate(
    request: AdvocateCreate,
    organization_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Register a new advocate."""
    service = AdvocateService(db)
    advocate = await service.create_advocate(
        organization_id=(organization_id or current_user.organization_id),
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return advocate


@router.get(
    "/advocates",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="List Advocates",
)
async def list_advocates(
    organization_id: UUID | None = Query(None),
    law_firm_id: UUID | None = None,
    specialization: SpecializationType | None = None,
    is_empaneled: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """List advocates with filtering."""
    service = AdvocateService(db)
    items, total = await service.list_advocates(
        organization_id=(organization_id or current_user.organization_id),
        law_firm_id=law_firm_id,
        specialization=specialization,
        is_empaneled=is_empaneled,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[AdvocateResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/advocates/{advocate_id}",
    response_model=AdvocateResponse, response_model_by_alias=True,
    summary="Get Advocate",
)
async def get_advocate(
    advocate_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get advocate details."""
    service = AdvocateService(db)
    advocate = await service.get_advocate(advocate_id)
    if not advocate:
        raise NotFoundException(detail="Advocate not found", error_code="ADVOCATE_NOT_FOUND")
    return advocate


@router.post(
    "/advocates/{advocate_id}/assignments",
    response_model=AssignmentResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Assign Advocate to Case",
)
async def assign_to_case(
    advocate_id: UUID,
    request: AssignmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Assign advocate to a legal case."""
    service = AdvocateService(db)
    assignment = await service.assign_to_case(
        advocate_id=advocate_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return assignment


@router.get(
    "/advocates/{advocate_id}/cases",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Advocate Cases",
)
async def get_advocate_cases(
    advocate_id: UUID,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get cases assigned to an advocate."""
    service = AdvocateService(db)
    items, total = await service.get_advocate_cases(
        advocate_id=advocate_id,
        active_only=active_only,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[AssignmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/advocates/{advocate_id}/performance",
    response_model=PerformanceResponse, response_model_by_alias=True,
    summary="Get Advocate Performance",
)
async def get_advocate_performance(
    advocate_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get advocate performance metrics."""
    service = AdvocateService(db)
    performance = await service.get_advocate_performance(advocate_id)
    if not performance:
        raise NotFoundException(
            detail="Performance record not found",
            error_code="PERFORMANCE_RECORD_NOT_FOUND",
        )
    return performance
