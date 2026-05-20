"""Portal Dashboard API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.services.portal.dashboard_service import PortalDashboardService
from app.services.portal.entity_access import get_accessible_entity_ids

router = APIRouter(prefix="/dashboard", tags=["Portal Dashboard"])


# =============================================================================
# Response Schemas
# =============================================================================


class DashboardSummary(BaseModel):
    """Dashboard summary."""

    total_outstanding: float
    total_overdue: float
    active_loans: int
    next_due_date: str | None = None
    next_due_amount: float


class DashboardResponse(BaseModel):
    """Dashboard response."""

    summary: DashboardSummary
    loans: list[dict]
    upcoming_dues: list[dict]
    recent_payments: list[dict]
    notifications: dict
    service_requests: dict


class LoanSummary(BaseModel):
    """Loan summary."""

    id: str
    loan_account_id: str
    loan_account_number: str
    product_name: str
    sanctioned_amount: float
    disbursed_amount: float
    total_outstanding: float
    overdue_amount: float
    overdue_days: int
    emi_amount: float
    status: str
    dpd: int


class LoanDetails(BaseModel):
    """Detailed loan information."""

    id: str
    loan_account_id: str
    loan_account_number: str
    product_name: str
    product_type: str
    sanctioned_amount: float
    disbursed_amount: float
    disbursement_date: str | None = None
    maturity_date: str | None = None
    tenure_months: int
    interest_rate: float
    rate_type: str
    principal_outstanding: float
    interest_outstanding: float
    outstanding_principal: float
    outstanding_interest: float
    charges_outstanding: float
    charges_due: float
    total_outstanding: float
    overdue_amount: float
    emi_amount: float
    emi_date: int
    next_emi_date: str | None = None
    remaining_emis: int
    remaining_tenure: int
    next_emi_amount: float | None = None
    status: str
    dpd: int
    borrower_name: str
    co_borrowers: list[str] = []
    emi_start_date: str | None = None
    emi_end_date: str | None = None
    total_paid: float = 0
    total_principal_paid: float = 0
    total_interest_paid: float = 0
    prepaid_amount: float = 0
    nach_mandate_status: str | None = None


class RepaymentScheduleItem(BaseModel):
    """Repayment schedule item."""

    installment_number: int
    due_date: str
    emi_amount: float
    principal_component: float
    interest_component: float
    principal: float
    interest: float
    opening_balance: float
    closing_balance: float
    status: str
    paid_amount: float | None = None
    paid_date: str | None = None


class UpcomingDue(BaseModel):
    """Upcoming due item."""

    loan_account_id: str
    loan_account_number: str
    due_date: str
    amount: float
    principal: float
    interest: float
    is_overdue: bool
    days_until_due: int


class PaymentHistoryItem(BaseModel):
    """Payment history item."""

    id: str
    receipt_id: str
    receipt_number: str
    payment_date: str
    amount: float
    payment_mode: str
    loan_account_number: str
    status: str
    principal_applied: float = 0
    interest_applied: float = 0
    charges_applied: float = 0
    reference_number: str | None = None


class PrepaymentQuote(BaseModel):
    """Prepayment quote response."""

    loan_account_id: str
    quote_date: str
    prepayment_date: str
    prepayment_amount: float
    prepayment_charges: float
    interest_till_date: float
    total_payable: float
    valid_until: str
    impact: dict


class ForeclosureQuote(BaseModel):
    """Foreclosure quote response."""

    loan_account_id: str
    quote_date: str
    foreclosure_date: str
    principal_outstanding: float
    interest_till_date: float
    foreclosure_charges: float
    other_charges: float
    total_payable: float
    valid_until: str
    breakdown: dict


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get(
    "",
    response_model=DashboardResponse, response_model_by_alias=True,
    summary="Get Dashboard",
)
async def get_dashboard(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get portal dashboard summary."""
    service = PortalDashboardService(db)
    dashboard = await service.get_dashboard(
        user_id=user.id,
        customer_id=user.customer_id,
        entity_ids=await get_accessible_entity_ids(user, db),
    )

    return DashboardResponse(
        summary=DashboardSummary(**dashboard["summary"]),
        loans=dashboard["loans"],
        upcoming_dues=dashboard["upcoming_dues"],
        recent_payments=dashboard["recent_payments"],
        notifications=dashboard["notifications"],
        service_requests=dashboard["service_requests"],
    )


# =============================================================================
# Loan Endpoints
# =============================================================================


@router.get(
    "/loans",
    response_model=list[LoanSummary], response_model_by_alias=True,
    summary="Get All Loans",
)
async def get_loans(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get all loans for the customer."""
    service = PortalDashboardService(db)
    loans = await service.get_loan_summary(
        user.customer_id,
        entity_ids=await get_accessible_entity_ids(user, db),
    )

    return [LoanSummary(**loan) for loan in loans]


@router.get(
    "/loans/{loan_account_id}",
    response_model=LoanDetails, response_model_by_alias=True,
    summary="Get Loan Details",
)
async def get_loan_details(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get detailed information for a specific loan."""
    service = PortalDashboardService(db)
    loan = await service.get_loan_details(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
        entity_ids=await get_accessible_entity_ids(user, db),
    )

    if not loan:
        raise NotFoundException(detail="Loan not found", error_code="LOAN_NOT_FOUND")

    return LoanDetails(**loan)


@router.get(
    "/loans/{loan_account_id}/schedule",
    response_model=list[RepaymentScheduleItem], response_model_by_alias=True,
    summary="Get Repayment Schedule",
)
async def get_repayment_schedule(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get EMI repayment schedule for a loan."""
    service = PortalDashboardService(db)
    schedule = await service.get_repayment_schedule(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
        entity_ids=await get_accessible_entity_ids(user, db),
    )

    return [RepaymentScheduleItem(**item) for item in schedule]


# =============================================================================
# Upcoming Dues
# =============================================================================


@router.get(
    "/upcoming-dues",
    response_model=list[UpcomingDue], response_model_by_alias=True,
    summary="Get Upcoming Dues",
)
async def get_upcoming_dues(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get upcoming EMI dues across all loans."""
    service = PortalDashboardService(db)
    dues = await service.get_upcoming_dues(
        customer_id=user.customer_id,
        days=days,
    )

    return [UpcomingDue(**due) for due in dues]


@router.get(
    "/overdue",
    summary="Get Overdue Summary",
)
async def get_overdue_summary(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get summary of overdue amounts."""
    service = PortalDashboardService(db)
    summary = await service.get_overdue_summary(user.customer_id)

    return summary


# =============================================================================
# Payment History
# =============================================================================


@router.get(
    "/loans/{loan_account_id}/payments",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Payment History",
)
async def get_payment_history(
    loan_account_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get payment history for a specific loan."""
    service = PortalDashboardService(db)
    items, total = await service.get_payment_history(
        customer_id=user.customer_id,
        loan_account_id=loan_account_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        entity_ids=await get_accessible_entity_ids(user, db),
    )

    return PaginatedResponse(
        items=[PaymentHistoryItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


# =============================================================================
# Quotes
# =============================================================================


@router.get(
    "/loans/{loan_account_id}/prepayment-quote",
    response_model=PrepaymentQuote, response_model_by_alias=True,
    summary="Get Prepayment Quote",
)
async def get_prepayment_quote(
    loan_account_id: UUID,
    amount: Decimal,
    prepayment_date: date | None = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Calculate prepayment quote.

    Shows prepayment charges and impact on tenure/EMI.
    """
    service = PortalDashboardService(db)
    quote = await service.get_prepayment_quote(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
        prepayment_amount=amount,
        prepayment_date=prepayment_date,
    )

    return PrepaymentQuote(**quote)


@router.get(
    "/loans/{loan_account_id}/foreclosure-quote",
    response_model=ForeclosureQuote, response_model_by_alias=True,
    summary="Get Foreclosure Quote",
)
async def get_foreclosure_quote(
    loan_account_id: UUID,
    foreclosure_date: date | None = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Calculate foreclosure quote.

    Shows full settlement amount including charges.
    """
    service = PortalDashboardService(db)
    quote = await service.get_foreclosure_quote(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
        foreclosure_date=foreclosure_date,
    )

    return ForeclosureQuote(**quote)


# =============================================================================
# Statement
# =============================================================================


@router.get(
    "/loans/{loan_account_id}/statement",
    summary="Get Account Statement",
)
async def get_account_statement(
    loan_account_id: UUID,
    from_date: date,
    to_date: date,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Generate account statement for a loan."""
    service = PortalDashboardService(db)
    statement = await service.get_account_statement(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
        from_date=from_date,
        to_date=to_date,
    )

    return statement


# =============================================================================
# Borrower-portal: failed / missed / CSV (WI-5)
# =============================================================================
# These routes use the entity-access guard so a borrower cannot see
# schedules for a loan whose entity they don't own. They are appended
# here (rather than in a new router) so the FE's existing /loans/{id}
# URL space stays cohesive.


import csv as _csv
import io as _io
from datetime import date as _date

from fastapi import status as _http_status
from fastapi.responses import StreamingResponse as _StreamingResponse
from sqlalchemy import and_ as _and
from sqlalchemy import or_ as _or
from sqlalchemy import select as _select

from app.models.lending.loan_account import (
    RepaymentSchedule as _RepaymentSchedule,
)
from app.models.lending.loan_account import (
    ScheduleInstallment as _ScheduleInstallment,
)
from app.services.portal.entity_access import (
    assert_loan_access as _assert_loan_access,
)
from app.core.exceptions import NotFoundException


class _ScheduleAlertItem(BaseModel):
    """Failed / missed installment line for the borrower's attention surface."""

    installment_number: int
    due_date: str
    principal_due: float
    interest_due: float
    emi_amount: float
    days_past_due: int
    status: str
    fail_reason: str | None = None
    last_attempt_date: str | None = None


async def _current_schedule(
    db: AsyncSession,
    loan_account_id: UUID,
) -> _RepaymentSchedule | None:
    stmt = (
        _select(_RepaymentSchedule)
        .where(
            _RepaymentSchedule.loan_account_id == loan_account_id,
            _RepaymentSchedule.is_current.is_(True),
            _RepaymentSchedule.deleted_at.is_(None),
        )
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _dpd_for(installment: "_ScheduleInstallment") -> int:
    today = _date.today()
    if installment.due_date >= today:
        return 0
    if (
        installment.status.value
        if hasattr(installment.status, "value")
        else str(installment.status) == "PAID"
    ):
        return 0
    return (today - installment.due_date).days


@router.get(
    "/loans/{loan_account_id}/schedule/failed",
    response_model=list[_ScheduleAlertItem], response_model_by_alias=True,
    summary="List failed / bounced installments for the borrower",
)
async def get_failed_installments(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Return installments whose status indicates collection failure.

    The platform's :class:`InstallmentStatus` enum does not yet carry
    ``FAILED`` / ``BOUNCED`` / ``MISSED`` values — those concepts live
    on receipts / mandate retries. As a first cut we treat
    "overdue + not paid" as the failed/missed surface and degrade
    gracefully when the schedule has no installments yet (a draft loan
    that hasn't been disbursed).
    """
    schedule = await _current_schedule(db, await _verified_loan_id(user, loan_account_id, db))
    if schedule is None:
        return []

    today = _date.today()
    stmt = (
        _select(_ScheduleInstallment)
        .where(
            _ScheduleInstallment.schedule_id == schedule.id,
            _or(
                _ScheduleInstallment.status == "OVERDUE",
                _and(
                    _ScheduleInstallment.due_date < today,
                    _ScheduleInstallment.status.notin_(["PAID", "WAIVED", "WRITTEN_OFF"]),
                ),
            ),
        )
        .order_by(_ScheduleInstallment.due_date.asc())
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        _ScheduleAlertItem(
            installment_number=r.installment_number,
            due_date=r.due_date.isoformat(),
            principal_due=float(r.principal_amount),
            interest_due=float(r.interest_amount),
            emi_amount=float(r.emi_amount),
            days_past_due=_dpd_for(r),
            status=str(r.status.value if hasattr(r.status, "value") else r.status),
            fail_reason=None,
            last_attempt_date=None,
        )
        for r in rows
    ]


@router.get(
    "/loans/{loan_account_id}/schedule/missed",
    response_model=list[_ScheduleAlertItem], response_model_by_alias=True,
    summary="List missed installments for the borrower",
)
async def get_missed_installments(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Alias surface for "missed" — currently same query as ``/failed``
    filtered to past-due unpaid lines. Splits once the platform models
    NACH bounce vs no-show separately.
    """
    schedule = await _current_schedule(db, await _verified_loan_id(user, loan_account_id, db))
    if schedule is None:
        return []

    today = _date.today()
    stmt = (
        _select(_ScheduleInstallment)
        .where(
            _ScheduleInstallment.schedule_id == schedule.id,
            _ScheduleInstallment.due_date < today,
            _ScheduleInstallment.status.notin_(["PAID", "WAIVED", "WRITTEN_OFF", "OVERDUE"]),
        )
        .order_by(_ScheduleInstallment.due_date.asc())
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        _ScheduleAlertItem(
            installment_number=r.installment_number,
            due_date=r.due_date.isoformat(),
            principal_due=float(r.principal_amount),
            interest_due=float(r.interest_amount),
            emi_amount=float(r.emi_amount),
            days_past_due=_dpd_for(r),
            status=str(r.status.value if hasattr(r.status, "value") else r.status),
            fail_reason=None,
            last_attempt_date=None,
        )
        for r in rows
    ]


@router.get(
    "/loans/{loan_account_id}/schedule.csv",
    summary="Download the full repayment schedule as CSV",
)
async def get_schedule_csv(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> _StreamingResponse:
    """Stream the full repayment schedule as CSV."""
    loan = await _assert_loan_access(user, loan_account_id, db)
    schedule = await _current_schedule(db, loan_account_id)
    rows: list = []
    if schedule is not None:
        stmt = (
            _select(_ScheduleInstallment)
            .where(_ScheduleInstallment.schedule_id == schedule.id)
            .order_by(_ScheduleInstallment.installment_number.asc())
        )
        rows = list((await db.execute(stmt)).scalars().all())

    buf = _io.StringIO()
    writer = _csv.writer(buf)
    writer.writerow(
        [
            "Installment#",
            "Due Date",
            "Principal Due",
            "Interest Due",
            "EMI",
            "Opening Balance",
            "Closing Balance",
            "Status",
            "Paid Amount",
            "Paid Date",
        ]
    )
    for r in rows:
        paid_amount = (r.principal_paid or 0) + (r.interest_paid or 0)
        writer.writerow(
            [
                r.installment_number,
                r.due_date.isoformat() if r.due_date else "",
                str(r.principal_amount),
                str(r.interest_amount),
                str(r.emi_amount),
                str(r.opening_balance),
                str(r.closing_balance),
                str(r.status.value if hasattr(r.status, "value") else r.status),
                str(paid_amount),
                r.paid_date.isoformat() if r.paid_date else "",
            ]
        )

    filename = f"Schedule-{loan.loan_account_number}.csv"
    return _StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        status_code=_http_status.HTTP_200_OK,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _verified_loan_id(
    user,
    loan_account_id: UUID,
    db: AsyncSession,
) -> UUID:
    """Used inside the failed/missed handlers to enforce entity access
    without rebuilding the loan-account ORM object more than once."""
    loan = await _assert_loan_access(user, loan_account_id, db)
    return loan.id
