"""DMS Document models."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DocumentStatus(str, enum.Enum):
    """Document status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentAccessLevel(str, enum.Enum):
    """Document access levels."""

    PRIVATE = "private"
    RESTRICTED = "restricted"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class DMSDocument(BaseModel):
    """Document in the DMS."""

    __tablename__ = "dms_document"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Folder reference
    folder_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_folder.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Document identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Auto-generated document code",
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File information
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Size in bytes")

    # Storage
    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="Path in storage system",
    )
    storage_provider: Mapped[str] = mapped_column(
        String(50),
        default="local",
        nullable=False,
        comment="s3, azure, gcs, local",
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="MD5 or SHA256 hash",
    )

    # Metadata
    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Type category (e.g., kyc, legal, financial)",
    )
    document_subtype: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Subtype (e.g., pan_card, loan_agreement)",
    )

    # Status and access
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        default=DocumentStatus.ACTIVE,
        nullable=False,
    )
    access_level: Mapped[DocumentAccessLevel] = mapped_column(
        Enum(DocumentAccessLevel, native_enum=False),
        default=DocumentAccessLevel.ORGANIZATION,
        nullable=False,
    )

    # Version tracking
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Entity reference (link to business entity)
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., loan, customer, employee",
    )
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # OCR and content extraction
    is_ocr_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Search keywords
    keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="Search keywords",
    )

    # Expiry
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization = relationship("Organization", lazy="selectin")
    folder = relationship("DMSFolder", back_populates="documents", lazy="selectin")
    versions = relationship("DMSDocumentVersion", back_populates="document", lazy="dynamic")
    access_list = relationship("DMSDocumentAccess", back_populates="document", lazy="dynamic")
    tags = relationship("DMSDocumentTag", back_populates="document", lazy="selectin")
    history = relationship("DMSDocumentHistory", back_populates="document", lazy="dynamic")


class DMSDocumentVersion(BaseModel):
    """Document version history."""

    __tablename__ = "dms_document_version"

    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version info
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File information (may differ from current version)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Status
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    document = relationship("DMSDocument", back_populates="versions")


class DMSDocumentAccess(BaseModel):
    """Document access control list entry."""

    __tablename__ = "dms_document_access"

    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Access grantee (user or role)
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=True,
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Permissions
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Access expiry
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("DMSDocument", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    role = relationship("Role", foreign_keys=[role_id], lazy="selectin")


class DMSDocumentHistory(BaseModel):
    """Document action history for audit trail."""

    __tablename__ = "dms_document_history"

    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="created, viewed, downloaded, updated, shared, deleted",
    )
    action_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Actor
    performed_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # IP/Client info
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    document = relationship("DMSDocument", back_populates="history")
    user = relationship("User", foreign_keys=[performed_by], lazy="selectin")
