"""DMS Tag schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema


class TagCreate(CamelSchema):
    """Schema for creating a tag."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)


class TagUpdate(CamelSchema):
    """Schema for updating a tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)


class TagResponse(CamelSchema):
    """Schema for tag response."""

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class TagListResponse(CamelSchema):
    """Schema for tag list response."""

    items: List[TagResponse]
    total: int


class DocumentTagResponse(CamelSchema):
    """Schema for document-tag relationship response."""

    id: UUID
    document_id: UUID
    tag_id: UUID
    tag: Optional[TagResponse] = None
    created_by: Optional[UUID] = None
    created_at: datetime


class TagDocumentsRequest(CamelSchema):
    """Schema for bulk tagging documents."""

    document_ids: List[UUID]
    tag_ids: List[UUID]
