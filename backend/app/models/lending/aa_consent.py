"""Account Aggregator models for consent management and data fetching."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean, Date, DateTime,
    ForeignKey, Enum as SQLEnum, Index, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.lending.enums import (
    AAProvider, AAConsentStatus, AAConsentPurpose, AAConsentMode,
    AAFetchFrequency, AAFIType, AAFetchSessionStatus, AADataStatus
)


class AAConsent(Base):
    """Account Aggregator consent request and tracking."""

    __tablename__ = "lms_aa_consent"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    # Customer/Entity reference
    entity_id = Column(PGUUID(as_uuid=True), ForeignKey("los_entity.id"), nullable=True)
    loan_application_id = Column(PGUUID(as_uuid=True), ForeignKey("los_loan_application.id"), nullable=True)
    loan_account_id = Column(PGUUID(as_uuid=True), ForeignKey("lms_loan_account.id"), nullable=True)

    # Customer identification for AA
    customer_id = Column(String(100), nullable=False)  # VUA (Virtual User Address) or mobile
    customer_name = Column(String(200), nullable=True)
    customer_mobile = Column(String(15), nullable=True)
    customer_email = Column(String(255), nullable=True)

    # AA Provider details
    provider = Column(SQLEnum(AAProvider), nullable=False)
    consent_handle = Column(String(100), unique=True, nullable=True)  # AA's consent handle
    consent_id = Column(String(100), unique=True, nullable=True)  # AA's consent ID after approval

    # Consent purpose and scope
    purpose = Column(SQLEnum(AAConsentPurpose), nullable=False, default=AAConsentPurpose.UNDERWRITING)
    purpose_description = Column(Text, nullable=True)
    consent_mode = Column(SQLEnum(AAConsentMode), nullable=False, default=AAConsentMode.VIEW)

    # FI Types requested
    fi_types = Column(JSONB, nullable=False, default=list)  # List of AAFIType values

    # Data range
    fi_data_from = Column(Date, nullable=True)  # Start date for data
    fi_data_to = Column(Date, nullable=True)  # End date for data

    # Fetch configuration
    fetch_frequency = Column(SQLEnum(AAFetchFrequency), nullable=False, default=AAFetchFrequency.ONETIME)
    fetch_frequency_value = Column(Integer, nullable=True)  # For non-standard frequencies

    # Consent validity
    consent_start = Column(DateTime, nullable=True)  # When consent becomes active
    consent_expiry = Column(DateTime, nullable=True)  # When consent expires

    # Data life (how long we can store the data)
    data_life_unit = Column(String(20), nullable=True)  # MONTH, YEAR, INF
    data_life_value = Column(Integer, nullable=True)

    # Status tracking
    status = Column(SQLEnum(AAConsentStatus), nullable=False, default=AAConsentStatus.PENDING)
    status_updated_at = Column(DateTime, nullable=True)

    # Consent URL for customer to approve
    consent_url = Column(String(500), nullable=True)
    redirect_url = Column(String(500), nullable=True)  # Where to redirect after consent

    # Timestamps and audit
    request_timestamp = Column(DateTime, nullable=True)  # When request was sent to AA
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    aa_response = Column(JSONB, nullable=True)  # Full response from AA
    extra_data = Column(JSONB, nullable=True)  # Additional metadata

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    # Relationships
    entity = relationship("Entity")
    fetch_sessions = relationship("AAFetchSession", back_populates="consent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_aa_consent_org_status", "organization_id", "status"),
        Index("ix_aa_consent_customer", "customer_id"),
        Index("ix_aa_consent_handle", "consent_handle"),
        Index("ix_aa_consent_entity", "entity_id"),
    )

    def __repr__(self):
        return f"<AAConsent {self.consent_handle or self.id} - {self.status}>"


class AAFetchSession(Base):
    """AA data fetch session tracking."""

    __tablename__ = "lms_aa_fetch_session"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    consent_id = Column(PGUUID(as_uuid=True), ForeignKey("lms_aa_consent.id"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    # Session identifiers from AA
    session_id = Column(String(100), unique=True, nullable=True)
    data_session_id = Column(String(100), nullable=True)  # For data fetch

    # FI Types being fetched in this session
    fi_types_requested = Column(JSONB, nullable=False, default=list)

    # Date range for this fetch
    data_from = Column(Date, nullable=True)
    data_to = Column(Date, nullable=True)

    # Status
    status = Column(SQLEnum(AAFetchSessionStatus), nullable=False, default=AAFetchSessionStatus.INITIATED)

    # Counts
    total_accounts_requested = Column(Integer, default=0)
    accounts_received = Column(Integer, default=0)
    accounts_failed = Column(Integer, default=0)

    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow)
    data_requested_at = Column(DateTime, nullable=True)
    data_received_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # AA Response
    aa_response = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    consent = relationship("AAConsent", back_populates="fetch_sessions")
    bank_accounts = relationship("AABankAccount", back_populates="fetch_session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_aa_fetch_session_consent", "consent_id"),
        Index("ix_aa_fetch_session_status", "status"),
    )

    def __repr__(self):
        return f"<AAFetchSession {self.session_id or self.id} - {self.status}>"


class AABankAccount(Base):
    """Bank account data fetched via AA."""

    __tablename__ = "lms_aa_bank_account"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    fetch_session_id = Column(PGUUID(as_uuid=True), ForeignKey("lms_aa_fetch_session.id"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    # Entity reference
    entity_id = Column(PGUUID(as_uuid=True), ForeignKey("los_entity.id"), nullable=True)

    # FI Type
    fi_type = Column(SQLEnum(AAFIType), nullable=False, default=AAFIType.DEPOSIT)

    # FIP (Financial Information Provider) details
    fip_id = Column(String(50), nullable=True)
    fip_name = Column(String(200), nullable=True)

    # Account details
    account_type = Column(String(50), nullable=True)  # SAVINGS, CURRENT, etc.
    account_number_masked = Column(String(50), nullable=True)
    account_ref_number = Column(String(100), nullable=True)  # AA's reference
    ifsc_code = Column(String(20), nullable=True)
    branch = Column(String(200), nullable=True)

    # Account holder
    holder_name = Column(String(300), nullable=True)
    holder_pan = Column(String(20), nullable=True)
    holder_mobile = Column(String(15), nullable=True)
    holder_email = Column(String(255), nullable=True)
    holder_dob = Column(Date, nullable=True)
    holder_type = Column(String(50), nullable=True)  # SINGLE, JOINT

    # Balance information
    current_balance = Column(Numeric(18, 2), nullable=True)
    available_balance = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(3), default="INR")
    balance_as_on = Column(DateTime, nullable=True)

    # For term deposits / FDs
    opening_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    maturity_amount = Column(Numeric(18, 2), nullable=True)
    interest_rate = Column(Numeric(8, 4), nullable=True)
    principal_amount = Column(Numeric(18, 2), nullable=True)

    # Data status
    status = Column(SQLEnum(AADataStatus), nullable=False, default=AADataStatus.RECEIVED)

    # Raw data from AA
    raw_data = Column(JSONB, nullable=True)
    profile_data = Column(JSONB, nullable=True)
    summary_data = Column(JSONB, nullable=True)

    # Data fetch timestamp
    data_fetched_at = Column(DateTime, nullable=True)
    data_from = Column(Date, nullable=True)
    data_to = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fetch_session = relationship("AAFetchSession", back_populates="bank_accounts")
    transactions = relationship("AABankTransaction", back_populates="bank_account", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_aa_bank_account_session", "fetch_session_id"),
        Index("ix_aa_bank_account_entity", "entity_id"),
        Index("ix_aa_bank_account_fi_type", "fi_type"),
    )

    def __repr__(self):
        return f"<AABankAccount {self.account_number_masked} - {self.fip_name}>"


class AABankTransaction(Base):
    """Individual transactions from AA bank statement data."""

    __tablename__ = "lms_aa_bank_transaction"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bank_account_id = Column(PGUUID(as_uuid=True), ForeignKey("lms_aa_bank_account.id"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    # Transaction details
    txn_id = Column(String(100), nullable=True)  # AA's transaction ID
    txn_type = Column(String(20), nullable=False)  # DEBIT, CREDIT
    mode = Column(String(50), nullable=True)  # UPI, NEFT, IMPS, CASH, etc.

    # Amount
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="INR")

    # Balance after transaction
    balance_after = Column(Numeric(18, 2), nullable=True)

    # Transaction date/time
    transaction_date = Column(Date, nullable=False)
    transaction_timestamp = Column(DateTime, nullable=True)
    value_date = Column(Date, nullable=True)

    # Narration/Description
    narration = Column(Text, nullable=True)
    reference = Column(String(200), nullable=True)

    # Counterparty details (if available)
    counterparty_name = Column(String(200), nullable=True)
    counterparty_account = Column(String(50), nullable=True)
    counterparty_ifsc = Column(String(20), nullable=True)

    # Categorization (can be computed)
    category = Column(String(100), nullable=True)  # SALARY, EMI, RENT, etc.
    sub_category = Column(String(100), nullable=True)

    # Raw data
    raw_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bank_account = relationship("AABankAccount", back_populates="transactions")

    __table_args__ = (
        Index("ix_aa_bank_txn_account", "bank_account_id"),
        Index("ix_aa_bank_txn_date", "transaction_date"),
        Index("ix_aa_bank_txn_type", "txn_type"),
    )

    def __repr__(self):
        return f"<AABankTransaction {self.txn_id} - {self.txn_type} {self.amount}>"


class AAConsentLog(Base):
    """Audit log for AA consent lifecycle events."""

    __tablename__ = "lms_aa_consent_log"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    consent_id = Column(PGUUID(as_uuid=True), ForeignKey("lms_aa_consent.id"), nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)  # CREATED, APPROVED, REVOKED, etc.
    old_status = Column(SQLEnum(AAConsentStatus), nullable=True)
    new_status = Column(SQLEnum(AAConsentStatus), nullable=True)

    # Event source
    source = Column(String(50), nullable=True)  # USER, WEBHOOK, SYSTEM

    # Details
    message = Column(Text, nullable=True)
    aa_response = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    __table_args__ = (
        Index("ix_aa_consent_log_consent", "consent_id"),
        Index("ix_aa_consent_log_event", "event_type"),
    )

    def __repr__(self):
        return f"<AAConsentLog {self.consent_id} - {self.event_type}>"
