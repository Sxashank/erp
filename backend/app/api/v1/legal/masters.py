"""Legal Master Data API endpoints.

Provides REST API for legal master data including:
- Statutory Periods
- Notice Templates
- Courts (DRT, DRAT, NCLT, etc.)
- Court Fee Slabs
- Expense Categories
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.legal.statutory_period import StatutoryPeriod
from app.models.legal.notice import NoticeTemplate
from app.models.legal.court import Court, CourtFeeSlab
from app.models.legal.expense import ExpenseCategory
from app.models.legal.enums import (
    NoticeType,
    CourtType,
    ExpenseCategoryType,
)

router = APIRouter(tags=["Legal Masters"])


# =============================================================================
# STATUTORY PERIOD SCHEMAS & ENDPOINTS
# =============================================================================


class StatutoryPeriodCreate(BaseModel):
    """Create statutory period request."""

    organization_id: UUID
    provision_code: str = Field(..., max_length=50)
    provision_name: str = Field(..., max_length=200)
    act_name: str = Field(..., max_length=200)
    section_reference: str = Field(..., max_length=100)
    period_days: int
    period_months: Optional[int] = None
    period_years: Optional[int] = None
    period_description: str = Field(..., max_length=100)
    start_event: str = Field(..., max_length=200)
    includes_holidays: bool = True
    extension_allowed: bool = False
    extension_grounds: Optional[str] = None
    consequence: str
    applicable_forums: Optional[List[str]] = None
    applicable_case_types: Optional[List[str]] = None
    alert_before_days: Optional[List[int]] = None
    legal_reference: Optional[str] = None
    description: Optional[str] = None


class StatutoryPeriodResponse(BaseModel):
    """Statutory period response."""

    id: UUID
    organization_id: UUID
    provision_code: str
    provision_name: str
    act_name: str
    section_reference: str
    period_days: int
    period_months: Optional[int] = None
    period_years: Optional[int] = None
    period_description: str
    start_event: str
    includes_holidays: bool
    extension_allowed: bool
    extension_grounds: Optional[str] = None
    consequence: str
    applicable_forums: Optional[List[str]] = None
    applicable_case_types: Optional[List[str]] = None
    alert_before_days: Optional[List[int]] = None
    legal_reference: Optional[str] = None

    class Config:
        from_attributes = True


@router.post(
    "/statutory-periods",
    response_model=StatutoryPeriodResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_statutory_period(
    data: StatutoryPeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new statutory period."""
    # Check for duplicate
    existing = await db.execute(
        select(StatutoryPeriod).where(
            and_(
                StatutoryPeriod.organization_id == data.organization_id,
                StatutoryPeriod.provision_code == data.provision_code,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Statutory period with code {data.provision_code} already exists",
        )

    period = StatutoryPeriod(
        **data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period


@router.get("/statutory-periods", response_model=List[StatutoryPeriodResponse])
async def list_statutory_periods(
    organization_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all statutory periods."""
    result = await db.execute(
        select(StatutoryPeriod)
        .where(StatutoryPeriod.organization_id == organization_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/statutory-periods/{period_id}", response_model=StatutoryPeriodResponse)
async def get_statutory_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a statutory period by ID."""
    result = await db.execute(
        select(StatutoryPeriod).where(StatutoryPeriod.id == period_id)
    )
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statutory period not found",
        )
    return period


# =============================================================================
# NOTICE TEMPLATE SCHEMAS & ENDPOINTS
# =============================================================================


class NoticeTemplateCreate(BaseModel):
    """Create notice template request."""

    organization_id: UUID
    template_code: str = Field(..., max_length=50)
    template_name: str = Field(..., max_length=200)
    notice_type: NoticeType
    act_reference: str = Field(..., max_length=200)
    section_reference: Optional[str] = Field(None, max_length=100)
    statutory_period_days: int
    response_period_days: Optional[int] = None
    template_content: str
    template_format: str = "HTML"
    placeholders: Optional[List[str]] = None
    language: str = "ENGLISH"
    is_default: bool = False
    remarks: Optional[str] = None


class NoticeTemplateResponse(BaseModel):
    """Notice template response."""

    id: UUID
    organization_id: UUID
    template_code: str
    template_name: str
    notice_type: str
    act_reference: str
    section_reference: Optional[str] = None
    statutory_period_days: int
    response_period_days: Optional[int] = None
    template_format: str
    language: str
    is_default: bool

    class Config:
        from_attributes = True


@router.post(
    "/notice-templates",
    response_model=NoticeTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notice_template(
    data: NoticeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new notice template."""
    # Check for duplicate
    existing = await db.execute(
        select(NoticeTemplate).where(
            and_(
                NoticeTemplate.organization_id == data.organization_id,
                NoticeTemplate.template_code == data.template_code,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Notice template with code {data.template_code} already exists",
        )

    template = NoticeTemplate(
        **data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/notice-templates", response_model=List[NoticeTemplateResponse])
async def list_notice_templates(
    organization_id: UUID = Query(...),
    notice_type: Optional[NoticeType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notice templates."""
    query = select(NoticeTemplate).where(
        NoticeTemplate.organization_id == organization_id
    )
    if notice_type:
        query = query.where(NoticeTemplate.notice_type == notice_type)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/notice-templates/{template_id}", response_model=NoticeTemplateResponse)
async def get_notice_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a notice template by ID."""
    result = await db.execute(
        select(NoticeTemplate).where(NoticeTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice template not found",
        )
    return template


# =============================================================================
# COURT SCHEMAS & ENDPOINTS
# =============================================================================


class CourtCreate(BaseModel):
    """Create court request."""

    organization_id: UUID
    court_code: str = Field(..., max_length=50)
    court_name: str = Field(..., max_length=300)
    court_type: CourtType
    short_name: Optional[str] = Field(None, max_length=50)
    state_code: str = Field(..., max_length=5)
    city: str = Field(..., max_length=100)
    jurisdiction: str = Field(..., max_length=200)
    jurisdiction_area: Optional[str] = None
    bench_number: Optional[str] = Field(None, max_length=20)
    circuit_bench: bool = False
    circuit_location: Optional[str] = Field(None, max_length=200)
    working_days: Optional[List[str]] = None
    working_hours: Optional[str] = Field(None, max_length=50)
    filing_time: Optional[str] = Field(None, max_length=50)
    e_filing_enabled: bool = False
    e_filing_portal: Optional[str] = Field(None, max_length=255)
    e_filing_instructions: Optional[str] = None
    min_claim_amount: Optional[Decimal] = None
    max_claim_amount: Optional[Decimal] = None
    presiding_officer: Optional[str] = Field(None, max_length=200)
    presiding_officer_designation: Optional[str] = Field(None, max_length=100)
    registrar: Optional[str] = Field(None, max_length=200)
    is_operational: bool = True
    remarks: Optional[str] = None


class CourtResponse(BaseModel):
    """Court response."""

    id: UUID
    organization_id: UUID
    court_code: str
    court_name: str
    court_type: str
    short_name: Optional[str] = None
    state_code: Optional[str] = None
    city: Optional[str] = None
    jurisdiction: str
    e_filing_enabled: bool
    e_filing_portal: Optional[str] = None
    is_operational: bool

    class Config:
        from_attributes = True


@router.post(
    "/courts",
    response_model=CourtResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_court(
    data: CourtCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new court."""
    # Check for duplicate
    existing = await db.execute(
        select(Court).where(
            and_(
                Court.organization_id == data.organization_id,
                Court.court_code == data.court_code,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Court with code {data.court_code} already exists",
        )

    court = Court(
        **data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(court)
    await db.commit()
    await db.refresh(court)
    return court


@router.get("/courts", response_model=List[CourtResponse])
async def list_courts(
    organization_id: UUID = Query(...),
    court_type: Optional[CourtType] = None,
    state_code: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all courts."""
    query = select(Court).where(Court.organization_id == organization_id)
    if court_type:
        query = query.where(Court.court_type == court_type)
    if state_code:
        query = query.where(Court.state_code == state_code)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/courts/{court_id}", response_model=CourtResponse)
async def get_court(
    court_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a court by ID."""
    result = await db.execute(select(Court).where(Court.id == court_id))
    court = result.scalar_one_or_none()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Court not found",
        )
    return court


# =============================================================================
# COURT FEE SLAB SCHEMAS & ENDPOINTS
# =============================================================================


class CourtFeeSlabCreate(BaseModel):
    """Create court fee slab request."""

    organization_id: Optional[UUID] = None
    court_id: Optional[UUID] = None
    court_type: Optional[CourtType] = None
    fee_type: str = Field(..., max_length=50)
    min_claim_amount: Decimal = Decimal("0")
    max_claim_amount: Optional[Decimal] = None
    calculation_type: str = Field(..., max_length=20)  # FIXED, PERCENTAGE, SLAB
    fixed_fee: Optional[Decimal] = None
    percentage_rate: Optional[Decimal] = None
    min_fee: Optional[Decimal] = None
    max_fee: Optional[Decimal] = None
    process_fee: Optional[Decimal] = None
    service_fee: Optional[Decimal] = None
    exemption_available: bool = False
    exemption_conditions: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    notification_reference: Optional[str] = Field(None, max_length=200)
    remarks: Optional[str] = None


class CourtFeeSlabResponse(BaseModel):
    """Court fee slab response."""

    id: UUID
    court_id: Optional[UUID] = None
    court_type: Optional[str] = None
    fee_type: str
    min_claim_amount: float
    max_claim_amount: Optional[float] = None
    calculation_type: str
    fixed_fee: Optional[float] = None
    percentage_rate: Optional[float] = None
    min_fee: Optional[float] = None
    max_fee: Optional[float] = None
    effective_from: date
    effective_to: Optional[date] = None

    class Config:
        from_attributes = True


@router.post(
    "/court-fee-slabs",
    response_model=CourtFeeSlabResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_court_fee_slab(
    data: CourtFeeSlabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new court fee slab."""
    slab = CourtFeeSlab(
        **data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(slab)
    await db.commit()
    await db.refresh(slab)
    return slab


@router.get("/court-fee-slabs", response_model=List[CourtFeeSlabResponse])
async def list_court_fee_slabs(
    court_type: Optional[CourtType] = None,
    fee_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all court fee slabs."""
    query = select(CourtFeeSlab)
    if court_type:
        query = query.where(CourtFeeSlab.court_type == court_type)
    if fee_type:
        query = query.where(CourtFeeSlab.fee_type == fee_type)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/court-fee-slabs/calculate")
async def calculate_court_fee(
    court_type: CourtType = Query(...),
    fee_type: str = Query(...),
    claim_amount: Decimal = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate court fee for given parameters."""
    today = date.today()
    result = await db.execute(
        select(CourtFeeSlab).where(
            and_(
                CourtFeeSlab.court_type == court_type,
                CourtFeeSlab.fee_type == fee_type,
                CourtFeeSlab.min_claim_amount <= claim_amount,
                (CourtFeeSlab.max_claim_amount >= claim_amount)
                | (CourtFeeSlab.max_claim_amount.is_(None)),
                CourtFeeSlab.effective_from <= today,
                (CourtFeeSlab.effective_to >= today)
                | (CourtFeeSlab.effective_to.is_(None)),
            )
        )
    )
    slab = result.scalar_one_or_none()

    if not slab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No applicable fee slab found",
        )

    fee = slab.calculate_fee(claim_amount)
    return {
        "court_type": court_type,
        "fee_type": fee_type,
        "claim_amount": float(claim_amount),
        "calculated_fee": float(fee),
        "slab_id": str(slab.id),
        "calculation_type": slab.calculation_type,
    }


# =============================================================================
# EXPENSE CATEGORY SCHEMAS & ENDPOINTS
# =============================================================================


class ExpenseCategoryCreate(BaseModel):
    """Create expense category request."""

    organization_id: UUID
    category_code: str = Field(..., max_length=50)
    category_name: str = Field(..., max_length=200)
    category_type: ExpenseCategoryType
    gl_account_id: Optional[UUID] = None
    tds_applicable: bool = False
    tds_section: Optional[str] = Field(None, max_length=20)
    tds_rate: Optional[Decimal] = None
    gst_applicable: bool = False
    gst_rate: Optional[Decimal] = None
    hsn_sac_code: Optional[str] = Field(None, max_length=20)
    recoverable_from_borrower: bool = True
    recovery_priority: int = 0
    display_order: int = 0
    description: Optional[str] = None


class ExpenseCategoryMasterResponse(BaseModel):
    """Expense category master response."""

    id: UUID
    organization_id: UUID
    category_code: str
    category_name: str
    category_type: str
    tds_applicable: bool
    tds_section: Optional[str] = None
    tds_rate: Optional[float] = None
    gst_applicable: bool
    gst_rate: Optional[float] = None
    recoverable_from_borrower: bool
    recovery_priority: int
    display_order: int

    class Config:
        from_attributes = True


@router.post(
    "/expense-categories",
    response_model=ExpenseCategoryMasterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense_category(
    data: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new expense category."""
    # Check for duplicate
    existing = await db.execute(
        select(ExpenseCategory).where(
            and_(
                ExpenseCategory.organization_id == data.organization_id,
                ExpenseCategory.category_code == data.category_code,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Expense category with code {data.category_code} already exists",
        )

    category = ExpenseCategory(
        **data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/expense-categories", response_model=List[ExpenseCategoryMasterResponse])
async def list_expense_categories(
    organization_id: UUID = Query(...),
    category_type: Optional[ExpenseCategoryType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all expense categories."""
    query = select(ExpenseCategory).where(
        ExpenseCategory.organization_id == organization_id
    )
    if category_type:
        query = query.where(ExpenseCategory.category_type == category_type)
    query = query.order_by(ExpenseCategory.display_order).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/expense-categories/{category_id}", response_model=ExpenseCategoryMasterResponse
)
async def get_expense_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an expense category by ID."""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found",
        )
    return category
