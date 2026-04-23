"""Legal Analytics API endpoints."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.services.legal.analytics_service import LegalAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Legal Analytics"])


# =============================================================================
# Response Schemas
# =============================================================================


class DashboardMetrics(BaseModel):
    """Legal dashboard metrics."""

    total_legal_cases: int
    active_cases: int
    cases_this_month: int
    cases_closed_this_month: int

    total_claim_amount: float
    total_recovered: float
    recovery_rate: float

    pending_notices: int
    overdue_notices: int
    upcoming_hearings: int
    upcoming_auctions: int

    expenses_this_month: float
    expenses_pending_approval: int
    expenses_pending_payment: float

    sarfaesi_cases: int
    drt_cases: int
    arbitration_cases: int


class PortfolioStatus(BaseModel):
    """Portfolio legal status breakdown."""

    total_npa_accounts: int
    total_npa_amount: float

    under_notice: int
    under_notice_amount: float

    sarfaesi_initiated: int
    sarfaesi_amount: float

    possession_taken: int
    possession_amount: float

    auction_scheduled: int
    auction_amount: float

    drt_filed: int
    drt_amount: float

    lok_adalat: int
    lok_adalat_amount: float

    written_off: int
    written_off_amount: float


class ForumWiseAnalysis(BaseModel):
    """Forum-wise case analysis."""

    forum_type: str
    forum_name: str
    total_cases: int
    active_cases: int
    disposed_cases: int
    claim_amount: float
    recovered_amount: float
    recovery_rate: float
    avg_case_duration_days: Optional[int] = None
    success_rate: float


class DeadlineItem(BaseModel):
    """Upcoming deadline item."""

    deadline_type: str
    deadline_date: date
    days_remaining: int
    legal_case_id: UUID
    case_number: str
    customer_name: str
    loan_account_number: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW


class RecoveryEfficiency(BaseModel):
    """Recovery efficiency metrics."""

    period: str
    cases_initiated: int
    cases_resolved: int
    amount_claimed: float
    amount_recovered: float
    recovery_rate: float
    avg_resolution_days: int
    cost_of_recovery: float
    net_recovery: float
    roi_percentage: float


class AgingBucket(BaseModel):
    """Aging bucket details."""

    bucket: str
    case_count: int
    claim_amount: float
    recovered_amount: float
    pending_amount: float


class AgingAnalysis(BaseModel):
    """Case aging analysis."""

    buckets: List[AgingBucket]
    total_cases: int
    total_claim: float
    total_recovered: float
    avg_age_days: int


class AdvocatePerformanceSummary(BaseModel):
    """Advocate performance summary."""

    advocate_id: UUID
    advocate_name: str
    law_firm_name: Optional[str] = None
    total_cases: int
    active_cases: int
    cases_won: int
    cases_lost: int
    success_rate: float
    total_claim: float
    total_recovered: float
    recovery_rate: float
    avg_case_duration: int
    hearings_attended: int
    total_fees_paid: float


class NoticeAnalytics(BaseModel):
    """Notice analytics."""

    notice_type: str
    total_issued: int
    delivered: int
    delivery_rate: float
    responded: int
    response_rate: float
    complied: int
    compliance_rate: float
    avg_delivery_days: float


class MonthlyTrend(BaseModel):
    """Monthly trend data."""

    month: str
    cases_filed: int
    cases_closed: int
    amount_claimed: float
    amount_recovered: float
    expenses: float
    net_recovery: float


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get(
    "/dashboard",
    response_model=DashboardMetrics,
    summary="Legal Dashboard",
)
async def get_dashboard(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get legal module dashboard metrics."""
    service = LegalAnalyticsService(db)
    metrics = await service.get_dashboard_metrics(organization_id)
    return DashboardMetrics(**metrics)


@router.get(
    "/portfolio",
    response_model=PortfolioStatus,
    summary="Portfolio Legal Status",
)
async def get_portfolio_status(
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get portfolio-level legal status breakdown."""
    service = LegalAnalyticsService(db)
    status = await service.get_portfolio_status(
        organization_id=organization_id,
        as_of_date=as_of_date,
    )
    return PortfolioStatus(**status)


# =============================================================================
# Deadline & Calendar
# =============================================================================


@router.get(
    "/deadlines",
    response_model=List[DeadlineItem],
    summary="Upcoming Deadlines",
)
async def get_upcoming_deadlines(
    organization_id: UUID,
    days: int = Query(30, ge=1, le=90),
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """
    Get upcoming legal deadlines.

    Includes:
    - Statutory period expiries
    - Hearing dates
    - Appeal deadlines
    - Auction dates
    - Limitation periods
    """
    service = LegalAnalyticsService(db)
    deadlines = await service.get_upcoming_deadlines(
        organization_id=organization_id,
        days=days,
        priority=priority,
    )
    return [DeadlineItem(**d) for d in deadlines]


@router.get(
    "/calendar",
    summary="Legal Calendar",
)
async def get_legal_calendar(
    organization_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get legal calendar with hearings, auctions, and deadlines."""
    service = LegalAnalyticsService(db)
    calendar = await service.get_legal_calendar(
        organization_id=organization_id,
        month=month,
        year=year,
    )
    return calendar


# =============================================================================
# Recovery Analysis
# =============================================================================


@router.get(
    "/recovery",
    response_model=List[RecoveryEfficiency],
    summary="Recovery Efficiency",
)
async def get_recovery_efficiency(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    group_by: str = Query("month", description="month, quarter, year"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get recovery efficiency metrics by period."""
    service = LegalAnalyticsService(db)
    efficiency = await service.get_recovery_efficiency(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
    )
    return [RecoveryEfficiency(**e) for e in efficiency]


@router.get(
    "/recovery/forum-wise",
    response_model=List[ForumWiseAnalysis],
    summary="Forum-wise Analysis",
)
async def get_forum_wise_analysis(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get forum-wise case analysis and recovery metrics."""
    service = LegalAnalyticsService(db)
    analysis = await service.get_forum_wise_analysis(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [ForumWiseAnalysis(**a) for a in analysis]


# =============================================================================
# Aging Analysis
# =============================================================================


@router.get(
    "/aging",
    response_model=AgingAnalysis,
    summary="Case Aging Analysis",
)
async def get_aging_analysis(
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """
    Get case aging analysis.

    Buckets: 0-30, 31-60, 61-90, 91-180, 181-365, >365 days
    """
    service = LegalAnalyticsService(db)
    aging = await service.get_aging_analysis(
        organization_id=organization_id,
        as_of_date=as_of_date,
    )
    return AgingAnalysis(**aging)


# =============================================================================
# Advocate Performance
# =============================================================================


@router.get(
    "/advocate-performance",
    response_model=List[AdvocatePerformanceSummary],
    summary="Advocate Performance",
)
async def get_advocate_performance(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    law_firm_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get advocate performance summary."""
    service = LegalAnalyticsService(db)
    performance = await service.get_advocate_performance_summary(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        law_firm_id=law_firm_id,
    )
    return [AdvocatePerformanceSummary(**p) for p in performance]


# =============================================================================
# Notice Analytics
# =============================================================================


@router.get(
    "/notices",
    response_model=List[NoticeAnalytics],
    summary="Notice Analytics",
)
async def get_notice_analytics(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get notice type-wise analytics."""
    service = LegalAnalyticsService(db)
    analytics = await service.get_notice_analytics(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [NoticeAnalytics(**a) for a in analytics]


# =============================================================================
# Trends
# =============================================================================


@router.get(
    "/trends",
    response_model=List[MonthlyTrend],
    summary="Monthly Trends",
)
async def get_monthly_trends(
    organization_id: UUID,
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """Get monthly legal trends for the past N months."""
    service = LegalAnalyticsService(db)
    trends = await service.get_monthly_trends(
        organization_id=organization_id,
        months=months,
    )
    return [MonthlyTrend(**t) for t in trends]


# =============================================================================
# Reports
# =============================================================================


@router.get(
    "/reports/mis",
    summary="Legal MIS Report",
)
async def get_mis_report(
    organization_id: UUID,
    from_date: date,
    to_date: date,
    report_format: str = Query("json", description="json, csv, excel"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """
    Generate Legal MIS Report.

    Includes:
    - Case summary by forum type
    - Recovery summary
    - Expense summary
    - Advocate-wise performance
    - Notice effectiveness
    """
    service = LegalAnalyticsService(db)
    report = await service.generate_mis_report(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        report_format=report_format,
    )
    return report


@router.get(
    "/reports/rbi-submission",
    summary="RBI Submission Data",
)
async def get_rbi_submission_data(
    organization_id: UUID,
    quarter: str = Query(..., description="Q1, Q2, Q3, Q4"),
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """
    Get data for RBI quarterly submission.

    Includes NPA movement, recovery data, write-off details.
    """
    service = LegalAnalyticsService(db)
    data = await service.get_rbi_submission_data(
        organization_id=organization_id,
        quarter=quarter,
        year=year,
    )
    return data


@router.get(
    "/reports/sarfaesi-progress",
    summary="SARFAESI Progress Report",
)
async def get_sarfaesi_progress_report(
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.analytics.read")),
):
    """
    Get SARFAESI progress report.

    Stage-wise breakdown of all SARFAESI cases.
    """
    service = LegalAnalyticsService(db)
    report = await service.get_sarfaesi_progress_report(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )
    return report
