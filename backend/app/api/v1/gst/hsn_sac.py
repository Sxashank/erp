"""HSN/SAC API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.gst.hsn_sac_service import HSNSACService
from app.schemas.gst.hsn_sac import HSNSACCreate, HSNSACUpdate, HSNSACResponse
from app.schemas.base import PaginatedResponse
from app.core.constants import HSNSACType

router = APIRouter()


def _to_response(hsn_sac) -> HSNSACResponse:
    """Convert model to response."""
    return HSNSACResponse(
        id=hsn_sac.id,
        code=hsn_sac.code,
        description=hsn_sac.description,
        hsn_sac_type=hsn_sac.hsn_sac_type,
        chapter=hsn_sac.chapter,
        section=hsn_sac.section,
        gst_rate_id=hsn_sac.gst_rate_id,
        gst_rate_code=hsn_sac.gst_rate.code if hsn_sac.gst_rate else None,
        gst_rate_name=hsn_sac.gst_rate.name if hsn_sac.gst_rate else None,
        gst_rate_value=hsn_sac.gst_rate.rate if hsn_sac.gst_rate else None,
        unit_of_measurement=hsn_sac.unit_of_measurement,
        created_at=hsn_sac.created_at,
        updated_at=hsn_sac.updated_at,
        is_active=hsn_sac.is_active,
    )


@router.get("", response_model=PaginatedResponse[HSNSACResponse], response_model_by_alias=True)
async def search_hsn_sac(
    search: str = Query("", description="Search by code or description"),
    hsn_sac_type: Optional[HSNSACType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Search HSN/SAC codes."""
    service = HSNSACService(db)
    skip = (page - 1) * page_size
    items, total = await service.search(search, hsn_sac_type, skip, page_size)
    responses = [_to_response(item) for item in items]
    return PaginatedResponse.create(responses, total, page, page_size)


@router.post("", response_model=HSNSACResponse, response_model_by_alias=True)
async def create_hsn_sac(
    data: HSNSACCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new HSN/SAC code."""
    service = HSNSACService(db)
    hsn_sac = await service.create(data, current_user.id)
    return _to_response(hsn_sac)


@router.get("/{hsn_sac_id}", response_model=HSNSACResponse, response_model_by_alias=True)
async def get_hsn_sac(
    hsn_sac_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get HSN/SAC by ID."""
    service = HSNSACService(db)
    hsn_sac = await service.get(hsn_sac_id)
    return _to_response(hsn_sac)


@router.put("/{hsn_sac_id}", response_model=HSNSACResponse, response_model_by_alias=True)
async def update_hsn_sac(
    hsn_sac_id: UUID,
    data: HSNSACUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update an HSN/SAC code."""
    service = HSNSACService(db)
    hsn_sac = await service.update(hsn_sac_id, data, current_user.id)
    return _to_response(hsn_sac)


@router.delete("/{hsn_sac_id}")
async def delete_hsn_sac(
    hsn_sac_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete an HSN/SAC code."""
    service = HSNSACService(db)
    await service.delete(hsn_sac_id, current_user.id)
    return {"message": "HSN/SAC code deleted successfully"}
