"""SFC borrower-portal borrower-visible products."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.schemas.portal.application import ProductListItem
from app.services.portal.application_service import PortalApplicationService

router = APIRouter(prefix="/products", tags=["Borrower Portal · Products"])


@router.get(
    "",
    response_model=list[ProductListItem],
    response_model_by_alias=True,
    summary="List scheme-eligible products for the logged-in borrower",
)
async def list_products(
    entity_id: UUID | None = Query(None, alias="entityId"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> list[ProductListItem]:
    service = PortalApplicationService(db)
    return await service.list_products(portal_user=user, entity_id=entity_id)
