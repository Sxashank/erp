"""NACH Batch models for automated EMI collection."""

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
    NachBatchStatus, NachTransactionStatus, NachReturnCode, NachFileFormat
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.loan_account import LoanAccount, LoanMandate, ScheduleInstallment
    from app.models.auth.user import User


class NachBatch(BaseModel):
    """NACH batch for bulk debit presentation to NPCI."""

    __tablename__ = "lms_nach_batch"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Batch identification
    batch_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Batch reference number (e.g., NACH/2025/01/00001)",
    )
    batch_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Batch creation/scheduled date",
    )
    debit_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Scheduled debit date for all transactions",
    )

    # Provider/Integration config reference
    integration_config_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sys_integration_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="NACH integration config used",
    )

    # Batch type
    file_format: Mapped[NachFileFormat] = mapped_column(
        Enum(NachFileFormat),
        nullable=False,
        default=NachFileFormat.ACH_DEBIT,
        comment="NACH file format type",
    )

    # Summary counts
    total_transactions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total transactions in batch",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total debit amount",
    )

    # Response counts
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Successful transactions",
    )
    success_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total successful amount",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Failed/bounced transactions",
    )
    failure_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total failed amount",
    )
    pending_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Pending transactions",
    )

    # File details
    file_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Generated file name",
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="File storage path",
    )
    file_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="File generation timestamp",
    )
    file_checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="File checksum for integrity",
    )

    # Submission details
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Submission timestamp to NPCI/provider",
    )
    submission_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Provider submission reference",
    )

    # Response details
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Response file received timestamp",
    )
    response_file_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Response file name",
    )
    response_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Response file storage path",
    )

    # Status
    status: Mapped[NachBatchStatus] = mapped_column(
        Enum(NachBatchStatus),
        nullable=False,
        default=NachBatchStatus.CREATED,
        index=True,
        comment="Batch status",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # Processing by
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Created by user",
    )
    submitted_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Submitted by user",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional data",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    transactions: Mapped[List["NachTransaction"]] = relationship(
        "NachTransaction",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_nach_batch_org_date", "organization_id", "batch_date"),
        Index("ix_lms_nach_batch_org_status", "organization_id", "status"),
        Index("ix_lms_nach_batch_debit_date", "debit_date"),
    )

    def __repr__(self) -> str:
        return f"<NachBatch(ref={self.batch_reference}, count={self.total_transactions}, status={self.status})>"


class NachTransaction(BaseModel):
    """Individual NACH transaction within a batch."""

    __tablename__ = "lms_nach_transaction"

    # Parent batch
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_nach_batch.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent batch",
    )

    # Loan references
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Loan account",
    )
    loan_mandate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_mandate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="NACH mandate used",
    )
    installment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_schedule_installment.id", ondelete="SET NULL"),
        nullable=True,
        comment="Related installment (if specific)",
    )

    # Transaction identification
    transaction_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique transaction reference",
    )
    umrn: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Mandate UMRN",
    )

    # Bank account details (denormalized for file generation)
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
    account_holder_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Account holder name",
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Bank name",
    )

    # Amount
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Amount to debit",
    )
    debit_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Scheduled debit date",
    )

    # Purpose
    narration: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Transaction narration/purpose",
    )

    # Status tracking
    status: Mapped[NachTransactionStatus] = mapped_column(
        Enum(NachTransactionStatus),
        nullable=False,
        default=NachTransactionStatus.PENDING,
        index=True,
        comment="Transaction status",
    )

    # Provider response
    bank_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Bank/NPCI transaction reference",
    )
    return_code: Mapped[Optional[NachReturnCode]] = mapped_column(
        Enum(NachReturnCode),
        nullable=True,
        comment="NPCI return code",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Detailed failure reason",
    )
    response_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full response message from provider",
    )

    # Timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Processing timestamp",
    )
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Settlement timestamp",
    )

    # Receipt reference (created on success)
    receipt_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_receipt.id", ondelete="SET NULL"),
        nullable=True,
        comment="Loan receipt created on success",
    )

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum allowed retries",
    )
    next_retry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next retry date if applicable",
    )
    original_transaction_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_nach_transaction.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original transaction if this is a retry",
    )

    # Bounce charges
    bounce_charges_applied: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Bounce charges applied to borrower",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional data",
    )

    # Relationships
    batch: Mapped["NachBatch"] = relationship(
        "NachBatch",
        back_populates="transactions",
    )
    loan_account: Mapped["LoanAccount"] = relationship(
        "LoanAccount",
        lazy="selectin",
    )
    loan_mandate: Mapped["LoanMandate"] = relationship(
        "LoanMandate",
        lazy="selectin",
    )
    installment: Mapped[Optional["ScheduleInstallment"]] = relationship(
        "ScheduleInstallment",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_nach_txn_batch", "batch_id", "status"),
        Index("ix_lms_nach_txn_loan", "loan_account_id"),
        Index("ix_lms_nach_txn_umrn", "umrn"),
        Index("ix_lms_nach_txn_debit_date", "debit_date", "status"),
        Index("ix_lms_nach_txn_retry", "next_retry_date", "status"),
    )

    def __repr__(self) -> str:
        return f"<NachTransaction(ref={self.transaction_reference}, amount={self.debit_amount}, status={self.status})>"


class NachMandateLog(BaseModel):
    """Log of mandate registration/modification/cancellation activities."""

    __tablename__ = "lms_nach_mandate_log"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Mandate reference
    loan_mandate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_mandate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Loan mandate",
    )

    # Operation type
    operation: Mapped[NachFileFormat] = mapped_column(
        Enum(NachFileFormat),
        nullable=False,
        comment="Operation type (REGISTER, MODIFY, CANCEL)",
    )

    # Request details
    request_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Request reference number",
    )
    request_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Request date",
    )
    request_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Request payload sent",
    )

    # Response details
    response_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Response date",
    )
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Response payload received",
    )

    # Status
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was operation successful?",
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Error code if failed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # UMRN (updated on successful registration)
    umrn_assigned: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="UMRN assigned by NPCI",
    )

    # Integration config reference
    integration_config_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sys_integration_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="Integration config used",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    loan_mandate: Mapped["LoanMandate"] = relationship(
        "LoanMandate",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lms_mandate_log_org", "organization_id", "request_date"),
        Index("ix_lms_mandate_log_mandate", "loan_mandate_id"),
    )

    def __repr__(self) -> str:
        return f"<NachMandateLog(mandate={self.loan_mandate_id}, op={self.operation}, success={self.is_success})>"
