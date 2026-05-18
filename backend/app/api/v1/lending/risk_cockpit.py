"""Corporate lending credit-risk cockpit endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.risk_cockpit import RiskCockpitResponse
from app.services.lending.risk_cockpit_service import RiskCockpitService

router = APIRouter()


@router.get(
    "",
    response_model=RiskCockpitResponse,
    response_model_by_alias=True,
    summary="Corporate lending credit-risk cockpit",
    description=(
        "Returns SMA/NPA, DPD, provisioning and top risk exposure metrics for "
        "the caller's organization."
    ),
)
async def get_risk_cockpit(
    top_n: int = Query(10, ge=1, le=50, description="Top risky exposures to return"),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> RiskCockpitResponse:
    service = RiskCockpitService(db)
    return await service.get_cockpit(
        organization_id=current_user.organization_id,
        top_n=top_n,
    )
