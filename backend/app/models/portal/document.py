"""Portal Document Models.

Handles document access, requests, and KYC verification.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.portal.enums import (
    PortalDocumentType,
    DocumentRequestStatus,
    KYCType,
    KYCStatus,
)


class PortalDocument(BaseModel):
    """Documents available to customer in portal.

    Provides access to loan documents, statements, certificates.
    """

    __tablename__ = "portal_document"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("lms_loan_account.id"),
        index=True,
    )

    # Document Info
    document_type: Mapped[PortalDocumentType] = mapped_column(nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # File Info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PDF, etc.
    file_size: Mapped[int] = mapped_column(nullable=False)  # bytes
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA256

    # Document specific details
    document_date: Mapped[Optional[date]] = mapped_column(Date)
    period_from: Mapped[Optional[date]] = mapped_column(Date)
    period_to: Mapped[Optional[date]] = mapped_column(Date)
    financial_year: Mapped[Optional[str]] = mapped_column(String(10))  # 2024-25

    # Access Control
    is_downloadable: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_otp: Mapped[bool] = mapped_column(Boolean, default=False)
    is_watermarked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Access Tracking
    view_count: Mapped[int] = mapped_column(default=0)
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    download_count: Mapped[int] = mapped_column(default=0)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Generation Info (for auto-generated documents)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_params: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    source_document_id: Mapped[Optional[UUID]] = mapped_column()

    __table_args__ = (
        Index("ix_portal_doc_user_type", "user_id", "document_type"),
        Index("ix_portal_doc_loan", "loan_account_id", "document_type"),
    )


class PortalDocumentRequest(BaseModel):
    """Document requests from customers.

    Handles requests for documents like NOC, statements, certificates.
    """

    __tablename__ = "portal_document_request"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("lms_loan_account.id"),
        index=True,
    )

    # Request Info
    request_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    document_type: Mapped[PortalDocumentType] = mapped_column(nullable=False)
    request_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Parameters (for statements, certificates)
    period_from: Mapped[Optional[date]] = mapped_column(Date)
    period_to: Mapped[Optional[date]] = mapped_column(Date)
    financial_year: Mapped[Optional[str]] = mapped_column(String(10))
    additional_params: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # Delivery
    delivery_mode: Mapped[str] = mapped_column(
        String(20), default="DOWNLOAD"
    )  # DOWNLOAD, EMAIL, COURIER
    delivery_address: Mapped[Optional[str]] = mapped_column(Text)
    delivery_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    status: Mapped[DocumentRequestStatus] = mapped_column(
        default=DocumentRequestStatus.REQUESTED
    )
    status_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Processing
    processed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Fulfillment
    generated_document_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("portal_document.id")
    )
    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    courier_tracking: Mapped[Optional[str]] = mapped_column(String(100))

    # Charges (if applicable)
    charges_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    charges_amount: Mapped[Optional[float]] = mapped_column()
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_portal_doc_req_user", "user_id", "status"),
        Index("ix_portal_doc_req_org", "organization_id", "status"),
    )


class PortalKYCVerification(BaseModel):
    """eKYC verification records.

    Tracks Aadhaar eKYC, PAN verification, Video KYC.
    """

    __tablename__ = "portal_kyc_verification"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_customer.id"),
        nullable=False,
        index=True,
    )

    # KYC Type
    kyc_type: Mapped[KYCType] = mapped_column(nullable=False)
    reference_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    # Input Data
    aadhaar_last4: Mapped[Optional[str]] = mapped_column(String(4))
    aadhaar_reference_id: Mapped[Optional[str]] = mapped_column(String(100))
    pan_number: Mapped[Optional[str]] = mapped_column(String(10))
    ckyc_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Verification Status
    status: Mapped[KYCStatus] = mapped_column(default=KYCStatus.INITIATED)
    status_message: Mapped[Optional[str]] = mapped_column(String(500))

    # UIDAI/Provider Response
    provider_name: Mapped[Optional[str]] = mapped_column(String(50))
    provider_txn_id: Mapped[Optional[str]] = mapped_column(String(100))
    verification_response: Mapped[Optional[str]] = mapped_column(Text)  # JSON (sanitized)

    # Extracted Data
    verified_name: Mapped[Optional[str]] = mapped_column(String(200))
    verified_dob: Mapped[Optional[date]] = mapped_column(Date)
    verified_gender: Mapped[Optional[str]] = mapped_column(String(10))
    verified_address: Mapped[Optional[str]] = mapped_column(Text)
    photo_match_score: Mapped[Optional[float]] = mapped_column()

    # Timestamps
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    otp_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    otp_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Device Info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    device_id: Mapped[Optional[str]] = mapped_column(String(255))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Audit
    consent_captured: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    consent_text: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_portal_kyc_user_type", "user_id", "kyc_type"),
        Index("ix_portal_kyc_customer", "customer_id", "kyc_type"),
    )
