"""Recurring Voucher model for automated periodic entries."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import RecurrenceFrequency, RecurringVoucherStatus

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.voucher_type import VoucherType


class RecurringVoucher(BaseModel):
    """
    Recurring Voucher template for automated periodic entries.

    Examples: Monthly rent, depreciation, salary provisions, loan EMIs
    """

    __tablename__ = "fin_recurring_voucher"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voucher_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_voucher_type.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the recurring voucher template",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of this recurring voucher",
    )
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        SQLEnum(RecurrenceFrequency),
        nullable=False,
        comment="How often to generate vouchers",
    )
    day_of_month: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Day of month for monthly/quarterly/yearly frequency (1-31)",
    )
    day_of_week: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Day of week for weekly frequency (0=Monday, 6=Sunday)",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date from which recurring vouchers start",
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date until which recurring vouchers should be generated (null = indefinite)",
    )
    next_run_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Next scheduled date for voucher generation",
    )
    last_run_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last date when voucher was generated",
    )
    total_occurrences: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of vouchers to generate (null = unlimited)",
    )
    completed_occurrences: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of vouchers already generated",
    )
    status: Mapped[RecurringVoucherStatus] = mapped_column(
        SQLEnum(RecurringVoucherStatus),
        default=RecurringVoucherStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    auto_post: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Automatically post generated vouchers",
    )
    auto_approve: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Automatically approve generated vouchers (requires auto_post)",
    )
    narration_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Narration template with placeholders like {month}, {year}",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total debit/credit amount",
    )
    template_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Voucher line items as JSON [{account_id, debit, credit, narration}]",
    )
    notify_on_generation: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Send notification when voucher is generated",
    )
    notify_days_before: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Days before next_run_date to send reminder notification",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    voucher_type: Mapped["VoucherType"] = relationship(
        "VoucherType",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RecurringVoucher(name={self.template_name}, freq={self.frequency})>"


class RecurringVoucherLog(BaseModel):
    """Log of vouchers generated from recurring templates."""

    __tablename__ = "fin_recurring_voucher_log"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recurring_voucher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fin_recurring_voucher.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voucher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Generated voucher ID",
    )
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="The date this voucher was scheduled for",
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the voucher was actually generated",
    )
    occurrence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Which occurrence this is (1, 2, 3...)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
        comment="PENDING, GENERATED, SKIPPED, FAILED",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if generation failed",
    )

    # Relationships
    recurring_voucher: Mapped["RecurringVoucher"] = relationship(
        "RecurringVoucher",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RecurringVoucherLog(rv_id={self.recurring_voucher_id}, date={self.scheduled_date})>"
