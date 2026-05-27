"""
Fixed Deposit Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema

from app.models.fixed_deposits.fixed_deposit import FDStatus, FDTransactionType
from app.models.fixed_deposits.fd_product import (
    FDInterestPayoutFrequency,
    FDCompoundingFrequency,
    FDCustomerCategory,
)


# Nominee Schemas
class FDNomineeBase(CamelSchema):
    """Base schema for FD nominee."""

    nominee_name: str = Field(..., min_length=1, max_length=200)
    relationship: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    share_percentage: Decimal = Field(Decimal("100"), ge=0, le=100)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_minor: bool = False
    guardian_name: Optional[str] = None
    guardian_relationship: Optional[str] = None


class FDNomineeCreate(FDNomineeBase):
    """Schema for creating nominee."""

    pass


class FDNomineeUpdate(CamelSchema):
    """Schema for updating nominee."""

    nominee_name: Optional[str] = None
    relationship: Optional[str] = None
    date_of_birth: Optional[date] = None
    share_percentage: Optional[Decimal] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_minor: Optional[bool] = None
    guardian_name: Optional[str] = None
    guardian_relationship: Optional[str] = None


class FDNomineeResponse(FDNomineeBase):
    """Schema for nominee response."""

    id: UUID
    fixed_deposit_id: UUID


# Transaction Schema
class FDTransactionResponse(CamelSchema):
    """Schema for FD transaction response."""

    id: UUID
    fixed_deposit_id: UUID
    transaction_date: date
    transaction_type: FDTransactionType
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    payment_mode: Optional[str] = None
    reference_number: Optional[str] = None
    voucher_id: Optional[UUID] = None
    remarks: Optional[str] = None
    created_at: datetime


# Interest Accrual Schema
class FDInterestAccrualResponse(CamelSchema):
    """Schema for interest accrual response."""

    id: UUID
    fixed_deposit_id: UUID
    accrual_date: date
    period_from: date
    period_to: date
    days: int
    principal_amount: Decimal
    interest_rate: Decimal
    interest_amount: Decimal
    cumulative_interest: Decimal
    is_paid: bool
    paid_date: Optional[date] = None
    payment_reference: Optional[str] = None
    voucher_id: Optional[UUID] = None


# Fixed Deposit Schemas
class FixedDepositBase(CamelSchema):
    """Base schema for fixed deposit."""

    product_id: UUID
    customer_id: UUID
    customer_category: FDCustomerCategory = FDCustomerCategory.GENERAL

    deposit_amount: Decimal = Field(..., gt=0)
    deposit_date: date
    value_date: Optional[date] = None
    tenure_days: int = Field(..., ge=7)

    interest_payout_frequency: Optional[FDInterestPayoutFrequency] = None
    compounding_frequency: Optional[FDCompoundingFrequency] = None

    interest_payout_mode: str = Field(
        "BANK_TRANSFER", pattern="^(BANK_TRANSFER|CAPITALIZE|CHEQUE)$"
    )
    payout_bank_account_id: Optional[UUID] = None

    auto_renew: bool = False
    renewal_tenure_days: Optional[int] = None

    branch_id: Optional[UUID] = None
    remarks: Optional[str] = None


class FixedDepositCreate(FixedDepositBase):
    """Schema for creating fixed deposit."""

    organization_id: Optional[UUID] = None
    nominees: Optional[List[FDNomineeCreate]] = None


class FixedDepositUpdate(CamelSchema):
    """Schema for updating fixed deposit."""

    interest_payout_mode: Optional[str] = None
    payout_bank_account_id: Optional[UUID] = None
    auto_renew: Optional[bool] = None
    renewal_tenure_days: Optional[int] = None
    remarks: Optional[str] = None


class FixedDepositResponse(CamelSchema):
    """Schema for fixed deposit response."""

    id: UUID
    organization_id: UUID
    fd_number: str
    certificate_number: Optional[str] = None

    product_id: UUID
    product_code: Optional[str] = None
    product_name: Optional[str] = None

    customer_id: UUID
    customer_name: Optional[str] = None
    customer_category: FDCustomerCategory

    deposit_amount: Decimal
    deposit_date: date
    value_date: date
    tenure_days: int
    maturity_date: date

    interest_rate: Decimal
    interest_payout_frequency: FDInterestPayoutFrequency
    compounding_frequency: FDCompoundingFrequency

    maturity_amount: Decimal
    accrued_interest: Decimal
    paid_interest: Decimal
    tds_deducted: Decimal

    interest_payout_mode: str
    payout_bank_account_id: Optional[UUID] = None

    auto_renew: bool
    renewal_tenure_days: Optional[int] = None
    renewal_count: int
    parent_fd_id: Optional[UUID] = None

    has_loan: bool
    loan_account_id: Optional[UUID] = None

    status: FDStatus
    last_interest_calc_date: Optional[date] = None
    last_interest_payout_date: Optional[date] = None
    closed_date: Optional[date] = None
    closure_amount: Optional[Decimal] = None
    closure_remarks: Optional[str] = None

    branch_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_user_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    remarks: Optional[str] = None
    created_at: datetime

    # Nested data
    nominees: List[FDNomineeResponse] = []


class FixedDepositListResponse(CamelSchema):
    """Schema for paginated fixed deposit list."""

    items: List[FixedDepositResponse]
    total: int


class FixedDepositSummary(CamelSchema):
    """Summary statistics for FDs."""

    total_fds: int
    active_fds: int
    total_deposit_amount: Decimal
    total_maturity_amount: Decimal
    maturing_this_month: int
    maturing_next_month: int
    by_status: dict
    by_customer_category: dict


class FDMaturityProjection(CamelSchema):
    """Maturity projection for an FD."""

    fd_id: UUID
    fd_number: str
    deposit_amount: Decimal
    interest_rate: Decimal
    tenure_days: int
    maturity_date: date
    projected_interest: Decimal
    projected_maturity_amount: Decimal
    tds_estimate: Decimal
    net_maturity_amount: Decimal
    schedule: List[dict] = []  # Period-wise breakdown


class FDClosureRequest(CamelSchema):
    """Request for closing an FD."""

    closure_date: date
    closure_reason: str = Field(..., pattern="^(MATURITY|PREMATURE|CUSTOMER_REQUEST)$")
    payout_mode: str = Field("BANK_TRANSFER", pattern="^(BANK_TRANSFER|CHEQUE|CASH)$")
    bank_account_id: Optional[UUID] = None
    remarks: Optional[str] = None


class FDRenewalRequest(CamelSchema):
    """Request for renewing an FD."""

    new_tenure_days: Optional[int] = None  # If null, same tenure
    new_product_id: Optional[UUID] = None  # If null, same product
    include_interest: bool = True  # Add maturity interest to principal
    partial_withdrawal: Optional[Decimal] = None  # Amount to withdraw at renewal
    remarks: Optional[str] = None
