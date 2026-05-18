"""Account Group API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.account_group_service import AccountGroupService
from app.schemas.finance.account_group import (
    AccountGroupCreate,
    AccountGroupUpdate,
    AccountGroupResponse,
    AccountGroupTreeResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AccountGroupResponse], response_model_by_alias=True)
async def list_account_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of account groups.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountGroupService(db)
    skip = (page - 1) * page_size
    groups, total = await service.get_all(current_user.organization_id, skip, page_size, include_inactive)

    items = [_group_to_response(g) for g in groups]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=AccountGroupResponse, response_model_by_alias=True)
async def create_account_group(
    data: AccountGroupCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new account group.
    Requires FIN_COA_CREATE permission.
    """
    service = AccountGroupService(db)
    group = await service.create(data, current_user.id)

    return _group_to_response(group)


@router.get("/tree", response_model=List[AccountGroupTreeResponse], response_model_by_alias=True)
async def get_account_group_tree(
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get account group hierarchy tree.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountGroupService(db)
    tree = await service.get_tree(current_user.organization_id)
    return tree


@router.get("/{group_id}", response_model=AccountGroupResponse, response_model_by_alias=True)
async def get_account_group(
    group_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get account group by ID.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountGroupService(db)
    group = await service.get(group_id)

    return _group_to_response(group)


@router.put("/{group_id}", response_model=AccountGroupResponse, response_model_by_alias=True)
async def update_account_group(
    group_id: UUID,
    data: AccountGroupUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an account group.
    Requires FIN_COA_UPDATE permission.
    """
    service = AccountGroupService(db)
    group = await service.update(group_id, data, current_user.id)

    return _group_to_response(group)


@router.delete("/{group_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_account_group(
    group_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete an account group.
    Requires FIN_COA_DELETE permission.
    """
    service = AccountGroupService(db)
    await service.delete(group_id, current_user.id)

    return MessageResponse(message="Account group deleted successfully")


@router.get("/{group_id}/children", response_model=List[AccountGroupResponse], response_model_by_alias=True)
async def get_account_group_children(
    group_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get child account groups.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountGroupService(db)
    children = await service.get_children(group_id)

    return [_group_to_response(g) for g in children]


def _group_to_response(group) -> AccountGroupResponse:
    """Convert AccountGroup model to response."""
    return AccountGroupResponse(
        id=group.id,
        code=group.code,
        name=group.name,
        nature=group.nature,
        parent_group_id=group.parent_group_id,
        parent_group_name=group.parent_group.name if group.parent_group else None,
        level=group.level,
        path=group.path,
        sequence=group.sequence,
        description=group.description,
        is_system=group.is_system,
        organization_id=group.organization_id,
        account_count=getattr(group, "account_count", 0),
        created_at=group.created_at,
        updated_at=group.updated_at,
        is_active=group.is_active,
    )
