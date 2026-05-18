"""Credit Bureau Pull Models.

Models for managing credit bureau pulls (CIBIL, Experian, Equifax)
for loan underwriting and credit assessment.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    Date,
    Numeric,
    Enum as PgEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, VersionedMixin


class CreditBureau(str, Enum):
    """Credit bureau providers."""
    CIBIL = "CIBIL"
    EXPERIAN = "EXPERIAN"
    EQUIFAX = "EQUIFAX"
    CRIF = "CRIF"


class CreditPullType(str, Enum):
    """Type of credit inquiry."""
    SOFT = "SOFT"  # Does not affect credit score
    HARD = "HARD"  # May affect credit score


class CreditPullStatus(str, Enum):
    """Status of credit pull request."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NO_HIT = "NO_HIT"  # No credit record found
    EXPIRED = "EXPIRED"


class CreditAccountType(str, Enum):
    """Type of credit account."""
    HOME_LOAN = "HOME_LOAN"
    AUTO_LOAN = "AUTO_LOAN"
    PERSONAL_LOAN = "PERSONAL_LOAN"
    CREDIT_CARD = "CREDIT_CARD"
    BUSINESS_LOAN = "BUSINESS_LOAN"
    GOLD_LOAN = "GOLD_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"
    PROPERTY_LOAN = "PROPERTY_LOAN"
    CONSUMER_LOAN = "CONSUMER_LOAN"
    TWO_WHEELER_LOAN = "TWO_WHEELER_LOAN"
    OVERDRAFT = "OVERDRAFT"
    OTHER = "OTHER"


class CreditAccountStatus(str, Enum):
    """Status of credit account."""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    WRITTEN_OFF = "WRITTEN_OFF"
    SETTLED = "SETTLED"
    SUIT_FILED = "SUIT_FILED"
    WILLFUL_DEFAULT = "WILLFUL_DEFAULT"


class AccountOwnership(str, Enum):
    """Ownership type of credit account."""
    INDIVIDUAL = "INDIVIDUAL"
    JOINT = "JOINT"
    AUTHORIZED_USER = "AUTHORIZED_USER"
    GUARANTOR = "GUARANTOR"


class CreditPull(Base, TimestampMixin):
    """Credit Bureau Pull Request.

    Tracks credit report pulls from various bureaus for customers/entities.
    """

    __tablename__ = "lending_credit_pull"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Link to entity or loan application
    entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id"),
        nullable=True,
        index=True,
    )
    loan_application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id"),
        nullable=True,
        index=True,
    )

    # Bureau details
    bureau: Mapped[CreditBureau] = mapped_column(
        PgEnum(CreditBureau, name="credit_bureau", create_type=False),
        nullable=False,
    )
    pull_type: Mapped[CreditPullType] = mapped_column(
        PgEnum(CreditPullType, name="credit_pull_type", create_type=False),
        default=CreditPullType.SOFT,
        nullable=False,
    )

    # Customer identification
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aadhaar_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    mobile_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Address for bureau match
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Request tracking
    request_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bureau_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[CreditPullStatus] = mapped_column(
        PgEnum(CreditPullStatus, name="credit_pull_status", create_type=False),
        default=CreditPullStatus.PENDING,
        nullable=False,
    )

    # Credit Score
    credit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., CIBIL_V2, EXPERIAN_ND
    score_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Report summary
    total_accounts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_accounts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_sanctioned: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    total_outstanding: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    total_overdue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    max_dpd_last_12m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_dpd_last_24m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enquiries_last_30d: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enquiries_last_12m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Raw report data
    report_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    report_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    pulled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Audit
    pulled_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    accounts: Mapped[List["CreditAccount"]] = relationship(
        "CreditAccount",
        back_populates="credit_pull",
        cascade="all, delete-orphan",
    )
    enquiries: Mapped[List["CreditEnquiry"]] = relationship(
        "CreditEnquiry",
        back_populates="credit_pull",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_credit_pull_pan", "pan_number"),
        Index("ix_credit_pull_org_entity", "organization_id", "entity_id"),
        Index("ix_credit_pull_status", "status"),
    )

    def is_valid(self) -> bool:
        """Check if credit pull is still valid (not expired)."""
        if self.status != CreditPullStatus.SUCCESS:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def get_score_band(self) -> str:
        """Get credit score band classification."""
        if not self.credit_score:
            return "NA"
        if self.credit_score >= 750:
            return "EXCELLENT"
        elif self.credit_score >= 700:
            return "GOOD"
        elif self.credit_score >= 650:
            return "FAIR"
        elif self.credit_score >= 550:
            return "POOR"
        else:
            return "VERY_POOR"


class CreditAccount(Base, TimestampMixin, VersionedMixin):
    """Credit Account Summary from Bureau Report.

    Individual credit accounts parsed from the bureau report.
    """

    __tablename__ = "lending_credit_account"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    credit_pull_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lending_credit_pull.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Account identification
    account_number_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bureau_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Institution details
    institution_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    institution_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Account type and status
    account_type: Mapped[CreditAccountType] = mapped_column(
        PgEnum(CreditAccountType, name="credit_account_type", create_type=False),
        default=CreditAccountType.OTHER,
        nullable=False,
    )
    account_status: Mapped[CreditAccountStatus] = mapped_column(
        PgEnum(CreditAccountStatus, name="credit_account_status", create_type=False),
        default=CreditAccountStatus.ACTIVE,
        nullable=False,
    )
    ownership: Mapped[AccountOwnership] = mapped_column(
        PgEnum(AccountOwnership, name="account_ownership", create_type=False),
        default=AccountOwnership.INDIVIDUAL,
        nullable=False,
    )

    # Financial details
    sanctioned_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    current_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    overdue_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    emi_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    cash_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    high_credit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    write_off_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Dates
    opened_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    closed_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    last_payment_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    reported_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Payment behavior
    payment_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    remaining_tenure: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # DPD (Days Past Due) history - stored as JSONB
    # Format: {"202401": 0, "202402": 30, "202403": 0, ...}
    dpd_history: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    max_dpd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Flags
    is_secured: Mapped[bool] = mapped_column(Boolean, default=False)
    has_dispute: Mapped[bool] = mapped_column(Boolean, default=False)

    # Raw data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    credit_pull: Mapped["CreditPull"] = relationship(
        "CreditPull", back_populates="accounts"
    )

    __table_args__ = (
        Index("ix_credit_account_type_status", "account_type", "account_status"),
    )


class CreditEnquiry(Base, TimestampMixin):
    """Credit Enquiry Record from Bureau Report.

    Historical credit enquiries made by other institutions.
    """

    __tablename__ = "lending_credit_enquiry"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    credit_pull_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lending_credit_pull.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Enquiry details
    enquiry_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    enquiry_purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enquiry_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Raw data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    credit_pull: Mapped["CreditPull"] = relationship(
        "CreditPull", back_populates="enquiries"
    )
