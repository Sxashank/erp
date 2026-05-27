"""Treasury investment portfolio API endpoints.

Routes are tenant-scoped via ``get_db_with_tenant`` (CLAUDE.md §3.4), gated
by per-action permissions (CLAUDE.md §8.2), and the two mutating endpoints
declare ``Idempotency-Key`` per CLAUDE.md §6.3. Wire format is camelCase —
all responses use ``response_model_by_alias=True``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.lending.investment import (
    InvestmentCreateRequest,
    InvestmentListResponse,
    InvestmentMatureRequest,
    InvestmentMaturityResponse,
    InvestmentResponse,
    PortfolioSummaryResponse,
)
from app.services.lending.investment_service import InvestmentService

router = APIRouter()


# =============================================================================
# Create / Mature  (mutations — Idempotency-Key required, §6.3)
# =============================================================================


@router.post(
    "",
    response_model=InvestmentResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_investment(
    data: InvestmentCreateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> InvestmentResponse:
    """Record a new investment holding for the current organisation.

    Requires `Idempotency-Key` header (CLAUDE.md §6.3) — a financial
    mutation. Returns the freshly-persisted record with generated
    ``investment_number``.
    """
    if not idempotency_key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )

    async with db.begin():
        service = InvestmentService(db)
        inv = await service.create_investment(data, current_user)
    await db.refresh(inv)
    return InvestmentResponse.model_validate(inv)


@router.post(
    "/{investment_id}/mature",
    response_model=InvestmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def mark_investment_matured(
    investment_id: UUID,
    data: InvestmentMatureRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> InvestmentResponse:
    """Mark an investment as MATURED (default) or SOLD (when sale_value is set).

    Books realised gain/loss against purchase value. GL posting is deferred
    until the treasury GL contract is wired in `InvestmentService.mark_matured`.
    """
    if not idempotency_key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )

    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )

    async with db.begin():
        service = InvestmentService(db)
        inv = await service.mark_matured(
            current_user.organization_id, investment_id, data, current_user
        )
    await db.refresh(inv)
    return InvestmentResponse.model_validate(inv)


# =============================================================================
# Read
# =============================================================================


@router.get(
    "",
    response_model=InvestmentListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_investments(
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> InvestmentListResponse:
    """Paginated list of investments for the current organisation."""
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )

    skip = (page - 1) * page_size
    service = InvestmentService(db)
    items, total = await service.list_investments(
        organization_id=current_user.organization_id,
        status=status_filter,
        category=category,
        skip=skip,
        limit=page_size,
    )
    item_models = [InvestmentResponse.model_validate(i) for i in items]
    return InvestmentListResponse.create(item_models, total, page, page_size)


@router.get(
    "/portfolio/summary",
    response_model=PortfolioSummaryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> PortfolioSummaryResponse:
    """Aggregate portfolio metrics for the dashboard cards."""
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    service = InvestmentService(db)
    return await service.get_portfolio_summary(current_user.organization_id)


@router.get(
    "/maturity",
    response_model=InvestmentMaturityResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_maturity_schedule(
    months: int = Query(12, ge=1, le=120),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> InvestmentMaturityResponse:
    """Maturity ladder for the next ``months`` months (default 12)."""
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    service = InvestmentService(db)
    return await service.get_maturity_schedule(current_user.organization_id, months_ahead=months)


@router.get(
    "/{investment_id}",
    response_model=InvestmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_investment(
    investment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> InvestmentResponse:
    """Get a single investment by id, scoped to the caller's organisation."""
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    service = InvestmentService(db)
    inv = await service.get_investment(current_user.organization_id, investment_id)
    return InvestmentResponse.model_validate(inv)
