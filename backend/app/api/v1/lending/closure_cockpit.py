"""Manual loan closure and release cockpit endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.closure_cockpit import ClosureCockpitResponse
from app.services.lending.closure_cockpit_service import ClosureCockpitService

router = APIRouter()


@router.get(
    "",
    response_model=ClosureCockpitResponse,
    response_model_by_alias=True,
    summary="Manual loan closure and security release cockpit",
    description=(
        "Returns loan closure-ready accounts, closed accounts pending security/NOC "
        "release and recent manual closure receipts for the caller's organization."
    ),
)
async def get_closure_cockpit(
    limit: int = Query(10, ge=1, le=50, description="Rows to return in exception lists"),
    recent_days: int = Query(30, ge=1, le=180, description="Closure receipt lookback window"),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> ClosureCockpitResponse:
    service = ClosureCockpitService(db)
    return await service.get_cockpit(
        organization_id=current_user.organization_id,
        limit=limit,
        recent_days=recent_days,
    )
