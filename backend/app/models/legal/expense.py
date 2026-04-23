"""Legal Expense management models.

Provides comprehensive expense tracking for legal cases
including court fees, advocate fees, and recovery tracking.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.legal.enums import (
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
    FeeStructureType,
)

if TYPE_CHECKING:
    from app.models.lending.collections import LegalCase
    from app.models.legal.advocate import Advocate


class ExpenseCategory(BaseModel):
    """Master table for legal expense categories.

    Defines the categories of expenses with their
    accounting and tax treatment.
    """

    __tablename__ = "mst_expense_category"
    __table_args__ = (
        Index("ix_expense_cat_org", "organization_id"),
        Index("ix_expense_cat_type", "category_type"),
        UniqueConstraint(
            "organization_id", "category_code", name="uq_expense_cat_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Category Details
    category_code: Mapped[str] = mapped_column(String(50), nullable=False)
    category_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_type: Mapped[ExpenseCategoryType] = mapped_column(
        String(50), nullable=False
    )

    # Accounting
    gl_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
    )

    # Tax Treatment
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    tds_section: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # 194C, 194J, etc.
    tds_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Recovery
    recoverable_from_borrower: Mapped[bool] = mapped_column(Boolean, default=True)
    recovery_priority: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Priority in recovery

    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    expenses: Mapped[List["LegalExpense"]] = relationship(back_populates="category")


class LegalExpense(BaseModel):
    """Legal expenses incurred for cases.

    Tracks all expenses with complete tax calculations
    and recovery tracking.
    """

    __tablename__ = "txn_legal_expense"
    __table_args__ = (
        Index("ix_legal_expense_org", "organization_id"),
        Index("ix_legal_expense_case", "legal_case_id"),
        Index("ix_legal_expense_category", "category_id"),
        Index("ix_legal_expense_status", "status"),
        Index("ix_legal_expense_date", "expense_date"),
        UniqueConstraint(
            "organization_id", "expense_reference", name="uq_legal_expense_ref"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_expense_category.id"),
        nullable=False,
    )
    advocate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_advocate.id"),
    )

    # Expense Identity
    expense_reference: Mapped[str] = mapped_column(String(50), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Status
    status: Mapped[ExpenseStatus] = mapped_column(
        String(50), default=ExpenseStatus.PENDING
    )

    # Amounts
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # GST
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    cgst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    cgst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    sgst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    sgst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    igst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    igst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    total_gst: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # TDS
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    tds_section: Mapped[Optional[str]] = mapped_column(String(20))
    tds_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Net Amount
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )  # Base + GST
    net_payable: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )  # Gross - TDS

    # Vendor/Payee
    payee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    payee_pan: Mapped[Optional[str]] = mapped_column(String(10))
    payee_gstin: Mapped[Optional[str]] = mapped_column(String(15))

    # Invoice Details
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50))
    invoice_date: Mapped[Optional[date]] = mapped_column(Date)
    invoice_document_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Approval
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    approved_by_name: Mapped[Optional[str]] = mapped_column(String(200))
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Payment
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(50))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id"),
    )

    # Recovery Tracking
    is_recoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    amount_recovered: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    recovery_status: Mapped[Optional[str]] = mapped_column(String(50))

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    category: Mapped["ExpenseCategory"] = relationship(back_populates="expenses")
    legal_case: Mapped["LegalCase"] = relationship()
    advocate: Mapped[Optional["Advocate"]] = relationship()
    recoveries: Mapped[List["ExpenseRecovery"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
    )


class ExpenseRecovery(BaseModel):
    """Recovery tracking for legal expenses.

    Tracks how expenses are recovered from borrowers
    or sale proceeds.
    """

    __tablename__ = "txn_expense_recovery"
    __table_args__ = (
        Index("ix_expense_recovery_expense", "legal_expense_id"),
        Index("ix_expense_recovery_type", "recovery_type"),
        Index("ix_expense_recovery_date", "recovery_date"),
    )

    # Foreign Keys
    legal_expense_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_expense.id"),
        nullable=False,
    )

    # Recovery Details
    recovery_type: Mapped[RecoveryType] = mapped_column(String(50), nullable=False)
    recovery_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_recovered: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Source Details
    source_reference: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Receipt/OTS Reference
    source_transaction_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # For Sale Proceeds
    auction_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_property_auction.id"),
    )

    # For OTS
    ots_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_ots_proposal.id"),
    )

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    expense: Mapped["LegalExpense"] = relationship(back_populates="recoveries")


class AdvocateFee(BaseModel):
    """Advocate fee records.

    Tracks fee payments to advocates with proper
    tax deductions.
    """

    __tablename__ = "txn_advocate_fee"
    __table_args__ = (
        Index("ix_advocate_fee_advocate", "advocate_id"),
        Index("ix_advocate_fee_case", "legal_case_id"),
        Index("ix_advocate_fee_date", "fee_date"),
        Index("ix_advocate_fee_status", "status"),
    )

    # Foreign Keys
    advocate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_advocate.id"),
        nullable=False,
    )
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    assignment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_advocate_assignment.id"),
    )
    hearing_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_hearing.id"),
    )
    expense_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_legal_expense.id"),
    )

    # Fee Details
    fee_type: Mapped[FeeStructureType] = mapped_column(String(50), nullable=False)
    fee_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Status
    status: Mapped[ExpenseStatus] = mapped_column(
        String(50), default=ExpenseStatus.PENDING
    )

    # Amounts
    base_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # GST (Advocates are typically exempt, but some may charge)
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # TDS under Section 194J
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    tds_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Net Payable
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_payable: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # For Success Fee
    is_success_fee: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2)
    )  # Amount recovered
    success_fee_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Payment
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(50))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    voucher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    advocate: Mapped["Advocate"] = relationship()
    legal_case: Mapped["LegalCase"] = relationship()
