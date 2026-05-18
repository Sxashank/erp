"""Borrower-visible fund-utilization category endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_with_tenant
from app.api.v1.portal.auth import get_portal_user
from app.schemas.portal.application import UtilizationCategoryListItem
from app.services.portal.application_service import PortalApplicationService

router = APIRouter(
    prefix="/utilization-categories",
    tags=["Borrower Portal · Utilization Categories"],
)


@router.get(
    "",
    response_model=list[UtilizationCategoryListItem],
    response_model_by_alias=True,
    summary="List borrower-visible fund-utilization categories",
)
async def list_utilization_categories(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> list[UtilizationCategoryListItem]:
    service = PortalApplicationService(db)
    return await service.list_utilization_categories(portal_user=user)
