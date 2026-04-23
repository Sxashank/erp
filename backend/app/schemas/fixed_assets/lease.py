"""Lease Accounting schemas (Ind AS 116)."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.models.fixed_assets.lease import (
    LeaseType,
    LeaseAssetType,
    LeaseStatus,
    PaymentFrequency,
)


class LeaseCreate(BaseSchema):
    """Schema for creating a new lease."""

    organization_id: UUID
    lease_number: str = Field(..., max_length=50)
    lease_name: str = Field(..., max_length=200)
    lease_type: LeaseType = LeaseType.FINANCE
    asset_type: LeaseAssetType

    # Lessor
    lessor_id: Optional[UUID] = None
    lessor_name: Optional[str] = Field(None, max_length=200)

    # Asset details
    asset_description: str
    asset_location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None

    # Lease terms
    commencement_date: date
    end_date: date
    lease_term_months: int = Field(..., gt=0)

    # Payment details
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    payment_amount: Decimal = Field(..., ge=0)
    payment_day: int = Field(1, ge=1, le=31)
    payment_in_advance: bool = False

    # Variable payments
    has_variable_payments: bool = False
    variable_payment_description: Optional[str] = None

    # Escalation
    has_escalation: bool = False
    escalation_percentage: Decimal = Field(default=Decimal("0.00"), ge=0)
    escalation_frequency_months: int = 12

    # Security deposit
    security_deposit: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Options
    has_renewal_option: bool = False
    renewal_term_months: Optional[int] = None
    renewal_reasonably_certain: bool = False

    has_purchase_option: bool = False
    purchase_option_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    purchase_reasonably_certain: bool = False

    has_termination_option: bool = False
    termination_penalty: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Discount rate
    discount_rate: Decimal = Field(..., gt=0, description="Incremental borrowing rate %")

    # Initial costs
    initial_direct_costs: Decimal = Field(default=Decimal("0.00"), ge=0)
    estimated_restoration_cost: Decimal = Field(default=Decimal("0.00"), ge=0)

    # GL Accounts
    roua_account_id: Optional[UUID] = None
    lease_liability_account_id: Optional[UUID] = None
    interest_expense_account_id: Optional[UUID] = None
    depreciation_expense_account_id: Optional[UUID] = None
    accumulated_depreciation_account_id: Optional[UUID] = None

    notes: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if "commencement_date" in info.data and v <= info.data["commencement_date"]:
            raise ValueError("End date must be after commencement date")
        return v


class LeaseUpdate(BaseSchema):
    """Schema for updating a lease."""

    lease_name: Optional[str] = Field(None, max_length=200)
    lessor_id: Optional[UUID] = None
    lessor_name: Optional[str] = Field(None, max_length=200)
    asset_description: Optional[str] = None
    asset_location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None

    # Only certain fields can be updated without modification
    has_variable_payments: Optional[bool] = None
    variable_payment_description: Optional[str] = None

    # GL Accounts can be updated
    roua_account_id: Optional[UUID] = None
    lease_liability_account_id: Optional[UUID] = None
    interest_expense_account_id: Optional[UUID] = None
    depreciation_expense_account_id: Optional[UUID] = None
    accumulated_depreciation_account_id: Optional[UUID] = None

    notes: Optional[str] = None


class LeaseModificationCreate(BaseSchema):
    """Schema for lease modification."""

    modification_date: date
    modification_type: str = Field(..., max_length=50)
    description: str

    # New terms
    new_end_date: Optional[date] = None
    new_payment_amount: Optional[Decimal] = None
    new_discount_rate: Optional[Decimal] = None


class LeaseActivate(BaseSchema):
    """Schema for activating a lease."""

    activation_date: Optional[date] = None  # Defaults to commencement_date


class LeaseTerminate(BaseSchema):
    """Schema for early termination."""

    termination_date: date
    termination_reason: str
    settlement_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class LeasePaymentRecord(BaseSchema):
    """Schema for recording lease payment."""

    payment_date: date
    paid_amount: Decimal = Field(..., ge=0)
    payment_reference: Optional[str] = Field(None, max_length=100)


class LeasePaymentScheduleResponse(AuditSchema):
    """Schema for lease payment schedule response."""

    id: UUID
    lease_id: UUID
    payment_number: int
    payment_date: date
    financial_year: str

    opening_liability: Decimal
    payment_amount: Decimal
    interest_component: Decimal
    principal_component: Decimal
    closing_liability: Decimal

    depreciation_amount: Decimal
    roua_carrying_value: Decimal

    is_paid: bool
    paid_date: Optional[date] = None
    paid_amount: Decimal
    payment_reference: Optional[str] = None

    interest_posted: bool
    depreciation_posted: bool
    variance_amount: Decimal


class LeaseResponse(AuditSchema):
    """Schema for lease response."""

    id: UUID
    organization_id: UUID
    lease_number: str
    lease_name: str
    lease_type: LeaseType
    asset_type: LeaseAssetType
    status: LeaseStatus

    # Lessor
    lessor_id: Optional[UUID] = None
    lessor_name: Optional[str] = None

    # Asset details
    asset_description: str
    asset_location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None

    # Lease terms
    commencement_date: date
    end_date: date
    lease_term_months: int
    remaining_term_months: int

    # Payment details
    payment_frequency: PaymentFrequency
    payment_amount: Decimal
    payment_day: int
    payment_in_advance: bool

    # Escalation
    has_escalation: bool
    escalation_percentage: Decimal

    # Security deposit
    security_deposit: Decimal

    # Options
    has_renewal_option: bool
    renewal_term_months: Optional[int] = None
    has_purchase_option: bool
    purchase_option_price: Decimal
    has_termination_option: bool

    # Discount rate
    discount_rate: Decimal

    # Initial costs
    initial_direct_costs: Decimal
    estimated_restoration_cost: Decimal

    # Ind AS 116 Values
    roua_initial_value: Decimal
    roua_accumulated_depreciation: Decimal
    roua_carrying_value: Decimal

    lease_liability_initial: Decimal
    lease_liability_current: Decimal
    lease_liability_current_portion: Decimal
    lease_liability_non_current: Decimal

    total_lease_payments: Decimal
    total_interest_expense: Decimal
    interest_expense_ytd: Decimal
    depreciation_expense_ytd: Decimal

    # Processing dates
    last_payment_date: Optional[date] = None
    next_payment_date: Optional[date] = None

    # Flags
    is_short_term: bool
    is_low_value: bool
    is_modified: bool

    notes: Optional[str] = None


class LeaseListResponse(BaseSchema):
    """Paginated lease list response."""

    items: List[LeaseResponse]
    total: int
    skip: int
    limit: int


class LeaseSummaryResponse(BaseSchema):
    """Summary of lease portfolio."""

    organization_id: UUID
    as_on_date: date

    # Counts
    total_leases: int
    active_leases: int
    expiring_within_90_days: int

    # ROUA Summary
    total_roua_initial: Decimal
    total_roua_accumulated_depreciation: Decimal
    total_roua_carrying_value: Decimal

    # Liability Summary
    total_lease_liability: Decimal
    total_current_portion: Decimal
    total_non_current_portion: Decimal

    # Annual expenses
    total_interest_expense_ytd: Decimal
    total_depreciation_ytd: Decimal

    # By type breakdown
    by_asset_type: List[dict]
    by_lease_type: List[dict]

    # Upcoming payments
    upcoming_payments_30_days: Decimal
    upcoming_payments_90_days: Decimal


class LeaseDisclosureResponse(BaseSchema):
    """Ind AS 116 disclosure requirements."""

    organization_id: UUID
    financial_year: str

    # Maturity analysis of lease liabilities
    maturity_analysis: dict  # Within 1 year, 1-2 years, 2-5 years, > 5 years

    # Expense recognized in P&L
    depreciation_expense: Decimal
    interest_expense: Decimal
    short_term_lease_expense: Decimal
    low_value_lease_expense: Decimal
    variable_lease_payments: Decimal
    total_cash_outflow: Decimal

    # Additions/modifications during year
    roua_additions: Decimal
    roua_modifications: Decimal

    # Average discount rate
    weighted_avg_discount_rate: Decimal


class InterestPostingRequest(BaseSchema):
    """Request to post interest for a period."""

    period_from: date
    period_to: date
    lease_ids: Optional[List[UUID]] = None  # If None, process all active leases


class DepreciationPostingRequest(BaseSchema):
    """Request to post ROUA depreciation for a period."""

    depreciation_period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    lease_ids: Optional[List[UUID]] = None
