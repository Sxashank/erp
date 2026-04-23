"""
Fixed Deposit Product Models
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Date,
    Boolean,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.models.base import BaseModel
import enum


class FDInterestPayoutFrequency(str, enum.Enum):
    """Interest payout frequency options."""
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    ANNUALLY = "ANNUALLY"
    ON_MATURITY = "ON_MATURITY"


class FDCompoundingFrequency(str, enum.Enum):
    """Interest compounding frequency options."""
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    ANNUALLY = "ANNUALLY"
    SIMPLE = "SIMPLE"


class FDCustomerCategory(str, enum.Enum):
    """Customer categories for interest rates."""
    GENERAL = "GENERAL"
    SENIOR_CITIZEN = "SENIOR_CITIZEN"
    STAFF = "STAFF"
    NRI = "NRI"
    CORPORATE = "CORPORATE"


class FDProduct(BaseModel):
    """
    Fixed Deposit Product Master.
    Defines product terms, interest rates, and configurations.
    """
    __tablename__ = "fd_product"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    product_code: Mapped[str] = mapped_column(String(20), nullable=False)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tenure configuration
    min_tenure_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    max_tenure_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3650)
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=1000
    )
    max_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Interest configuration
    interest_payout_frequency: Mapped[FDInterestPayoutFrequency] = mapped_column(
        SQLEnum(FDInterestPayoutFrequency, name="fdinterestpayoutfrequency"),
        nullable=False,
        default=FDInterestPayoutFrequency.QUARTERLY,
    )
    compounding_frequency: Mapped[FDCompoundingFrequency] = mapped_column(
        SQLEnum(FDCompoundingFrequency, name="fdcompoundingfrequency"),
        nullable=False,
        default=FDCompoundingFrequency.QUARTERLY,
    )

    # Premature withdrawal
    allow_premature_withdrawal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    premature_penalty_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True, default=1.00
    )  # Percentage reduction in interest rate

    # Auto-renewal
    allow_auto_renewal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    auto_renewal_tenure_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # If null, same tenure as original

    # Loan against FD
    allow_loan_against_fd: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    max_loan_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True, default=90.00
    )
    loan_interest_premium: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True, default=2.00
    )  # Premium over FD rate

    # TDS configuration
    tds_applicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    tds_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=40000
    )  # Annual interest threshold for TDS

    # GL Accounts
    fd_liability_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
    )
    interest_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
    )
    tds_payable_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    interest_slabs: Mapped[List["FDInterestSlab"]] = relationship(
        "FDInterestSlab",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FDProduct {self.product_code}: {self.product_name}>"


class FDInterestSlab(BaseModel):
    """
    Interest rate slabs for FD products.
    Rates vary by tenure and customer category.
    """
    __tablename__ = "fd_interest_slab"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fd_product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_category: Mapped[FDCustomerCategory] = mapped_column(
        SQLEnum(FDCustomerCategory, name="fdcustomercategory"),
        nullable=False,
        default=FDCustomerCategory.GENERAL,
    )

    # Tenure range (in days)
    min_tenure_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_tenure_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Amount range (optional)
    min_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    max_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Interest rate
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # Annual rate

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    product: Mapped["FDProduct"] = relationship(
        "FDProduct",
        back_populates="interest_slabs",
    )

    def __repr__(self) -> str:
        return f"<FDInterestSlab {self.customer_category}: {self.interest_rate}%>"
