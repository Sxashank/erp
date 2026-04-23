"""Loan Account models for Phase 2 - Loan Accounting."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    LoanAccountStatus, DisbursementStatus, DisbursementMode,
    ScheduleType, InstallmentType, InstallmentStatus,
    AccrualCategory, AccrualStatus, AssetClassification,
    ReceiptType, ReceiptStatus, ReceiptMode,
    AllocationPriority, AllocationComponent,
    AdjustmentType, WaiverType, ProvisioningCategory,
    MandateStatus, GLEntryType,
    InterestType, RateResetFrequency, RepaymentFrequency,
    RepaymentMode, DayCountConvention
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.entity import Entity, EntityBankAccount
    from app.models.lending.product import LoanProduct, InterestRate
    from app.models.lending.sanction import LoanSanction
    from app.models.finance.account import Account
    from app.models.finance.voucher import Voucher
    # Phase 3: Collections models
    from app.models.lending.collections import (
        CollectionFollowUp,
        DemandNotice,
        NPARecord,
        PenalInterest,
        PenalWaiver,
        OTSProposal,
        LoanRestructure,
        LegalCase,
        WriteOffRecord,
    )


class LoanAccount(BaseModel):
    """Master loan account created from sanctioned loan."""

    __tablename__ = "lms_loan_account"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # References from LOS
    sanction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_sanction.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        comment="Parent sanction",
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Borrower entity",
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_product.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Loan product",
    )

    # Account identification
    loan_account_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Loan account number e.g., 'SMFC/LA/2025/00001'",
    )
    loan_reference_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="External reference number",
    )

    # Dates
    account_open_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Account opening date",
    )
    first_disbursement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="First disbursement date",
    )
    last_disbursement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last disbursement date",
    )
    repayment_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual repayment start date",
    )
    maturity_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Loan maturity date",
    )
    closure_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Account closure date",
    )

    # Sanctioned terms
    sanctioned_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Sanctioned loan amount",
    )
    tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sanctioned tenure in months",
    )
    moratorium_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Moratorium period in months",
    )
    moratorium_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Moratorium end date",
    )

    # Interest terms
    interest_type: Mapped[InterestType] = mapped_column(
        Enum(InterestType),
        nullable=False,
        comment="FIXED or FLOATING",
    )
    base_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_interest_rate.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Base rate for floating loans",
    )
    current_base_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Current base rate",
    )
    spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Spread over base rate in basis points",
    )
    current_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Current effective interest rate",
    )
    rate_reset_frequency: Mapped[Optional[RateResetFrequency]] = mapped_column(
        Enum(RateResetFrequency),
        nullable=True,
        comment="Rate reset frequency",
    )
    next_rate_reset_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next rate reset date",
    )
    last_rate_reset_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last rate reset date",
    )

    # Penal interest
    penal_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("2.00"),
        comment="Penal interest rate % over regular rate",
    )

    # Repayment terms
    repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        Enum(RepaymentFrequency),
        nullable=False,
        comment="Repayment frequency",
    )
    repayment_mode: Mapped[RepaymentMode] = mapped_column(
        Enum(RepaymentMode),
        nullable=False,
        comment="Repayment mode - EMI, STRUCTURED, BULLET",
    )
    day_count_convention: Mapped[DayCountConvention] = mapped_column(
        Enum(DayCountConvention),
        nullable=False,
        default=DayCountConvention.ACT_365,
        comment="Day count convention",
    )
    installment_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Day of month for installment (1-28)",
    )
    current_emi_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Current EMI amount",
    )

    # Outstanding balances
    total_disbursed_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total amount disbursed",
    )
    undisbursed_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Remaining amount to be disbursed",
    )
    principal_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Principal outstanding",
    )
    interest_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest outstanding (accrued not due)",
    )
    interest_overdue: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest overdue (past due date)",
    )
    principal_overdue: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Principal overdue",
    )
    penal_interest_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Penal interest outstanding",
    )
    charges_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Charges outstanding",
    )
    total_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total outstanding amount",
    )

    # Cumulative totals
    total_principal_received: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total principal received",
    )
    total_interest_received: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total interest received",
    )
    total_penal_interest_received: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total penal interest received",
    )
    total_charges_received: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total charges received",
    )

    # Accrual tracking
    interest_accrued_not_due: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest accrued but not yet due",
    )
    last_accrual_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last interest accrual date",
    )
    accrual_suspended: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is accrual suspended (NPA)?",
    )
    accrual_suspension_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date accrual was suspended",
    )
    suspended_interest: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest in suspense (NPA)",
    )

    # DPD and NPA tracking
    days_past_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Days past due",
    )
    oldest_due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Oldest unpaid installment date",
    )
    asset_classification: Mapped[AssetClassification] = mapped_column(
        Enum(AssetClassification),
        nullable=False,
        default=AssetClassification.STANDARD,
        index=True,
        comment="Current asset classification",
    )
    npa_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date account became NPA",
    )
    npa_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Amount considered as NPA",
    )

    # Provisioning
    provision_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.40"),
        comment="Current provision percentage",
    )
    provision_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Current provision amount",
    )
    provision_held: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Provision already held",
    )

    # Write-off tracking
    principal_written_off: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Principal written off",
    )
    interest_written_off: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest written off",
    )
    write_off_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Write-off date",
    )

    # Prepayment/Foreclosure
    prepayment_penalty_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Prepayment penalty rate",
    )
    foreclosure_penalty_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Foreclosure penalty rate",
    )
    lock_in_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Lock-in period end date",
    )

    # Receipt allocation order
    allocation_priority: Mapped[AllocationPriority] = mapped_column(
        Enum(AllocationPriority),
        nullable=False,
        default=AllocationPriority.FIFO,
        comment="Receipt allocation priority",
    )
    allocation_order: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["CHARGES", "PENAL_INTEREST", "INTEREST", "PRINCIPAL"],
        comment="Component allocation order",
    )

    # Status
    status: Mapped[LoanAccountStatus] = mapped_column(
        Enum(LoanAccountStatus),
        nullable=False,
        default=LoanAccountStatus.CREATED,
        index=True,
        comment="Account status",
    )

    # GL Account mapping
    loan_asset_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Loan asset GL account",
    )
    interest_receivable_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Interest receivable GL account",
    )
    interest_income_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Interest income GL account",
    )
    interest_suspense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Interest suspense GL account",
    )
    provision_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Provision GL account",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    sanction: Mapped["LoanSanction"] = relationship(
        "LoanSanction",
        lazy="selectin",
    )
    entity: Mapped["Entity"] = relationship(
        "Entity",
        lazy="selectin",
    )
    product: Mapped["LoanProduct"] = relationship(
        "LoanProduct",
        lazy="selectin",
    )
    base_rate: Mapped[Optional["InterestRate"]] = relationship(
        "InterestRate",
        lazy="selectin",
    )
    disbursements: Mapped[List["Disbursement"]] = relationship(
        "Disbursement",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    schedules: Mapped[List["RepaymentSchedule"]] = relationship(
        "RepaymentSchedule",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    receipts: Mapped[List["LoanReceipt"]] = relationship(
        "LoanReceipt",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mandates: Mapped[List["LoanMandate"]] = relationship(
        "LoanMandate",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Phase 3: Collections relationships
    follow_ups: Mapped[List["CollectionFollowUp"]] = relationship(
        "CollectionFollowUp",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    demand_notices: Mapped[List["DemandNotice"]] = relationship(
        "DemandNotice",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    npa_record: Mapped[Optional["NPARecord"]] = relationship(
        "NPARecord",
        back_populates="loan_account",
        uselist=False,
        lazy="noload",
    )
    penal_interests: Mapped[List["PenalInterest"]] = relationship(
        "PenalInterest",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    penal_waivers: Mapped[List["PenalWaiver"]] = relationship(
        "PenalWaiver",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    ots_proposals: Mapped[List["OTSProposal"]] = relationship(
        "OTSProposal",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    restructures: Mapped[List["LoanRestructure"]] = relationship(
        "LoanRestructure",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    legal_cases: Mapped[List["LegalCase"]] = relationship(
        "LegalCase",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    write_offs: Mapped[List["WriteOffRecord"]] = relationship(
        "WriteOffRecord",
        back_populates="loan_account",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    __table_args__ = (
        Index("ix_lms_loan_account_org_status", "organization_id", "status"),
        Index("ix_lms_loan_account_entity", "entity_id"),
        Index("ix_lms_loan_account_asset_class", "asset_classification"),
        Index("ix_lms_loan_account_dpd", "days_past_due"),
    )

    def __repr__(self) -> str:
        return f"<LoanAccount(number={self.loan_account_number}, outstanding={self.total_outstanding}, status={self.status})>"


class Disbursement(BaseModel):
    """Individual disbursement tranche."""

    __tablename__ = "lms_disbursement"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Disbursement identification
    disbursement_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Disbursement sequence number",
    )
    disbursement_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Disbursement reference number",
    )

    # Amount
    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Requested disbursement amount",
    )
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Approved disbursement amount",
    )
    disbursed_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Actual disbursed amount",
    )
    disbursement_charges: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Disbursement related charges",
    )
    net_disbursement: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Net amount after charges",
    )

    # Dates
    request_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Disbursement request date",
    )
    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Approval date",
    )
    scheduled_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Scheduled disbursement date",
    )
    disbursement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual disbursement date",
    )
    value_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Value date for interest calculation",
    )

    # Disbursement mode
    disbursement_mode: Mapped[DisbursementMode] = mapped_column(
        Enum(DisbursementMode),
        nullable=False,
        default=DisbursementMode.RTGS,
        comment="Mode of disbursement",
    )

    # Beneficiary details
    beneficiary_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Beneficiary name",
    )
    beneficiary_account_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Beneficiary account number",
    )
    beneficiary_ifsc: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
        comment="Beneficiary IFSC code",
    )
    beneficiary_bank: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Beneficiary bank name",
    )
    bank_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_bank_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Entity bank account reference",
    )

    # Payment reference
    utr_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="UTR/Transaction reference number",
    )
    cheque_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Cheque/DD number if applicable",
    )

    # Purpose and milestone
    purpose: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Purpose of disbursement",
    )
    milestone_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_project_milestone.id", ondelete="SET NULL"),
        nullable=True,
        comment="Related project milestone",
    )

    # Pre-disbursement conditions
    conditions_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Pre-disbursement conditions verified?",
    )
    conditions_verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Conditions verified by",
    )
    conditions_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Conditions verification timestamp",
    )

    # Status
    status: Mapped[DisbursementStatus] = mapped_column(
        Enum(DisbursementStatus),
        nullable=False,
        default=DisbursementStatus.PENDING,
        index=True,
        comment="Disbursement status",
    )

    # Approval
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approved by",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approval timestamp",
    )

    # Processing
    processed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Processed by",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Processing timestamp",
    )

    # Rejection/Failure details
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rejection/failure reason",
    )

    # GL Entry reference
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="GL voucher reference",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount",
        back_populates="disbursements",
    )
    bank_account: Mapped[Optional["EntityBankAccount"]] = relationship(
        "EntityBankAccount",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("loan_account_id", "disbursement_number", name="uq_disbursement_num"),
        Index("ix_lms_disbursement_status", "loan_account_id", "status"),
        Index("ix_lms_disbursement_date", "disbursement_date"),
    )

    def __repr__(self) -> str:
        return f"<Disbursement(ref={self.disbursement_reference}, amount={self.disbursed_amount}, status={self.status})>"


class RepaymentSchedule(BaseModel):
    """Repayment schedule header."""

    __tablename__ = "lms_repayment_schedule"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Schedule identification
    schedule_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Schedule version number",
    )
    schedule_type: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType),
        nullable=False,
        default=ScheduleType.ORIGINAL,
        comment="ORIGINAL, RESCHEDULED, RESTRUCTURED, REVISED",
    )

    # Schedule basis
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Principal amount for this schedule",
    )
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Interest rate for schedule calculation",
    )
    tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tenure in months",
    )
    emi_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Calculated EMI amount",
    )

    # Dates
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Schedule effective date",
    )
    first_installment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First installment date",
    )
    last_installment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Last installment date",
    )

    # Totals
    total_installments: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total number of installments",
    )
    total_principal: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total principal in schedule",
    )
    total_interest: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total interest in schedule",
    )

    # Status
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is this the current active schedule?",
    )
    superseded_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date this schedule was superseded",
    )
    superseded_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_repayment_schedule.id", ondelete="SET NULL"),
        nullable=True,
        comment="Superseded by schedule ID",
    )

    # Reason for new schedule
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for schedule change",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount",
        back_populates="schedules",
    )
    installments: Mapped[List["ScheduleInstallment"]] = relationship(
        "ScheduleInstallment",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ScheduleInstallment.installment_number",
    )

    __table_args__ = (
        UniqueConstraint("loan_account_id", "schedule_number", name="uq_schedule_num"),
        Index("ix_lms_schedule_current", "loan_account_id", "is_current"),
    )

    def __repr__(self) -> str:
        return f"<RepaymentSchedule(loan={self.loan_account_id}, num={self.schedule_number}, current={self.is_current})>"


class ScheduleInstallment(BaseModel):
    """Individual installment in repayment schedule."""

    __tablename__ = "lms_schedule_installment"

    # Parent schedule
    schedule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_repayment_schedule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent schedule",
    )

    # Installment identification
    installment_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Installment sequence number",
    )

    # Due date
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Installment due date",
    )

    # Scheduled amounts
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Principal due",
    )
    interest_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Interest due",
    )
    emi_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total EMI amount",
    )

    # Opening/Closing balances
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Opening principal balance",
    )
    closing_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Closing principal balance",
    )

    # Paid amounts
    principal_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Principal paid",
    )
    interest_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest paid",
    )
    penal_interest_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Penal interest paid",
    )

    # Overdue tracking
    principal_overdue: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Principal overdue",
    )
    interest_overdue: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Interest overdue",
    )
    penal_interest_due: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Penal interest calculated",
    )

    # Status
    status: Mapped[InstallmentStatus] = mapped_column(
        Enum(InstallmentStatus),
        nullable=False,
        default=InstallmentStatus.NOT_DUE,
        index=True,
        comment="Installment status",
    )
    paid_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date fully paid",
    )

    # Relationships
    schedule: Mapped["RepaymentSchedule"] = relationship(
        "RepaymentSchedule",
        back_populates="installments",
    )

    __table_args__ = (
        UniqueConstraint("schedule_id", "installment_number", name="uq_installment_num"),
        Index("ix_lms_installment_due", "due_date", "status"),
        Index("ix_lms_installment_status", "schedule_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ScheduleInstallment(num={self.installment_number}, due={self.due_date}, status={self.status})>"


class LoanAccrual(BaseModel):
    """Daily accrual entries for interest and fees."""

    __tablename__ = "lms_loan_accrual"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Accrual date
    accrual_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Accrual date",
    )

    # Category
    accrual_category: Mapped[AccrualCategory] = mapped_column(
        Enum(AccrualCategory),
        nullable=False,
        comment="INTEREST, PENAL_INTEREST, FEE, COMMITMENT_FEE",
    )

    # Calculation basis
    principal_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Principal balance for calculation",
    )
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Interest rate used",
    )
    day_count_basis: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=365,
        comment="Day count basis (365/360)",
    )

    # Accrued amount
    accrued_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        nullable=False,
        comment="Amount accrued (4 decimals for precision)",
    )
    cumulative_accrued: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Cumulative accrued amount",
    )

    # Status
    status: Mapped[AccrualStatus] = mapped_column(
        Enum(AccrualStatus),
        nullable=False,
        default=AccrualStatus.ACCRUED,
        comment="ACCRUED, REVERSED, SUSPENDED, WRITTEN_OFF",
    )

    # If accrual was moved to suspense (NPA)
    moved_to_suspense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Moved to suspense (NPA)?",
    )
    suspense_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date moved to suspense",
    )

    # GL reference
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="GL voucher reference",
    )

    __table_args__ = (
        UniqueConstraint("loan_account_id", "accrual_date", "accrual_category", name="uq_accrual_date_cat"),
        Index("ix_lms_accrual_date", "accrual_date"),
        Index("ix_lms_accrual_status", "loan_account_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<LoanAccrual(loan={self.loan_account_id}, date={self.accrual_date}, amount={self.accrued_amount})>"


class LoanReceipt(BaseModel):
    """Receipts/payments from borrower."""

    __tablename__ = "lms_loan_receipt"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Receipt identification
    receipt_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Receipt number",
    )

    # Receipt details
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Receipt date",
    )
    value_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Value date for accounting",
    )
    receipt_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total receipt amount",
    )

    # Receipt type and mode
    receipt_type: Mapped[ReceiptType] = mapped_column(
        Enum(ReceiptType),
        nullable=False,
        default=ReceiptType.REGULAR,
        comment="REGULAR, PREPAYMENT, FORECLOSURE, etc.",
    )
    receipt_mode: Mapped[ReceiptMode] = mapped_column(
        Enum(ReceiptMode),
        nullable=False,
        comment="CASH, CHEQUE, NEFT, UPI, NACH, etc.",
    )

    # Instrument details
    instrument_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Cheque/DD/UTR number",
    )
    instrument_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Instrument date",
    )
    instrument_bank: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Drawn on bank",
    )

    # NACH/Mandate reference
    mandate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_mandate.id", ondelete="SET NULL"),
        nullable=True,
        comment="NACH mandate reference",
    )

    # Allocation
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Amount allocated to dues",
    )
    unallocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Unallocated/excess amount",
    )

    # Component-wise allocation
    principal_allocated: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Allocated to principal",
    )
    interest_allocated: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Allocated to interest",
    )
    penal_interest_allocated: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Allocated to penal interest",
    )
    charges_allocated: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Allocated to charges",
    )

    # Prepayment/Foreclosure charges
    prepayment_charges: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Prepayment/foreclosure charges",
    )

    # Status
    status: Mapped[ReceiptStatus] = mapped_column(
        Enum(ReceiptStatus),
        nullable=False,
        default=ReceiptStatus.PENDING,
        index=True,
        comment="PENDING, ALLOCATED, REVERSED, BOUNCED",
    )

    # Bounce details
    bounced: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is receipt bounced?",
    )
    bounce_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Bounce date",
    )
    bounce_reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Bounce reason",
    )
    bounce_charges: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Bounce charges applied",
    )

    # GL reference
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="GL voucher reference",
    )

    # Processed by
    processed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Processed by",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Processing timestamp",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount",
        back_populates="receipts",
    )
    allocations: Mapped[List["ReceiptAllocation"]] = relationship(
        "ReceiptAllocation",
        back_populates="receipt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_receipt_org_date", "organization_id", "receipt_date"),
        Index("ix_lms_receipt_loan_date", "loan_account_id", "receipt_date"),
        Index("ix_lms_receipt_status", "loan_account_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<LoanReceipt(number={self.receipt_number}, amount={self.receipt_amount}, status={self.status})>"


class ReceiptAllocation(BaseModel):
    """Allocation of receipt to specific installments/components."""

    __tablename__ = "lms_receipt_allocation"

    # Parent receipt
    receipt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_receipt.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent receipt",
    )

    # Installment reference (if allocated to specific installment)
    installment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_schedule_installment.id", ondelete="SET NULL"),
        nullable=True,
        comment="Target installment",
    )

    # Allocation component
    allocation_component: Mapped[AllocationComponent] = mapped_column(
        Enum(AllocationComponent),
        nullable=False,
        comment="CHARGES, PENAL_INTEREST, INTEREST, PRINCIPAL, EMI",
    )

    # Allocation amount
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Amount allocated",
    )

    # Allocation sequence
    allocation_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Allocation sequence order",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Allocation remarks",
    )

    # Relationships
    receipt: Mapped["LoanReceipt"] = relationship(
        "LoanReceipt",
        back_populates="allocations",
    )
    installment: Mapped[Optional["ScheduleInstallment"]] = relationship(
        "ScheduleInstallment",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_allocation_receipt", "receipt_id"),
        Index("ix_lms_allocation_installment", "installment_id"),
    )

    def __repr__(self) -> str:
        return f"<ReceiptAllocation(receipt={self.receipt_id}, component={self.allocation_component}, amount={self.allocated_amount})>"


class LoanMandate(BaseModel):
    """NACH/eMandate for auto-debit."""

    __tablename__ = "lms_loan_mandate"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Mandate identification
    mandate_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Mandate reference number",
    )
    umrn: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="UMRN - Unique Mandate Reference Number",
    )

    # Mandate type
    mandate_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NACH",
        comment="NACH, E_MANDATE, UPI_AUTOPAY",
    )

    # Bank account details
    bank_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_bank_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Entity bank account reference",
    )
    account_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Bank account number",
    )
    ifsc_code: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
        comment="IFSC code",
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Bank name",
    )
    account_holder_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Account holder name",
    )

    # Mandate amount
    mandate_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Mandate amount (max debit)",
    )
    amount_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="FIXED",
        comment="FIXED or MAXIMUM",
    )

    # Frequency
    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MONTHLY",
        comment="MONTHLY, QUARTERLY, YEARLY, AS_PRESENTED",
    )
    debit_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Day of month for debit (1-28)",
    )

    # Validity period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Mandate start date",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Mandate end date",
    )

    # Registration
    registration_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="NPCI registration date",
    )

    # Status
    status: Mapped[MandateStatus] = mapped_column(
        Enum(MandateStatus),
        nullable=False,
        default=MandateStatus.INITIATED,
        index=True,
        comment="Mandate status",
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Rejection reason if rejected",
    )

    # Cancellation
    cancellation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Cancellation date",
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Cancellation reason",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount",
        back_populates="mandates",
    )
    bank_account: Mapped[Optional["EntityBankAccount"]] = relationship(
        "EntityBankAccount",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_mandate_loan", "loan_account_id", "status"),
        Index("ix_lms_mandate_umrn", "umrn"),
    )

    def __repr__(self) -> str:
        return f"<LoanMandate(ref={self.mandate_reference}, status={self.status})>"


class AssetClassificationHistory(BaseModel):
    """History of asset classification changes."""

    __tablename__ = "lms_asset_classification_history"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Classification change
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Effective date of classification",
    )
    previous_classification: Mapped[Optional[AssetClassification]] = mapped_column(
        Enum(AssetClassification),
        nullable=True,
        comment="Previous classification",
    )
    new_classification: Mapped[AssetClassification] = mapped_column(
        Enum(AssetClassification),
        nullable=False,
        comment="New classification",
    )

    # DPD at change
    days_past_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="DPD at time of classification",
    )

    # Outstanding at change
    principal_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Principal outstanding at classification",
    )
    total_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total outstanding at classification",
    )

    # Change reason
    change_reason: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="SYSTEM_AUTO, MANUAL_UPGRADE, MANUAL_DOWNGRADE, REGULARIZATION",
    )
    change_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Change remarks",
    )

    # Approval (if manual)
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approved by (for manual changes)",
    )

    __table_args__ = (
        Index("ix_lms_asset_class_hist_loan", "loan_account_id", "effective_date"),
    )

    def __repr__(self) -> str:
        return f"<AssetClassificationHistory(loan={self.loan_account_id}, date={self.effective_date}, class={self.new_classification})>"


class LoanProvision(BaseModel):
    """Provisioning entries for loans."""

    __tablename__ = "lms_loan_provision"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Provision date
    provision_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Provision date (usually month-end)",
    )

    # Asset classification
    asset_classification: Mapped[AssetClassification] = mapped_column(
        Enum(AssetClassification),
        nullable=False,
        comment="Asset classification for provisioning",
    )
    provisioning_category: Mapped[ProvisioningCategory] = mapped_column(
        Enum(ProvisioningCategory),
        nullable=False,
        comment="Provisioning category",
    )

    # Outstanding basis
    principal_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Principal outstanding",
    )
    total_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Total outstanding",
    )
    security_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Realizable security value",
    )
    unsecured_portion: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Unsecured portion",
    )

    # Provision calculation
    provision_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Provision percentage applied",
    )
    provision_required: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Provision required",
    )
    provision_held: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Provision already held",
    )
    provision_movement: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Provision movement (increase/decrease)",
    )

    # GL reference
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="GL voucher reference",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Provision remarks",
    )

    __table_args__ = (
        UniqueConstraint("loan_account_id", "provision_date", name="uq_provision_loan_date"),
        Index("ix_lms_provision_org_date", "organization_id", "provision_date"),
    )

    def __repr__(self) -> str:
        return f"<LoanProvision(loan={self.loan_account_id}, date={self.provision_date}, amount={self.provision_required})>"


class LoanAdjustment(BaseModel):
    """Loan adjustments - rate change, reschedule, waiver, etc."""

    __tablename__ = "lms_loan_adjustment"

    # Parent loan account
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent loan account",
    )

    # Adjustment identification
    adjustment_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Adjustment reference number",
    )

    # Adjustment type
    adjustment_type: Mapped[AdjustmentType] = mapped_column(
        Enum(AdjustmentType),
        nullable=False,
        comment="Type of adjustment",
    )

    # Effective date
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Adjustment effective date",
    )

    # Before values
    previous_interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Previous interest rate",
    )
    previous_emi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Previous EMI amount",
    )
    previous_tenure: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Previous remaining tenure",
    )
    previous_maturity_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Previous maturity date",
    )

    # After values
    new_interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="New interest rate",
    )
    new_emi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="New EMI amount",
    )
    new_tenure: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="New remaining tenure",
    )
    new_maturity_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="New maturity date",
    )

    # Waiver details
    waiver_type: Mapped[Optional[WaiverType]] = mapped_column(
        Enum(WaiverType),
        nullable=True,
        comment="Type of waiver if applicable",
    )
    waiver_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Waiver amount",
    )

    # Write-off details
    write_off_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Write-off amount",
    )

    # Moratorium details
    moratorium_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Moratorium months granted",
    )
    moratorium_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Moratorium end date",
    )

    # New schedule reference
    new_schedule_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_repayment_schedule.id", ondelete="SET NULL"),
        nullable=True,
        comment="New schedule created",
    )

    # Reason and approval
    adjustment_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reason for adjustment",
    )
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approved by",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approval timestamp",
    )

    # GL reference
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="GL voucher reference",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    __table_args__ = (
        Index("ix_lms_adjustment_loan", "loan_account_id", "effective_date"),
        Index("ix_lms_adjustment_type", "adjustment_type"),
    )

    def __repr__(self) -> str:
        return f"<LoanAdjustment(ref={self.adjustment_reference}, type={self.adjustment_type})>"
