"""Role and Permission repositories."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth.role import Role, Permission, RolePermission, UserRole
from app.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)

    async def get_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by code."""
        return await self.get_by_field("code", code)

    async def get_by_module(self, module: str) -> List[Permission]:
        """Get all permissions for a module."""
        return await self.get_many_by_field("module", module)

    async def get_all_grouped_by_module(self) -> dict:
        """Get all permissions grouped by module."""
        query = select(Permission).where(Permission.is_active == True)
        result = await self.session.execute(query)
        permissions = result.scalars().all()

        grouped = {}
        for perm in permissions:
            if perm.module not in grouped:
                grouped[perm.module] = []
            grouped[perm.module].append(perm)

        return grouped

    async def bulk_create(self, permissions_data: List[dict]) -> List[Permission]:
        """Create multiple permissions."""
        permissions = [Permission(**data) for data in permissions_data]
        self.session.add_all(permissions)
        await self.session.flush()
        return permissions


class RoleRepository(BaseRepository[Role]):
    """Repository for Role operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_code(self, code: str) -> Optional[Role]:
        """Get role by code."""
        query = select(Role).where(
            and_(
                Role.code == code,
                Role.is_active == True,
            )
        ).options(selectinload(Role.role_permissions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_permissions(self, id: UUID) -> Optional[Role]:
        """Get role with permissions loaded."""
        query = select(Role).where(
            and_(
                Role.id == id,
                Role.is_active == True,
            )
        ).options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_counts(self) -> List[dict]:
        """Get all roles with permission and user counts."""
        query = select(Role).where(Role.is_active == True).options(
            selectinload(Role.role_permissions),
            selectinload(Role.user_roles),
        )
        result = await self.session.execute(query)
        roles = result.scalars().all()

        return [
            {
                "role": role,
                "permission_count": len(role.role_permissions),
                "user_count": len([ur for ur in role.user_roles if ur.is_valid]),
            }
            for role in roles
        ]

    async def set_permissions(
        self,
        role_id: UUID,
        permission_ids: List[UUID],
        updated_by: Optional[UUID] = None,
    ) -> Role:
        """Set permissions for a role (replace all)."""
        role = await self.get_with_permissions(role_id)
        if not role:
            raise ValueError("Role not found")

        # Remove existing permissions
        for rp in role.role_permissions:
            await self.session.delete(rp)

        # Add new permissions
        for perm_id in permission_ids:
            role_perm = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                created_by=updated_by,
            )
            self.session.add(role_perm)

        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def add_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
        created_by: Optional[UUID] = None,
    ) -> RolePermission:
        """Add a permission to a role."""
        role_perm = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            created_by=created_by,
        )
        self.session.add(role_perm)
        await self.session.flush()
        return role_perm

    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a permission from a role."""
        query = select(RolePermission).where(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        result = await self.session.execute(query)
        role_perm = result.scalar_one_or_none()

        if role_perm:
            await self.session.delete(role_perm)
            await self.session.flush()
            return True
        return False

    async def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if role code already exists."""
        query = select(Role.id).where(Role.code == code)
        if exclude_id:
            query = query.where(Role.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_default_role(self) -> Optional[Role]:
        """Get the default role for new users."""
        query = select(Role).where(
            and_(
                Role.is_default == True,
                Role.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
