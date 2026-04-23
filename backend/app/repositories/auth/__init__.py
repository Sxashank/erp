"""Auth repositories."""

from app.repositories.auth.user_repo import UserRepository
from app.repositories.auth.role_repo import RoleRepository, PermissionRepository

__all__ = ["UserRepository", "RoleRepository", "PermissionRepository"]
