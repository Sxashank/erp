"""
Fixed Deposit Account Models
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.models.base import BaseModel
from app.models.fixed_deposits.fd_product import (
    FDInterestPayoutFrequency,
    FDCompoundingFrequency,
    FDCustomerCategory,
)
import enum


class FDStatus(str, enum.Enum):
    """Fixed Deposit status."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    PREMATURE_CLOSED = "PREMATURE_CLOSED"
    RENEWED = "RENEWED"
    CANCELLED = "CANCELLED"


class FDTransactionType(str, enum.Enum):
    """Types of FD transactions."""
    DEPOSIT = "DEPOSIT"
    INTEREST_PAYOUT = "INTEREST_PAYOUT"
    INTEREST_CAPITALIZATION = "INTEREST_CAPITALIZATION"
    TDS_DEDUCTION = "TDS_DEDUCTION"
    MATURITY_PAYOUT = "MATURITY_PAYOUT"
    PREMATURE_PAYOUT = "PREMATURE_PAYOUT"
    RENEWAL = "RENEWAL"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    PENALTY = "PENALTY"


class FixedDeposit(BaseModel):
    """
    Fixed Deposit Account.
    Represents an individual FD with its terms and status.
    """
    __tablename__ = "fd_fixed_deposit"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # FD Identification
    fd_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Product reference
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_product.id"),
        nullable=False,
        index=True,
    )

    # Customer reference
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id"),
        nullable=False,
        index=True,
    )
    customer_category: Mapped[FDCustomerCategory] = mapped_column(
        SQLEnum(FDCustomerCategory, name="fdcustomercategory", create_type=False),
        nullable=False,
        default=FDCustomerCategory.GENERAL,
    )

    # Deposit details
    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    deposit_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)  # Interest start date

    # Tenure
    tenure_days: Mapped[int] = mapped_column(Integer, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Interest terms
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    interest_payout_frequency: Mapped[FDInterestPayoutFrequency] = mapped_column(
        SQLEnum(FDInterestPayoutFrequency, name="fdinterestpayoutfrequency", create_type=False),
        nullable=False,
    )
    compounding_frequency: Mapped[FDCompoundingFrequency] = mapped_column(
        SQLEnum(FDCompoundingFrequency, name="fdcompoundingfrequency", create_type=False),
        nullable=False,
    )

    # Calculated values
    maturity_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    accrued_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    paid_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    tds_deducted: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )

    # Interest payout account
    interest_payout_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="BANK_TRANSFER"
    )  # BANK_TRANSFER, CAPITALIZE, CHEQUE
    payout_bank_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )  # Customer's bank account for interest credit

    # Auto-renewal settings
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    renewal_tenure_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_fd_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_fixed_deposit.id"),
        nullable=True,
    )  # Reference to original FD if renewed

    # Loan against FD
    has_loan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )  # Reference to loan if any

    # Status and lifecycle
    status: Mapped[FDStatus] = mapped_column(
        SQLEnum(FDStatus, name="fdstatus"),
        nullable=False,
        default=FDStatus.DRAFT,
    )
    last_interest_calc_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_interest_payout_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closure_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    closure_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Branch/Staff
    branch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id"),
        nullable=True,
    )
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    approved_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped["FDProduct"] = relationship("FDProduct", lazy="joined")
    interest_accruals: Mapped[List["FDInterestAccrual"]] = relationship(
        "FDInterestAccrual",
        back_populates="fixed_deposit",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["FDTransaction"]] = relationship(
        "FDTransaction",
        back_populates="fixed_deposit",
        cascade="all, delete-orphan",
    )
    nominees: Mapped[List["FDNominee"]] = relationship(
        "FDNominee",
        back_populates="fixed_deposit",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FixedDeposit {self.fd_number}: {self.deposit_amount}>"


class FDInterestAccrual(BaseModel):
    """
    Interest accrual records for FDs.
    Tracks daily/periodic interest calculations.
    """
    __tablename__ = "fd_interest_accrual"

    fixed_deposit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_fixed_deposit.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    accrual_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)

    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    interest_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    cumulative_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )

    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id"),
        nullable=True,
    )

    # Relationships
    fixed_deposit: Mapped["FixedDeposit"] = relationship(
        "FixedDeposit",
        back_populates="interest_accruals",
    )

    def __repr__(self) -> str:
        return f"<FDInterestAccrual {self.accrual_date}: {self.interest_amount}>"


class FDTransaction(BaseModel):
    """
    All transactions related to an FD.
    Includes deposits, payouts, TDS deductions, etc.
    """
    __tablename__ = "fd_transaction"

    fixed_deposit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_fixed_deposit.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_type: Mapped[FDTransactionType] = mapped_column(
        SQLEnum(FDTransactionType, name="fdtransactiontype"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)

    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )

    # Payment details
    payment_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id"),
        nullable=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    fixed_deposit: Mapped["FixedDeposit"] = relationship(
        "FixedDeposit",
        back_populates="transactions",
    )

    def __repr__(self) -> str:
        return f"<FDTransaction {self.transaction_type}: {self.credit_amount - self.debit_amount}>"


class FDNominee(BaseModel):
    """
    Nominee details for FDs.
    """
    __tablename__ = "fd_nominee"

    fixed_deposit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_fixed_deposit.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nominee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nominee_relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    share_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=100
    )

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Guardian (if nominee is minor)
    is_minor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guardian_relationship: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    fixed_deposit: Mapped["FixedDeposit"] = relationship(
        "FixedDeposit",
        back_populates="nominees",
    )

    def __repr__(self) -> str:
        return f"<FDNominee {self.nominee_name}: {self.share_percentage}%>"


# Import for type hints
from app.models.fixed_deposits.fd_product import FDProduct
