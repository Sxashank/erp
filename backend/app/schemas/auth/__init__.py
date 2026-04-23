"""Authentication and authorization schemas."""

from app.schemas.auth.token import (
    Token,
    TokenPayload,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    MFASetupResponse,
    MFAVerifyRequest,
)
from app.schemas.auth.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleAssign,
)
from app.schemas.auth.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionResponse,
    RolePermissionUpdate,
)

__all__ = [
    # Token
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "MFASetupResponse",
    "MFAVerifyRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserRoleAssign",
    # Role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "PermissionResponse",
    "RolePermissionUpdate",
]
