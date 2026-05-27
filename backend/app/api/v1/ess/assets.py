"""ESS asset API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.schemas.ess.operations import ESSAssignedAssetsResponse
from app.services.ess.asset_service import ESSAssetService

router = APIRouter(prefix="/assets", tags=["ESS Assets"])


@router.get("", response_model=ESSAssignedAssetsResponse, response_model_by_alias=True)
async def list_assigned_assets(
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """List fixed assets assigned to the authenticated employee."""
    service = ESSAssetService(session)
    return await service.list_assigned_assets(ess_context.employee_id)
