"""Pydantic schemas for Leave models."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema

from app.core.constants import (
    LeaveCategory,
    LeaveApplicationStatus,
    Gender,
    EmploymentType,
)


# ============================================
# Leave Type Schemas
# ============================================
class LeaveTypeBase(CamelSchema):
    """Base schema for leave type."""
    leave_code: str = Field(..., max_length=20)
    leave_name: str = Field(..., max_length=100)
    category: LeaveCategory
    description: Optional[str] = None

    # Annual Quota
    annual_quota: Decimal = Field(0, ge=0)
    max_accumulation: Optional[Decimal] = Field(None, ge=0)

    # Accrual Settings
    accrual_type: str = Field("YEARLY", max_length=20)  # YEARLY, MONTHLY, PRORATE
    accrual_on_joining: bool = True
    prorate_on_joining: bool = True

    # Carry Forward
    carry_forward_allowed: bool = False
    max_carry_forward: Optional[Decimal] = Field(None, ge=0)
    carry_forward_expiry_months: Optional[int] = None

    # Encashment
    encashment_allowed: bool = False
    max_encashment_days: Optional[Decimal] = Field(None, ge=0)
    encashment_on_separation: bool = False

    # Application Rules
    min_days_per_application: Decimal = Field(0.5, ge=0)
    max_days_per_application: Optional[Decimal] = Field(None, ge=0)
    max_consecutive_days: Optional[int] = None

    # Advance Notice
    min_advance_days: int = 0
    max_advance_days: Optional[int] = None

    # Club with Other Leaves
    can_club_with_holidays: bool = True
    can_club_with_weekoff: bool = True
    excluded_holidays_counted: bool = False

    # Negative Balance
    negative_balance_allowed: bool = False
    max_negative_balance: Optional[Decimal] = Field(None, ge=0)

    # Document Required
    document_required: bool = False
    document_required_after_days: Optional[int] = None

    # Gender Specific
    gender_specific: Optional[Gender] = None

    # Employment Type Specific
    applicable_employment_types: Optional[List[EmploymentType]] = None

    # Probation
    applicable_in_probation: bool = True
    probation_quota: Optional[Decimal] = Field(None, ge=0)

    # Notice Period
    applicable_in_notice: bool = False

    # Compensatory Off Settings
    comp_off_validity_days: Optional[int] = None

    # Half Day Settings
    half_day_allowed: bool = True

    # Paid/Unpaid
    is_paid: bool = True

    # Status
    is_active: bool = True
    display_order: int = 0


class LeaveTypeCreate(LeaveTypeBase):
    """Schema for creating leave type."""
    organization_id: UUID


class LeaveTypeUpdate(CamelSchema):
    """Schema for updating leave type."""
    leave_name: Optional[str] = None
    category: Optional[LeaveCategory] = None
    description: Optional[str] = None
    annual_quota: Optional[Decimal] = None
    max_accumulation: Optional[Decimal] = None
    accrual_type: Optional[str] = None
    accrual_on_joining: Optional[bool] = None
    prorate_on_joining: Optional[bool] = None
    carry_forward_allowed: Optional[bool] = None
    max_carry_forward: Optional[Decimal] = None
    carry_forward_expiry_months: Optional[int] = None
    encashment_allowed: Optional[bool] = None
    max_encashment_days: Optional[Decimal] = None
    encashment_on_separation: Optional[bool] = None
    min_days_per_application: Optional[Decimal] = None
    max_days_per_application: Optional[Decimal] = None
    max_consecutive_days: Optional[int] = None
    min_advance_days: Optional[int] = None
    max_advance_days: Optional[int] = None
    can_club_with_holidays: Optional[bool] = None
    can_club_with_weekoff: Optional[bool] = None
    excluded_holidays_counted: Optional[bool] = None
    negative_balance_allowed: Optional[bool] = None
    max_negative_balance: Optional[Decimal] = None
    document_required: Optional[bool] = None
    document_required_after_days: Optional[int] = None
    gender_specific: Optional[Gender] = None
    applicable_employment_types: Optional[List[EmploymentType]] = None
    applicable_in_probation: Optional[bool] = None
    probation_quota: Optional[Decimal] = None
    applicable_in_notice: Optional[bool] = None
    comp_off_validity_days: Optional[int] = None
    half_day_allowed: Optional[bool] = None
    is_paid: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class LeaveTypeResponse(LeaveTypeBase):
    """Response schema for leave type."""
    id: UUID
    organization_id: UUID


# ============================================
# Leave Balance Schemas
# ============================================
class LeaveBalanceBase(CamelSchema):
    """Base schema for leave balance."""
    year: int
    opening_balance: Decimal = Field(0, ge=0)
    accrued: Decimal = Field(0, ge=0)
    carry_forward: Decimal = Field(0, ge=0)
    adjustment: Decimal = Field(0)
    used: Decimal = Field(0, ge=0)
    encashed: Decimal = Field(0, ge=0)
    lapsed: Decimal = Field(0, ge=0)


class LeaveBalanceCreate(LeaveBalanceBase):
    """Schema for creating leave balance."""
    employee_id: UUID
    leave_type_id: UUID


class LeaveBalanceUpdate(CamelSchema):
    """Schema for updating leave balance."""
    opening_balance: Optional[Decimal] = None
    accrued: Optional[Decimal] = None
    carry_forward: Optional[Decimal] = None
    adjustment: Optional[Decimal] = None
    used: Optional[Decimal] = None
    encashed: Optional[Decimal] = None
    lapsed: Optional[Decimal] = None


class LeaveBalanceResponse(LeaveBalanceBase):
    """Response schema for leave balance."""
    id: UUID
    employee_id: UUID
    leave_type_id: UUID
    available_balance: Decimal
    leave_type_name: Optional[str] = None
    leave_type_code: Optional[str] = None


class LeaveBalanceSummary(CamelSchema):
    """Summary of all leave balances for an employee."""
    employee_id: UUID
    year: int
    balances: List[LeaveBalanceResponse]


# ============================================
# Leave Application Schemas
# ============================================
class LeaveApplicationBase(CamelSchema):
    """Base schema for leave application."""
    leave_type_id: UUID
    from_date: date
    to_date: date
    is_half_day: bool = False
    half_day_type: Optional[str] = None  # FIRST_HALF, SECOND_HALF
    reason: str = Field(..., min_length=10)
    contact_number: Optional[str] = Field(None, max_length=20)
    contact_address: Optional[str] = None
    attachments: Optional[List[str]] = None
    comp_off_date: Optional[date] = None


class LeaveApplicationCreate(LeaveApplicationBase):
    """Schema for creating leave application."""
    employee_id: UUID


class LeaveApplicationUpdate(CamelSchema):
    """Schema for updating leave application."""
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    is_half_day: Optional[bool] = None
    half_day_type: Optional[str] = None
    reason: Optional[str] = None
    contact_number: Optional[str] = None
    contact_address: Optional[str] = None
    attachments: Optional[List[str]] = None


class LeaveApplicationApprove(CamelSchema):
    """Schema for approving leave application."""
    remarks: Optional[str] = None


class LeaveApplicationReject(CamelSchema):
    """Schema for rejecting leave application."""
    reason: str = Field(..., min_length=10)


class LeaveApplicationCancel(CamelSchema):
    """Schema for cancelling leave application."""
    reason: str = Field(..., min_length=10)


class LeaveApplicationResponse(LeaveApplicationBase):
    """Response schema for leave application."""
    id: UUID
    employee_id: UUID
    application_number: str
    total_days: Decimal
    working_days: Decimal
    status: LeaveApplicationStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[date] = None
    approver_remarks: Optional[str] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[date] = None
    rejection_reason: Optional[str] = None
    cancelled_at: Optional[date] = None
    cancellation_reason: Optional[str] = None

    # Related info
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    leave_type_name: Optional[str] = None
    leave_type_code: Optional[str] = None


class LeaveApplicationFilters(CamelSchema):
    """Filters for leave application list."""
    organization_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    leave_type_id: Optional[UUID] = None
    status: Optional[LeaveApplicationStatus] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    department_id: Optional[UUID] = None
    reporting_manager_id: Optional[UUID] = None


# ============================================
# Leave Encashment Schemas
# ============================================
class LeaveEncashmentBase(CamelSchema):
    """Base schema for leave encashment."""
    leave_type_id: UUID
    year: int
    encashment_date: date
    days_encashed: Decimal = Field(..., gt=0)
    per_day_amount: Decimal = Field(..., gt=0)
    gross_amount: Decimal = Field(..., gt=0)
    tds_amount: Decimal = Field(0, ge=0)
    net_amount: Decimal = Field(..., gt=0)
    encashment_type: str = Field("ANNUAL", max_length=20)


class LeaveEncashmentCreate(LeaveEncashmentBase):
    """Schema for creating leave encashment."""
    employee_id: UUID


class LeaveEncashmentResponse(LeaveEncashmentBase):
    """Response schema for leave encashment."""
    id: UUID
    employee_id: UUID
    payroll_run_id: Optional[UUID] = None
    voucher_id: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[date] = None
    status: str

    # Related info
    employee_name: Optional[str] = None
    leave_type_name: Optional[str] = None

