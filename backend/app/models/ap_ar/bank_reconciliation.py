"""Bank Statement and Reconciliation Models."""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, AuditMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.account import Account
    from app.models.finance.voucher import Voucher
    from app.models.auth.user import User


class StatementTransactionType(str, enum.Enum):
    """Type of bank statement transaction."""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class ReconciliationStatus(str, enum.Enum):
    """Status of bank statement entry reconciliation."""
    UNRECONCILED = "UNRECONCILED"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    RECONCILED = "RECONCILED"


class BankReconciliationStatus(str, enum.Enum):
    """Status of bank reconciliation session."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class BankStatement(BaseModel, AuditMixin, SoftDeleteMixin):
    """Bank Statement entry imported from bank."""

    __tablename__ = "txn_bank_statement"

    # Bank Account
    bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_account.id"), nullable=False, index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"), nullable=False, index=True
    )

    # Transaction Details
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transaction_type: Mapped[StatementTransactionType] = mapped_column(
        Enum(StatementTransactionType), nullable=False
    )

    # Amounts
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    running_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Additional Bank Info
    cheque_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    utr_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Bank's internal transaction ID

    # Reconciliation Status
    reconciliation_status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(ReconciliationStatus),
        nullable=False,
        default=ReconciliationStatus.UNRECONCILED,
        index=True,
    )
    reconciled_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    reconciled_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("txn_voucher.id"), nullable=True
    )
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reconciled_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )

    # Import Tracking
    import_batch_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    import_row_number: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Relationships
    bank_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[bank_account_id], lazy="selectin"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", lazy="selectin"
    )
    reconciled_voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher", lazy="selectin"
    )
    reconciled_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reconciled_by_id], lazy="selectin"
    )
    matches: Mapped[list["BankStatementMatch"]] = relationship(
        "BankStatementMatch",
        back_populates="statement",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_bank_stmt_account_date", "bank_account_id", "transaction_date"),
        Index("ix_bank_stmt_import", "import_batch_id", "import_row_number"),
        CheckConstraint(
            "(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)",
            name="ck_bank_stmt_amount_exclusive"
        ),
    )

    def __repr__(self) -> str:
        return f"<BankStatement {self.reference_number} {self.transaction_date}>"

    @property
    def amount(self) -> Decimal:
        """Get the transaction amount (positive for credit, negative for debit)."""
        if self.transaction_type == StatementTransactionType.CREDIT:
            return self.credit_amount
        return -self.debit_amount

    @property
    def unreconciled_amount(self) -> Decimal:
        """Calculate unreconciled amount."""
        total = self.credit_amount if self.credit_amount > 0 else self.debit_amount
        return total - self.reconciled_amount


class BankStatementMatch(BaseModel):
    """Match between bank statement and voucher/payment."""

    __tablename__ = "txn_bank_statement_match"

    statement_id: Mapped[UUID] = mapped_column(
        ForeignKey("txn_bank_statement.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voucher_id: Mapped[UUID] = mapped_column(
        ForeignKey("txn_voucher.id"), nullable=False, index=True
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    match_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MANUAL"
    )  # MANUAL, AUTO

    # Relationships
    statement: Mapped["BankStatement"] = relationship(
        "BankStatement", back_populates="matches", lazy="selectin"
    )
    voucher: Mapped["Voucher"] = relationship("Voucher", lazy="selectin")

    __table_args__ = (
        CheckConstraint("matched_amount > 0", name="ck_match_positive_amount"),
    )

    def __repr__(self) -> str:
        return f"<BankStatementMatch {self.statement_id} -> {self.voucher_id}>"


class BankReconciliation(BaseModel, AuditMixin):
    """Bank Reconciliation session/summary."""

    __tablename__ = "txn_bank_reconciliation"

    bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_account.id"), nullable=False, index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"), nullable=False, index=True
    )

    # Reconciliation Period
    reconciliation_date: Mapped[date] = mapped_column(Date, nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Balances
    statement_opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    statement_closing_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    book_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )

    # Reconciliation Summary
    deposits_in_transit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )  # Credits in books, not in bank
    outstanding_cheques: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )  # Debits in books, not in bank
    bank_charges: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )  # In bank, not in books
    bank_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )  # In bank, not in books
    other_adjustments: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    reconciled_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    difference: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )

    # Status
    status: Mapped[BankReconciliationStatus] = mapped_column(
        Enum(BankReconciliationStatus),
        nullable=False,
        default=BankReconciliationStatus.DRAFT,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    bank_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[bank_account_id], lazy="selectin"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", lazy="selectin"
    )
    completed_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[completed_by_id], lazy="selectin"
    )

    __table_args__ = (
        Index("ix_bank_recon_account_date", "bank_account_id", "reconciliation_date"),
    )

    def __repr__(self) -> str:
        return f"<BankReconciliation {self.bank_account_id} {self.reconciliation_date}>"

    def calculate_reconciled_balance(self) -> Decimal:
        """Calculate the reconciled book balance."""
        return (
            self.book_balance
            - self.deposits_in_transit
            + self.outstanding_cheques
            + self.bank_charges
            - self.bank_interest
            + self.other_adjustments
        )

    def calculate_difference(self) -> Decimal:
        """Calculate the difference between statement and reconciled balance."""
        return self.statement_closing_balance - self.calculate_reconciled_balance()
