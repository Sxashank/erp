"""
MIS Reports API Endpoints
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
from app.services.reports.mis_report_service import MISReportService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get key metrics for MIS dashboard
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = MISReportService(db)
    return await service.get_dashboard_metrics(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


@router.get("/portfolio-summary")
async def get_portfolio_summary(
    as_of_date: date = Query(default=None, description="Report date"),
    unit_id: Optional[UUID] = Query(default=None, description="Filter by unit/branch"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Portfolio Summary Report
    Overview of entire loan portfolio
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = MISReportService(db)
    return await service.generate_portfolio_summary(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
        unit_id=unit_id,
    )


@router.get("/disbursement")
async def get_disbursement_report(
    from_date: date = Query(default=None, description="Start date"),
    to_date: date = Query(default=None, description="End date"),
    group_by: str = Query(default="PRODUCT", description="Group by: PRODUCT, CHANNEL, BRANCH"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Disbursement Report
    Shows disbursements over a period
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = MISReportService(db)
    return await service.generate_disbursement_report(
        org_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
    )


@router.get("/collection")
async def get_collection_report(
    from_date: date = Query(default=None, description="Start date"),
    to_date: date = Query(default=None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Collection Report
    Shows collection performance
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = MISReportService(db)
    return await service.generate_collection_report(
        org_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/delinquency")
async def get_delinquency_report(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Delinquency Report
    Shows overdue position and trends
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = MISReportService(db)
    return await service.generate_delinquency_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


@router.get("/profitability")
async def get_profitability_report(
    from_date: date = Query(default=None, description="Start date"),
    to_date: date = Query(default=None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Profitability Report
    Shows income, expenses and margins
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = MISReportService(db)
    return await service.generate_profitability_report(
        org_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/branch-performance")
async def get_branch_performance_report(
    from_date: date = Query(default=None, description="Start date"),
    to_date: date = Query(default=None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Branch Performance Report
    Compares performance across branches
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = MISReportService(db)
    return await service.generate_branch_performance_report(
        org_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/employee-productivity")
async def get_employee_productivity_report(
    from_date: date = Query(default=None, description="Start date"),
    to_date: date = Query(default=None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Employee Productivity Report
    Shows sales and collection staff performance
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = MISReportService(db)
    return await service.generate_employee_productivity_report(
        org_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )
