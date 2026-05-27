"""Schemas for DMS filing rules and entity vaults."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema
from app.schemas.dms.document import DocumentResponse
from app.schemas.dms.folder import FolderResponse


class FilingRuleResponse(CamelSchema):
    id: UUID
    module: str
    document_type: str
    entity_type: str
    path_template: str
    access_level: str
    retention_policy: str | None = None
    portal_visible: bool
    default_tags: list[str] = Field(default_factory=list)
    description: str | None = None
    priority: int
    is_system: bool


class FilingRuleCreate(CamelSchema):
    module: str = Field(..., min_length=1, max_length=50)
    document_type: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=100)
    path_template: str = Field(..., min_length=1, max_length=2000)
    access_level: str = "organization"
    retention_policy: str | None = None
    portal_visible: bool = False
    default_tags: list[str] = Field(default_factory=list)
    description: str | None = None
    priority: int = 100


class ResolveFolderRequest(CamelSchema):
    module: str = Field(..., min_length=1)
    document_type: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    entity_id: UUID | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ResolveFolderResponse(CamelSchema):
    folder: FolderResponse
    path: str
    rule: FilingRuleResponse | None = None


class EntityVaultResponse(CamelSchema):
    entity_type: str
    entity_id: UUID
    folders: list[FolderResponse] = Field(default_factory=list)
    documents: list[DocumentResponse] = Field(default_factory=list)
