"""Pydantic schemas for Attendance models."""

from datetime import date, time, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import (
    AttendanceStatus,
    AttendanceSource,
    RegularizationStatus,
)


# ============================================
# Attendance Punch Schemas
# ============================================
class AttendancePunchBase(BaseModel):
    """Base schema for attendance punch."""
    punch_datetime: datetime
    punch_type: str = Field(..., pattern="^(IN|OUT)$")
    source: AttendanceSource = AttendanceSource.BIOMETRIC
    device_id: Optional[str] = Field(None, max_length=50)
    device_name: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=45)
    location: Optional[str] = Field(None, max_length=200)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class AttendancePunchCreate(AttendancePunchBase):
    """Schema for creating attendance punch."""
    employee_id: UUID


class AttendancePunchBulkCreate(BaseModel):
    """Schema for bulk creating attendance punches (import)."""
    punches: List[AttendancePunchCreate]


class AttendancePunchResponse(AttendancePunchBase):
    """Response schema for attendance punch."""
    id: UUID
    employee_id: UUID
    is_processed: bool
    is_valid: bool
    invalid_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# Attendance Schemas
# ============================================
class AttendanceBase(BaseModel):
    """Base schema for attendance."""
    attendance_date: date
    shift_id: Optional[UUID] = None
    scheduled_in: Optional[time] = None
    scheduled_out: Optional[time] = None
    first_in: Optional[time] = None
    last_out: Optional[time] = None
    all_punches: Optional[List[Dict[str, Any]]] = None
    status: AttendanceStatus = AttendanceStatus.ABSENT
    total_work_minutes: int = 0
    break_minutes: int = 0
    effective_work_minutes: int = 0
    late_minutes: int = 0
    early_leave_minutes: int = 0
    overtime_minutes: int = 0
    overtime_approved: bool = False
    leave_application_id: Optional[UUID] = None
    leave_type_id: Optional[UUID] = None
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    is_week_off: bool = False
    is_regularized: bool = False
    is_on_duty: bool = False
    on_duty_reference: Optional[str] = None
    is_work_from_home: bool = False
    remarks: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    """Schema for creating attendance (manual entry)."""
    employee_id: UUID


class AttendanceUpdate(BaseModel):
    """Schema for updating attendance."""
    shift_id: Optional[UUID] = None
    first_in: Optional[time] = None
    last_out: Optional[time] = None
    status: Optional[AttendanceStatus] = None
    overtime_approved: Optional[bool] = None
    is_on_duty: Optional[bool] = None
    on_duty_reference: Optional[str] = None
    is_work_from_home: Optional[bool] = None
    remarks: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    """Response schema for attendance."""
    id: UUID
    employee_id: UUID
    is_processed: bool
    is_locked: bool
    regularization_id: Optional[UUID] = None

    # Related info
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    shift_name: Optional[str] = None
    leave_type_name: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceFilters(BaseModel):
    """Filters for attendance list."""
    organization_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    status: Optional[AttendanceStatus] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    is_processed: Optional[bool] = None
    is_locked: Optional[bool] = None


# ============================================
# Attendance Regularization Schemas
# ============================================
class AttendanceRegularizationBase(BaseModel):
    """Base schema for attendance regularization."""
    attendance_date: date
    request_type: str = Field(..., max_length=20)  # MISSED_PUNCH, CORRECTION, ON_DUTY, WFH
    reason: str = Field(..., min_length=10)
    original_first_in: Optional[time] = None
    original_last_out: Optional[time] = None
    original_status: Optional[str] = None
    requested_first_in: Optional[time] = None
    requested_last_out: Optional[time] = None
    requested_status: Optional[str] = None
    attachments: Optional[List[str]] = None


class AttendanceRegularizationCreate(AttendanceRegularizationBase):
    """Schema for creating attendance regularization."""
    employee_id: UUID


class AttendanceRegularizationApprove(BaseModel):
    """Schema for approving regularization."""
    remarks: Optional[str] = None


class AttendanceRegularizationReject(BaseModel):
    """Schema for rejecting regularization."""
    reason: str = Field(..., min_length=10)


class AttendanceRegularizationResponse(AttendanceRegularizationBase):
    """Response schema for attendance regularization."""
    id: UUID
    employee_id: UUID
    status: RegularizationStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[date] = None
    approver_remarks: Optional[str] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[date] = None
    rejection_reason: Optional[str] = None

    # Related info
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceRegularizationFilters(BaseModel):
    """Filters for regularization list."""
    organization_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    status: Optional[RegularizationStatus] = None
    request_type: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


# ============================================
# Monthly Attendance Summary Schemas
# ============================================
class MonthlyAttendanceSummaryBase(BaseModel):
    """Base schema for monthly attendance summary."""
    year: int
    month: int
    total_days: int
    working_days: int
    holidays: int = 0
    week_offs: int = 0
    present_days: Decimal = Field(0, ge=0)
    absent_days: Decimal = Field(0, ge=0)
    half_days: Decimal = Field(0, ge=0)
    late_days: int = 0
    early_leave_days: int = 0
    paid_leave_days: Decimal = Field(0, ge=0)
    unpaid_leave_days: Decimal = Field(0, ge=0)
    leave_breakdown: Optional[Dict[str, Decimal]] = None
    on_duty_days: Decimal = Field(0, ge=0)
    wfh_days: Decimal = Field(0, ge=0)
    comp_off_availed: Decimal = Field(0, ge=0)
    total_overtime_hours: Decimal = Field(0, ge=0)
    approved_overtime_hours: Decimal = Field(0, ge=0)
    total_late_minutes: int = 0
    late_deduction_lop: Decimal = Field(0, ge=0)
    payable_days: Decimal
    lop_days: Decimal = Field(0, ge=0)
    remarks: Optional[str] = None


class MonthlyAttendanceSummaryCreate(MonthlyAttendanceSummaryBase):
    """Schema for creating monthly attendance summary."""
    employee_id: UUID


class MonthlyAttendanceSummaryResponse(MonthlyAttendanceSummaryBase):
    """Response schema for monthly attendance summary."""
    id: UUID
    employee_id: UUID
    is_processed: bool
    processed_at: Optional[datetime] = None
    is_locked: bool
    locked_at: Optional[datetime] = None

    # Related info
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# Attendance Processing Schemas
# ============================================
class ProcessDailyAttendanceRequest(BaseModel):
    """Request schema for processing daily attendance."""
    organization_id: UUID
    attendance_date: date
    employee_ids: Optional[List[UUID]] = None  # None means all employees


class ProcessMonthlyAttendanceRequest(BaseModel):
    """Request schema for processing monthly attendance."""
    organization_id: UUID
    year: int
    month: int
    employee_ids: Optional[List[UUID]] = None  # None means all employees


class LockAttendanceRequest(BaseModel):
    """Request schema for locking attendance for payroll."""
    organization_id: UUID
    year: int
    month: int


class AttendanceProcessingResult(BaseModel):
    """Result of attendance processing."""
    total_employees: int
    processed: int
    skipped: int
    errors: List[Dict[str, Any]]
