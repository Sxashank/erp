"""Asset Category API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.asset_category import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryResponse,
    AssetCategoryTreeResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse
from app.services.fixed_assets.asset_category_service import AssetCategoryService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _to_response(category) -> AssetCategoryResponse:
    """Convert model to response schema."""
    return AssetCategoryResponse(
        id=category.id,
        organization_id=category.organization_id,
        category_code=category.category_code,
        category_name=category.category_name,
        description=category.description,
        parent_category_id=category.parent_category_id,
        parent_category_name=category.parent_category.category_name if category.parent_category else None,
        asset_type=category.asset_type,
        depreciation_method=category.depreciation_method,
        useful_life_years=category.useful_life_years,
        residual_value_pct=category.residual_value_pct,
        depreciation_rate_slm=category.depreciation_rate_slm,
        depreciation_rate_wdv=category.depreciation_rate_wdv,
        it_act_rate=category.it_act_rate,
        it_act_block=category.it_act_block,
        capitalization_threshold=category.capitalization_threshold,
        gl_asset_account_id=category.gl_asset_account_id,
        gl_asset_account_name=category.gl_asset_account.name if category.gl_asset_account else None,
        gl_accum_dep_account_id=category.gl_accum_dep_account_id,
        gl_accum_dep_account_name=category.gl_accum_dep_account.name if category.gl_accum_dep_account else None,
        gl_dep_expense_account_id=category.gl_dep_expense_account_id,
        gl_dep_expense_account_name=category.gl_dep_expense_account.name if category.gl_dep_expense_account else None,
        gl_disposal_gain_account_id=category.gl_disposal_gain_account_id,
        gl_disposal_loss_account_id=category.gl_disposal_loss_account_id,
        gl_revaluation_reserve_account_id=category.gl_revaluation_reserve_account_id,
        gl_impairment_account_id=category.gl_impairment_account_id,
        requires_insurance=category.requires_insurance,
        requires_amc=category.requires_amc,
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
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_VIEW])),
):
    """List asset categories for an organization."""
    service = AssetCategoryService(db)
    items = await service.list_by_organization(organization_id, skip, limit)
    total = await service.count_by_organization(organization_id)

    return {
        "items": [_to_response(cat) for cat in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/tree", response_model=List[AssetCategoryTreeResponse], response_model_by_alias=True)
async def get_category_tree(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_VIEW])),
):
    """Get asset category hierarchy as tree."""
    service = AssetCategoryService(db)
    return await service.get_tree(organization_id)


@router.get("/{id}", response_model=AssetCategoryResponse, response_model_by_alias=True)
async def get_category(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_VIEW])),
):
    """Get asset category by ID."""
    service = AssetCategoryService(db)
    category = await service.get(id)
    if not category:
        raise NotFoundException(detail="Asset category not found", error_code="ASSET_CATEGORY_NOT_FOUND")
    return _to_response(category)


@router.post("", response_model=AssetCategoryResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    data: AssetCategoryCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_CREATE])),
):
    """Create a new asset category."""
    service = AssetCategoryService(db)
    try:
        category = await service.create(data, created_by=current_user.id)
        return _to_response(category)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put("/{id}", response_model=AssetCategoryResponse, response_model_by_alias=True)
async def update_category(
    request: Request,
    id: UUID,
    data: AssetCategoryUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_UPDATE])),
):
    """Update an asset category."""
    service = AssetCategoryService(db)
    try:
        category = await service.update(id, data, updated_by=current_user.id)
        if not category:
            raise NotFoundException(
                detail="Asset category not found",
                error_code="ASSET_CATEGORY_NOT_FOUND",
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
    _: None = Depends(PermissionChecker([Permissions.FA_CATEGORY_DELETE])),
):
    """Delete an asset category."""
    service = AssetCategoryService(db)
    try:
        success = await service.delete(id, deleted_by=current_user.id)
        if not success:
            raise NotFoundException(
                detail="Asset category not found",
                error_code="ASSET_CATEGORY_NOT_FOUND",
            )
        return MessageResponse(message="Asset category deleted successfully")
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
