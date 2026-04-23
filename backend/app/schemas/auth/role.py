"""Role and Permission schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema


class PermissionBase(BaseSchema):
    """Base permission schema."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    module: str = Field(..., min_length=1, max_length=50)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=20)


class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass


class PermissionResponse(PermissionBase, AuditSchema):
    """Permission response schema."""

    id: UUID


class PermissionGrouped(BaseSchema):
    """Permissions grouped by module."""

    module: str
    permissions: List[PermissionResponse]


class RoleBase(BaseSchema):
    """Base role schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema."""

    permission_ids: Optional[List[UUID]] = Field(default_factory=list)
    is_default: bool = False


class RoleUpdate(BaseSchema):
    """Role update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: Optional[bool] = None


class RolePermissionUpdate(BaseSchema):
    """Role permission update schema."""

    permission_ids: List[UUID]


class RoleResponse(RoleBase, AuditSchema):
    """Role response schema."""

    id: UUID
    is_system_role: bool
    is_default: bool
    permissions: List[PermissionResponse] = []


class RoleListResponse(BaseSchema):
    """Role list item response schema."""

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_system_role: bool
    is_default: bool
    permission_count: int
    user_count: int
