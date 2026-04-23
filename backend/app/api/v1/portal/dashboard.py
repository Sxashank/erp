"""Portal Dashboard API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_user
from app.services.portal.dashboard_service import PortalDashboardService

router = APIRouter(prefix="/dashboard", tags=["Portal Dashboard"])


# =============================================================================
# Response Schemas
# =============================================================================


class DashboardSummary(BaseModel):
    """Dashboard summary."""

    total_outstanding: float
    total_overdue: float
    active_loans: int
    next_due_date: Optional[str] = None
    next_due_amount: float


class DashboardResponse(BaseModel):
    """Dashboard response."""

    summary: DashboardSummary
    loans: List[dict]
    upcoming_dues: List[dict]
    recent_payments: List[dict]
    notifications: dict
    service_requests: dict


class LoanSummary(BaseModel):
    """Loan summary."""

    loan_account_id: str
    loan_account_number: str
    product_name: str
    sanctioned_amount: float
    disbursed_amount: float
    total_outstanding: float
    overdue_amount: float
    emi_amount: float
    status: str
    dpd: int


class LoanDetails(BaseModel):
    """Detailed loan information."""

    loan_account_id: str
    loan_account_number: str
    product_name: str
    product_type: str
    sanctioned_amount: float
    disbursed_amount: float
    disbursement_date: Optional[str] = None
    maturity_date: Optional[str] = None
    tenure_months: int
    interest_rate: float
    rate_type: str
    principal_outstanding: float
    interest_outstanding: float
    charges_outstanding: float
    total_outstanding: float
    overdue_amount: float
    emi_amount: float
    emi_date: int
    next_emi_date: Optional[str] = None
    remaining_emis: int
    status: str
    dpd: int


class RepaymentScheduleItem(BaseModel):
    """Repayment schedule item."""

    installment_number: int
    due_date: str
    emi_amount: float
    principal_component: float
    interest_component: float
    opening_balance: float
    closing_balance: float
    status: str
    paid_amount: Optional[float] = None
    paid_date: Optional[str] = None


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

    receipt_id: str
    receipt_number: str
    payment_date: str
    amount: float
    payment_mode: str
    loan_account_number: str
    status: str


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

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Get Dashboard",
)
async def get_dashboard(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get portal dashboard summary."""
    service = PortalDashboardService(db)
    dashboard = await service.get_dashboard(
        user_id=user.id,
        customer_id=user.customer_id,
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
    response_model=List[LoanSummary],
    summary="Get All Loans",
)
async def get_loans(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all loans for the customer."""
    service = PortalDashboardService(db)
    loans = await service.get_loan_summary(user.customer_id)

    return [LoanSummary(**loan) for loan in loans]


@router.get(
    "/loans/{loan_account_id}",
    response_model=LoanDetails,
    summary="Get Loan Details",
)
async def get_loan_details(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a specific loan."""
    service = PortalDashboardService(db)
    loan = await service.get_loan_details(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
    )

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    return LoanDetails(**loan)


@router.get(
    "/loans/{loan_account_id}/schedule",
    response_model=List[RepaymentScheduleItem],
    summary="Get Repayment Schedule",
)
async def get_repayment_schedule(
    loan_account_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get EMI repayment schedule for a loan."""
    service = PortalDashboardService(db)
    schedule = await service.get_repayment_schedule(
        loan_account_id=loan_account_id,
        customer_id=user.customer_id,
    )

    return [RepaymentScheduleItem(**item) for item in schedule]


# =============================================================================
# Upcoming Dues
# =============================================================================


@router.get(
    "/upcoming-dues",
    response_model=List[UpcomingDue],
    summary="Get Upcoming Dues",
)
async def get_upcoming_dues(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    response_model=PaginatedResponse,
    summary="Get Payment History",
)
async def get_payment_history(
    loan_account_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
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
    response_model=PrepaymentQuote,
    summary="Get Prepayment Quote",
)
async def get_prepayment_quote(
    loan_account_id: UUID,
    amount: Decimal,
    prepayment_date: Optional[date] = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
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
    response_model=ForeclosureQuote,
    summary="Get Foreclosure Quote",
)
async def get_foreclosure_quote(
    loan_account_id: UUID,
    foreclosure_date: Optional[date] = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
