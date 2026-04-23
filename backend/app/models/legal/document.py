"""Legal Document management models with versioning.

Provides comprehensive document management for legal cases
including version control and checklist tracking.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.legal.enums import DocumentCategory

if TYPE_CHECKING:
    from app.models.lending.collections import LegalCase


class LegalDocumentType(BaseModel):
    """Master table for legal document types.

    Defines the types of documents that can be uploaded
    for legal cases with their requirements.
    """

    __tablename__ = "mst_legal_document_type"
    __table_args__ = (
        Index("ix_legal_doc_type_org", "organization_id"),
        Index("ix_legal_doc_type_category", "category"),
        UniqueConstraint(
            "organization_id", "type_code", name="uq_legal_doc_type_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Type Details
    type_code: Mapped[str] = mapped_column(String(50), nullable=False)
    type_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(String(50), nullable=False)

    # Requirements
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_original: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_certification: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_notarization: Mapped[bool] = mapped_column(Boolean, default=False)

    # Applicable For
    applicable_case_types: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # List of LegalCaseType values
    applicable_forums: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # List of LegalForumType values

    # Validation
    allowed_formats: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # List: ["PDF", "JPEG", "PNG"]
    max_file_size_mb: Mapped[Optional[int]] = mapped_column(Integer)

    # Display Order
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    documents: Mapped[List["LegalDocument"]] = relationship(
        back_populates="document_type"
    )
    checklist_items: Mapped[List["LegalDocumentChecklist"]] = relationship(
        back_populates="document_type"
    )


class LegalDocument(BaseModel):
    """Legal documents uploaded for cases.

    Stores documents with version control and metadata
    for complete audit trail.
    """

    __tablename__ = "txn_legal_document"
    __table_args__ = (
        Index("ix_legal_doc_org", "organization_id"),
        Index("ix_legal_doc_case", "legal_case_id"),
        Index("ix_legal_doc_type", "document_type_id"),
        Index("ix_legal_doc_category", "category"),
        UniqueConstraint(
            "organization_id",
            "document_reference",
            name="uq_legal_doc_reference",
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    document_type_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_legal_document_type.id"),
    )

    # Document Identity
    document_reference: Mapped[str] = mapped_column(String(50), nullable=False)
    document_name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(String(50), nullable=False)

    # Document Details
    document_number: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # External reference like order number
    document_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # File Details
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Version Control
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    # Authentication
    is_original: Mapped[bool] = mapped_column(Boolean, default=False)
    is_certified_copy: Mapped[bool] = mapped_column(Boolean, default=False)
    certified_by: Mapped[Optional[str]] = mapped_column(String(200))
    certification_date: Mapped[Optional[date]] = mapped_column(Date)
    is_notarized: Mapped[bool] = mapped_column(Boolean, default=False)
    notarized_by: Mapped[Optional[str]] = mapped_column(String(200))
    notarization_date: Mapped[Optional[date]] = mapped_column(Date)

    # Court Filing
    is_filed_with_court: Mapped[bool] = mapped_column(Boolean, default=False)
    filing_date: Mapped[Optional[date]] = mapped_column(Date)
    filing_index_number: Mapped[Optional[str]] = mapped_column(String(50))
    filed_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Tags for searching
    tags: Mapped[Optional[dict]] = mapped_column(JSONB)  # List of tags

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    document_type: Mapped[Optional["LegalDocumentType"]] = relationship(
        back_populates="documents"
    )
    legal_case: Mapped["LegalCase"] = relationship()
    versions: Mapped[List["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentVersion(BaseModel):
    """Version history for legal documents.

    Tracks all versions of a document with change history.
    """

    __tablename__ = "txn_document_version"
    __table_args__ = (
        Index("ix_doc_version_document", "legal_document_id"),
        Index("ix_doc_version_number", "version_number"),
        UniqueConstraint(
            "legal_document_id",
            "version_number",
            name="uq_doc_version",
        ),
    )

    # Foreign Keys
    legal_document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_document.id"),
        nullable=False,
    )
    previous_version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_document_version.id"),
    )

    # Version Details
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # File Details
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Change Details
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(Text)
    changed_by_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Status
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False)
    superseded_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_document_version.id"),
    )

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    document: Mapped["LegalDocument"] = relationship(back_populates="versions")
    previous_version: Mapped[Optional["DocumentVersion"]] = relationship(
        foreign_keys=[previous_version_id],
        remote_side="DocumentVersion.id",
    )


class LegalDocumentChecklist(BaseModel):
    """Document checklist for legal cases.

    Tracks required documents for each case and their status.
    """

    __tablename__ = "txn_legal_document_checklist"
    __table_args__ = (
        Index("ix_doc_checklist_case", "legal_case_id"),
        Index("ix_doc_checklist_type", "document_type_id"),
        UniqueConstraint(
            "legal_case_id",
            "document_type_id",
            name="uq_case_doc_checklist",
        ),
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    document_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_legal_document_type.id"),
        nullable=False,
    )
    document_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_document.id"),
    )

    # Checklist Item
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    verified_by_name: Mapped[Optional[str]] = mapped_column(String(200))
    verified_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Requirements
    requires_original: Mapped[bool] = mapped_column(Boolean, default=False)
    has_original: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_certified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_certified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Deficiency
    is_deficient: Mapped[bool] = mapped_column(Boolean, default=False)
    deficiency_reason: Mapped[Optional[str]] = mapped_column(Text)
    deficiency_raised_date: Mapped[Optional[date]] = mapped_column(Date)
    deficiency_resolved_date: Mapped[Optional[date]] = mapped_column(Date)

    # Due Date
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    document_type: Mapped["LegalDocumentType"] = relationship(
        back_populates="checklist_items"
    )
    document: Mapped[Optional["LegalDocument"]] = relationship()
    legal_case: Mapped["LegalCase"] = relationship()
