"""MIS Reports API endpoints."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.reports.mis import (
    AllModulesReportResponse,
    BranchPerformanceResponse,
    CollectionReportResponse,
    DashboardSummary,
    DelinquencyReportResponse,
    DisbursementReportResponse,
    PortfolioSummaryResponse,
    ProfitabilityReportResponse,
    ReportCatalogResponse,
    ReportRunCreate,
    ReportRunResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
)
from app.services.reports.mis_report_service import MISReportService

router = APIRouter()


def _default_as_of(value: date | None) -> date:
    return value or date.today()


def _default_period(from_date: date | None, to_date: date | None) -> tuple[date, date]:
    end = to_date or date.today()
    start = from_date or end - timedelta(days=30)
    return start, end


@router.get(
    "/catalog",
    response_model=ReportCatalogResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_report_catalog(
    db: AsyncSession = Depends(get_db_with_tenant),
) -> ReportCatalogResponse:
    """Return the enterprise MIS report catalog."""
    return await MISReportService(db).get_report_catalog()


@router.get(
    "/dashboard",
    response_model=DashboardSummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_dashboard_metrics(
    as_of_date: date | None = Query(default=None, alias="asOfDate", description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    """Get key metrics for the MIS command center."""
    return await MISReportService(db).get_dashboard_metrics(
        org_id=current_user.organization_id,
        as_of_date=_default_as_of(as_of_date),
    )


@router.get(
    "/all-modules",
    response_model=AllModulesReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_all_modules_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    as_of_date: date | None = Query(default=None, alias="asOfDate", description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AllModulesReportResponse:
    """Generate a live MIS summary across every ERP module."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_all_modules_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
        as_of_date=_default_as_of(as_of_date),
    )


@router.get(
    "/portfolio-summary",
    response_model=PortfolioSummaryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_portfolio_summary(
    as_of_date: date | None = Query(default=None, alias="asOfDate", description="Report date"),
    unit_id: UUID | None = Query(default=None, alias="unitId", description="Filter by unit/branch"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> PortfolioSummaryResponse:
    """Generate a live portfolio summary report."""
    return await MISReportService(db).generate_portfolio_summary(
        org_id=current_user.organization_id,
        as_of_date=_default_as_of(as_of_date),
        unit_id=unit_id,
    )


@router.get(
    "/disbursement",
    response_model=DisbursementReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_disbursement_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    group_by: str = Query(
        default="PRODUCT", alias="groupBy", description="PRODUCT, CHANNEL, BRANCH"
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DisbursementReportResponse:
    """Generate a live disbursement report."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_disbursement_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
        group_by=group_by,
    )


@router.get(
    "/collection",
    response_model=CollectionReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_collection_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> CollectionReportResponse:
    """Generate a live collection report."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_collection_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
    )


@router.get(
    "/delinquency",
    response_model=DelinquencyReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_delinquency_report(
    as_of_date: date | None = Query(default=None, alias="asOfDate", description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DelinquencyReportResponse:
    """Generate a live delinquency report."""
    return await MISReportService(db).generate_delinquency_report(
        org_id=current_user.organization_id,
        as_of_date=_default_as_of(as_of_date),
    )


@router.get(
    "/profitability",
    response_model=ProfitabilityReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_profitability_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ProfitabilityReportResponse:
    """Generate a live profitability report."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_profitability_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
    )


@router.get(
    "/branch-performance",
    response_model=BranchPerformanceResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_branch_performance_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> BranchPerformanceResponse:
    """Generate a live branch performance report."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_branch_performance_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
    )


@router.get(
    "/employee-productivity",
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def get_employee_productivity_report(
    from_date: date | None = Query(default=None, alias="fromDate", description="Start date"),
    to_date: date | None = Query(default=None, alias="toDate", description="End date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate a live employee productivity summary."""
    start, end = _default_period(from_date, to_date)
    return await MISReportService(db).generate_employee_productivity_report(
        org_id=current_user.organization_id,
        from_date=start,
        to_date=end,
    )


@router.get(
    "/runs",
    response_model=list[ReportRunResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def list_report_runs(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> list[ReportRunResponse]:
    """List generated report run history."""
    return await MISReportService(db).list_runs(current_user.organization_id, limit=limit)


@router.post(
    "/runs",
    response_model=ReportRunResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def create_report_run(
    payload: ReportRunCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ReportRunResponse:
    """Create a manual report run record and generate the report payload."""
    return await MISReportService(db).create_run(
        org_id=current_user.organization_id,
        user_id=current_user.id,
        report_code=payload.report_code,
        export_format=payload.export_format,
        parameters=payload.parameters,
    )


@router.get(
    "/schedules",
    response_model=list[ReportScheduleResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def list_report_schedules(
    active_only: bool = Query(default=False, alias="activeOnly"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> list[ReportScheduleResponse]:
    """List manual-first report schedules."""
    return await MISReportService(db).list_schedules(
        current_user.organization_id,
        active_only=active_only,
    )


@router.post(
    "/schedules",
    response_model=ReportScheduleResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def create_report_schedule(
    payload: ReportScheduleCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ReportScheduleResponse:
    """Create a manual-download report schedule."""
    return await MISReportService(db).create_schedule(
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.post(
    "/schedules/{schedule_id}/run-now",
    response_model=ReportRunResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("FIN_REPORT_VIEW"))],
)
async def run_schedule_now(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ReportRunResponse:
    """Run a scheduled report immediately and store run history."""
    return await MISReportService(db).run_schedule_now(
        org_id=current_user.organization_id,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )
