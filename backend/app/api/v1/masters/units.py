"""Unit API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.masters.unit_service import UnitService
from app.schemas.masters.unit import (
    UnitCreate,
    UnitUpdate,
    UnitResponse,
    UnitTreeResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UnitResponse], response_model_by_alias=True)
async def list_units(
    organization_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of units.
    Requires MASTER_UNIT_VIEW permission.
    """
    unit_service = UnitService(db)
    skip = (page - 1) * page_size
    units, total = await unit_service.get_all(organization_id, skip, page_size, include_inactive)

    items = [_unit_to_response(u) for u in units]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=UnitResponse, response_model_by_alias=True)
async def create_unit(
    data: UnitCreate,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new unit.
    Requires MASTER_UNIT_CREATE permission.
    """
    unit_service = UnitService(db)
    unit = await unit_service.create(data, current_user.id)

    return _unit_to_response(unit)


@router.get("/tree", response_model=List[UnitTreeResponse], response_model_by_alias=True)
async def get_unit_tree(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get unit hierarchy tree for an organization.
    Requires MASTER_UNIT_VIEW permission.
    """
    unit_service = UnitService(db)
    # Service now returns pre-built tree as dictionaries
    tree = await unit_service.get_tree(organization_id)
    return tree


@router.get("/{unit_id}", response_model=UnitResponse, response_model_by_alias=True)
async def get_unit(
    unit_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get unit by ID.
    Requires MASTER_UNIT_VIEW permission.
    """
    unit_service = UnitService(db)
    unit = await unit_service.get(unit_id)

    return _unit_to_response(unit)


@router.put("/{unit_id}", response_model=UnitResponse, response_model_by_alias=True)
async def update_unit(
    unit_id: UUID,
    data: UnitUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing unit.
    Requires MASTER_UNIT_UPDATE permission.
    """
    unit_service = UnitService(db)
    unit = await unit_service.update(unit_id, data, current_user.id)

    return _unit_to_response(unit)


@router.delete("/{unit_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_unit(
    unit_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a unit.
    Requires MASTER_UNIT_DELETE permission.
    """
    unit_service = UnitService(db)
    await unit_service.delete(unit_id, current_user.id)

    return MessageResponse(message="Unit deleted successfully")


@router.get("/{unit_id}/children", response_model=List[UnitResponse], response_model_by_alias=True)
async def get_unit_children(
    unit_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_UNIT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get child units of a unit.
    Requires MASTER_UNIT_VIEW permission.
    """
    unit_service = UnitService(db)
    children = await unit_service.get_children(unit_id)

    return [_unit_to_response(u) for u in children]


def _unit_to_response(unit) -> UnitResponse:
    """Convert Unit model to UnitResponse."""
    return UnitResponse(
        id=unit.id,
        code=unit.code,
        name=unit.name,
        short_name=unit.short_name,
        description=unit.description,
        unit_type=unit.unit_type,
        organization_id=unit.organization_id,
        parent_unit_id=unit.parent_unit_id,
        level=unit.level,
        path=unit.path,
        is_separate_accounting=unit.is_separate_accounting,
        gstin=unit.gstin,
        gst_state_code=unit.gst_state_code,
        address_line1=unit.address_line1,
        address_line2=unit.address_line2,
        city=unit.city,
        district=unit.district,
        state_code=unit.state_code,
        pincode=unit.pincode,
        country=unit.country,
        phone=unit.phone,
        email=unit.email,
        manager_name=unit.manager_name,
        status=unit.status,
        is_head_office=unit.is_head_office,
        created_at=unit.created_at,
        updated_at=unit.updated_at,
        is_active=unit.is_active,
        organization_name=unit.organization.name if unit.organization else None,
        parent_unit_name=unit.parent_unit.name if unit.parent_unit else None,
    )


def _build_unit_tree(unit) -> UnitTreeResponse:
    """Build unit tree response recursively."""
    return UnitTreeResponse(
        id=unit.id,
        code=unit.code,
        name=unit.name,
        unit_type=unit.unit_type,
        level=unit.level,
        is_head_office=unit.is_head_office,
        status=unit.status,
        children=[_build_unit_tree(child) for child in unit.child_units if child.is_active],
    )
