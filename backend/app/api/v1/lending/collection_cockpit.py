"""Corporate lending collection and reconciliation cockpit endpoint."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.collection_cockpit import CollectionCockpitResponse
from app.services.lending.collection_cockpit_service import CollectionCockpitService

router = APIRouter()


@router.get(
    "",
    response_model=CollectionCockpitResponse,
    response_model_by_alias=True,
    summary="Corporate lending collection cockpit",
    description=(
        "Returns borrower demand, receipt allocation, overdue ageing and "
        "unmatched bank-credit metrics for the caller's organization."
    ),
)
async def get_collection_cockpit(
    period_from: date | None = Query(None, description="Collection period start date"),
    period_to: date | None = Query(None, description="Collection period end date"),
    limit: int = Query(10, ge=1, le=50, description="Rows to return in exception lists"),
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> CollectionCockpitResponse:
    today = date.today()
    start = period_from or today.replace(day=1)
    end = period_to or today

    service = CollectionCockpitService(db)
    return await service.get_cockpit(
        organization_id=current_user.organization_id,
        period_from=start,
        period_to=end,
        limit=limit,
    )
