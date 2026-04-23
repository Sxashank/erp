"""Legal Notice management models.

Provides comprehensive notice generation, tracking, and delivery
management for various Indian legal proceedings.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.legal.enums import (
    NoticeType,
    NoticeStatus,
    DeliveryMode,
    DeliveryStatus,
)

if TYPE_CHECKING:
    from app.models.lending.loan_account import LoanAccount
    from app.models.lending.collections import LegalCase


class NoticeTemplate(BaseModel):
    """Legal notice templates.

    Pre-defined templates for various types of legal notices
    as per Indian legal requirements.
    """

    __tablename__ = "mst_notice_template"
    __table_args__ = (
        Index("ix_notice_template_org", "organization_id"),
        Index("ix_notice_template_type", "notice_type"),
        UniqueConstraint(
            "organization_id", "template_code", name="uq_notice_template_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Template Details
    template_code: Mapped[str] = mapped_column(String(50), nullable=False)
    template_name: Mapped[str] = mapped_column(String(200), nullable=False)
    notice_type: Mapped[NoticeType] = mapped_column(String(50), nullable=False)

    # Legal Reference
    act_reference: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # e.g., "SARFAESI Act 2002, Section 13(2)"
    section_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Statutory Period
    statutory_period_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # e.g., 60 days for 13(2)
    response_period_days: Mapped[Optional[int]] = mapped_column(Integer)

    # Template Content
    template_content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # HTML/Text template with placeholders
    template_format: Mapped[str] = mapped_column(
        String(20), default="HTML"
    )  # HTML, TEXT, PDF

    # Placeholders as JSON array
    placeholders: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # List of placeholders like {{borrower_name}}, {{amount}}

    # Language Support
    language: Mapped[str] = mapped_column(
        String(20), default="ENGLISH"
    )  # ENGLISH, HINDI, REGIONAL

    # Status
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    notices: Mapped[List["LegalNotice"]] = relationship(back_populates="template")


class LegalNotice(BaseModel):
    """Generated legal notices.

    Tracks all legal notices generated for loan accounts
    with full audit trail.
    """

    __tablename__ = "txn_legal_notice"
    __table_args__ = (
        Index("ix_legal_notice_org", "organization_id"),
        Index("ix_legal_notice_loan", "loan_account_id"),
        Index("ix_legal_notice_case", "legal_case_id"),
        Index("ix_legal_notice_type", "notice_type"),
        Index("ix_legal_notice_status", "status"),
        Index("ix_legal_notice_date", "notice_date"),
        UniqueConstraint(
            "organization_id", "notice_number", name="uq_legal_notice_number"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )
    legal_case_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
    )
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_notice_template.id"),
    )

    # Notice Identity
    notice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    notice_type: Mapped[NoticeType] = mapped_column(String(50), nullable=False)
    status: Mapped[NoticeStatus] = mapped_column(
        String(50), default=NoticeStatus.DRAFT
    )

    # Dates
    notice_date: Mapped[date] = mapped_column(Date, nullable=False)
    statutory_period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    response_due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Borrower Details (denormalized for notice generation)
    borrower_name: Mapped[str] = mapped_column(String(200), nullable=False)
    borrower_address: Mapped[str] = mapped_column(Text, nullable=False)
    co_borrower_names: Mapped[Optional[str]] = mapped_column(Text)
    guarantor_names: Mapped[Optional[str]] = mapped_column(Text)

    # Loan Details (as on notice date)
    loan_account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    principal_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    interest_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    penal_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    other_charges: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    total_amount_demanded: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    future_interest_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))

    # Security Details (for SARFAESI notices)
    security_description: Mapped[Optional[str]] = mapped_column(Text)
    security_address: Mapped[Optional[str]] = mapped_column(Text)
    security_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Legal Reference
    act_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    section_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Generated Content
    notice_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="ENGLISH")

    # Approval
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[Optional[str]] = mapped_column(String(200))
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Document
    document_path: Mapped[Optional[str]] = mapped_column(String(500))
    document_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    template: Mapped[Optional["NoticeTemplate"]] = relationship(back_populates="notices")
    deliveries: Mapped[List["NoticeDelivery"]] = relationship(
        back_populates="notice",
        cascade="all, delete-orphan",
    )
    responses: Mapped[List["NoticeResponse"]] = relationship(
        back_populates="notice",
        cascade="all, delete-orphan",
    )
    loan_account: Mapped["LoanAccount"] = relationship()
    legal_case: Mapped[Optional["LegalCase"]] = relationship()


class NoticeDelivery(BaseModel):
    """Notice delivery tracking.

    Tracks delivery attempts and status for each notice
    across multiple delivery modes.
    """

    __tablename__ = "txn_notice_delivery"
    __table_args__ = (
        Index("ix_notice_delivery_notice", "legal_notice_id"),
        Index("ix_notice_delivery_status", "delivery_status"),
        Index("ix_notice_delivery_mode", "delivery_mode"),
    )

    # Foreign Keys
    legal_notice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_notice.id"),
        nullable=False,
    )

    # Delivery Details
    delivery_mode: Mapped[DeliveryMode] = mapped_column(String(50), nullable=False)
    delivery_attempt: Mapped[int] = mapped_column(
        Integer, default=1
    )  # Attempt number
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        String(50), default=DeliveryStatus.PENDING
    )

    # Recipient
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipient_type: Mapped[str] = mapped_column(
        String(50), default="BORROWER"
    )  # BORROWER, CO_BORROWER, GUARANTOR
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)

    # Dispatch Details
    dispatch_date: Mapped[Optional[date]] = mapped_column(Date)
    dispatch_time: Mapped[Optional[str]] = mapped_column(String(20))
    dispatched_by: Mapped[Optional[str]] = mapped_column(String(200))

    # Tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    consignment_number: Mapped[Optional[str]] = mapped_column(String(100))
    courier_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Delivery Confirmation
    delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    delivery_time: Mapped[Optional[str]] = mapped_column(String(20))
    received_by: Mapped[Optional[str]] = mapped_column(String(200))
    relationship_to_borrower: Mapped[Optional[str]] = mapped_column(String(100))

    # Proof of Delivery
    pod_document_path: Mapped[Optional[str]] = mapped_column(String(500))
    pod_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Return/Failure Details
    return_date: Mapped[Optional[date]] = mapped_column(Date)
    return_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Publication Details (for notice via newspaper)
    publication_name: Mapped[Optional[str]] = mapped_column(String(200))
    publication_date: Mapped[Optional[date]] = mapped_column(Date)
    publication_edition: Mapped[Optional[str]] = mapped_column(String(100))
    publication_page: Mapped[Optional[str]] = mapped_column(String(20))
    publication_proof_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Email/SMS Details
    email_id: Mapped[Optional[str]] = mapped_column(String(255))
    mobile_number: Mapped[Optional[str]] = mapped_column(String(20))
    message_id: Mapped[Optional[str]] = mapped_column(String(100))
    delivery_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    read_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Cost
    delivery_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    notice: Mapped["LegalNotice"] = relationship(back_populates="deliveries")


class NoticeResponse(BaseModel):
    """Responses received for legal notices.

    Tracks borrower responses to legal notices including
    objections and representations.
    """

    __tablename__ = "txn_notice_response"
    __table_args__ = (
        Index("ix_notice_response_notice", "legal_notice_id"),
        Index("ix_notice_response_date", "response_date"),
    )

    # Foreign Keys
    legal_notice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_notice.id"),
        nullable=False,
    )

    # Response Details
    response_date: Mapped[date] = mapped_column(Date, nullable=False)
    response_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # OBJECTION, REPRESENTATION, REPLY, PAYMENT_PROPOSAL

    # Respondent
    respondent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    respondent_type: Mapped[str] = mapped_column(
        String(50), default="BORROWER"
    )  # BORROWER, CO_BORROWER, GUARANTOR, ADVOCATE

    # Receipt Details
    received_mode: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # POST, COURIER, EMAIL, HAND_DELIVERY
    received_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Content
    response_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[Optional[dict]] = mapped_column(JSONB)  # List of key points

    # Document
    document_path: Mapped[Optional[str]] = mapped_column(String(500))
    document_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # For Objection under Section 13(3A) SARFAESI
    is_valid_objection: Mapped[Optional[bool]] = mapped_column(Boolean)
    objection_grounds: Mapped[Optional[str]] = mapped_column(Text)
    disposal_date: Mapped[Optional[date]] = mapped_column(Date)
    disposal_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Our Response
    our_reply_date: Mapped[Optional[date]] = mapped_column(Date)
    our_reply_summary: Mapped[Optional[str]] = mapped_column(Text)
    our_reply_document_path: Mapped[Optional[str]] = mapped_column(String(500))

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    notice: Mapped["LegalNotice"] = relationship(back_populates="responses")
