"""GSTN Portal Integration models for return filing and ITC reconciliation."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, ForeignKey, Enum as SQLEnum, Boolean, Date, DateTime,
    Numeric, Integer, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, VersionedMixin

if TYPE_CHECKING:
    from app.models.gst.gst_registration import GSTRegistration


# =============================================================================
# Enums for GSTN Integration
# =============================================================================

class GSTReturnType(str, Enum):
    """GST Return form types."""
    GSTR1 = "GSTR1"          # Outward supplies
    GSTR2A = "GSTR2A"        # Auto-populated inward supplies (read-only)
    GSTR2B = "GSTR2B"        # Auto-generated ITC statement (read-only)
    GSTR3B = "GSTR3B"        # Summary return
    GSTR4 = "GSTR4"          # Quarterly return for composition dealers
    GSTR9 = "GSTR9"          # Annual return
    GSTR9C = "GSTR9C"        # Reconciliation statement


class GSTReturnStatus(str, Enum):
    """Status of GST return filing."""
    NOT_STARTED = "NOT_STARTED"
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    FILED = "FILED"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAYMENT_DONE = "PAYMENT_DONE"
    ERROR = "ERROR"


class GSTNSessionStatus(str, Enum):
    """Status of GSTN API session."""
    ACTIVE = "ACTIVE"
    OTP_PENDING = "OTP_PENDING"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


class ITCMismatchType(str, Enum):
    """Type of ITC mismatch between books and GSTR-2B."""
    MISSING_IN_2B = "MISSING_IN_2B"      # Invoice in books but not in 2B
    MISSING_IN_BOOKS = "MISSING_IN_BOOKS"  # Invoice in 2B but not in books
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"   # Amount differs
    GSTIN_MISMATCH = "GSTIN_MISMATCH"     # GSTIN differs
    DATE_MISMATCH = "DATE_MISMATCH"       # Invoice date differs


class ITCMismatchResolution(str, Enum):
    """Resolution status of ITC mismatch."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"           # Accept 2B value
    REJECTED = "REJECTED"           # Reject 2B, use books value
    SUPPLIER_ACTION = "SUPPLIER_ACTION"  # Supplier needs to amend
    IGNORED = "IGNORED"             # Ignore mismatch


class GSTR1Section(str, Enum):
    """GSTR-1 sections for invoice categorization."""
    B2B = "B2B"                    # B2B invoices (>2.5L)
    B2CL = "B2CL"                  # B2C Large (>2.5L, inter-state)
    B2CS = "B2CS"                  # B2C Small (<2.5L)
    CDNR = "CDNR"                  # Credit/Debit notes (registered)
    CDNUR = "CDNUR"                # Credit/Debit notes (unregistered)
    EXP = "EXP"                    # Exports
    AT = "AT"                      # Advances received (tax rate wise)
    ATADJ = "ATADJ"                # Advance adjustments
    NIL = "NIL"                    # Nil rated/exempted
    HSN = "HSN"                    # HSN-wise summary
    DOC = "DOC"                    # Document summary


# =============================================================================
# GSTN Session Model - API Authentication
# =============================================================================

class GSTNSession(Base, TimestampMixin, VersionedMixin):
    """GSTN API session for authenticated API calls.

    Stores session tokens for GSTN portal access via OTP/EVC authentication.
    Sessions are tenant-specific and GSTIN-specific.
    """

    __tablename__ = "gst_gstn_session"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
        comment="GSTIN for which session is created",
    )
    status: Mapped[GSTNSessionStatus] = mapped_column(
        SQLEnum(GSTNSessionStatus),
        nullable=False,
        default=GSTNSessionStatus.OTP_PENDING,
    )
    # Authentication tokens (encrypted)
    auth_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="GSTN auth token (encrypted)",
    )
    sek_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Session encryption key (encrypted)",
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # OTP request tracking
    otp_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    otp_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="OTP reference from GSTN",
    )
    # Session metadata
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # User who initiated the session
    initiated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_gstn_session_org_gstin", "organization_id", "gstin"),
        Index("ix_gstn_session_status_expires", "status", "token_expires_at"),
    )

    def __repr__(self) -> str:
        return f"<GSTNSession(gstin={self.gstin}, status={self.status})>"

    @property
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        if self.status != GSTNSessionStatus.ACTIVE:
            return False
        if not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at.replace(tzinfo=None)


# =============================================================================
# GST Return Filing Model
# =============================================================================

class GSTReturnFiling(Base, TimestampMixin, VersionedMixin):
    """GST return filing record.

    Tracks the status and data for each GST return filing attempt.
    Supports GSTR-1, GSTR-3B, GSTR-2A/2B download, and annual returns.
    """

    __tablename__ = "gst_return_filing"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    return_type: Mapped[GSTReturnType] = mapped_column(
        SQLEnum(GSTReturnType),
        nullable=False,
        index=True,
    )
    return_period: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Return period in MMYYYY format",
    )
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Financial year e.g., 2024-25",
    )
    status: Mapped[GSTReturnStatus] = mapped_column(
        SQLEnum(GSTReturnStatus),
        nullable=False,
        default=GSTReturnStatus.NOT_STARTED,
    )
    # Filing details
    arn: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Acknowledgment Reference Number from GSTN",
    )
    filing_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    # Summary amounts
    total_taxable_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_igst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_cgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_sgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_cess: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_tax_liability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    total_itc_claimed: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    cash_payment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Tax paid in cash",
    )
    # Statistics (for GSTR-1)
    invoice_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    b2b_invoice_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    b2c_invoice_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    cdn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Credit/Debit note count",
    )
    # JSON data storage
    summary_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Summary data for the return",
    )
    section_wise_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Section-wise breakdown (B2B, B2C, etc.)",
    )
    error_details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Validation/submission errors",
    )
    # Workflow tracking
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    filed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # User tracking
    prepared_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Reference to GSTN session used
    gstn_session_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gst_gstn_session.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Late fee details
    late_fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    interest: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )
    gstn_session: Mapped[Optional["GSTNSession"]] = relationship(
        "GSTNSession",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "gstin", "return_type", "return_period",
            name="uq_gst_return_filing_period"
        ),
        Index("ix_gst_return_filing_period", "organization_id", "return_period"),
        Index("ix_gst_return_filing_type_status", "return_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<GSTReturnFiling(gstin={self.gstin}, type={self.return_type}, period={self.return_period})>"


# =============================================================================
# ITC Mismatch Model - GSTR-2B Reconciliation
# =============================================================================

class GSTItcMismatch(Base, TimestampMixin, VersionedMixin):
    """ITC mismatch record for GSTR-2B reconciliation.

    Tracks discrepancies between purchase records in books and
    supplier-reported data in GSTR-2B for ITC eligibility verification.
    """

    __tablename__ = "gst_itc_mismatch"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    return_period: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Return period in MMYYYY format",
    )
    # Supplier details
    supplier_gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    # Invoice details
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    invoice_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    mismatch_type: Mapped[ITCMismatchType] = mapped_column(
        SQLEnum(ITCMismatchType),
        nullable=False,
        index=True,
    )
    # Amount comparison - Books
    books_taxable_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    books_igst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    books_cgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    books_sgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    books_cess: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    books_total_tax: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    # Amount comparison - GSTR-2B
    gstr2b_taxable_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    gstr2b_igst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    gstr2b_cgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    gstr2b_sgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    gstr2b_cess: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    gstr2b_total_tax: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    # Variance
    variance_taxable: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    variance_igst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    variance_cgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    variance_sgst: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    variance_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    # Resolution
    resolution_status: Mapped[ITCMismatchResolution] = mapped_column(
        SQLEnum(ITCMismatchResolution),
        nullable=False,
        default=ITCMismatchResolution.PENDING,
        index=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Link to purchase bill if matched
    purchase_bill_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_purchase_bill.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Raw data from 2B for reference
    gstr2b_raw_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_itc_mismatch_period_supplier", "return_period", "supplier_gstin"),
        Index("ix_itc_mismatch_resolution", "organization_id", "resolution_status"),
        Index("ix_itc_mismatch_type", "organization_id", "mismatch_type"),
    )

    def __repr__(self) -> str:
        return f"<GSTItcMismatch(supplier={self.supplier_gstin}, inv={self.invoice_number}, type={self.mismatch_type})>"


# =============================================================================
# GSTR-2B Data Cache Model
# =============================================================================

class GSTR2BData(Base, TimestampMixin, VersionedMixin):
    """Cached GSTR-2B data from GSTN.

    Stores the downloaded GSTR-2B invoice data for reconciliation.
    Updated periodically by fetching from GSTN portal.
    """

    __tablename__ = "gst_gstr2b_data"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    return_period: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Return period in MMYYYY format",
    )
    # Supplier invoice details from 2B
    supplier_gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    supplier_filing_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Y/N - whether supplier filed GSTR-1",
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    invoice_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="R/DE/SEZ/SEZWOP etc.",
    )
    place_of_supply: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    reverse_charge: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    # Tax amounts
    taxable_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    igst: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    cgst: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    sgst: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    cess: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    # ITC eligibility
    itc_eligible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    itc_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether ITC was claimed for this invoice",
    )
    # Matching status
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    matched_purchase_bill_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_purchase_bill.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Fetch metadata
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    source_section: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Section in 2B (ITC Available, ITC Reversed, etc.)",
    )
    # Raw response for debugging
    raw_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "return_period", "supplier_gstin", "invoice_number",
            name="uq_gstr2b_invoice"
        ),
        Index("ix_gstr2b_period_gstin", "organization_id", "return_period"),
        Index("ix_gstr2b_supplier", "supplier_gstin", "return_period"),
        Index("ix_gstr2b_matched", "organization_id", "is_matched"),
    )

    def __repr__(self) -> str:
        return f"<GSTR2BData(supplier={self.supplier_gstin}, inv={self.invoice_number}, period={self.return_period})>"
