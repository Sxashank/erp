"""Role and Permission API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.auth.role_service import RoleService
from app.schemas.auth.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RolePermissionUpdate,
    PermissionResponse,
    PermissionGrouped,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


# Permission endpoints
@router.get("/permissions", response_model=List[PermissionResponse], response_model_by_alias=True)
async def list_permissions(
    current_user: User = Depends(RequirePermissions("ROLE_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all permissions.
    Requires ROLE_VIEW permission.
    """
    role_service = RoleService(db)
    permissions, _ = await role_service.get_permissions()

    return [
        PermissionResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            module=p.module,
            resource=p.resource,
            action=p.action,
            created_at=p.created_at,
            updated_at=p.updated_at,
            is_active=p.is_active,
        )
        for p in permissions
    ]


@router.get("/permissions/grouped", response_model=List[PermissionGrouped], response_model_by_alias=True)
async def list_permissions_grouped(
    current_user: User = Depends(RequirePermissions("ROLE_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all permissions grouped by module.
    Requires ROLE_VIEW permission.
    """
    role_service = RoleService(db)
    grouped = await role_service.get_permissions_grouped()

    return [
        PermissionGrouped(
            module=module,
            permissions=[
                PermissionResponse(
                    id=p.id,
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    module=p.module,
                    resource=p.resource,
                    action=p.action,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    is_active=p.is_active,
                )
                for p in perms
            ],
        )
        for module, perms in grouped.items()
    ]


# Role endpoints
@router.get("", response_model=List[RoleListResponse], response_model_by_alias=True)
async def list_roles(
    current_user: User = Depends(RequirePermissions("ROLE_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all roles with counts.
    Requires ROLE_VIEW permission.
    """
    role_service = RoleService(db)
    roles_data, _ = await role_service.get_roles()

    return [
        RoleListResponse(
            id=rd["role"].id,
            code=rd["role"].code,
            name=rd["role"].name,
            description=rd["role"].description,
            is_system_role=rd["role"].is_system_role,
            is_default=rd["role"].is_default,
            permission_count=rd["permission_count"],
            user_count=rd["user_count"],
        )
        for rd in roles_data
    ]


@router.post("", response_model=RoleResponse, response_model_by_alias=True)
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(RequirePermissions("ROLE_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new role.
    Requires ROLE_CREATE permission.
    """
    role_service = RoleService(db)
    role = await role_service.create_role(data, current_user.id)

    return await _role_to_response(role)


@router.get("/{role_id}", response_model=RoleResponse, response_model_by_alias=True)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(RequirePermissions("ROLE_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get role by ID with permissions.
    Requires ROLE_VIEW permission.
    """
    role_service = RoleService(db)
    role = await role_service.get_role(role_id)

    return await _role_to_response(role)


@router.put("/{role_id}", response_model=RoleResponse, response_model_by_alias=True)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: User = Depends(RequirePermissions("ROLE_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing role.
    Requires ROLE_UPDATE permission.
    """
    role_service = RoleService(db)
    role = await role_service.update_role(role_id, data, current_user.id)

    return await _role_to_response(role)


@router.delete("/{role_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(RequirePermissions("ROLE_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a role.
    Requires ROLE_DELETE permission.
    """
    role_service = RoleService(db)
    await role_service.delete_role(role_id, current_user.id)

    return MessageResponse(message="Role deleted successfully")


@router.put("/{role_id}/permissions", response_model=RoleResponse, response_model_by_alias=True)
async def set_role_permissions(
    role_id: UUID,
    data: RolePermissionUpdate,
    current_user: User = Depends(RequirePermissions("ROLE_PERMISSION_ASSIGN")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Set permissions for a role (replaces all existing permissions).
    Requires ROLE_PERMISSION_ASSIGN permission.
    """
    role_service = RoleService(db)
    role = await role_service.set_role_permissions(
        role_id,
        data.permission_ids,
        current_user.id,
    )

    return await _role_to_response(role)


async def _role_to_response(role) -> RoleResponse:
    """Convert Role model to RoleResponse."""
    return RoleResponse(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system_role=role.is_system_role,
        is_default=role.is_default,
        created_at=role.created_at,
        updated_at=role.updated_at,
        is_active=role.is_active,
        permissions=[
            PermissionResponse(
                id=rp.permission.id,
                code=rp.permission.code,
                name=rp.permission.name,
                description=rp.permission.description,
                module=rp.permission.module,
                resource=rp.permission.resource,
                action=rp.permission.action,
                created_at=rp.permission.created_at,
                updated_at=rp.permission.updated_at,
                is_active=rp.permission.is_active,
            )
            for rp in role.role_permissions
        ],
    )
