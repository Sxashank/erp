"""API dependencies for dependency injection."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.constants import TokenType
from app.core.exceptions import BadRequestException, ForbiddenException, UnauthorizedException
from app.core.security import verify_token
from app.database import get_db, set_tenant_context
from app.models.auth.user import User
from app.models.ess.enums import ESSUserStatus
from app.models.ess.ess_user import ESSUser
from app.repositories.auth.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass(frozen=True)
class ESSUserContext:
    """Authenticated ESS identity resolved from the portal access token."""

    ess_user: ESSUser

    @property
    def ess_user_id(self) -> UUID:
        return self.ess_user.id

    @property
    def employee_id(self) -> UUID:
        return self.ess_user.employee_id

    @property
    def organization_id(self) -> UUID:
        return self.ess_user.organization_id


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
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
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
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
) -> set[str]:
    """Get permissions for the current user."""
    user_repo = UserRepository(db)
    permissions = set(await user_repo.get_user_permissions(user.id))

    for user_role in getattr(user, "user_roles", []) or []:
        role = getattr(user_role, "role", None)
        role_code = getattr(role, "code", None)
        if role_code:
            permissions.add(str(role_code))

        for role_permission in getattr(role, "role_permissions", []) or []:
            permission = getattr(role_permission, "permission", None)
            permission_code = getattr(permission, "code", None)
            if permission_code:
                permissions.add(str(permission_code))

    return permissions


async def get_active_organization_id(
    request: Request,
    current_user: User = Depends(get_current_user),
    user_permissions: set[str] = Depends(get_current_user_permissions),
) -> UUID | None:
    """Resolve the active tenant for the current request.

    Tenant-scoped admin APIs honor ``X-Organization-Id`` for users allowed to
    switch organizations from the UI. Non-super-admin users remain pinned to
    their own organization.
    """
    active_organization_id = current_user.organization_id
    requested_org_id = request.headers.get("X-Organization-Id")

    if requested_org_id:
        try:
            requested_uuid = UUID(requested_org_id)
        except ValueError as exc:
            raise BadRequestException("Invalid X-Organization-Id header") from exc

        if requested_uuid != current_user.organization_id and "SUPER_ADMIN" not in user_permissions:
            raise ForbiddenException("Cross-tenant access requires SUPER_ADMIN")

        active_organization_id = requested_uuid

    if active_organization_id is not None:
        setattr(current_user, "_active_organization_id", active_organization_id)

    return active_organization_id


class RequirePermissions:
    """Dependency to require specific permissions."""

    def __init__(self, *permissions: str, require_all: bool = True):
        self.permissions = set(permissions)
        self.require_all = require_all

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        user_permissions: set[str] = Depends(get_current_user_permissions),
    ) -> User:
        """Check if user has required permissions."""
        if "SUPER_ADMIN" in user_permissions:
            return user

        if self.require_all:
            missing = self.permissions - user_permissions
            if missing:
                raise ForbiddenException(f"Missing required permissions: {', '.join(missing)}")
        else:
            if not (self.permissions & user_permissions):
                raise ForbiddenException(f"Requires one of: {', '.join(self.permissions)}")

        return user


def require_permission(*permissions: str):
    """Shortcut for RequirePermissions dependency."""
    return Depends(RequirePermissions(*permissions))


async def get_db_with_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_organization_id: UUID | None = Depends(get_active_organization_id),
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
    if active_organization_id and current_user.organization_id != active_organization_id:
        # Keep endpoint code paths that still read `current_user.organization_id`
        # aligned with the tenant RLS context for this request without
        # persisting a profile change back to the user row.
        set_committed_value(current_user, "organization_id", active_organization_id)

    if active_organization_id:
        await set_tenant_context(db, active_organization_id)
    return db


async def get_current_ess_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> ESSUserContext:
    """Resolve the authenticated ESS user and set tenant RLS context."""
    if not token:
        raise UnauthorizedException("Not authenticated")

    payload = verify_token(token, TokenType.ACCESS)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    ess_user_id = payload.get("sub")
    if not ess_user_id:
        raise UnauthorizedException("Invalid token payload")

    ess_user = await db.get(ESSUser, UUID(ess_user_id))
    if not ess_user:
        raise UnauthorizedException("ESS user not found")

    if ess_user.status != ESSUserStatus.ACTIVE:
        raise UnauthorizedException("ESS user is inactive")

    token_employee_id = payload.get("employee_id")
    token_organization_id = payload.get("organization_id")
    if (
        token_employee_id
        and str(ess_user.employee_id) != str(token_employee_id)
        or token_organization_id
        and str(ess_user.organization_id) != str(token_organization_id)
    ):
        raise UnauthorizedException("Invalid token identity")

    await set_tenant_context(db, ess_user.organization_id)
    return ESSUserContext(ess_user=ess_user)


async def get_ess_db_with_tenant(
    db: AsyncSession = Depends(get_db),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
) -> AsyncSession:
    """Get database session with tenant RLS set for the authenticated ESS user."""
    await set_tenant_context(db, ess_context.organization_id)
    return db
