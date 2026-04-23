"""KYC and Credit Bureau models for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    KYCDocCategory, KYCVerificationStatus, KYCVerificationMethod,
    CKYCTransactionType, BureauType, BureauPullStatus
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.entity import Entity


class KYCDocumentType(BaseModel):
    """Master list of KYC document types."""

    __tablename__ = "los_kyc_document_type"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this document type belongs to",
    )

    # Document identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique document type code e.g., 'PAN_CARD', 'AADHAAR'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Document type name e.g., 'PAN Card'",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the document",
    )

    # Category
    category: Mapped[KYCDocCategory] = mapped_column(
        Enum(KYCDocCategory),
        nullable=False,
        index=True,
        comment="Category - IDENTITY, ADDRESS, FINANCIAL, etc.",
    )

    # Applicability
    applicable_for_individual: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Applicable for individual borrowers?",
    )
    applicable_for_corporate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Applicable for corporate borrowers?",
    )
    applicable_for_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Applicable for entity contacts (directors, etc.)?",
    )

    # Verification
    supports_api_verification: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Can be verified via API?",
    )
    verification_api_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="API integration code for verification",
    )
    supports_ocr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Can be processed via OCR?",
    )

    # Validity
    has_expiry: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Does this document expire?",
    )
    default_validity_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Default validity in days (for docs with expiry)",
    )

    # Requirements
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this document mandatory?",
    )
    mandatory_for_categories: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of entity types where this is mandatory",
    )

    # File requirements
    allowed_file_types: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["pdf", "jpg", "jpeg", "png"],
        comment="Allowed file extensions",
    )
    max_file_size_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Maximum file size in MB",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order in UI",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_kyc_doc_type_org_code"),
        Index("ix_los_kyc_doc_type_org_cat", "organization_id", "category"),
    )

    def __repr__(self) -> str:
        return f"<KYCDocumentType(code={self.code}, name={self.name})>"


class EntityKYCDocument(BaseModel):
    """KYC documents uploaded for an entity."""

    __tablename__ = "los_entity_kyc_document"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Document type reference
    document_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_kyc_document_type.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Document type",
    )

    # Optional contact reference (for director KYC, etc.)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_contact.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Contact if this is contact-level KYC",
    )

    # Document details
    document_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Document number (PAN, Aadhaar, etc.)",
    )
    document_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name as per document",
    )

    # File storage
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original file name",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path/key",
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes",
    )
    file_mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type of file",
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of file",
    )

    # Validity dates
    issue_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Document issue date",
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Document expiry date",
    )

    # Verification status
    verification_status: Mapped[KYCVerificationStatus] = mapped_column(
        Enum(KYCVerificationStatus),
        nullable=False,
        default=KYCVerificationStatus.PENDING,
        index=True,
        comment="Verification status - PENDING, VERIFIED, REJECTED, etc.",
    )
    verification_method: Mapped[Optional[KYCVerificationMethod]] = mapped_column(
        Enum(KYCVerificationMethod),
        nullable=True,
        comment="Method of verification - MANUAL, API, PHYSICAL, etc.",
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Verification timestamp",
    )
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who verified",
    )

    # Rejection/resubmission
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for rejection if rejected",
    )
    resubmission_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times resubmitted",
    )

    # API verification response
    api_verification_response: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Response from verification API",
    )
    api_verification_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="API transaction reference",
    )

    # OCR extracted data
    ocr_extracted_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Data extracted via OCR",
    )
    ocr_confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="OCR confidence score (0-100)",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional remarks",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="kyc_documents",
    )
    document_type: Mapped["KYCDocumentType"] = relationship(
        "KYCDocumentType",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_los_entity_kyc_doc_entity_type", "entity_id", "document_type_id"),
        Index("ix_los_entity_kyc_doc_status", "entity_id", "verification_status"),
        Index("ix_los_entity_kyc_doc_expiry", "expiry_date"),
    )

    def __repr__(self) -> str:
        return f"<EntityKYCDocument(entity={self.entity_id}, type={self.document_type_id}, status={self.verification_status})>"


class CKYCTransaction(BaseModel):
    """CKYC search/download/upload transaction log."""

    __tablename__ = "los_ckyc_transaction"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Entity reference (optional - may be search before entity creation)
    entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related entity if applicable",
    )

    # Transaction type
    transaction_type: Mapped[CKYCTransactionType] = mapped_column(
        Enum(CKYCTransactionType),
        nullable=False,
        index=True,
        comment="SEARCH, DOWNLOAD, UPLOAD, UPDATE",
    )

    # Search/input parameters
    search_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="PAN used for search",
    )
    search_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name used for search",
    )
    search_dob: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="DOB used for search",
    )

    # CKYC result
    ckyc_number: Mapped[Optional[str]] = mapped_column(
        String(14),
        nullable=True,
        index=True,
        comment="CKYC number returned/used",
    )
    ckyc_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CKYC record status",
    )

    # Transaction details
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="CKYC registry transaction ID",
    )
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Request timestamp",
    )
    response_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Response timestamp",
    )

    # Status
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Transaction successful?",
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Error code if failed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # Request/Response data (encrypted or sanitized)
    request_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sanitized request data",
    )
    response_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sanitized response data",
    )

    # Download result
    downloaded_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to downloaded CKYC record",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    entity: Mapped[Optional["Entity"]] = relationship(
        "Entity",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_los_ckyc_txn_org_type", "organization_id", "transaction_type"),
        Index("ix_los_ckyc_txn_pan", "search_pan"),
        Index("ix_los_ckyc_txn_ckyc", "ckyc_number"),
    )

    def __repr__(self) -> str:
        return f"<CKYCTransaction(type={self.transaction_type}, pan={self.search_pan}, success={self.is_success})>"


class BureauPull(BaseModel):
    """Credit bureau pull history."""

    __tablename__ = "los_bureau_pull"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Entity reference
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Entity for which bureau was pulled",
    )

    # Optional contact reference (for individual bureau pull)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_contact.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Contact if individual bureau pull",
    )

    # Bureau details
    bureau_type: Mapped[BureauType] = mapped_column(
        Enum(BureauType),
        nullable=False,
        index=True,
        comment="Bureau - CIBIL, EXPERIAN, EQUIFAX, CRIF_HIGH_MARK",
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CONSUMER",
        comment="Report type - CONSUMER, COMMERCIAL",
    )

    # Request details
    request_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Internal request reference",
    )
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Request timestamp",
    )

    # Input parameters used
    input_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="PAN used for pull",
    )
    input_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name used for pull",
    )
    input_dob: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="DOB used for pull",
    )
    input_mobile: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="Mobile used for pull",
    )
    input_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Address used for pull",
    )

    # Status
    status: Mapped[BureauPullStatus] = mapped_column(
        Enum(BureauPullStatus),
        nullable=False,
        default=BureauPullStatus.INITIATED,
        index=True,
        comment="Status - INITIATED, SUCCESS, FAILED, PARTIAL, NO_HIT",
    )
    response_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Response timestamp",
    )

    # Bureau response reference
    bureau_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bureau transaction reference",
    )
    bureau_report_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bureau report ID",
    )

    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Error code if failed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # Consent
    consent_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Consent reference number",
    )
    consent_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Consent timestamp",
    )

    # Purpose
    purpose: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="LOAN_APPLICATION",
        comment="Purpose of bureau pull",
    )
    application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Related loan application if applicable",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="bureau_pulls",
    )

    __table_args__ = (
        Index("ix_los_bureau_pull_entity_bureau", "entity_id", "bureau_type"),
        Index("ix_los_bureau_pull_org_status", "organization_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<BureauPull(entity={self.entity_id}, bureau={self.bureau_type}, status={self.status})>"


class BureauReport(BaseModel):
    """Credit bureau report data storage."""

    __tablename__ = "los_bureau_report"

    # Parent pull
    bureau_pull_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_bureau_pull.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent bureau pull",
    )

    # Report file
    report_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to stored report file (PDF/XML)",
    )
    report_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="JSON",
        comment="Report format - JSON, XML, PDF",
    )

    # Credit score
    credit_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Credit score (300-900 typically)",
    )
    score_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Score model version",
    )
    score_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Score calculation date",
    )

    # Score factors
    score_factors: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Factors affecting score",
    )

    # Account summary
    total_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total number of accounts",
    )
    active_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of active accounts",
    )
    closed_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of closed accounts",
    )
    overdue_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of overdue accounts",
    )
    default_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of default accounts",
    )
    written_off_accounts: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of written off accounts",
    )

    # Credit summary
    total_sanctioned_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total sanctioned amount across all loans",
    )
    total_outstanding: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total outstanding amount",
    )
    total_overdue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total overdue amount",
    )
    total_written_off: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total written off amount",
    )
    highest_dpd_last_12m: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Highest DPD in last 12 months",
    )
    highest_dpd_last_24m: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Highest DPD in last 24 months",
    )

    # Enquiry summary
    total_enquiries: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total enquiries",
    )
    enquiries_last_30d: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Enquiries in last 30 days",
    )
    enquiries_last_90d: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Enquiries in last 90 days",
    )
    enquiries_last_6m: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Enquiries in last 6 months",
    )
    enquiries_last_12m: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Enquiries in last 12 months",
    )

    # Payment history
    payment_history_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Months of payment history",
    )
    on_time_payments_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Percentage of on-time payments",
    )

    # Account details (stored as JSON array)
    account_details: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Detailed account information",
    )

    # Enquiry details (stored as JSON array)
    enquiry_details: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Detailed enquiry information",
    )

    # DPD history (month-wise)
    dpd_history: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Month-wise DPD history",
    )

    # Raw report data
    raw_report_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Complete raw report data",
    )

    # Analysis flags
    has_fraud_indicator: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Fraud indicators present?",
    )
    has_suit_filed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Suit filed cases present?",
    )
    has_wilful_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Wilful default flag?",
    )
    is_cibil_defaulter: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="In CIBIL defaulter list?",
    )

    # Relationships
    bureau_pull: Mapped["BureauPull"] = relationship(
        "BureauPull",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_los_bureau_report_score", "credit_score"),
    )

    def __repr__(self) -> str:
        return f"<BureauReport(pull={self.bureau_pull_id}, score={self.credit_score})>"
