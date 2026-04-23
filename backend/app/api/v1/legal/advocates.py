"""Advocate & Law Firm API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.legal.enums import (
    AdvocateRole,
    FeeStructureType,
    SpecializationType,
    BarCouncilState,
)
from app.services.legal.advocate_service import AdvocateService

router = APIRouter(prefix="/advocates", tags=["Advocates"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class LawFirmCreate(BaseModel):
    """Create law firm request."""

    name: str = Field(..., max_length=200)
    registration_number: Optional[str] = None
    bar_council_id: Optional[str] = None
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = None
    email: Optional[str] = None
    empanelment_date: Optional[date] = None
    empanelment_category: Optional[str] = None
    default_fee_structure: Optional[FeeStructureType] = None
    retainer_amount: Optional[Decimal] = None
    specializations: Optional[List[str]] = None


class LawFirmResponse(BaseModel):
    """Law firm response."""

    id: UUID
    name: str
    registration_number: Optional[str] = None
    bar_council_id: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    is_empaneled: bool
    empanelment_date: Optional[date] = None
    empanelment_category: Optional[str] = None
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
    law_firm_id: Optional[UUID] = None
    middle_name: Optional[str] = None
    salutation: Optional[str] = None
    enrollment_date: Optional[date] = None
    designation: str = "Advocate"
    pan: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)
    default_fee_structure: Optional[FeeStructureType] = None
    fee_per_appearance: Optional[Decimal] = None
    years_of_experience: Optional[int] = None
    specializations: Optional[List[SpecializationType]] = None


class AdvocateResponse(BaseModel):
    """Advocate response."""

    id: UUID
    full_name: str
    enrollment_number: str
    bar_council_state: str
    designation: str
    is_empaneled: bool
    law_firm_id: Optional[UUID] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    default_fee_structure: Optional[str] = None
    fee_per_appearance: Optional[float] = None
    years_of_experience: Optional[int] = None

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    """Create advocate assignment request."""

    legal_case_id: UUID
    role: AdvocateRole = AdvocateRole.LEAD_COUNSEL
    assigned_date: Optional[date] = None
    fee_structure: Optional[FeeStructureType] = None
    agreed_fee: Optional[Decimal] = None
    success_fee_percentage: Optional[Decimal] = None
    assignment_reason: Optional[str] = None


class AssignmentResponse(BaseModel):
    """Advocate assignment response."""

    id: UUID
    advocate_id: UUID
    legal_case_id: UUID
    role: str
    assigned_date: date
    is_active: bool
    fee_structure: Optional[str] = None
    agreed_fee: Optional[float] = None
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
    recovery_percentage: Optional[float] = None
    success_rate: Optional[float] = None
    internal_rating: Optional[float] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Law Firm Endpoints
# =============================================================================


@router.post(
    "/law-firms",
    response_model=LawFirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Law Firm",
)
async def create_law_firm(
    organization_id: UUID,
    request: LawFirmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.law_firm.create")),
):
    """Register a new law firm."""
    service = AdvocateService(db)
    law_firm = await service.create_law_firm(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return law_firm


@router.get(
    "/law-firms",
    response_model=PaginatedResponse,
    summary="List Law Firms",
)
async def list_law_firms(
    organization_id: UUID,
    is_empaneled: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.law_firm.read")),
):
    """List law firms with filtering."""
    service = AdvocateService(db)
    items, total = await service.list_law_firms(
        organization_id=organization_id,
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
    response_model=LawFirmResponse,
    summary="Get Law Firm",
)
async def get_law_firm(
    law_firm_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.law_firm.read")),
):
    """Get law firm details."""
    service = AdvocateService(db)
    law_firm = await service.get_law_firm(law_firm_id)
    if not law_firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Law firm not found",
        )
    return law_firm


# =============================================================================
# Advocate Endpoints
# =============================================================================


@router.post(
    "",
    response_model=AdvocateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Advocate",
)
async def create_advocate(
    organization_id: UUID,
    request: AdvocateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.advocate.create")),
):
    """Register a new advocate."""
    service = AdvocateService(db)
    advocate = await service.create_advocate(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return advocate


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List Advocates",
)
async def list_advocates(
    organization_id: UUID,
    law_firm_id: Optional[UUID] = None,
    specialization: Optional[SpecializationType] = None,
    is_empaneled: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.advocate.read")),
):
    """List advocates with filtering."""
    service = AdvocateService(db)
    items, total = await service.list_advocates(
        organization_id=organization_id,
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
    "/{advocate_id}",
    response_model=AdvocateResponse,
    summary="Get Advocate",
)
async def get_advocate(
    advocate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.advocate.read")),
):
    """Get advocate details."""
    service = AdvocateService(db)
    advocate = await service.get_advocate(advocate_id)
    if not advocate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advocate not found",
        )
    return advocate


@router.post(
    "/{advocate_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign Advocate to Case",
)
async def assign_to_case(
    advocate_id: UUID,
    request: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.assignment.create")),
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
    "/{advocate_id}/cases",
    response_model=PaginatedResponse,
    summary="Get Advocate Cases",
)
async def get_advocate_cases(
    advocate_id: UUID,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.advocate.read")),
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
    "/{advocate_id}/performance",
    response_model=PerformanceResponse,
    summary="Get Advocate Performance",
)
async def get_advocate_performance(
    advocate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.advocate.read")),
):
    """Get advocate performance metrics."""
    service = AdvocateService(db)
    performance = await service.get_advocate_performance(advocate_id)
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance record not found",
        )
    return performance
