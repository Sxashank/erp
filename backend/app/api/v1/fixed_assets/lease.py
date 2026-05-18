"""Lease Accounting API endpoints (Ind AS 116)."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.models.fixed_assets.lease import LeaseType, LeaseStatus
from app.schemas.fixed_assets.lease import (
    LeaseCreate,
    LeaseUpdate,
    LeaseResponse,
    LeaseListResponse,
    LeaseModificationCreate,
    LeaseActivate,
    LeaseTerminate,
    LeasePaymentRecord,
    LeasePaymentScheduleResponse,
    LeaseSummaryResponse,
    LeaseDisclosureResponse,
    InterestPostingRequest,
    DepreciationPostingRequest,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.lease_service import LeaseService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _lease_to_response(lease) -> LeaseResponse:
    """Convert lease model to response schema."""
    return LeaseResponse(
        id=lease.id,
        organization_id=lease.organization_id,
        lease_number=lease.lease_number,
        lease_name=lease.lease_name,
        lease_type=lease.lease_type,
        asset_type=lease.asset_type,
        status=lease.status,
        lessor_id=lease.lessor_id,
        lessor_name=lease.lessor_name or (lease.lessor.name if lease.lessor else None),
        asset_description=lease.asset_description,
        asset_location_id=lease.asset_location_id,
        location_name=lease.location.name if lease.location else None,
        department_id=lease.department_id,
        department_name=lease.department.name if lease.department else None,
        commencement_date=lease.commencement_date,
        end_date=lease.end_date,
        lease_term_months=lease.lease_term_months,
        remaining_term_months=lease.remaining_term_months,
        payment_frequency=lease.payment_frequency,
        payment_amount=lease.payment_amount,
        payment_day=lease.payment_day,
        payment_in_advance=lease.payment_in_advance,
        has_escalation=lease.has_escalation,
        escalation_percentage=lease.escalation_percentage,
        security_deposit=lease.security_deposit,
        has_renewal_option=lease.has_renewal_option,
        renewal_term_months=lease.renewal_term_months,
        has_purchase_option=lease.has_purchase_option,
        purchase_option_price=lease.purchase_option_price,
        has_termination_option=lease.has_termination_option,
        discount_rate=lease.discount_rate,
        initial_direct_costs=lease.initial_direct_costs,
        estimated_restoration_cost=lease.estimated_restoration_cost,
        roua_initial_value=lease.roua_initial_value,
        roua_accumulated_depreciation=lease.roua_accumulated_depreciation,
        roua_carrying_value=lease.roua_carrying_value,
        lease_liability_initial=lease.lease_liability_initial,
        lease_liability_current=lease.lease_liability_current,
        lease_liability_current_portion=lease.lease_liability_current_portion,
        lease_liability_non_current=lease.lease_liability_non_current,
        total_lease_payments=lease.total_lease_payments,
        total_interest_expense=lease.total_interest_expense,
        interest_expense_ytd=lease.interest_expense_ytd,
        depreciation_expense_ytd=lease.depreciation_expense_ytd,
        last_payment_date=lease.last_payment_date,
        next_payment_date=lease.next_payment_date,
        is_short_term=lease.is_short_term,
        is_low_value=lease.is_low_value,
        is_modified=lease.is_modified,
        notes=lease.notes,
        is_active=True,
        created_at=lease.created_at,
        updated_at=lease.updated_at,
        created_by=lease.created_by,
        updated_by=lease.updated_by,
    )


def _schedule_to_response(schedule) -> LeasePaymentScheduleResponse:
    """Convert schedule model to response schema."""
    return LeasePaymentScheduleResponse(
        id=schedule.id,
        lease_id=schedule.lease_id,
        payment_number=schedule.payment_number,
        payment_date=schedule.payment_date,
        financial_year=schedule.financial_year,
        opening_liability=schedule.opening_liability,
        payment_amount=schedule.payment_amount,
        interest_component=schedule.interest_component,
        principal_component=schedule.principal_component,
        closing_liability=schedule.closing_liability,
        depreciation_amount=schedule.depreciation_amount,
        roua_carrying_value=schedule.roua_carrying_value,
        is_paid=schedule.is_paid,
        paid_date=schedule.paid_date,
        paid_amount=schedule.paid_amount,
        payment_reference=schedule.payment_reference,
        interest_posted=schedule.interest_posted,
        depreciation_posted=schedule.depreciation_posted,
        variance_amount=schedule.variance_amount,
        is_active=True,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        created_by=schedule.created_by,
        updated_by=schedule.updated_by,
    )


# ============================================
# Lease CRUD Endpoints
# ============================================

@router.get("", response_model=LeaseListResponse, response_model_by_alias=True)
async def list_leases(
    request: Request,
    organization_id: UUID,
    status: Optional[LeaseStatus] = None,
    lease_type: Optional[LeaseType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List leases with filters."""
    service = LeaseService(db)
    leases, total = await service.list_leases(
        organization_id, status, lease_type, skip, limit
    )

    return LeaseListResponse(
        items=[_lease_to_response(l) for l in leases],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{lease_id}", response_model=LeaseResponse, response_model_by_alias=True)
async def get_lease(
    request: Request,
    lease_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get lease by ID."""
    service = LeaseService(db)
    lease = await service.get_lease(lease_id)
    if not lease:
        raise NotFoundException(detail="Lease not found", error_code="LEASE_NOT_FOUND")
    return _lease_to_response(lease)


@router.post("", response_model=LeaseResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_lease(
    request: Request,
    data: LeaseCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new lease.

    This will:
    - Calculate initial ROUA and lease liability using NPV
    - Generate the payment amortization schedule
    - Set up current/non-current liability bifurcation
    """
    service = LeaseService(db)
    try:
        lease = await service.create_lease(data, created_by=current_user.id)
        return _lease_to_response(lease)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put("/{lease_id}", response_model=LeaseResponse, response_model_by_alias=True)
async def update_lease(
    request: Request,
    lease_id: UUID,
    data: LeaseUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update lease details (limited fields).

    For term/payment changes, use the modify endpoint instead.
    """
    service = LeaseService(db)
    try:
        lease = await service.update_lease(lease_id, data, updated_by=current_user.id)
        if not lease:
            raise NotFoundException(detail="Lease not found", error_code="LEASE_NOT_FOUND")
        return _lease_to_response(lease)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Lifecycle Endpoints
# ============================================

@router.post("/{lease_id}/activate", response_model=LeaseResponse, response_model_by_alias=True)
async def activate_lease(
    request: Request,
    lease_id: UUID,
    data: Optional[LeaseActivate] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CAPITALIZE])),
):
    """Activate a lease (start recognition).

    This will:
    - Create initial recognition GL entries (DR: ROUA, CR: Lease Liability)
    - Set the first payment due date
    - Change status to ACTIVE
    """
    service = LeaseService(db)
    try:
        lease = await service.activate_lease(
            lease_id, data or LeaseActivate(), activated_by=current_user.id
        )
        return _lease_to_response(lease)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{lease_id}/terminate", response_model=LeaseResponse, response_model_by_alias=True)
async def terminate_lease(
    request: Request,
    lease_id: UUID,
    data: LeaseTerminate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_DISPOSE])),
):
    """Early terminate a lease.

    This will:
    - Calculate gain/loss on termination
    - Write off remaining ROUA and liability
    - Record settlement payment if any
    - Create termination GL entries
    """
    service = LeaseService(db)
    try:
        lease = await service.terminate_lease(
            lease_id, data, terminated_by=current_user.id
        )
        return _lease_to_response(lease)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{lease_id}/modify", response_model=LeaseResponse, response_model_by_alias=True)
async def modify_lease(
    request: Request,
    lease_id: UUID,
    data: LeaseModificationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Modify lease terms (requires remeasurement).

    This will:
    - Remeasure lease liability using new terms and revised discount rate
    - Adjust ROUA accordingly
    - Regenerate payment schedule
    - Record modification details for audit
    """
    service = LeaseService(db)
    try:
        lease = await service.modify_lease(
            lease_id, data, modified_by=current_user.id
        )
        return _lease_to_response(lease)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Payment Schedule Endpoints
# ============================================

@router.get("/{lease_id}/schedule", response_model=List[LeasePaymentScheduleResponse], response_model_by_alias=True)
async def get_payment_schedule(
    request: Request,
    lease_id: UUID,
    unpaid_only: bool = Query(False, description="Show only unpaid installments"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get payment amortization schedule for a lease.

    Shows principal/interest breakdown for each payment.
    """
    service = LeaseService(db)
    schedules = await service.get_payment_schedule(lease_id, unpaid_only)
    return [_schedule_to_response(s) for s in schedules]


@router.post("/schedule/{schedule_id}/record-payment", response_model=LeasePaymentScheduleResponse, response_model_by_alias=True)
async def record_payment(
    request: Request,
    schedule_id: UUID,
    data: LeasePaymentRecord,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Record a lease payment.

    This will:
    - Mark the schedule entry as paid
    - Update lease liability balance
    - Update current/non-current bifurcation
    - Record any variance between scheduled and actual amount
    """
    service = LeaseService(db)
    try:
        schedule = await service.record_payment(
            schedule_id, data, recorded_by=current_user.id
        )
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/upcoming-payments", response_model=List[dict], response_model_by_alias=True)
async def get_upcoming_payments(
    request: Request,
    organization_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Days to look ahead"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get upcoming lease payments due within specified days."""
    service = LeaseService(db)
    return await service.get_upcoming_payments(organization_id, days)


# ============================================
# Interest and Depreciation Posting
# ============================================

@router.post("/post-interest", response_model=dict, response_model_by_alias=True)
async def post_interest(
    request: Request,
    data: InterestPostingRequest,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Post interest expense for lease liabilities.

    Creates GL entries for interest expense on lease liabilities
    for the specified period.
    """
    service = LeaseService(db)
    result = await service.post_interest(
        organization_id,
        data.period_from,
        data.period_to,
        data.lease_ids,
        posted_by=current_user.id,
    )
    return result


@router.post("/post-depreciation", response_model=dict, response_model_by_alias=True)
async def post_roua_depreciation(
    request: Request,
    data: DepreciationPostingRequest,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Post ROUA depreciation for leases.

    Creates GL entries for Right-of-Use Asset depreciation
    for the specified period.
    """
    service = LeaseService(db)
    result = await service.post_roua_depreciation(
        organization_id,
        data.depreciation_period,
        data.lease_ids,
        posted_by=current_user.id,
    )
    return result


# ============================================
# Reports and Analytics
# ============================================

@router.get("/summary", response_model=LeaseSummaryResponse, response_model_by_alias=True)
async def get_lease_summary(
    request: Request,
    organization_id: UUID,
    as_on_date: Optional[date] = Query(None, description="As on date (defaults to today)"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get lease portfolio summary.

    Provides:
    - Total ROUA and lease liability values
    - Current vs non-current bifurcation
    - YTD interest and depreciation expense
    - Breakdown by asset type and lease type
    - Upcoming payment obligations
    """
    service = LeaseService(db)
    return await service.get_lease_summary(organization_id, as_on_date)


@router.get("/disclosure", response_model=LeaseDisclosureResponse, response_model_by_alias=True)
async def get_disclosure_report(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Generate Ind AS 116 disclosure report.

    Provides all information required for financial statement disclosure:
    - Maturity analysis of lease liabilities
    - Expense breakdown (depreciation, interest, short-term, low-value)
    - Additions and modifications during the year
    - Weighted average discount rate
    """
    service = LeaseService(db)
    return await service.get_disclosure_report(organization_id, financial_year)
