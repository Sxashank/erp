"""DMS Document schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    folder_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    document_type: Optional[str] = Field(None, max_length=50)
    document_subtype: Optional[str] = Field(None, max_length=50)
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[UUID] = None
    access_level: str = Field("organization", max_length=20)
    keywords: Optional[List[str]] = None
    expiry_date: Optional[datetime] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    folder_id: Optional[UUID] = None
    document_type: Optional[str] = Field(None, max_length=50)
    document_subtype: Optional[str] = Field(None, max_length=50)
    access_level: Optional[str] = Field(None, max_length=20)
    keywords: Optional[List[str]] = None
    expiry_date: Optional[datetime] = None


class DocumentVersionResponse(BaseModel):
    """Schema for document version response."""

    id: UUID
    document_id: UUID
    version_number: int
    change_notes: Optional[str] = None
    file_name: str
    file_size: int
    mime_type: str
    checksum: Optional[str] = None
    is_current: bool
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentHistoryResponse(BaseModel):
    """Schema for document history response."""

    id: UUID
    document_id: UUID
    action: str
    action_details: Optional[dict] = None
    performed_by: Optional[UUID] = None
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID
    organization_id: UUID
    folder_id: Optional[UUID] = None
    code: str
    name: str
    description: Optional[str] = None
    file_name: str
    file_extension: Optional[str] = None
    mime_type: str
    file_size: int
    storage_path: str
    storage_provider: str
    checksum: Optional[str] = None
    document_type: Optional[str] = None
    document_subtype: Optional[str] = None
    status: str
    access_level: str
    current_version: int
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    keywords: Optional[List[str]] = None
    expiry_date: Optional[datetime] = None
    is_ocr_processed: bool
    ocr_text: Optional[str] = None
    download_count: int
    view_count: int
    last_accessed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""

    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentDownloadResponse(BaseModel):
    """Schema for document download info."""

    storage_path: str
    file_name: str
    mime_type: str


class DocumentStatsResponse(BaseModel):
    """Schema for document statistics response."""

    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    total_folders: int
    by_type: dict
    by_status: dict
    by_extension: dict


class DocumentSearchRequest(BaseModel):
    """Schema for document search request."""

    query: Optional[str] = None
    folder_id: Optional[UUID] = None
    document_type: Optional[str] = None
    document_subtype: Optional[str] = None
    mime_type: Optional[str] = None
    tags: Optional[List[str]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    include_archived: bool = False
    skip: int = 0
    limit: int = 20


class NewVersionCreate(BaseModel):
    """Schema for uploading a new document version."""

    change_notes: Optional[str] = Field(None, max_length=1000)
