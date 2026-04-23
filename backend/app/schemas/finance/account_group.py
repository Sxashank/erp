"""Account Group schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import AccountNature


class AccountGroupCreate(BaseSchema):
    """Schema for creating an account group."""

    code: str = Field(..., min_length=1, max_length=20, description="Group code")
    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    nature: AccountNature
    parent_group_id: Optional[UUID] = None
    sequence: int = 0
    description: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class AccountGroupUpdate(BaseSchema):
    """Schema for updating an account group."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_group_id: Optional[UUID] = None
    sequence: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)


class AccountGroupResponse(AuditSchema):
    """Account Group response schema."""

    id: UUID
    code: str
    name: str
    nature: AccountNature
    parent_group_id: Optional[UUID] = None
    parent_group_name: Optional[str] = None
    level: int
    path: Optional[str] = None
    sequence: int
    description: Optional[str] = None
    is_system: bool
    organization_id: UUID
    account_count: int = 0


class AccountGroupTreeResponse(BaseSchema):
    """Account Group tree node response."""

    id: UUID
    code: str
    name: str
    nature: AccountNature
    level: int
    sequence: int
    is_system: bool
    account_count: int = 0
    children: List["AccountGroupTreeResponse"] = []


# Enable self-referential type for Pydantic
AccountGroupTreeResponse.model_rebuild()
