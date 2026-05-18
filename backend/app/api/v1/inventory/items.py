"""Item Master API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.inventory.item_master import (
    ItemMasterCreate,
    ItemMasterUpdate,
    ItemMasterResponse,
)
from app.schemas.base import MessageResponse
from app.services.inventory.item_service import ItemMasterService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _to_response(item) -> ItemMasterResponse:
    """Convert model to response schema."""
    return ItemMasterResponse(
        id=item.id,
        organization_id=item.organization_id,
        category_id=item.category_id,
        category_name=item.category.category_name if item.category else None,
        item_code=item.item_code,
        item_name=item.item_name,
        description=item.description,
        item_type=item.item_type,
        uom=item.uom,
        brand=item.brand,
        model_number=item.model_number,
        sku=item.sku,
        barcode=item.barcode,
        is_stockable=item.is_stockable,
        requires_serial_number=item.requires_serial_number,
        requires_batch_number=item.requires_batch_number,
        shelf_life_days=item.shelf_life_days,
        minimum_stock_level=item.minimum_stock_level,
        maximum_stock_level=item.maximum_stock_level,
        reorder_quantity=item.reorder_quantity,
        standard_cost=item.standard_cost,
        selling_price=item.selling_price,
        hsn_code=item.hsn_code,
        gst_rate=item.gst_rate,
        gl_inventory_account_id=item.gl_inventory_account_id,
        gl_expense_account_id=item.gl_expense_account_id,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
        created_by=item.created_by,
        updated_by=item.updated_by,
    )


@router.get("", response_model=dict, response_model_by_alias=True)
async def list_items(
    request: Request,
    organization_id: UUID,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_VIEW])),
):
    """List items for an organization."""
    service = ItemMasterService(db)
    items = await service.list_by_organization(
        organization_id, category_id, search, skip, limit
    )
    total = await service.count_by_organization(organization_id, category_id, search)

    return {
        "items": [_to_response(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/low-stock", response_model=List[dict], response_model_by_alias=True)
async def get_low_stock_items(
    request: Request,
    organization_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_VIEW])),
):
    """Get items with stock below minimum level."""
    service = ItemMasterService(db)
    items = await service.get_low_stock_items(organization_id, skip, limit)
    return [
        {
            "item": _to_response(item_data["item"]),
            "current_stock": float(item_data["current_stock"]),
            "minimum_level": float(item_data["minimum_level"]),
            "shortfall": float(item_data["shortfall"]),
        }
        for item_data in items
    ]


@router.get("/{id}", response_model=ItemMasterResponse, response_model_by_alias=True)
async def get_item(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_VIEW])),
):
    """Get item by ID."""
    service = ItemMasterService(db)
    item = await service.get(id)
    if not item:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
    return _to_response(item)


@router.get("/{id}/stock-summary", response_model=dict, response_model_by_alias=True)
async def get_item_stock_summary(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """Get stock summary for an item across all warehouses."""
    service = ItemMasterService(db)
    item = await service.get(id)
    if not item:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
    summary = await service.get_stock_summary(id)
    return {
        "total_on_hand": float(summary["total_on_hand"]),
        "total_reserved": float(summary["total_reserved"]),
        "available_quantity": float(summary["available_quantity"]),
        "total_value": float(summary["total_value"]),
    }


@router.post("", response_model=ItemMasterResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_item(
    request: Request,
    data: ItemMasterCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_CREATE])),
):
    """Create a new item."""
    service = ItemMasterService(db)
    try:
        item = await service.create(data, created_by=current_user.id)
        return _to_response(item)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put("/{id}", response_model=ItemMasterResponse, response_model_by_alias=True)
async def update_item(
    request: Request,
    id: UUID,
    data: ItemMasterUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_UPDATE])),
):
    """Update an item."""
    service = ItemMasterService(db)
    try:
        item = await service.update(id, data, updated_by=current_user.id)
        if not item:
            raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
        return _to_response(item)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.delete("/{id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_item(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_ITEM_DELETE])),
):
    """Delete an item."""
    service = ItemMasterService(db)
    try:
        success = await service.delete(id, deleted_by=current_user.id)
        if not success:
            raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
        return MessageResponse(message="Item deleted successfully")
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
