"""Attendance models for HRIS module."""

from datetime import date, time, datetime
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
    Time,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import (
    AttendanceStatus,
    AttendanceSource,
    RegularizationStatus,
)

if TYPE_CHECKING:
    from app.models.hris.employee import Employee
    from app.models.hris.shift import Shift


class AttendancePunch(BaseModel):
    """Raw attendance punch records from biometric/web/mobile."""

    __tablename__ = "hris_attendance_punch"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    punch_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    punch_type: Mapped[str] = mapped_column(String(10), nullable=False)  # IN, OUT
    source: Mapped[str] = mapped_column(
        SQLEnum(AttendanceSource, name="attendance_source_enum", create_type=False),
        nullable=False,
        default=AttendanceSource.BIOMETRIC,
    )

    # Device/Location Info
    device_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)

    # Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    invalid_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship()


class Attendance(BaseModel):
    """Daily attendance record model."""

    __tablename__ = "hris_attendance"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "attendance_date", name="uq_attendance_emp_date"
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Shift
    shift_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_shift.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scheduled Times
    scheduled_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Actual Times
    first_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    last_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # All punches for the day (JSONB array)
    all_punches: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(AttendanceStatus, name="attendance_status_enum", create_type=False),
        nullable=False,
        default=AttendanceStatus.ABSENT,
    )

    # Duration in minutes
    total_work_minutes: Mapped[int] = mapped_column(Integer, default=0)
    break_minutes: Mapped[int] = mapped_column(Integer, default=0)
    effective_work_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Late/Early calculations
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    early_leave_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Overtime
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Leave reference (if on leave)
    leave_application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_leave_application.id", ondelete="SET NULL"),
        nullable=True,
    )
    leave_type_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_leave_type.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Holiday/Week-off
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    holiday_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_week_off: Mapped[bool] = mapped_column(Boolean, default=False)

    # Regularization
    is_regularized: Mapped[bool] = mapped_column(Boolean, default=False)
    regularization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_attendance_regularization.id", ondelete="SET NULL"),
        nullable=True,
    )

    # On-Duty/WFH
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=False)
    on_duty_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_work_from_home: Mapped[bool] = mapped_column(Boolean, default=False)

    # Processing Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)  # Locked for payroll

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship()
    shift: Mapped[Optional["Shift"]] = relationship()


class AttendanceRegularization(BaseModel):
    """Attendance regularization/correction request model."""

    __tablename__ = "hris_attendance_regularization"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Request Details
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)  # MISSED_PUNCH, CORRECTION, ON_DUTY, WFH
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Original Values
    original_first_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    original_last_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    original_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Requested Values
    requested_first_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    requested_last_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    requested_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Supporting Documents
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(RegularizationStatus, name="regularization_status_enum", create_type=False),
        nullable=False,
        default=RegularizationStatus.PENDING,
    )

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approver_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rejection
    rejected_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship()


class DailyAttendanceSummary(BaseModel):
    """Daily attendance summary for a period - used by payroll."""

    __tablename__ = "hris_daily_attendance_summary"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "period_from", "period_to", name="uq_daily_attendance_summary_emp_period"
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)

    # Attendance counts
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    present_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    absent_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    half_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    paid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    unpaid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    holidays: Mapped[int] = mapped_column(Integer, default=0)
    week_offs: Mapped[int] = mapped_column(Integer, default=0)

    # Payable calculation
    payable_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    lop_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Relationships
    employee: Mapped["Employee"] = relationship()


class MonthlyAttendanceSummary(BaseModel):
    """Monthly attendance summary for payroll processing."""

    __tablename__ = "hris_monthly_attendance_summary"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "year", "month", name="uq_monthly_attendance_emp_year_month"
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Days in Month
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    working_days: Mapped[int] = mapped_column(Integer, nullable=False)
    holidays: Mapped[int] = mapped_column(Integer, default=0)
    week_offs: Mapped[int] = mapped_column(Integer, default=0)

    # Attendance
    present_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    absent_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    half_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    late_days: Mapped[int] = mapped_column(Integer, default=0)
    early_leave_days: Mapped[int] = mapped_column(Integer, default=0)

    # Leave
    paid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    unpaid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # LOP
    leave_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # By leave type

    # Other
    on_duty_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    wfh_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    comp_off_availed: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Overtime
    total_overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    approved_overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)

    # Late Deduction (in minutes or LOP)
    total_late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    late_deduction_lop: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Payable Days Calculation
    payable_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    lop_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Processing Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship()
