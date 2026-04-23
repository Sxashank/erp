"""Role and Permission service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
)
from app.models.auth.role import Role, Permission
from app.repositories.auth.role_repo import RoleRepository, PermissionRepository
from app.schemas.auth.role import RoleCreate, RoleUpdate, PermissionCreate


class RoleService:
    """Service for role and permission management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.role_repo = RoleRepository(session)
        self.permission_repo = PermissionRepository(session)

    # Permission methods
    async def create_permission(
        self,
        data: PermissionCreate,
        created_by: Optional[UUID] = None,
    ) -> Permission:
        """Create a new permission."""
        # Check if code exists
        existing = await self.permission_repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Permission code '{data.code}' already exists")

        perm_data = data.model_dump()
        perm_data["created_by"] = created_by

        return await self.permission_repo.create(perm_data)

    async def get_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Permission], int]:
        """Get all permissions."""
        permissions = await self.permission_repo.get_all(skip, limit)
        total = await self.permission_repo.count()
        return permissions, total

    async def get_permissions_grouped(self) -> dict:
        """Get permissions grouped by module."""
        return await self.permission_repo.get_all_grouped_by_module()

    # Role methods
    async def create_role(
        self,
        data: RoleCreate,
        created_by: Optional[UUID] = None,
    ) -> Role:
        """Create a new role."""
        # Check if code exists
        if await self.role_repo.code_exists(data.code):
            raise ConflictException(f"Role code '{data.code}' already exists")

        role_data = {
            "code": data.code,
            "name": data.name,
            "description": data.description,
            "is_default": data.is_default,
            "is_system_role": False,
            "created_by": created_by,
        }

        role = await self.role_repo.create(role_data)

        # Assign permissions if provided
        if data.permission_ids:
            await self.role_repo.set_permissions(
                role.id,
                data.permission_ids,
                created_by,
            )

        await self.session.refresh(role)
        return role

    async def update_role(
        self,
        role_id: UUID,
        data: RoleUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Role:
        """Update an existing role."""
        role = await self.role_repo.get(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if role.is_system_role:
            raise BadRequestException("Cannot modify system role")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.role_repo.update(role, update_data)

    async def get_role(self, role_id: UUID) -> Role:
        """Get role by ID with permissions."""
        role = await self.role_repo.get_with_permissions(role_id)
        if not role:
            raise NotFoundException("Role not found")
        return role

    async def get_roles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[dict], int]:
        """Get all roles with counts."""
        roles_data = await self.role_repo.get_all_with_counts()
        total = await self.role_repo.count()
        return roles_data, total

    async def delete_role(
        self,
        role_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Role:
        """Soft delete a role."""
        role = await self.role_repo.get(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if role.is_system_role:
            raise BadRequestException("Cannot delete system role")

        return await self.role_repo.soft_delete(role_id, deleted_by)

    async def set_role_permissions(
        self,
        role_id: UUID,
        permission_ids: List[UUID],
        updated_by: Optional[UUID] = None,
    ) -> Role:
        """Set permissions for a role (replace all)."""
        role = await self.role_repo.get(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if role.is_system_role:
            raise BadRequestException("Cannot modify system role permissions")

        return await self.role_repo.set_permissions(role_id, permission_ids, updated_by)

    async def add_role_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
        created_by: Optional[UUID] = None,
    ) -> Role:
        """Add a permission to a role."""
        role = await self.role_repo.get(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if role.is_system_role:
            raise BadRequestException("Cannot modify system role permissions")

        permission = await self.permission_repo.get(permission_id)
        if not permission:
            raise NotFoundException("Permission not found")

        await self.role_repo.add_permission(role_id, permission_id, created_by)
        await self.session.refresh(role)
        return role

    async def remove_role_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> Role:
        """Remove a permission from a role."""
        role = await self.role_repo.get(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if role.is_system_role:
            raise BadRequestException("Cannot modify system role permissions")

        await self.role_repo.remove_permission(role_id, permission_id)
        await self.session.refresh(role)
        return role
