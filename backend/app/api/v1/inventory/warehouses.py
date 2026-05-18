"""Warehouse API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.inventory.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from app.schemas.base import MessageResponse
from app.services.inventory.warehouse_service import WarehouseService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _to_response(warehouse) -> WarehouseResponse:
    """Convert model to response schema."""
    return WarehouseResponse(
        id=warehouse.id,
        organization_id=warehouse.organization_id,
        unit_id=warehouse.unit_id,
        unit_name=warehouse.unit.name if warehouse.unit else None,
        warehouse_code=warehouse.warehouse_code,
        warehouse_name=warehouse.warehouse_name,
        description=warehouse.description,
        warehouse_type=warehouse.warehouse_type,
        address_line1=warehouse.address_line1,
        address_line2=warehouse.address_line2,
        city=warehouse.city,
        state=warehouse.state,
        pincode=warehouse.pincode,
        contact_person=warehouse.contact_person,
        contact_phone=warehouse.contact_phone,
        contact_email=warehouse.contact_email,
        is_default=warehouse.is_default,
        allow_negative_stock=warehouse.allow_negative_stock,
        is_active=warehouse.is_active,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at,
        created_by=warehouse.created_by,
        updated_by=warehouse.updated_by,
    )


@router.get("", response_model=dict, response_model_by_alias=True)
async def list_warehouses(
    request: Request,
    organization_id: UUID,
    unit_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_VIEW])),
):
    """List warehouses for an organization."""
    service = WarehouseService(db)
    items = await service.list_by_organization(organization_id, unit_id, skip, limit)
    total = await service.count_by_organization(organization_id, unit_id)

    return {
        "items": [_to_response(wh) for wh in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/default", response_model=WarehouseResponse, response_model_by_alias=True)
async def get_default_warehouse(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_VIEW])),
):
    """Get the default warehouse for an organization."""
    service = WarehouseService(db)
    warehouse = await service.get_default(organization_id)
    if not warehouse:
        raise NotFoundException(
            detail="No default warehouse found",
            error_code="NO_DEFAULT_WAREHOUSE_FOUND",
        )
    return _to_response(warehouse)


@router.get("/{id}", response_model=WarehouseResponse, response_model_by_alias=True)
async def get_warehouse(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_VIEW])),
):
    """Get warehouse by ID."""
    service = WarehouseService(db)
    warehouse = await service.get(id)
    if not warehouse:
        raise NotFoundException(detail="Warehouse not found", error_code="WAREHOUSE_NOT_FOUND")
    return _to_response(warehouse)


@router.get("/{id}/stock-summary", response_model=dict, response_model_by_alias=True)
async def get_warehouse_stock_summary(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """Get stock summary for a warehouse."""
    service = WarehouseService(db)
    warehouse = await service.get(id)
    if not warehouse:
        raise NotFoundException(detail="Warehouse not found", error_code="WAREHOUSE_NOT_FOUND")
    summary = await service.get_stock_summary(id)
    return {
        "total_items": summary["total_items"],
        "total_value": float(summary["total_value"]),
    }


@router.post("", response_model=WarehouseResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    request: Request,
    data: WarehouseCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_CREATE])),
):
    """Create a new warehouse."""
    service = WarehouseService(db)
    try:
        warehouse = await service.create(data, created_by=current_user.id)
        return _to_response(warehouse)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put("/{id}", response_model=WarehouseResponse, response_model_by_alias=True)
async def update_warehouse(
    request: Request,
    id: UUID,
    data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_UPDATE])),
):
    """Update a warehouse."""
    service = WarehouseService(db)
    try:
        warehouse = await service.update(id, data, updated_by=current_user.id)
        if not warehouse:
            raise NotFoundException(detail="Warehouse not found", error_code="WAREHOUSE_NOT_FOUND")
        return _to_response(warehouse)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.delete("/{id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_warehouse(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_WAREHOUSE_DELETE])),
):
    """Delete a warehouse."""
    service = WarehouseService(db)
    try:
        success = await service.delete(id, deleted_by=current_user.id)
        if not success:
            raise NotFoundException(detail="Warehouse not found", error_code="WAREHOUSE_NOT_FOUND")
        return MessageResponse(message="Warehouse deleted successfully")
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
