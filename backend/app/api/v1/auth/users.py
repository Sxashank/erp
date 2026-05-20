"""User management API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.auth.user_service import UserService
from app.schemas.auth.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleAssign,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserListResponse], response_model_by_alias=True)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("USER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of users.
    Requires USER_VIEW permission.
    """
    user_service = UserService(db)
    skip = (page - 1) * page_size
    users, total = await user_service.get_users(skip, page_size, include_inactive)

    items = [
        UserListResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            employee_code=u.employee_code,
            status=u.status,
            organization_name=u.organization.name if u.organization else None,
            default_unit_name=u.default_unit.name if u.default_unit else None,
            last_login_at=u.last_login_at,
            roles=[ur.role.code for ur in u.user_roles if ur.is_valid],
            is_active=u.is_active,
        )
        for u in users
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=UserResponse, response_model_by_alias=True)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(RequirePermissions("USER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new user.
    Requires USER_CREATE permission.
    """
    user_service = UserService(db)
    user = await user_service.create_user(data, current_user.id)

    return await _user_to_response(user, db)


@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=True)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(RequirePermissions("USER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get user by ID.
    Requires USER_VIEW permission.
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    return await _user_to_response(user, db)


@router.put("/{user_id}", response_model=UserResponse, response_model_by_alias=True)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(RequirePermissions("USER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing user.
    Requires USER_UPDATE permission.
    """
    user_service = UserService(db)
    user = await user_service.update_user(user_id, data, current_user.id)

    return await _user_to_response(user, db)


@router.delete("/{user_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(RequirePermissions("USER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a user (deactivate).
    Requires USER_DELETE permission.
    """
    user_service = UserService(db)
    await user_service.delete_user(user_id, current_user.id)

    return MessageResponse(message="User deleted successfully")


@router.post("/{user_id}/roles", response_model=UserResponse, response_model_by_alias=True)
async def assign_role(
    user_id: UUID,
    data: UserRoleAssign,
    current_user: User = Depends(RequirePermissions("USER_ROLE_ASSIGN")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Assign a role to a user.
    Requires USER_ROLE_ASSIGN permission.
    """
    user_service = UserService(db)
    user = await user_service.assign_role(user_id, data, current_user.id)

    return await _user_to_response(user, db)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse, response_model_by_alias=True)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    unit_id: Optional[UUID] = Query(None, alias="unitId"),
    current_user: User = Depends(RequirePermissions("USER_ROLE_ASSIGN")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Remove a role from a user.
    Requires USER_ROLE_ASSIGN permission.
    """
    user_service = UserService(db)
    user = await user_service.remove_role(user_id, role_id, unit_id)

    return await _user_to_response(user, db)


@router.post("/{user_id}/unlock", response_model=MessageResponse, response_model_by_alias=True)
async def unlock_user(
    user_id: UUID,
    current_user: User = Depends(RequirePermissions("USER_UNLOCK")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Unlock a locked user account.
    Requires USER_UNLOCK permission.
    """
    user_service = UserService(db)
    await user_service.unlock_user(user_id)

    return MessageResponse(message="User account unlocked successfully")


@router.post("/{user_id}/reset-password", response_model=MessageResponse, response_model_by_alias=True)
async def reset_user_password(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, alias="newPassword"),
    must_change: bool = Query(True, alias="mustChange"),
    current_user: User = Depends(RequirePermissions("USER_RESET_PASSWORD")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Admin reset user password.
    Requires USER_RESET_PASSWORD permission.
    """
    user_service = UserService(db)
    await user_service.reset_password(user_id, new_password, must_change)

    return MessageResponse(message="Password reset successfully")


async def _user_to_response(user: User, db: AsyncSession) -> UserResponse:
    """Convert User model to UserResponse."""
    from app.repositories.auth.user_repo import UserRepository

    user_repo = UserRepository(db)
    permissions = await user_repo.get_user_permissions(user.id)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        employee_code=user.employee_code,
        phone=user.phone,
        timezone=user.timezone,
        auth_type=user.auth_type,
        mfa_enabled=user.mfa_enabled,
        status=user.status,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        default_unit_id=user.default_unit_id,
        default_unit_name=user.default_unit.name if user.default_unit else None,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
        roles=[
            {
                "id": ur.role.id,
                "code": ur.role.code,
                "name": ur.role.name,
                "unit_id": ur.unit_id,
                "unit_name": ur.unit.name if ur.unit else None,
            }
            for ur in user.user_roles
            if ur.is_valid
        ],
        permissions=list(permissions),
    )
