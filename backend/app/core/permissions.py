"""Permission checking utilities and decorators."""

from functools import wraps
from typing import Callable, List, Optional, Set

from fastapi import Depends, Request

from app.core.exceptions import ForbiddenException


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
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            # Get user permissions from request state (set by auth middleware)
            user_permissions: Set[str] = getattr(
                request.state if request else None,
                "permissions",
                set()
            )

            # Check if user has all required permissions
            missing = set(required_permissions) - user_permissions
            if missing:
                raise ForbiddenException(
                    detail=f"Missing required permissions: {', '.join(missing)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(user_permissions: Set[str], required_permission: str) -> bool:
    """Check if user has a specific permission."""
    return required_permission in user_permissions


def has_any_permission(user_permissions: Set[str], required_permissions: List[str]) -> bool:
    """Check if user has any of the required permissions."""
    return bool(user_permissions & set(required_permissions))


def has_all_permissions(user_permissions: Set[str], required_permissions: List[str]) -> bool:
    """Check if user has all required permissions."""
    return set(required_permissions).issubset(user_permissions)


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
        required_permissions: List[str],
        require_all: bool = True,
    ) -> None:
        self.required_permissions = required_permissions
        self.require_all = require_all

    async def __call__(self, request: Request) -> None:
        """Check permissions on the request."""
        user_permissions: Set[str] = getattr(
            request.state,
            "permissions",
            set()
        )

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


def RequirePermissions(permissions: List[str], require_all: bool = True):
    """
    Decorator for permission checking on FastAPI routes.

    Usage:
        @router.get("/items")
        @RequirePermissions(["ITEM_VIEW"])
        async def get_items(request: Request, current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Try to find request in kwargs or args
            req = request
            if not req:
                req = kwargs.get("request")
            if not req:
                for arg in args:
                    if isinstance(arg, Request):
                        req = arg
                        break

            # Get user permissions from request state
            user_permissions: Set[str] = set()
            if req and hasattr(req, "state"):
                user_permissions = getattr(req.state, "permissions", set())

            # Check permissions
            if require_all:
                if not has_all_permissions(user_permissions, permissions):
                    missing = set(permissions) - user_permissions
                    raise ForbiddenException(
                        detail=f"Missing required permissions: {', '.join(missing)}"
                    )
            else:
                if not has_any_permission(user_permissions, permissions):
                    raise ForbiddenException(
                        detail=f"Requires one of: {', '.join(permissions)}"
                    )

            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
