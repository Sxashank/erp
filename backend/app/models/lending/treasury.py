"""Treasury and ALM models for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.loan_account import Disbursement, LoanAccount
    from app.models.masters.organization import Organization


# ============================================================================
# Lender/Borrowing Source Models
# ============================================================================


class Lender(BaseModel):
    """Master record for lenders/funding sources."""

    __tablename__ = "trs_lender"
    __table_args__ = (
        UniqueConstraint("organization_id", "lender_code", name="uq_trs_lender_code"),
        Index("ix_trs_lender_org_type", "organization_id", "lender_type"),
        Index("ix_trs_lender_org_status", "organization_id", "status"),
    )

    lender_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )
    lender_code: Mapped[str] = mapped_column(String(30), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lender_type: Mapped[str] = mapped_column(String(50), nullable=False)  # LenderType enum

    # Registration details
    pan: Mapped[str | None] = mapped_column(String(20))
    cin: Mapped[str | None] = mapped_column(String(25))
    gstin: Mapped[str | None] = mapped_column(String(20))
    rbi_registration: Mapped[str | None] = mapped_column(String(50))

    # Contact details
    registered_address: Mapped[str | None] = mapped_column(Text)
    contact_person: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(20))

    # Bank details for payments
    bank_name: Mapped[str | None] = mapped_column(String(100))
    bank_branch: Mapped[str | None] = mapped_column(String(100))
    bank_account_number: Mapped[str | None] = mapped_column(String(30))
    bank_ifsc: Mapped[str | None] = mapped_column(String(15))

    # Credit rating
    external_rating: Mapped[str | None] = mapped_column(String(20))
    rating_agency: Mapped[str | None] = mapped_column(String(50))
    rating_date: Mapped[date | None] = mapped_column(Date)

    # Limits
    total_sanction_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    available_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # LenderStatus
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
    borrowings: Mapped[list["Borrowing"]] = relationship(
        "Borrowing", back_populates="lender", cascade="all, delete-orphan", lazy="noload"
    )


class Borrowing(BaseModel):
    """Borrowing facility/sanction from a lender."""

    __tablename__ = "trs_borrowing"
    __table_args__ = (
        UniqueConstraint("organization_id", "borrowing_number", name="uq_trs_borrowing_number"),
        Index("ix_trs_borrowing_org_lender", "organization_id", "lender_id"),
        Index("ix_trs_borrowing_org_status", "organization_id", "status"),
        Index("ix_trs_borrowing_maturity", "maturity_date"),
    )

    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )
    lender_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_lender.id"),
        nullable=False,
    )
    borrowing_number: Mapped[str] = mapped_column(String(50), nullable=False)
    borrowing_type: Mapped[str] = mapped_column(String(50), nullable=False)  # BorrowingType

    # Sanction details
    sanction_date: Mapped[date] = mapped_column(Date, nullable=False)
    sanction_reference: Mapped[str | None] = mapped_column(String(100))
    sanctioned_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    # Disbursement tracking
    drawn_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    available_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    principal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Interest terms
    rate_type: Mapped[str] = mapped_column(String(30), nullable=False)  # BorrowingRateType
    base_rate_name: Mapped[str | None] = mapped_column(String(50))  # MCLR, REPO, etc.
    base_rate_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    spread_bps: Mapped[int] = mapped_column(Integer, default=0)  # Spread in basis points
    effective_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    rate_reset_frequency: Mapped[str | None] = mapped_column(String(30))
    next_rate_reset_date: Mapped[date | None] = mapped_column(Date)

    # Day count and payment frequency
    day_count_convention: Mapped[str] = mapped_column(String(20), default="ACT_365")
    interest_payment_frequency: Mapped[str] = mapped_column(String(20), default="MONTHLY")
    principal_payment_frequency: Mapped[str] = mapped_column(String(20), default="QUARTERLY")

    # Tenure
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    moratorium_months: Mapped[int] = mapped_column(Integer, default=0)
    first_interest_date: Mapped[date | None] = mapped_column(Date)
    first_principal_date: Mapped[date | None] = mapped_column(Date)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Security
    security_type: Mapped[str] = mapped_column(
        String(30), default="UNSECURED"
    )  # BorrowingSecurityType
    security_description: Mapped[str | None] = mapped_column(Text)
    security_cover_required: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2)
    )  # e.g., 1.10 = 110%

    # Fees
    processing_fee_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    commitment_fee_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    prepayment_penalty_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # Covenants stored as JSON
    financial_covenants: Mapped[dict | None] = mapped_column(JSONB)
    reporting_requirements: Mapped[dict | None] = mapped_column(JSONB)

    # Documents
    sanction_letter_path: Mapped[str | None] = mapped_column(String(500))
    agreement_date: Mapped[date | None] = mapped_column(Date)
    agreement_path: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(String(30), default="SANCTIONED")  # BorrowingStatus
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
    lender: Mapped["Lender"] = relationship("Lender", back_populates="borrowings")
    tranches: Mapped[list["BorrowingTranche"]] = relationship(
        "BorrowingTranche", back_populates="borrowing", cascade="all, delete-orphan", lazy="noload"
    )
    schedule: Mapped[list["BorrowingSchedule"]] = relationship(
        "BorrowingSchedule", back_populates="borrowing", cascade="all, delete-orphan", lazy="noload"
    )
    payments: Mapped[list["BorrowingPayment"]] = relationship(
        "BorrowingPayment", back_populates="borrowing", cascade="all, delete-orphan", lazy="noload"
    )
    covenants: Mapped[list["BorrowingCovenant"]] = relationship(
        "BorrowingCovenant", back_populates="borrowing", cascade="all, delete-orphan", lazy="noload"
    )
    fund_deployments: Mapped[list["FundDeployment"]] = relationship(
        "FundDeployment", back_populates="borrowing", cascade="all, delete-orphan", lazy="noload"
    )


class BorrowingTranche(BaseModel):
    """Individual drawdown/tranche from a borrowing facility."""

    __tablename__ = "trs_borrowing_tranche"
    __table_args__ = (
        UniqueConstraint("borrowing_id", "tranche_number", name="uq_trs_tranche_number"),
        Index("ix_trs_tranche_status", "status"),
    )

    tranche_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id"),
        nullable=False,
    )
    tranche_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Request details
    request_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text)

    # Disbursement details
    disbursement_date: Mapped[date | None] = mapped_column(Date)
    disbursed_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    principal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Rate (may differ from facility rate for floating)
    effective_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # Payment tracking
    utr_number: Mapped[str | None] = mapped_column(String(50))
    bank_reference: Mapped[str | None] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(30), default="REQUESTED")  # DrawdownStatus
    approved_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    borrowing: Mapped["Borrowing"] = relationship("Borrowing", back_populates="tranches")


class BorrowingSchedule(BaseModel):
    """Repayment schedule for borrowing."""

    __tablename__ = "trs_borrowing_schedule"
    __table_args__ = (
        Index("ix_trs_schedule_borrowing", "borrowing_id"),
        Index("ix_trs_schedule_due_date", "due_date"),
        Index("ix_trs_schedule_status", "status"),
    )

    schedule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id"),
        nullable=False,
    )
    tranche_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing_tranche.id"),
    )

    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Amounts
    principal_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    interest_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Payment tracking
    principal_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    interest_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    paid_date: Mapped[date | None] = mapped_column(Date)

    # Balance after this installment
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="NOT_DUE")  # InstallmentStatus

    # Relationships
    borrowing: Mapped["Borrowing"] = relationship("Borrowing", back_populates="schedule")


class BorrowingPayment(BaseModel):
    """Payment made against borrowing (interest/principal/fees)."""

    __tablename__ = "trs_borrowing_payment"
    __table_args__ = (
        Index("ix_trs_payment_borrowing", "borrowing_id"),
        Index("ix_trs_payment_date", "payment_date"),
    )

    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id"),
        nullable=False,
    )
    schedule_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing_schedule.id"),
    )

    payment_type: Mapped[str] = mapped_column(String(30), nullable=False)  # BorrowingPaymentType
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Amount details
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Payment details
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # RTGS/NEFT/etc.
    utr_number: Mapped[str | None] = mapped_column(String(50))
    bank_reference: Mapped[str | None] = mapped_column(String(100))
    from_bank_account: Mapped[str | None] = mapped_column(String(30))

    # Interest calculation period (for interest payments)
    interest_from_date: Mapped[date | None] = mapped_column(Date)
    interest_to_date: Mapped[date | None] = mapped_column(Date)
    days_counted: Mapped[int | None] = mapped_column(Integer)
    rate_applied: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    borrowing: Mapped["Borrowing"] = relationship("Borrowing", back_populates="payments")


class BorrowingCovenant(BaseModel):
    """Financial covenant tracking for borrowing."""

    __tablename__ = "trs_borrowing_covenant"
    __table_args__ = (
        Index("ix_trs_covenant_borrowing", "borrowing_id"),
        Index("ix_trs_covenant_type", "covenant_type"),
    )

    covenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id"),
        nullable=False,
    )

    covenant_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CovenantType
    covenant_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Threshold values
    threshold_type: Mapped[str] = mapped_column(String(20), nullable=False)  # MIN, MAX, RANGE
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    threshold_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    threshold_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))

    # Testing frequency
    testing_frequency: Mapped[str] = mapped_column(String(20), default="QUARTERLY")
    next_test_date: Mapped[date | None] = mapped_column(Date)

    # Current status
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    last_tested_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="COMPLIANT")  # CovenantStatus

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    borrowing: Mapped["Borrowing"] = relationship("Borrowing", back_populates="covenants")


class FundDeployment(BaseModel):
    """Mapping of borrowed funds deployed into corporate loan assets."""

    __tablename__ = "trs_fund_deployment"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "deployment_reference",
            name="uq_trs_fund_deployment_reference",
        ),
        CheckConstraint("allocated_amount > 0", name="ck_trs_fund_deployment_amount"),
        CheckConstraint("cost_rate >= 0", name="ck_trs_fund_deployment_cost_rate"),
        CheckConstraint("lending_rate >= 0", name="ck_trs_fund_deployment_lending_rate"),
        Index("ix_trs_fund_deployment_org_date", "organization_id", "allocation_date"),
        Index("ix_trs_fund_deployment_borrowing", "borrowing_id", "status"),
        Index("ix_trs_fund_deployment_loan", "loan_account_id", "status"),
        Index("ix_trs_fund_deployment_disbursement", "disbursement_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    borrowing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    borrowing_tranche_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing_tranche.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    disbursement_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_disbursement.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deployment_reference: Mapped[str] = mapped_column(String(50), nullable=False)
    allocation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    cost_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    lending_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    spread_bps: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    allocation_basis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
    borrowing: Mapped["Borrowing"] = relationship("Borrowing", back_populates="fund_deployments")
    borrowing_tranche: Mapped[Optional["BorrowingTranche"]] = relationship(
        "BorrowingTranche", foreign_keys=[borrowing_tranche_id], lazy="selectin"
    )
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount", foreign_keys=[loan_account_id], lazy="selectin"
    )
    disbursement: Mapped[Optional["Disbursement"]] = relationship(
        "Disbursement", foreign_keys=[disbursement_id], lazy="selectin"
    )


# ============================================================================
# ALM (Asset Liability Management) Models
# ============================================================================


class ALMPosition(BaseModel):
    """ALM position snapshot for a specific date."""

    __tablename__ = "trs_alm_position"
    __table_args__ = (
        UniqueConstraint("organization_id", "position_date", name="uq_trs_alm_position_date"),
        Index("ix_trs_alm_position_org", "organization_id"),
    )

    position_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )
    position_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Summary totals
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    net_position: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Gap analysis stored as JSON for each bucket
    # {bucket: {assets: x, liabilities: y, gap: z, cumulative_gap: w}}
    bucket_analysis: Mapped[dict | None] = mapped_column(JSONB)

    # Key ratios
    cumulative_gap_1_year: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cumulative_gap_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    generated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
    assets: Mapped[list["ALMAsset"]] = relationship(
        "ALMAsset", back_populates="position", cascade="all, delete-orphan", lazy="noload"
    )
    liabilities: Mapped[list["ALMLiability"]] = relationship(
        "ALMLiability", back_populates="position", cascade="all, delete-orphan", lazy="noload"
    )


class ALMAsset(BaseModel):
    """Asset breakdown for ALM position."""

    __tablename__ = "trs_alm_asset"
    __table_args__ = (
        Index("ix_trs_alm_asset_position", "position_id"),
        Index("ix_trs_alm_asset_bucket", "alm_bucket"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    position_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_alm_position.id"),
        nullable=False,
    )

    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ALMAssetType
    alm_bucket: Mapped[str] = mapped_column(String(30), nullable=False)  # ALMBucket

    # Amounts
    book_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Interest rate sensitivity
    rate_sensitive_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    non_rate_sensitive_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    weighted_avg_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    weighted_avg_maturity_days: Mapped[int | None] = mapped_column(Integer)

    # Source details (for drill-down)
    source_type: Mapped[str | None] = mapped_column(String(50))  # LOAN_ACCOUNT, INVESTMENT, etc.
    source_count: Mapped[int | None] = mapped_column(Integer)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    position: Mapped["ALMPosition"] = relationship("ALMPosition", back_populates="assets")


class ALMLiability(BaseModel):
    """Liability breakdown for ALM position."""

    __tablename__ = "trs_alm_liability"
    __table_args__ = (
        Index("ix_trs_alm_liability_position", "position_id"),
        Index("ix_trs_alm_liability_bucket", "alm_bucket"),
    )

    liability_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    position_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_alm_position.id"),
        nullable=False,
    )

    liability_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ALMLiabilityType
    alm_bucket: Mapped[str] = mapped_column(String(30), nullable=False)  # ALMBucket

    # Amounts
    book_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Interest rate sensitivity
    rate_sensitive_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    non_rate_sensitive_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    weighted_avg_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    weighted_avg_maturity_days: Mapped[int | None] = mapped_column(Integer)

    # Source details
    source_type: Mapped[str | None] = mapped_column(String(50))  # BORROWING, NCD, etc.
    source_count: Mapped[int | None] = mapped_column(Integer)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    position: Mapped["ALMPosition"] = relationship("ALMPosition", back_populates="liabilities")


class IRSAnalysis(BaseModel):
    """Interest Rate Sensitivity analysis."""

    __tablename__ = "trs_irs_analysis"
    __table_args__ = (
        Index("ix_trs_irs_org", "organization_id"),
        Index("ix_trs_irs_date", "analysis_date"),
    )

    analysis_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )
    position_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_alm_position.id"),
    )

    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    shock_type: Mapped[str] = mapped_column(String(30), nullable=False)  # IRSShockType
    shock_bps: Mapped[int] = mapped_column(Integer, nullable=False)  # Shock in basis points

    # Rate sensitive assets and liabilities
    rate_sensitive_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate_sensitive_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate_sensitivity_gap: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Impact calculation
    nii_impact: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )  # Net Interest Income impact
    nii_impact_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    # Economic Value impact (for longer term)
    ev_impact: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    ev_impact_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # Detailed bucket-wise analysis
    bucket_analysis: Mapped[dict | None] = mapped_column(JSONB)

    generated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )


# ============================================================================
# Exposure/Risk Management Models
# ============================================================================


class ExposureLimit(BaseModel):
    """Exposure limits (regulatory and internal)."""

    __tablename__ = "trs_exposure_limit"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "limit_type", "limit_key", name="uq_trs_exposure_limit"
        ),
        Index("ix_trs_exposure_limit_org", "organization_id"),
    )

    limit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    limit_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ExposureLimitType
    limit_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Sector name, rating, etc.
    limit_description: Mapped[str | None] = mapped_column(Text)

    # Limit values
    regulatory_limit_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    regulatory_limit_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    internal_limit_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    internal_limit_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Warning thresholds
    warning_threshold_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("80"))

    # Current utilization
    current_exposure: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    current_exposure_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"))
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)

    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="WITHIN_LIMIT")  # ExposureStatus

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approved_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )


class ExposureTracking(BaseModel):
    """Individual exposure records for tracking."""

    __tablename__ = "trs_exposure_tracking"
    __table_args__ = (
        Index("ix_trs_exposure_tracking_limit", "limit_id"),
        Index("ix_trs_exposure_tracking_entity", "entity_id"),
        Index("ix_trs_exposure_tracking_loan", "loan_account_id"),
    )

    tracking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    limit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_exposure_limit.id"),
        nullable=False,
    )

    # Source of exposure
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id"),
    )
    loan_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
    )
    borrowing_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trs_borrowing.id"),
    )

    exposure_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    funded_exposure: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    non_funded_exposure: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
