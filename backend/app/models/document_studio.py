"""Platform document studio models.

These tables provide a governed, tenant-scoped customer communication
management layer for generated documents. DMS remains the system of record for
the actual file bytes; these rows preserve template governance and render
lineage.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DocumentModule(StrEnum):
    LENDING = "LENDING"
    TREASURY = "TREASURY"
    HRIS = "HRIS"
    PAYROLL = "PAYROLL"
    LEGAL = "LEGAL"
    FINANCE = "FINANCE"
    AP_AR = "AP_AR"
    VENDOR_PORTAL = "VENDOR_PORTAL"
    BORROWER_PORTAL = "BORROWER_PORTAL"
    ESS = "ESS"


class DocumentTemplateStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"


class DocumentTemplateFormat(StrEnum):
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    DOCX = "DOCX"
    PDF_BACKGROUND = "PDF_BACKGROUND"


class DocumentPackageStatus(StrEnum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    SENT = "SENT"
    ARCHIVED = "ARCHIVED"


class DocumentStudioTemplate(BaseModel):
    """Tenant-scoped reusable template shell."""

    __tablename__ = "dst_template"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_dst_template_org_code"),
        Index("ix_dst_template_org_module_type", "organization_id", "module", "document_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[DocumentModule] = mapped_column(
        Enum(DocumentModule, native_enum=False), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    product_code: Mapped[str | None] = mapped_column(String(100))
    entity_type: Mapped[str | None] = mapped_column(String(100))
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    channel: Mapped[str] = mapped_column(String(40), nullable=False, default="PDF")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    selection_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    versions: Mapped[list[DocumentStudioTemplateVersion]] = relationship(
        "DocumentStudioTemplateVersion",
        back_populates="template",
        lazy="selectin",
    )


class DocumentStudioTemplateVersion(BaseModel):
    """Immutable authored content version for a template."""

    __tablename__ = "dst_template_version"
    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_dst_template_version_number"),
        Index("ix_dst_template_version_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dst_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentTemplateStatus] = mapped_column(
        Enum(DocumentTemplateStatus, native_enum=False),
        nullable=False,
        default=DocumentTemplateStatus.DRAFT,
    )
    format: Mapped[DocumentTemplateFormat] = mapped_column(
        Enum(DocumentTemplateFormat, native_enum=False),
        nullable=False,
        default=DocumentTemplateFormat.HTML,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    header: Mapped[str | None] = mapped_column(Text)
    footer: Mapped[str | None] = mapped_column(Text)
    style_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    variable_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    required_variables: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    locked_blocks: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    source_document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="SET NULL"),
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    change_notes: Mapped[str | None] = mapped_column(Text)

    template: Mapped[DocumentStudioTemplate] = relationship(
        "DocumentStudioTemplate",
        back_populates="versions",
        lazy="selectin",
    )


class GeneratedDocument(BaseModel):
    """Render lineage for a finalized generated document stored in DMS."""

    __tablename__ = "dst_generated_document"
    __table_args__ = (
        Index("ix_dst_generated_document_entity", "organization_id", "entity_type", "entity_id"),
        Index("ix_dst_generated_document_template", "template_id", "template_version_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[DocumentModule] = mapped_column(
        Enum(DocumentModule, native_enum=False), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_subtype: Mapped[str | None] = mapped_column(String(100))
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dst_template.id", ondelete="RESTRICT"), nullable=False
    )
    template_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dst_template_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_code: Mapped[str] = mapped_column(String(100), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    dms_document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dms_document.id", ondelete="RESTRICT"), nullable=False
    )
    folder_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dms_folder.id", ondelete="SET NULL")
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    generated_from: Mapped[str | None] = mapped_column(String(100))
    business_number: Mapped[str | None] = mapped_column(String(100))
    render_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    checksum: Mapped[str | None] = mapped_column(String(128))
    portal_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    finalized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalized_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("mst_user.id", ondelete="SET NULL")
    )


class DocumentPackage(BaseModel):
    """Governed group of documents for a business process."""

    __tablename__ = "dst_document_package"
    __table_args__ = (
        Index("ix_dst_document_package_entity", "organization_id", "entity_type", "entity_id"),
        UniqueConstraint("organization_id", "package_number", name="uq_dst_package_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_number: Mapped[str] = mapped_column(String(100), nullable=False)
    package_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DocumentPackageStatus] = mapped_column(
        Enum(DocumentPackageStatus, native_enum=False),
        nullable=False,
        default=DocumentPackageStatus.DRAFT,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("mst_user.id", ondelete="SET NULL")
    )


class DocumentPackageItem(BaseModel):
    """Document included in a package."""

    __tablename__ = "dst_document_package_item"
    __table_args__ = (
        UniqueConstraint("package_id", "dms_document_id", name="uq_dst_package_item_doc"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dst_document_package.id", ondelete="CASCADE"),
        nullable=False,
    )
    dms_document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="RESTRICT"),
        nullable=False,
    )
    generated_document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dst_generated_document.id", ondelete="SET NULL"),
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="SUPPORTING")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
