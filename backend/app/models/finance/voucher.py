"""Voucher and VoucherLine models for General Ledger transactions."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
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
from app.core.constants import VoucherStatus, PartyType, BalanceType

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.finance.voucher_type import VoucherType
    from app.models.finance.financial_year import FinancialYear, FinancialPeriod
    from app.models.finance.account import Account
    from app.models.finance.cost_center import CostCenter
    from app.models.workflow import WorkflowInstance


class Voucher(BaseModel):
    """Voucher/Transaction header for GL entries."""

    __tablename__ = "txn_voucher"

    voucher_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_voucher_type.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    voucher_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Auto-generated or manual voucher number",
    )
    voucher_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    financial_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_period.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="External reference number",
    )
    reference_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    narration: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Voucher narration/description",
    )
    total_debit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_credit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    status: Mapped[VoucherStatus] = mapped_column(
        SQLEnum(VoucherStatus),
        default=VoucherStatus.DRAFT,
        nullable=False,
        index=True,
    )
    approval_status: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Approval workflow status [{level, approved_by, approved_at}]",
    )
    current_approval_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    submitted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    posted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_reversed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    reversal_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )
    original_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is a reversal, reference to original voucher",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to active workflow instance",
    )

    # Relationships
    voucher_type: Mapped["VoucherType"] = relationship(
        "VoucherType",
        back_populates="vouchers",
        lazy="selectin",
    )
    financial_year: Mapped["FinancialYear"] = relationship(
        "FinancialYear",
        lazy="selectin",
    )
    period: Mapped["FinancialPeriod"] = relationship(
        "FinancialPeriod",
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="vouchers",
        lazy="selectin",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        foreign_keys=[workflow_instance_id],
        lazy="selectin",
    )
    lines: Mapped[List["VoucherLine"]] = relationship(
        "VoucherLine",
        back_populates="voucher",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="VoucherLine.line_number",
    )

    def is_balanced(self) -> bool:
        """Check if voucher debits equal credits."""
        return self.total_debit == self.total_credit

    def __repr__(self) -> str:
        return f"<Voucher(number={self.voucher_number}, date={self.voucher_date})>"


class VoucherLine(BaseModel):
    """Voucher line items for individual account entries."""

    __tablename__ = "txn_voucher_line"

    voucher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line sequence number",
    )
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    narration: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Line-level narration",
    )
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_cost_center.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Cost center for expense allocation",
    )
    party_type: Mapped[Optional[PartyType]] = mapped_column(
        SQLEnum(PartyType),
        nullable=True,
        comment="Type of party - CUSTOMER, VENDOR, EMPLOYEE",
    )
    party_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Party ID for sub-ledger",
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reference document type e.g. INVOICE, BILL",
    )
    reference_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference document ID",
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reference document number",
    )
    cheque_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    cheque_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    voucher: Mapped["Voucher"] = relationship(
        "Voucher",
        back_populates="lines",
    )
    account: Mapped["Account"] = relationship(
        "Account",
        lazy="selectin",
    )
    cost_center: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter",
        lazy="selectin",
    )

    @property
    def balance_type(self) -> Optional[BalanceType]:
        """Get the balance type based on amounts."""
        if self.debit_amount > 0:
            return BalanceType.DEBIT
        if self.credit_amount > 0:
            return BalanceType.CREDIT
        return None

    @property
    def amount(self) -> Decimal:
        """Get the non-zero amount."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    def __repr__(self) -> str:
        return f"<VoucherLine(line={self.line_number}, dr={self.debit_amount}, cr={self.credit_amount})>"
