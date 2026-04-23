"""API dependencies for dependency injection."""

from typing import Optional, Set
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, set_tenant_context
from app.core.security import verify_token
from app.core.constants import TokenType
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.auth.user import User
from app.repositories.auth.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    if not token:
        raise UnauthorizedException("Not authenticated")

    payload = verify_token(token, TokenType.ACCESS)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    user_repo = UserRepository(db)
    user = await user_repo.get_with_roles(UUID(user_id))

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("User is inactive")

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except UnauthorizedException:
        return None


async def get_current_user_permissions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Set[str]:
    """Get permissions for the current user."""
    user_repo = UserRepository(db)
    return await user_repo.get_user_permissions(user.id)


class RequirePermissions:
    """Dependency to require specific permissions."""

    def __init__(self, *permissions: str, require_all: bool = True):
        self.permissions = set(permissions)
        self.require_all = require_all

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        user_permissions: Set[str] = Depends(get_current_user_permissions),
    ) -> User:
        """Check if user has required permissions."""
        if self.require_all:
            missing = self.permissions - user_permissions
            if missing:
                raise ForbiddenException(
                    f"Missing required permissions: {', '.join(missing)}"
                )
        else:
            if not (self.permissions & user_permissions):
                raise ForbiddenException(
                    f"Requires one of: {', '.join(self.permissions)}"
                )

        return user


def require_permission(*permissions: str):
    """Shortcut for RequirePermissions dependency."""
    return Depends(RequirePermissions(*permissions))


async def get_db_with_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AsyncSession:
    """Get database session with tenant RLS context set.

    This dependency sets the PostgreSQL session variable used by Row-Level
    Security policies to filter data by organization. Use this instead of
    get_db when you want RLS to automatically filter by the current user's
    organization.

    Args:
        db: The database session from get_db dependency
        current_user: The authenticated user from get_current_user dependency

    Returns:
        The database session with tenant context configured
    """
    if current_user.organization_id:
        await set_tenant_context(db, current_user.organization_id)
    return db
