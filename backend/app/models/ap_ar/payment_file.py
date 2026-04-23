"""Payment File model for NEFT/RTGS file generation."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Date, DateTime, Numeric, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.organization_bank_account import OrganizationBankAccount


class PaymentFile(BaseModel):
    """
    Payment File for NEFT/RTGS batch processing.

    Aggregates multiple payments into a single file for bank upload.
    """

    __tablename__ = "txn_payment_file"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Bank account for remittance
    organization_bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization_bank_account.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # File identification
    file_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique file reference number",
    )
    file_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="NEFT, RTGS, IMPS, UPI",
    )

    # Payment date
    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
        index=True,
        comment="DRAFT, GENERATED, DOWNLOADED, UPLOADED, PROCESSING, COMPLETED, FAILED, PARTIALLY_COMPLETED",
    )

    # Aggregates
    total_transactions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    successful_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # File content (generated file as text/bytes reference)
    file_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Generated file content",
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="File checksum for integrity",
    )

    # Timestamps
    file_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    file_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    file_uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Bank response tracking
    bank_batch_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Batch ID returned by bank",
    )
    bank_response: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Full bank response",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    bank_account: Mapped["OrganizationBankAccount"] = relationship(
        "OrganizationBankAccount",
        lazy="selectin",
    )
    transactions: Mapped[List["PaymentFileTransaction"]] = relationship(
        "PaymentFileTransaction",
        back_populates="payment_file",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PaymentFile(reference={self.file_reference}, format={self.file_format}, status={self.status})>"


class PaymentFileTransaction(BaseModel):
    """
    Individual transaction within a payment file.

    Links to the actual payment record.
    """

    __tablename__ = "txn_payment_file_transaction"

    # Parent file
    payment_file_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_payment_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source payment
    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_payment.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Sequence in file
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Beneficiary details (denormalized for file generation)
    beneficiary_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    beneficiary_account_number: Mapped[str] = mapped_column(
        String(34),
        nullable=False,
    )
    beneficiary_ifsc: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
    )
    beneficiary_bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    # Narration
    narration: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Contact for notification
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    mobile: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
        comment="PENDING, SUCCESS, FAILED, REJECTED",
    )

    # Bank reference
    bank_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="UTR/RRN from bank",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    return_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Bank return code",
    )

    # Processing timestamp
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    payment_file: Mapped["PaymentFile"] = relationship(
        "PaymentFile",
        back_populates="transactions",
    )

    def __repr__(self) -> str:
        return f"<PaymentFileTransaction(seq={self.sequence_number}, beneficiary={self.beneficiary_name}, amount={self.amount})>"
