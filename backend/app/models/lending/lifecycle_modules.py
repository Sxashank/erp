"""Phase-D lifecycle modules — 8 transactional tables.

All link back to LoanAccount / Sanction / Application and emit
lifecycle events on every state transition.
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# ============================================================================
# 1. LoanTakeoverIn — incoming takeover from another lender
# ============================================================================


class TakeoverStatus(str, PyEnum):
    INITIATED = "INITIATED"
    NOC_RECEIVED = "NOC_RECEIVED"
    DD_PAID = "DD_PAID"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class LoanTakeoverIn(BaseModel):
    """Borrower brings a loan from another lender to us."""

    __tablename__ = "txn_loan_takeover_in"
    __table_args__ = (Index("ix_txn_loan_takeover_in_org_status", "organization_id", "status"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    takeover_reference: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="SET NULL"),
    )
    our_loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="SET NULL"),
    )

    source_lender_name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_loan_account_no: Mapped[str] = mapped_column(String(100), nullable=False)
    source_outstanding: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_noc_doc_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="SET NULL"),
    )

    transferred_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    transfer_date: Mapped[Optional[date_type]] = mapped_column(Date)
    dd_or_rtgs_reference: Mapped[Optional[str]] = mapped_column(String(100))

    status: Mapped[TakeoverStatus] = mapped_column(
        SAEnum(TakeoverStatus, name="loan_takeover_status"),
        nullable=False,
        default=TakeoverStatus.INITIATED,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 2. LoanTransferOut — borrower moves loan out to another lender
# ============================================================================


class TransferOutStatus(str, PyEnum):
    NOC_REQUESTED = "NOC_REQUESTED"
    OUTSTANDING_ISSUED = "OUTSTANDING_ISSUED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    SECURITY_DISCHARGED = "SECURITY_DISCHARGED"
    DOCS_RELEASED = "DOCS_RELEASED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class LoanTransferOut(BaseModel):
    """Borrower moves the loan out to another lender."""

    __tablename__ = "txn_loan_transfer_out"
    __table_args__ = (Index("ix_txn_loan_transfer_out_loan", "loan_account_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    transfer_reference: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_lender_name: Mapped[str] = mapped_column(String(300), nullable=False)
    noc_requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outstanding_letter_issued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    outstanding_amount_quoted: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    quote_valid_till: Mapped[Optional[date_type]] = mapped_column(Date)
    payment_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payment_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    security_discharged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    docs_released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    status: Mapped[TransferOutStatus] = mapped_column(
        SAEnum(TransferOutStatus, name="loan_transfer_out_status"),
        nullable=False,
        default=TransferOutStatus.NOC_REQUESTED,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 3. RateResetEvent — floating-rate reset workflow
# ============================================================================


class RateResetChoice(str, PyEnum):
    INCREASE_EMI = "INCREASE_EMI"
    EXTEND_TENOR = "EXTEND_TENOR"
    MIX = "MIX"
    SWITCH_TO_FIXED = "SWITCH_TO_FIXED"


class RateResetEvent(BaseModel):
    __tablename__ = "txn_rate_reset_event"
    __table_args__ = (
        Index("ix_txn_rate_reset_event_loan", "loan_account_id"),
        Index("ix_txn_rate_reset_event_due", "due_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )

    benchmark_code: Mapped[str] = mapped_column(String(30), nullable=False)
    due_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    old_rate_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    new_rate_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    communicated_on: Mapped[Optional[date_type]] = mapped_column(Date)
    intimation_doc_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="SET NULL"),
    )

    borrower_choice: Mapped[Optional[RateResetChoice]] = mapped_column(
        SAEnum(RateResetChoice, name="rate_reset_choice"),
    )
    choice_received_on: Mapped[Optional[date_type]] = mapped_column(Date)
    applied_on: Mapped[Optional[date_type]] = mapped_column(Date)
    new_emi_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    new_tenure_months: Mapped[Optional[int]] = mapped_column(Integer)

    remarks: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 4. NachPresentation — one row per ACH presentation
# ============================================================================


class NachPresentationStatus(str, PyEnum):
    PRESENTED = "PRESENTED"
    SUCCESS = "SUCCESS"
    BOUNCED = "BOUNCED"
    PENDING = "PENDING"


class NachPresentation(BaseModel):
    __tablename__ = "txn_nach_presentation"
    __table_args__ = (
        Index("ix_txn_nach_presentation_mandate", "mandate_id"),
        Index("ix_txn_nach_presentation_present_date", "presentation_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    mandate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_mandate.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )

    presentation_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    instalment_number: Mapped[Optional[int]] = mapped_column(Integer)

    status: Mapped[NachPresentationStatus] = mapped_column(
        SAEnum(NachPresentationStatus, name="nach_presentation_status"),
        nullable=False,
        default=NachPresentationStatus.PRESENTED,
    )
    cleared_on: Mapped[Optional[date_type]] = mapped_column(Date)
    return_reason_code: Mapped[Optional[str]] = mapped_column(String(10))
    return_reason_description: Mapped[Optional[str]] = mapped_column(String(300))
    bank_reference: Mapped[Optional[str]] = mapped_column(String(100))
    receipt_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_receipt.id", ondelete="SET NULL"),
    )


# ============================================================================
# 5. DocReleaseTracker — RBI Sep-2023 30-day clock
# ============================================================================


class DocReleaseStatus(str, PyEnum):
    PENDING = "PENDING"
    RELEASED = "RELEASED"
    BREACHED = "BREACHED"


class DocReleaseTracker(BaseModel):
    """Per-RBI Sep-2023: original docs must be released within 30 days of closure."""

    __tablename__ = "txn_doc_release_tracker"
    __table_args__ = (
        Index("ix_txn_doc_release_loan", "loan_account_id"),
        Index("ix_txn_doc_release_target_date", "target_release_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    closure_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    target_release_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    actual_release_date: Mapped[Optional[date_type]] = mapped_column(Date)

    status: Mapped[DocReleaseStatus] = mapped_column(
        SAEnum(DocReleaseStatus, name="doc_release_status"),
        nullable=False,
        default=DocReleaseStatus.PENDING,
    )
    breach_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compensation_payable: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Compensation accrued at ₹5000/day per RBI directive.",
    )
    documents_released: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    released_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 6. WilfulDefaulterProceeding — RBI 30-Jul-2024 Directions
# ============================================================================


class WilfulDefaulterStage(str, PyEnum):
    IDENTIFICATION = "IDENTIFICATION"
    SHOW_CAUSE_ISSUED = "SHOW_CAUSE_ISSUED"
    PERSONAL_HEARING = "PERSONAL_HEARING"
    REVIEW = "REVIEW"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    SETTLED = "SETTLED"


class WilfulDefaulterProceeding(BaseModel):
    __tablename__ = "txn_wilful_defaulter_proceeding"
    __table_args__ = (
        Index("ix_txn_wdp_org", "organization_id"),
        Index("ix_txn_wdp_loan", "loan_account_id"),
        Index("ix_txn_wdp_stage", "stage"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    proceeding_reference: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    npa_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    initiated_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    sla_due_date: Mapped[date_type] = mapped_column(
        Date,
        nullable=False,
        comment="180 days from NPA date per RBI Directions.",
    )

    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    grounds_of_wilful_default: Mapped[str] = mapped_column(Text, nullable=False)

    stage: Mapped[WilfulDefaulterStage] = mapped_column(
        SAEnum(WilfulDefaulterStage, name="wilful_defaulter_stage"),
        nullable=False,
        default=WilfulDefaulterStage.IDENTIFICATION,
    )

    show_cause_notice_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="SET NULL"),
    )
    show_cause_issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    borrower_response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    borrower_response_text: Mapped[Optional[str]] = mapped_column(Text)
    personal_hearing_date: Mapped[Optional[date_type]] = mapped_column(Date)
    personal_hearing_notes: Mapped[Optional[str]] = mapped_column(Text)

    id_committee_decision: Mapped[Optional[str]] = mapped_column(Text)
    id_committee_decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_committee_decision: Mapped[Optional[str]] = mapped_column(Text)
    review_committee_decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    bureau_reported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bureau_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ============================================================================
# 7. LoanWriteOff — technical + final
# ============================================================================


class WriteOffType(str, PyEnum):
    TECHNICAL = "TECHNICAL"
    FINAL = "FINAL"


class WriteOffStatus(str, PyEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EFFECTED = "EFFECTED"
    REVERSED = "REVERSED"


class LoanWriteOff(BaseModel):
    __tablename__ = "txn_loan_write_off"
    __table_args__ = (
        Index("ix_txn_loan_write_off_loan", "loan_account_id"),
        Index("ix_txn_loan_write_off_status", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    write_off_reference: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    write_off_type: Mapped[WriteOffType] = mapped_column(
        SAEnum(WriteOffType, name="loan_write_off_type"),
        nullable=False,
    )
    status: Mapped[WriteOffStatus] = mapped_column(
        SAEnum(WriteOffStatus, name="loan_write_off_status"),
        nullable=False,
        default=WriteOffStatus.PROPOSED,
    )

    proposed_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    proposed_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    proposed_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    proposed_reason: Mapped[str] = mapped_column(Text, nullable=False)

    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    approval_authority: Mapped[Optional[str]] = mapped_column(String(80))

    effected_date: Mapped[Optional[date_type]] = mapped_column(Date)
    gl_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
    )

    principal_written_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    interest_written_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    charges_written_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    # Recovery post write-off
    total_recovered_post_write_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    bureau_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    board_reported_quarter: Mapped[Optional[str]] = mapped_column(String(8))

    remarks: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 8. LoanInterestRevival — revive suspended interest on recovery
# ============================================================================


class InterestRevivalStatus(str, PyEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EFFECTED = "EFFECTED"


class LoanInterestRevival(BaseModel):
    __tablename__ = "txn_loan_interest_revival"
    __table_args__ = (Index("ix_txn_loan_interest_revival_loan", "loan_account_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    revival_reference: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    proposed_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revivable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    proposed_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[InterestRevivalStatus] = mapped_column(
        SAEnum(InterestRevivalStatus, name="interest_revival_status"),
        nullable=False,
        default=InterestRevivalStatus.PROPOSED,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    effected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    gl_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text)
