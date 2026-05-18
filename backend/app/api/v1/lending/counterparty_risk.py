"""Counterparty Risk read endpoints.

Multi-tenant per CLAUDE.md §3.4 — ``get_db_with_tenant`` sets the RLS GUC so
every query is implicitly scoped to the caller's organisation.

Permission gate: ``treasury.risk.view``. Read-only — no idempotency key
required (CLAUDE.md §6.3 applies only to mutations).

All responses are ``CamelSchema``-backed, so the decorator must pass
``response_model_by_alias=True`` (CLAUDE.md §6.x / schemas/base.py).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.counterparty_risk import (
    CounterpartyExposureResponse,
    LimitBreachResponse,
    RatingDistributionResponse,
    SectorConcentrationResponse,
)
from app.services.lending.counterparty_risk_service import CounterpartyRiskService

router = APIRouter()


@router.get(
    "/exposures",
    response_model=CounterpartyExposureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_counterparty_exposures(
    top_n: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> CounterpartyExposureResponse:
    """Top-N counterparties by total exposure with utilisation vs Tier-1 limit."""
    service = CounterpartyRiskService(db)
    data = await service.get_counterparty_exposures(current_user.organization_id, top_n=top_n)
    return CounterpartyExposureResponse.model_validate(data)


@router.get(
    "/sectors",
    response_model=SectorConcentrationResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_sector_concentration(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SectorConcentrationResponse:
    """Loan portfolio exposure grouped by entity industry sector."""
    service = CounterpartyRiskService(db)
    data = await service.get_sector_concentration(current_user.organization_id)
    return SectorConcentrationResponse.model_validate(data)


@router.get(
    "/ratings",
    response_model=RatingDistributionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_rating_distribution(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> RatingDistributionResponse:
    """Loan portfolio exposure grouped by ``entity.internal_rating``."""
    service = CounterpartyRiskService(db)
    data = await service.get_rating_distribution(current_user.organization_id)
    return RatingDistributionResponse.model_validate(data)


@router.get(
    "/breaches",
    response_model=LimitBreachResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_limit_breaches(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LimitBreachResponse:
    """Counterparties at >= 80% single-borrower limit utilisation."""
    service = CounterpartyRiskService(db)
    data = await service.get_limit_breaches(current_user.organization_id)
    return LimitBreachResponse.model_validate(data)
