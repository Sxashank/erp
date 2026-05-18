"""Item Category API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.inventory.item_category import (
    ItemCategoryCreate,
    ItemCategoryUpdate,
    ItemCategoryResponse,
    ItemCategoryTreeResponse,
)
from app.schemas.base import MessageResponse
from app.services.inventory.item_category_service import ItemCategoryService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _to_response(category) -> ItemCategoryResponse:
    """Convert model to response schema."""
    return ItemCategoryResponse(
        id=category.id,
        organization_id=category.organization_id,
        category_code=category.category_code,
        category_name=category.category_name,
        description=category.description,
        parent_category_id=category.parent_category_id,
        parent_category_name=category.parent_category.category_name if category.parent_category else None,
        is_stockable=category.is_stockable,
        requires_serial_number=category.requires_serial_number,
        requires_batch_number=category.requires_batch_number,
        gl_inventory_account_id=category.gl_inventory_account_id,
        gl_expense_account_id=category.gl_expense_account_id,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
        created_by=category.created_by,
        updated_by=category.updated_by,
    )


@router.get("", response_model=dict, response_model_by_alias=True)
async def list_categories(
    request: Request,
    organization_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_VIEW])),
):
    """List item categories for an organization."""
    service = ItemCategoryService(db)
    items = await service.list_by_organization(organization_id, skip, limit)
    total = await service.count_by_organization(organization_id)

    return {
        "items": [_to_response(cat) for cat in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/tree", response_model=List[ItemCategoryTreeResponse], response_model_by_alias=True)
async def get_category_tree(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_VIEW])),
):
    """Get item category hierarchy as tree."""
    service = ItemCategoryService(db)
    return await service.get_tree(organization_id)


@router.get("/{id}", response_model=ItemCategoryResponse, response_model_by_alias=True)
async def get_category(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_VIEW])),
):
    """Get item category by ID."""
    service = ItemCategoryService(db)
    category = await service.get(id)
    if not category:
        raise NotFoundException(detail="Item category not found", error_code="ITEM_CATEGORY_NOT_FOUND")
    return _to_response(category)


@router.post("", response_model=ItemCategoryResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    data: ItemCategoryCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_CREATE])),
):
    """Create a new item category."""
    service = ItemCategoryService(db)
    try:
        category = await service.create(data, created_by=current_user.id)
        return _to_response(category)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put("/{id}", response_model=ItemCategoryResponse, response_model_by_alias=True)
async def update_category(
    request: Request,
    id: UUID,
    data: ItemCategoryUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_UPDATE])),
):
    """Update an item category."""
    service = ItemCategoryService(db)
    try:
        category = await service.update(id, data, updated_by=current_user.id)
        if not category:
            raise NotFoundException(
                detail="Item category not found",
                error_code="ITEM_CATEGORY_NOT_FOUND",
            )
        return _to_response(category)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.delete("/{id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_category(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_CATEGORY_DELETE])),
):
    """Delete an item category."""
    service = ItemCategoryService(db)
    try:
        success = await service.delete(id, deleted_by=current_user.id)
        if not success:
            raise NotFoundException(
                detail="Item category not found",
                error_code="ITEM_CATEGORY_NOT_FOUND",
            )
        return MessageResponse(message="Item category deleted successfully")
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
