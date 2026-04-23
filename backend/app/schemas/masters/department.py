"""Department schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import EntityStatus


class DepartmentBase(BaseSchema):
    """Base department schema."""

    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Department creation schema."""

    organization_id: UUID
    parent_dept_id: Optional[UUID] = None
    cost_center_code: Optional[str] = Field(None, max_length=50)

    # Department Head
    head_user_id: Optional[UUID] = None

    # Contact (legacy)
    head_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)


class DepartmentUpdate(BaseSchema):
    """Department update schema."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    parent_dept_id: Optional[UUID] = None
    cost_center_code: Optional[str] = Field(None, max_length=50)

    # Department Head
    head_user_id: Optional[UUID] = None

    # Contact (legacy)
    head_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

    status: Optional[str] = None


class DepartmentResponse(DepartmentBase, AuditSchema):
    """Department response schema."""

    id: UUID
    organization_id: UUID
    parent_dept_id: Optional[UUID] = None
    level: int
    path: Optional[str] = None
    cost_center_code: Optional[str] = None

    # Department Head
    head_user_id: Optional[UUID] = None

    # Contact (legacy)
    head_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    status: str

    # Related
    organization_name: Optional[str] = None
    parent_dept_name: Optional[str] = None
    head_user_name: Optional[str] = None
    designation_count: int = 0


class DepartmentTreeResponse(BaseSchema):
    """Department tree node response schema."""

    id: UUID
    code: str
    name: str
    level: int
    status: str
    designation_count: int = 0
    children: List["DepartmentTreeResponse"] = []


# Rebuild model for forward reference
DepartmentTreeResponse.model_rebuild()
