"""Lending dashboard endpoint.

Aggregates the 6 widgets the frontend Lending Dashboard surfaces into
a single payload so the page makes one network round-trip instead of
six. Read-only — no writes, no audit rows.

See CLAUDE.md §4.8 for lending invariants this dashboard exposes
(NPA bucket math, RBI asset classes).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.dashboard import LendingDashboardResponse
from app.services.lending.dashboard_service import LendingDashboardService

router = APIRouter()


@router.get(
    "",
    response_model=LendingDashboardResponse,
    response_model_by_alias=True,  # serialise as camelCase per CamelSchema
    summary="Lending dashboard aggregate",
    description=(
        "Returns corporate lending lifecycle, treasury funding, margin, collection, "
        "cashflow, portfolio quality and approval metrics for the caller's org."
    ),
)
async def get_lending_dashboard(
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> LendingDashboardResponse:
    service = LendingDashboardService(db)
    data = await service.get_dashboard(organization_id=current_user.organization_id)
    return LendingDashboardResponse(
        portfolio_kpis=data.portfolio_kpis,
        lifecycle_pipeline=data.lifecycle_pipeline,
        treasury_funding=data.treasury_funding,
        source_of_funds=data.source_of_funds,
        margin_summary=data.margin_summary,
        collection_summary=data.collection_summary,
        cashflow_buckets=data.cashflow_buckets,
        monthly_disbursements=data.monthly_disbursements,
        portfolio_by_product=data.portfolio_by_product,
        asset_classification=data.asset_classification,
        pending_approvals=data.pending_approvals,
        upcoming_maturities=data.upcoming_maturities,
    )
