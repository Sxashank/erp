"""
Fixed Deposit Product Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema

from app.models.fixed_deposits.fd_product import (
    FDInterestPayoutFrequency,
    FDCompoundingFrequency,
    FDCustomerCategory,
)


# Interest Slab Schemas
class FDInterestSlabBase(CamelSchema):
    """Base schema for FD interest slab."""
    customer_category: FDCustomerCategory = FDCustomerCategory.GENERAL
    min_tenure_days: int = Field(..., ge=1)
    max_tenure_days: int = Field(..., ge=1)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    interest_rate: Decimal = Field(..., ge=0, le=20)
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class FDInterestSlabCreate(FDInterestSlabBase):
    """Schema for creating interest slab."""
    pass


class FDInterestSlabUpdate(CamelSchema):
    """Schema for updating interest slab."""
    customer_category: Optional[FDCustomerCategory] = None
    min_tenure_days: Optional[int] = Field(None, ge=1)
    max_tenure_days: Optional[int] = Field(None, ge=1)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=20)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class FDInterestSlabResponse(FDInterestSlabBase):
    """Schema for interest slab response."""

    id: UUID
    product_id: UUID
    created_at: datetime


# Product Schemas
class FDProductBase(CamelSchema):
    """Base schema for FD product."""
    product_code: str = Field(..., min_length=1, max_length=20)
    product_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    min_tenure_days: int = Field(7, ge=1)
    max_tenure_days: int = Field(3650, ge=1)
    min_amount: Decimal = Field(Decimal("1000"), ge=0)
    max_amount: Optional[Decimal] = None

    interest_payout_frequency: FDInterestPayoutFrequency = FDInterestPayoutFrequency.QUARTERLY
    compounding_frequency: FDCompoundingFrequency = FDCompoundingFrequency.QUARTERLY

    allow_premature_withdrawal: bool = True
    premature_penalty_rate: Optional[Decimal] = Field(Decimal("1.00"), ge=0, le=10)

    allow_auto_renewal: bool = True
    auto_renewal_tenure_days: Optional[int] = None

    allow_loan_against_fd: bool = True
    max_loan_percentage: Optional[Decimal] = Field(Decimal("90.00"), ge=0, le=100)
    loan_interest_premium: Optional[Decimal] = Field(Decimal("2.00"), ge=0, le=10)

    tds_applicable: bool = True
    tds_threshold: Decimal = Field(Decimal("40000"), ge=0)

    fd_liability_account_id: Optional[UUID] = None
    interest_expense_account_id: Optional[UUID] = None
    tds_payable_account_id: Optional[UUID] = None

    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class FDProductCreate(FDProductBase):
    """Schema for creating FD product."""
    organization_id: UUID
    interest_slabs: Optional[List[FDInterestSlabCreate]] = None


class FDProductUpdate(CamelSchema):
    """Schema for updating FD product."""
    product_code: Optional[str] = Field(None, min_length=1, max_length=20)
    product_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

    min_tenure_days: Optional[int] = Field(None, ge=1)
    max_tenure_days: Optional[int] = Field(None, ge=1)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

    interest_payout_frequency: Optional[FDInterestPayoutFrequency] = None
    compounding_frequency: Optional[FDCompoundingFrequency] = None

    allow_premature_withdrawal: Optional[bool] = None
    premature_penalty_rate: Optional[Decimal] = None

    allow_auto_renewal: Optional[bool] = None
    auto_renewal_tenure_days: Optional[int] = None

    allow_loan_against_fd: Optional[bool] = None
    max_loan_percentage: Optional[Decimal] = None
    loan_interest_premium: Optional[Decimal] = None

    tds_applicable: Optional[bool] = None
    tds_threshold: Optional[Decimal] = None

    fd_liability_account_id: Optional[UUID] = None
    interest_expense_account_id: Optional[UUID] = None
    tds_payable_account_id: Optional[UUID] = None

    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class FDProductResponse(FDProductBase):
    """Schema for FD product response."""

    id: UUID
    organization_id: UUID
    interest_slabs: List[FDInterestSlabResponse] = []
    created_at: datetime


class FDProductListResponse(CamelSchema):
    """Schema for paginated FD product list."""
    items: List[FDProductResponse]
    total: int
