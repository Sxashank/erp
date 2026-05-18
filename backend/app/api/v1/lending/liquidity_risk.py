"""Liquidity Risk API — LCR / NSFR / cash-flow ladder / funding concentration.

Read-only endpoints under ``/api/v1/lending/liquidity-risk``. All gated on the
``treasury.liquidity.view`` permission. Multi-tenant — the service reads the
organisation from the authenticated user, RLS enforces the rest.

See CLAUDE.md §4.9 (Treasury / ALM / Risk) and §6.3 (auth + permission +
tenant-scoped DB session on every authenticated route).
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.liquidity_risk import (
    CashflowLadderSnapshot,
    FundingConcentrationSnapshot,
    LCRSnapshot,
    NSFRSnapshot,
)
from app.services.lending.liquidity_risk_service import LiquidityRiskService

router = APIRouter()


@router.get(
    "/lcr",
    response_model=LCRSnapshot,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_lcr(
    as_of_date: date | None = Query(
        None,
        description=(
            "Reporting date for the LCR snapshot. Defaults to today (IST). "
            "Outflows / inflows are projected over the next 30 calendar days."
        ),
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LCRSnapshot:
    """Compute the Liquidity Coverage Ratio snapshot."""
    service = LiquidityRiskService(db)
    return await service.compute_lcr(current_user.organization_id, as_of_date)


@router.get(
    "/nsfr",
    response_model=NSFRSnapshot,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_nsfr(
    as_of_date: date | None = Query(
        None,
        description="Reporting date for the NSFR snapshot. Defaults to today (IST).",
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> NSFRSnapshot:
    """Compute the Net Stable Funding Ratio snapshot."""
    service = LiquidityRiskService(db)
    return await service.compute_nsfr(current_user.organization_id, as_of_date)


@router.get(
    "/cashflow-ladder",
    response_model=CashflowLadderSnapshot,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_cashflow_ladder(
    as_of_date: date | None = Query(
        None,
        description="Reporting date for the cash-flow ladder. Defaults to today (IST).",
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> CashflowLadderSnapshot:
    """Compute the RBI ALM cash-flow ladder."""
    service = LiquidityRiskService(db)
    return await service.get_cashflow_ladder(current_user.organization_id, as_of_date)


@router.get(
    "/funding-concentration",
    response_model=FundingConcentrationSnapshot,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_funding_concentration(
    top_n: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of top lenders to return (ranked by outstanding borrowing).",
    ),
    as_of_date: date | None = Query(
        None,
        description="Reporting date. Defaults to today (IST).",
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FundingConcentrationSnapshot:
    """Top-N lender funding concentration."""
    service = LiquidityRiskService(db)
    return await service.get_funding_concentration(current_user.organization_id, top_n, as_of_date)
