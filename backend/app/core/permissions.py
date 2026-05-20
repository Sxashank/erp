"""Permission checking utilities and decorators."""

from collections.abc import Callable
from functools import wraps
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TokenType
from app.core.exceptions import ForbiddenException
from app.core.security import verify_token
from app.database import get_db
from app.models.auth.user import User
from app.repositories.auth.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _permissions_from_loaded_user(user: User | None) -> set[str]:
    """Collect permission and role codes from an already-loaded user graph."""
    if not user:
        return set()

    permissions: set[str] = set()
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


def _find_arg(args, cls):
    for arg in args:
        if isinstance(arg, cls):
            return arg
    return None


async def _resolve_permissions_for_call(
    *,
    request: Request | None,
    args: tuple,
    kwargs: dict,
) -> set[str]:
    """Resolve permissions for decorator-wrapped FastAPI endpoints.

    Most endpoints do not declare a Request argument, so FastAPI calls the
    wrapper with the endpoint's dependency kwargs only. Fall back to the loaded
    current_user and db dependency in that case.
    """
    request_permissions: set[str] = set()
    if request and hasattr(request, "state"):
        request_permissions = set(getattr(request.state, "permissions", set()) or set())
    if request_permissions:
        return request_permissions

    current_user = kwargs.get("current_user")
    if current_user is None:
        current_user = _find_arg(args, User)

    user_permissions = _permissions_from_loaded_user(current_user)
    if user_permissions:
        return user_permissions

    db = kwargs.get("db")
    if db is None:
        db = _find_arg(args, AsyncSession)
    user_id = getattr(current_user, "id", None)
    if db is not None and user_id is not None:
        return await UserRepository(db).get_user_permissions(user_id)

    return set()


def require_permissions(*required_permissions: str):
    """
    Decorator to check if the current user has required permissions.

    Usage:
        @router.get("/items")
        @require_permissions("ITEM_VIEW")
        async def get_items(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request: Request | None = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            user_permissions = await _resolve_permissions_for_call(
                request=request,
                args=args,
                kwargs=kwargs,
            )

            # Check if user has all required permissions
            if not has_all_permissions(user_permissions, list(required_permissions)):
                missing = set(required_permissions) - user_permissions
                raise ForbiddenException(
                    detail=f"Missing required permissions: {', '.join(missing)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(user_permissions: set[str], required_permission: str) -> bool:
    """Check if user has a specific permission."""
    if "SUPER_ADMIN" in user_permissions:
        return True
    return required_permission in user_permissions


def has_any_permission(user_permissions: set[str], required_permissions: list[str]) -> bool:
    """Check if user has any of the required permissions."""
    if "SUPER_ADMIN" in user_permissions:
        return True
    return bool(user_permissions & set(required_permissions))


def has_all_permissions(user_permissions: set[str], required_permissions: list[str]) -> bool:
    """Check if user has all required permissions."""
    if "SUPER_ADMIN" in user_permissions:
        return True
    return set(required_permissions).issubset(user_permissions)


async def get_request_user_permissions(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> set[str]:
    """Resolve permission codes for dependency-based route guards."""
    if not token:
        return set()

    payload = verify_token(token, TokenType.ACCESS)
    if not payload:
        return set()

    user_id = payload.get("sub")
    if not user_id:
        return set()

    user_repo = UserRepository(db)
    return await user_repo.get_user_permissions(UUID(user_id))


class PermissionChecker:
    """
    Permission checker dependency for FastAPI routes.

    Usage:
        @router.get("/items")
        async def get_items(
            _: None = Depends(PermissionChecker(["ITEM_VIEW"])),
            current_user: User = Depends(get_current_user),
        ):
            ...
    """

    def __init__(
        self,
        required_permissions: list[str],
        require_all: bool = True,
    ) -> None:
        self.required_permissions = required_permissions
        self.require_all = require_all

    async def __call__(
        self,
        request: Request,
        resolved_permissions: set[str] = Depends(get_request_user_permissions),
    ) -> None:
        """Check permissions on the request."""
        state_permissions: set[str] = getattr(request.state, "permissions", set())
        user_permissions = resolved_permissions or state_permissions

        if self.require_all:
            if not has_all_permissions(user_permissions, self.required_permissions):
                missing = set(self.required_permissions) - user_permissions
                raise ForbiddenException(
                    detail=f"Missing required permissions: {', '.join(missing)}"
                )
        else:
            if not has_any_permission(user_permissions, self.required_permissions):
                raise ForbiddenException(
                    detail=f"Requires one of: {', '.join(self.required_permissions)}"
                )


# NOTE: A `def RequirePermissions(permissions: list[str], ...)` decorator
# factory used to live here. It clashed with the canonical
# `app.api.deps.RequirePermissions` class (the `Depends(...)` style required by
# CLAUDE.md §6.3) — and when the two were imported into the same module the
# decorator pattern silently broke FastAPI's signature introspection and made
# every route return plaintext "Internal Server Error" 500.
#
# The function was removed deliberately. There is only one `RequirePermissions`
# in the codebase now — the class in `app.api.deps`. Any module that needs to
# gate an endpoint imports `RequirePermissions` from `app.api.deps` and uses:
#
#     current_user: User = Depends(RequirePermissions(Permissions.X))
#
# Do not re-introduce a function-decorator form here.
