"""Dashboard API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.dashboard.dashboard import (
    DashboardSummary,
    APSummary,
    ARSummary,
    CashFlowSummary,
    TrendData,
    RecentActivity,
    PendingApprovalItem,
)
from app.services.dashboard.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary, response_model_by_alias=True,
    summary="Get dashboard summary",
)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    """Get overall dashboard summary with KPIs."""
    service = DashboardService(db)
    return await service.get_dashboard_summary(current_user.organization_id)


@router.get(
    "/ap-summary",
    response_model=APSummary, response_model_by_alias=True,
    summary="Get Accounts Payable summary",
)
async def get_ap_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> APSummary:
    """Get Accounts Payable (AP) summary including outstanding, overdue, and aging analysis."""
    service = DashboardService(db)
    return await service.get_ap_summary(current_user.organization_id)


@router.get(
    "/ar-summary",
    response_model=ARSummary, response_model_by_alias=True,
    summary="Get Accounts Receivable summary",
)
async def get_ar_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ARSummary:
    """Get Accounts Receivable (AR) summary including outstanding, overdue, and aging analysis."""
    service = DashboardService(db)
    return await service.get_ar_summary(current_user.organization_id)


@router.get(
    "/cashflow",
    response_model=CashFlowSummary, response_model_by_alias=True,
    summary="Get cash flow summary",
)
async def get_cashflow_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> CashFlowSummary:
    """Get cash flow summary including receipts, payments, and bank balances."""
    service = DashboardService(db)
    return await service.get_cashflow_summary(current_user.organization_id)


@router.get(
    "/trends",
    response_model=TrendData, response_model_by_alias=True,
    summary="Get trend data for charts",
)
async def get_trends(
    months: int = Query(6, ge=1, le=12, description="Number of months"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TrendData:
    """Get trend data for revenue, expenses, collections, and payments."""
    service = DashboardService(db)
    return await service.get_trends(current_user.organization_id, months)


@router.get(
    "/recent-activity",
    response_model=List[RecentActivity], response_model_by_alias=True,
    summary="Get recent activity",
)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of items"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> List[RecentActivity]:
    """Get recent transaction activity (payments, invoices, bills)."""
    service = DashboardService(db)
    return await service.get_recent_activity(current_user.organization_id, limit)


@router.get(
    "/pending-approvals",
    response_model=List[PendingApprovalItem], response_model_by_alias=True,
    summary="Get pending approvals",
)
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> List[PendingApprovalItem]:
    """Get pending approval items for the current user."""
    service = DashboardService(db)
    return await service.get_pending_approvals(current_user.organization_id, current_user.id)
