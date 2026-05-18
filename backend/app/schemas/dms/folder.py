"""DMS Folder schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema


class FolderCreate(CamelSchema):
    """Schema for creating a folder."""

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=1000)
    folder_type: Optional[str] = Field(None, max_length=50)
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[UUID] = None
    access_level: str = Field("organization", max_length=20)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)


class FolderUpdate(CamelSchema):
    """Schema for updating a folder."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    access_level: Optional[str] = Field(None, max_length=20)


class FolderResponse(CamelSchema):
    """Schema for folder response."""

    id: UUID
    organization_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    path: str
    level: int
    folder_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    access_level: str
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int
    document_count: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class FolderTreeResponse(CamelSchema):
    """Schema for folder tree node response."""

    id: str
    name: str
    path: str
    level: int
    folder_type: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    document_count: int
    children: List["FolderTreeResponse"] = []


# Enable self-reference for recursive type
FolderTreeResponse.model_rebuild()


class FolderMoveRequest(CamelSchema):
    """Schema for moving a folder."""

    new_parent_id: Optional[UUID] = None


class FolderAccessCreate(CamelSchema):
    """Schema for creating folder access."""

    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    can_view: bool = True
    can_upload: bool = False
    can_create_subfolder: bool = False
    can_edit: bool = False
    can_delete: bool = False
    expires_at: Optional[datetime] = None


class FolderAccessResponse(CamelSchema):
    """Schema for folder access response."""

    id: UUID
    folder_id: UUID
    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    can_view: bool
    can_upload: bool
    can_create_subfolder: bool
    can_edit: bool
    can_delete: bool
    expires_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime


class FolderListResponse(CamelSchema):
    """Schema for folder list response."""

    items: List[FolderResponse]
    total: int
