"""Document Studio API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.document_studio import (
    DocumentModule,
    DocumentPackageStatus,
    DocumentTemplateFormat,
    DocumentTemplateStatus,
)
from app.schemas.base import CamelSchema


class TemplateSummary(CamelSchema):
    id: UUID
    module: DocumentModule
    document_type: str
    code: str
    name: str
    description: str | None = None
    product_code: str | None = None
    entity_type: str | None = None
    locale: str
    channel: str
    priority: int
    selection_rules: dict[str, Any] = Field(default_factory=dict)
    is_system: bool


class TemplateListResponse(CamelSchema):
    items: list[TemplateSummary]
    total: int


class TemplateCreate(CamelSchema):
    module: DocumentModule
    document_type: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    product_code: str | None = None
    entity_type: str | None = None
    locale: str = "en"
    channel: str = "PDF"
    priority: int = 100
    selection_rules: dict[str, Any] = Field(default_factory=dict)


class TemplateVersionResponse(CamelSchema):
    id: UUID
    template_id: UUID
    version_number: int
    status: DocumentTemplateStatus
    format: DocumentTemplateFormat
    body: str
    header: str | None = None
    footer: str | None = None
    style_config: dict[str, Any] = Field(default_factory=dict)
    variable_schema: dict[str, Any] = Field(default_factory=dict)
    required_variables: list[str] = Field(default_factory=list)
    locked_blocks: list[dict[str, Any]] = Field(default_factory=list)
    source_document_id: UUID | None = None
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None
    retired_at: datetime | None = None
    change_notes: str | None = None


class TemplateDetail(TemplateSummary):
    versions: list[TemplateVersionResponse] = Field(default_factory=list)


class TemplateVersionCreate(CamelSchema):
    format: DocumentTemplateFormat = DocumentTemplateFormat.HTML
    body: str = Field(..., min_length=1)
    header: str | None = None
    footer: str | None = None
    style_config: dict[str, Any] = Field(default_factory=dict)
    variable_schema: dict[str, Any] = Field(default_factory=dict)
    required_variables: list[str] = Field(default_factory=list)
    locked_blocks: list[dict[str, Any]] = Field(default_factory=list)
    source_document_id: UUID | None = None
    change_notes: str | None = None


class VariableDefinition(CamelSchema):
    key: str
    label: str
    description: str
    required: bool = False
    formatter: str | None = None


class VariableListResponse(CamelSchema):
    module: DocumentModule
    document_type: str | None = None
    items: list[VariableDefinition]


class PreviewRequest(CamelSchema):
    template_version_id: UUID | None = None
    body: str | None = None
    header: str | None = None
    footer: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class PreviewResponse(CamelSchema):
    rendered_html: str
    missing_variables: list[str] = Field(default_factory=list)


class GenerateDocumentRequest(CamelSchema):
    template_id: UUID | None = None
    template_version_id: UUID | None = None
    module: DocumentModule
    document_type: str
    document_subtype: str | None = None
    entity_type: str
    entity_id: UUID
    context: dict[str, Any] = Field(default_factory=dict)
    generated_from: str | None = None
    business_number: str | None = None
    file_name: str | None = None
    portal_visible: bool | None = None


class GeneratedDocumentResponse(CamelSchema):
    id: UUID
    module: DocumentModule
    document_type: str
    document_subtype: str | None = None
    template_id: UUID
    template_version_id: UUID
    template_code: str
    template_version: int
    dms_document_id: UUID
    folder_id: UUID | None = None
    entity_type: str
    entity_id: UUID
    generated_from: str | None = None
    business_number: str | None = None
    render_snapshot: dict[str, Any] = Field(default_factory=dict)
    checksum: str | None = None
    portal_visible: bool
    finalized_at: datetime
    finalized_by_id: UUID | None = None


class DocumentPackageItemResponse(CamelSchema):
    id: UUID
    package_id: UUID
    dms_document_id: UUID
    generated_document_id: UUID | None = None
    role: str
    sort_order: int


class DocumentPackageCreate(CamelSchema):
    package_type: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: UUID
    manifest: dict[str, Any] = Field(default_factory=dict)


class DocumentPackageAddItem(CamelSchema):
    dms_document_id: UUID
    generated_document_id: UUID | None = None
    role: str = Field(default="SUPPORTING", min_length=1, max_length=100)
    sort_order: int = 0


class DocumentPackageFinalize(CamelSchema):
    manifest: dict[str, Any] | None = None


class DocumentPackageResponse(CamelSchema):
    id: UUID
    package_number: str
    package_type: str
    name: str
    status: DocumentPackageStatus
    entity_type: str
    entity_id: UUID
    manifest: dict[str, Any] = Field(default_factory=dict)
    finalized_at: datetime | None = None
    finalized_by_id: UUID | None = None


class DocumentPackageDetailResponse(DocumentPackageResponse):
    items: list[DocumentPackageItemResponse] = Field(default_factory=list)


class DocumentPackageListResponse(CamelSchema):
    items: list[DocumentPackageResponse]
    total: int
