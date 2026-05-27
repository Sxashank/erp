"""Phase 3: NPA & Collections models for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
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
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    AssetClassification,
    AuctionStatus,
    CollectionStage,
    DemandNoticeType,
    FollowUpOutcome,
    FollowUpStatus,
    FollowUpType,
    LegalCaseStatus,
    LegalCaseType,
    LegalForumType,
    NPAStatus,
    OTSStatus,
    RestructureStatus,
    SARFAESIStage,
    WriteOffStatus,
    WriteOffType,
)

if TYPE_CHECKING:
    from app.models.lending.loan_account import LoanAccount


class CollectionFollowUp(BaseModel):
    """Collection follow-up activities for overdue accounts."""

    __tablename__ = "col_collection_follow_up"
    __table_args__ = (
        Index("ix_col_follow_up_loan_account", "loan_account_id"),
        Index("ix_col_follow_up_scheduled_date", "scheduled_date"),
        Index("ix_col_follow_up_status", "status"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Follow-up Details
    follow_up_type: Mapped[FollowUpType] = mapped_column(String(50), nullable=False)
    collection_stage: Mapped[CollectionStage] = mapped_column(String(50), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[str | None] = mapped_column(String(20))

    # Assignment
    assigned_to_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    assigned_to_name: Mapped[str | None] = mapped_column(String(200))

    # Execution
    status: Mapped[FollowUpStatus] = mapped_column(String(50), default=FollowUpStatus.SCHEDULED)
    executed_date: Mapped[datetime | None] = mapped_column(DateTime)
    outcome: Mapped[FollowUpOutcome | None] = mapped_column(String(50))

    # PTP Details (Promise to Pay)
    ptp_date: Mapped[date | None] = mapped_column(Date)
    ptp_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    ptp_broken: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contact Details
    contact_person: Mapped[str | None] = mapped_column(String(200))
    contact_number: Mapped[str | None] = mapped_column(String(50))

    # Notes
    remarks: Mapped[str | None] = mapped_column(Text)
    follow_up_notes: Mapped[str | None] = mapped_column(Text)

    # Next Action
    next_follow_up_date: Mapped[date | None] = mapped_column(Date)
    next_action: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="follow_ups")


class DemandNotice(BaseModel):
    """Demand notices sent to borrowers."""

    __tablename__ = "col_demand_notice"
    __table_args__ = (
        Index("ix_col_demand_notice_loan_account", "loan_account_id"),
        Index("ix_col_demand_notice_type", "notice_type"),
        Index("ix_col_demand_notice_date", "notice_date"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Notice Details
    notice_number: Mapped[str] = mapped_column(String(50), unique=True)
    notice_type: Mapped[DemandNoticeType] = mapped_column(String(50), nullable=False)
    notice_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Amounts as on notice date
    principal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    penal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    other_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Response Period
    response_due_date: Mapped[date | None] = mapped_column(Date)

    # Delivery Details
    delivery_mode: Mapped[str | None] = mapped_column(String(50))  # Registered Post, Courier, Hand
    delivery_address: Mapped[str | None] = mapped_column(Text)
    dispatch_date: Mapped[date | None] = mapped_column(Date)
    delivery_date: Mapped[date | None] = mapped_column(Date)
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    delivery_status: Mapped[str | None] = mapped_column(String(50))

    # Document
    document_path: Mapped[str | None] = mapped_column(String(500))

    # Response
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_date: Mapped[date | None] = mapped_column(Date)
    response_summary: Mapped[str | None] = mapped_column(Text)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="demand_notices")


class NPARecord(BaseModel):
    """NPA tracking record for loan accounts."""

    __tablename__ = "col_npa_record"
    __table_args__ = (
        Index("ix_col_npa_record_loan_account", "loan_account_id"),
        Index("ix_col_npa_record_status", "npa_status"),
        Index("ix_col_npa_record_npa_date", "npa_date"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # NPA Details
    npa_status: Mapped[NPAStatus] = mapped_column(String(50), nullable=False)

    # Classification at NPA
    classification_at_npa: Mapped[AssetClassification] = mapped_column(String(50), nullable=False)
    current_classification: Mapped[AssetClassification] = mapped_column(String(50), nullable=False)

    # Dates
    npa_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_overdue_date: Mapped[date | None] = mapped_column(Date)
    upgrade_date: Mapped[date | None] = mapped_column(Date)
    closure_date: Mapped[date | None] = mapped_column(Date)

    # Outstanding at NPA
    principal_at_npa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_at_npa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_at_npa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Current Outstanding
    current_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_penal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    current_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Provisioning
    provision_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    provision_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Security Value
    realizable_security_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    erosion_in_security: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Recovery
    total_recovery: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    recovery_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    recovery_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Resolution
    resolution_strategy: Mapped[str | None] = mapped_column(String(100))
    expected_resolution_date: Mapped[date | None] = mapped_column(Date)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="npa_record")


class PenalInterest(BaseModel):
    """Penal interest calculation records."""

    __tablename__ = "col_penal_interest"
    __table_args__ = (
        Index("ix_col_penal_interest_loan_account", "loan_account_id"),
        Index("ix_col_penal_interest_period", "period_start", "period_end"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Calculation Base
    overdue_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    overdue_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    overdue_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Rate and Calculation
    penal_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Applied
    applied_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    waived_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Status
    is_accrued: Mapped[bool] = mapped_column(Boolean, default=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)

    # GL Reference
    gl_entry_reference: Mapped[str | None] = mapped_column(String(100))

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="penal_interests")


class PenalWaiver(BaseModel):
    """Waiver of penal interest."""

    __tablename__ = "col_penal_waiver"
    __table_args__ = (Index("ix_col_penal_waiver_loan_account", "loan_account_id"),)

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Waiver Details
    waiver_reference: Mapped[str] = mapped_column(String(50), unique=True)
    waiver_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Amounts
    total_penal_accrued: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    waiver_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance_after_waiver: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Justification
    waiver_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Approval
    approved_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[str | None] = mapped_column(String(200))
    approval_date: Mapped[date | None] = mapped_column(Date)
    approval_reference: Mapped[str | None] = mapped_column(String(100))

    # Status
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_effected: Mapped[bool] = mapped_column(Boolean, default=False)

    # GL Reference
    gl_entry_reference: Mapped[str | None] = mapped_column(String(100))

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="penal_waivers")


class OTSProposal(BaseModel):
    """One-Time Settlement proposals."""

    __tablename__ = "col_ots_proposal"
    __table_args__ = (
        Index("ix_col_ots_proposal_loan_account", "loan_account_id"),
        Index("ix_col_ots_proposal_status", "status"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Proposal Details
    ots_reference: Mapped[str] = mapped_column(String(50), unique=True)
    proposal_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[OTSStatus] = mapped_column(String(50), default=OTSStatus.DRAFT)

    # Outstanding at Proposal
    principal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    penal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    other_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # OTS Terms
    ots_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    haircut_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    haircut_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    # Waiver Breakdown
    principal_waiver: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    interest_waiver: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    penal_waiver: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    charges_waiver: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Payment Terms
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    upfront_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    upfront_due_date: Mapped[date | None] = mapped_column(Date)
    number_of_installments: Mapped[int] = mapped_column(Integer, default=1)

    # Validity
    valid_till: Mapped[date] = mapped_column(Date, nullable=False)

    # Security Release
    security_release_terms: Mapped[str | None] = mapped_column(Text)

    # Approval
    approved_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[str | None] = mapped_column(String(200))
    approval_date: Mapped[date | None] = mapped_column(Date)
    approval_authority: Mapped[str | None] = mapped_column(String(100))

    # Borrower Acceptance
    borrower_acceptance_date: Mapped[date | None] = mapped_column(Date)
    borrower_acceptance_document: Mapped[str | None] = mapped_column(String(500))

    # Payment Tracking
    total_received: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    balance_pending: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Completion
    completion_date: Mapped[date | None] = mapped_column(Date)

    remarks: Mapped[str | None] = mapped_column(Text)
    terms_and_conditions: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="ots_proposals")
    payment_schedule: Mapped[list["OTSPaymentSchedule"]] = relationship(
        back_populates="ots_proposal",
        cascade="all, delete-orphan",
    )


class OTSPaymentSchedule(BaseModel):
    """Payment schedule for OTS."""

    __tablename__ = "col_ots_payment_schedule"
    __table_args__ = (
        Index("ix_col_ots_payment_schedule_ots", "ots_proposal_id"),
        Index("ix_col_ots_payment_schedule_due_date", "due_date"),
    )

    # Foreign Keys
    ots_proposal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_ots_proposal.id"),
        nullable=False,
    )

    # Schedule Details
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Payment
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    paid_date: Mapped[date | None] = mapped_column(Date)
    receipt_reference: Mapped[str | None] = mapped_column(String(100))

    # Status
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    ots_proposal: Mapped["OTSProposal"] = relationship(back_populates="payment_schedule")


class LoanRestructure(BaseModel):
    """Loan restructuring records."""

    __tablename__ = "col_loan_restructure"
    __table_args__ = (
        Index("ix_col_restructure_loan_account", "loan_account_id"),
        Index("ix_col_restructure_status", "status"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Restructure Details
    restructure_reference: Mapped[str] = mapped_column(String(50), unique=True)
    restructure_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RestructureStatus] = mapped_column(String(50), default=RestructureStatus.DRAFT)
    proposal_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Pre-Restructure Terms
    pre_outstanding_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pre_outstanding_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pre_interest_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    pre_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    pre_emi_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    pre_maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Post-Restructure Terms
    post_outstanding_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    post_interest_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    post_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    post_emi_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    post_maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Moratorium if applicable
    moratorium_months: Mapped[int] = mapped_column(Integer, default=0)
    moratorium_start_date: Mapped[date | None] = mapped_column(Date)
    moratorium_end_date: Mapped[date | None] = mapped_column(Date)
    moratorium_interest_treatment: Mapped[str | None] = mapped_column(
        String(50)
    )  # CAPITALIZE, DEFER, WAIVE

    # Sacrifice/Relief
    interest_waived: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    penal_waived: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    principal_converted_to_fitl: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )  # Funded Interest Term Loan

    # RBI Classification
    is_standard_restructure: Mapped[bool] = mapped_column(Boolean, default=True)
    downgrade_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Conditions
    pre_conditions: Mapped[str | None] = mapped_column(Text)
    post_conditions: Mapped[str | None] = mapped_column(Text)

    # Approval
    approved_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[str | None] = mapped_column(String(200))
    approval_date: Mapped[date | None] = mapped_column(Date)
    approval_authority: Mapped[str | None] = mapped_column(String(100))

    # Implementation
    implementation_date: Mapped[date | None] = mapped_column(Date)
    new_schedule_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Justification
    justification: Mapped[str] = mapped_column(Text, nullable=False)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="restructures")


class LegalCase(BaseModel):
    """Legal proceedings for loan recovery."""

    __tablename__ = "col_legal_case"
    __table_args__ = (
        Index("ix_col_legal_case_org", "organization_id"),
        Index("ix_col_legal_case_loan_account", "loan_account_id"),
        Index("ix_col_legal_case_status", "status"),
        Index("ix_col_legal_case_forum", "forum_type"),
    )

    # Foreign Keys
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Case Details
    case_reference: Mapped[str] = mapped_column(String(50), unique=True)
    case_type: Mapped[LegalCaseType] = mapped_column(String(50), nullable=False)
    forum_type: Mapped[LegalForumType] = mapped_column(String(50), nullable=False)
    status: Mapped[LegalCaseStatus] = mapped_column(String(50), default=LegalCaseStatus.DRAFT)

    # Court/Tribunal Details
    court_name: Mapped[str] = mapped_column(String(200), nullable=False)
    court_location: Mapped[str] = mapped_column(String(200), nullable=False)
    case_number: Mapped[str | None] = mapped_column(String(100))
    filing_date: Mapped[date | None] = mapped_column(Date)

    # Claim Details
    claim_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    claim_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    claim_costs: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_claim: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_rate_claimed: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # SARFAESI Specific
    sarfaesi_stage: Mapped[SARFAESIStage | None] = mapped_column(String(50))
    demand_notice_date: Mapped[date | None] = mapped_column(Date)
    possession_date: Mapped[date | None] = mapped_column(Date)
    possession_type: Mapped[str | None] = mapped_column(String(50))  # PHYSICAL, SYMBOLIC

    # Decree/Order Details
    decree_date: Mapped[date | None] = mapped_column(Date)
    decree_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    decree_interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # Legal Representation
    advocate_name: Mapped[str | None] = mapped_column(String(200))
    advocate_contact: Mapped[str | None] = mapped_column(String(100))
    law_firm: Mapped[str | None] = mapped_column(String(200))

    # Dates
    next_hearing_date: Mapped[date | None] = mapped_column(Date)

    # Costs
    legal_costs_incurred: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    court_fees_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Recovery
    recovery_through_case: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Closure
    closure_date: Mapped[date | None] = mapped_column(Date)
    closure_reason: Mapped[str | None] = mapped_column(String(200))

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="legal_cases")
    hearings: Mapped[list["LegalHearing"]] = relationship(
        back_populates="legal_case",
        cascade="all, delete-orphan",
    )
    auctions: Mapped[list["PropertyAuction"]] = relationship(
        back_populates="legal_case",
        cascade="all, delete-orphan",
    )


class LegalHearing(BaseModel):
    """Hearing records for legal cases."""

    __tablename__ = "col_legal_hearing"
    __table_args__ = (
        Index("ix_col_legal_hearing_case", "legal_case_id"),
        Index("ix_col_legal_hearing_date", "hearing_date"),
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )

    # Hearing Details
    hearing_number: Mapped[int] = mapped_column(Integer, nullable=False)
    hearing_date: Mapped[date] = mapped_column(Date, nullable=False)
    hearing_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Court/Bench
    bench: Mapped[str | None] = mapped_column(String(200))
    presiding_officer: Mapped[str | None] = mapped_column(String(200))

    # Proceedings
    proceedings_summary: Mapped[str] = mapped_column(Text, nullable=False)
    order_passed: Mapped[str | None] = mapped_column(Text)

    # Attendance
    our_advocate_present: Mapped[bool] = mapped_column(Boolean, default=True)
    opposite_party_present: Mapped[bool] = mapped_column(Boolean, default=False)

    # Documents
    documents_filed: Mapped[str | None] = mapped_column(Text)
    documents_received: Mapped[str | None] = mapped_column(Text)

    # Next Steps
    next_hearing_date: Mapped[date | None] = mapped_column(Date)
    next_hearing_purpose: Mapped[str | None] = mapped_column(String(200))
    action_required: Mapped[str | None] = mapped_column(Text)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    legal_case: Mapped["LegalCase"] = relationship(back_populates="hearings")


class PropertyAuction(BaseModel):
    """Property auction records for SARFAESI/legal recovery."""

    __tablename__ = "col_property_auction"
    __table_args__ = (
        Index("ix_col_auction_legal_case", "legal_case_id"),
        Index("ix_col_auction_status", "status"),
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    loan_security_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_security.id"),
    )

    # Auction Details
    auction_reference: Mapped[str] = mapped_column(String(50), unique=True)
    auction_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AuctionStatus] = mapped_column(String(50), default=AuctionStatus.SCHEDULED)

    # Property Details
    property_description: Mapped[str] = mapped_column(Text, nullable=False)
    property_address: Mapped[str] = mapped_column(Text, nullable=False)
    property_area: Mapped[str | None] = mapped_column(String(100))

    # Valuation
    valuation_date: Mapped[date | None] = mapped_column(Date)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    forced_sale_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reserve_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # EMD (Earnest Money Deposit)
    emd_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    emd_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    # Publication
    publication_date: Mapped[date | None] = mapped_column(Date)
    publication_details: Mapped[str | None] = mapped_column(Text)
    newspapers: Mapped[str | None] = mapped_column(Text)

    # Auction Schedule
    auction_date: Mapped[date] = mapped_column(Date, nullable=False)
    auction_time: Mapped[str] = mapped_column(String(20), nullable=False)
    auction_venue: Mapped[str] = mapped_column(String(500), nullable=False)
    is_e_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    e_auction_portal: Mapped[str | None] = mapped_column(String(200))

    # Bidding
    number_of_bidders: Mapped[int] = mapped_column(Integer, default=0)
    highest_bid: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    successful_bidder_name: Mapped[str | None] = mapped_column(String(200))
    successful_bidder_address: Mapped[str | None] = mapped_column(Text)

    # Sale
    sale_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    sale_confirmation_date: Mapped[date | None] = mapped_column(Date)
    sale_certificate_date: Mapped[date | None] = mapped_column(Date)
    sale_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Payment
    total_received: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    balance_due: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    payment_due_date: Mapped[date | None] = mapped_column(Date)

    # Cancellation
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    legal_case: Mapped["LegalCase"] = relationship(back_populates="auctions")


class WriteOffRecord(BaseModel):
    """Write-off records for loan accounts."""

    __tablename__ = "col_write_off"
    __table_args__ = (
        Index("ix_col_write_off_loan_account", "loan_account_id"),
        Index("ix_col_write_off_status", "status"),
    )

    # Foreign Keys
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
        nullable=False,
    )

    # Write-off Details
    write_off_reference: Mapped[str] = mapped_column(String(50), unique=True)
    write_off_type: Mapped[WriteOffType] = mapped_column(String(50), nullable=False)
    status: Mapped[WriteOffStatus] = mapped_column(String(50), default=WriteOffStatus.PROPOSED)
    proposal_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Outstanding at Write-off
    principal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    penal_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    other_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Write-off Amounts
    principal_written_off: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_written_off: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    penal_written_off: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    total_written_off: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Provision Utilized
    provision_available: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    provision_utilized: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Security Status
    security_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    security_realized: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    shortfall: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Justification
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    recovery_efforts: Mapped[str | None] = mapped_column(Text)

    # Approval
    approved_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[str | None] = mapped_column(String(200))
    approval_date: Mapped[date | None] = mapped_column(Date)
    approval_authority: Mapped[str | None] = mapped_column(String(100))
    board_resolution_date: Mapped[date | None] = mapped_column(Date)
    board_resolution_number: Mapped[str | None] = mapped_column(String(100))

    # Effective Date
    effective_date: Mapped[date | None] = mapped_column(Date)

    # GL Reference
    gl_entry_reference: Mapped[str | None] = mapped_column(String(100))

    # Recovery after Write-off
    recovery_after_write_off: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Write-back
    write_back_date: Mapped[date | None] = mapped_column(Date)
    write_back_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    write_back_reason: Mapped[str | None] = mapped_column(Text)

    remarks: Mapped[str | None] = mapped_column(Text)

    # Relationships
    loan_account: Mapped["LoanAccount"] = relationship(back_populates="write_offs")
