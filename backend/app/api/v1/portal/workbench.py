"""Scheme-portal workbench endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_with_tenant
from app.api.v1.portal.auth import get_portal_user
from app.schemas.portal.workbench import PortalWorkbenchResponse
from app.services.portal.workbench_service import PortalWorkbenchService

router = APIRouter(prefix="/workbench", tags=["Scheme Portal · Workbench"])


@router.get(
    "",
    response_model=PortalWorkbenchResponse,
    response_model_by_alias=True,
    summary="Borrower workbench summary",
)
async def get_workbench(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> PortalWorkbenchResponse:
    service = PortalWorkbenchService(db)
    return await service.get_workbench(user)
