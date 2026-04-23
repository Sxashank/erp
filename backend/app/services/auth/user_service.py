"""User service."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_password_hash
from app.core.constants import UserStatus
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
)
from app.models.auth.user import User
from app.models.auth.role import UserRole
from app.repositories.auth.user_repo import UserRepository
from app.repositories.auth.role_repo import RoleRepository
from app.schemas.auth.user import UserCreate, UserUpdate, UserRoleAssign


class UserService:
    """Service for user management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)

    async def create_user(
        self,
        data: UserCreate,
        created_by: Optional[UUID] = None,
    ) -> User:
        """Create a new user."""
        # Check if username exists
        if await self.user_repo.username_exists(data.username):
            raise ConflictException(f"Username '{data.username}' already exists")

        # Check if email exists
        if await self.user_repo.email_exists(data.email):
            raise ConflictException(f"Email '{data.email}' already exists")

        # Hash password
        password_hash = get_password_hash(data.password)

        # Set password expiry
        password_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.PASSWORD_EXPIRY_DAYS
        )

        # Create user
        user_data = {
            "username": data.username,
            "email": data.email,
            "full_name": data.full_name,
            "employee_code": data.employee_code,
            "phone": data.phone,
            "timezone": data.timezone,
            "password_hash": password_hash,
            "password_changed_at": datetime.now(timezone.utc),
            "password_expires_at": password_expires_at,
            "organization_id": data.organization_id,
            "default_unit_id": data.default_unit_id,
            "mfa_enabled": data.mfa_enabled,
            "status": data.status,
            "created_by": created_by,
        }

        user = await self.user_repo.create(user_data)

        # Assign roles if provided
        if data.role_ids:
            for role_id in data.role_ids:
                await self._assign_role(
                    user_id=user.id,
                    role_id=role_id,
                    created_by=created_by,
                )

        # Assign default role if no roles provided
        if not data.role_ids:
            default_role = await self.role_repo.get_default_role()
            if default_role:
                await self._assign_role(
                    user_id=user.id,
                    role_id=default_role.id,
                    created_by=created_by,
                )

        await self.session.refresh(user)
        return user

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
        updated_by: Optional[UUID] = None,
    ) -> User:
        """Update an existing user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        # Check email uniqueness if updating
        if data.email and data.email != user.email:
            if await self.user_repo.email_exists(data.email, exclude_id=user_id):
                raise ConflictException(f"Email '{data.email}' already exists")

        # Prepare update data
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.user_repo.update(user, update_data)

    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        user = await self.user_repo.get_with_roles(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False,
    ) -> Tuple[List[User], int]:
        """Get paginated list of users."""
        users = await self.user_repo.get_all(skip, limit, include_inactive)
        total = await self.user_repo.count(include_inactive)
        return users, total

    async def delete_user(
        self,
        user_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> User:
        """Soft delete a user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        return await self.user_repo.soft_delete(user_id, deleted_by)

    async def assign_role(
        self,
        user_id: UUID,
        data: UserRoleAssign,
        created_by: Optional[UUID] = None,
    ) -> User:
        """Assign a role to a user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        role = await self.role_repo.get(data.role_id)
        if not role:
            raise NotFoundException("Role not found")

        await self._assign_role(
            user_id=user_id,
            role_id=data.role_id,
            unit_id=data.unit_id,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            created_by=created_by,
        )

        await self.session.refresh(user)
        return user

    async def remove_role(
        self,
        user_id: UUID,
        role_id: UUID,
        unit_id: Optional[UUID] = None,
    ) -> User:
        """Remove a role from a user."""
        user = await self.user_repo.get_with_roles(user_id)
        if not user:
            raise NotFoundException("User not found")

        # Find and remove the user role
        for user_role in user.user_roles:
            if user_role.role_id == role_id:
                if unit_id is None or user_role.unit_id == unit_id:
                    await self.session.delete(user_role)
                    break

        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def unlock_user(self, user_id: UUID) -> User:
        """Unlock a locked user account."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        return await self.user_repo.unlock_account(user)

    async def reset_password(
        self,
        user_id: UUID,
        new_password: str,
        must_change: bool = True,
    ) -> User:
        """Admin reset user password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.PASSWORD_EXPIRY_DAYS
        )
        user.must_change_password = must_change
        user.failed_login_attempts = 0
        user.locked_until = None

        await self.session.flush()
        return user

    async def _assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        unit_id: Optional[UUID] = None,
        effective_from: Optional[datetime] = None,
        effective_to: Optional[datetime] = None,
        created_by: Optional[UUID] = None,
    ) -> UserRole:
        """Internal method to assign a role to a user."""
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            unit_id=unit_id,
            effective_from=effective_from or datetime.now(timezone.utc),
            effective_to=effective_to,
            created_by=created_by,
        )
        self.session.add(user_role)
        await self.session.flush()
        return user_role
