"""Manual disbursement readiness cockpit endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.disbursement_readiness import DisbursementReadinessResponse
from app.services.lending.disbursement_readiness_service import DisbursementReadinessService

router = APIRouter()


@router.get(
    "",
    response_model=DisbursementReadinessResponse,
    response_model_by_alias=True,
    summary="Manual corporate disbursement readiness cockpit",
    description=(
        "Returns sanctioned-not-disbursed exposure, pre-disbursement condition "
        "blockers and manual disbursement requests for the caller's organization."
    ),
)
async def get_disbursement_readiness(
    limit: int = Query(10, ge=1, le=50, description="Rows to return in exception lists"),
    current_user: User = Depends(RequirePermissions("LMS_DISBURSEMENT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> DisbursementReadinessResponse:
    service = DisbursementReadinessService(db)
    return await service.get_cockpit(
        organization_id=current_user.organization_id,
        limit=limit,
    )
