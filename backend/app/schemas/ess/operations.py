"""Operational ESS schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.core.constants import LeaveApplicationStatus
from app.schemas.base import CamelSchema
from app.schemas.hris.performance import EmployeePerformanceDetailResponse


class ESSAssetResponse(CamelSchema):
    """Employee-scoped fixed asset view."""

    id: UUID
    asset_code: str
    asset_name: str
    category: str
    status: str
    serial_number: str | None = None
    assigned_date: date
    location: str | None = None
    department: str | None = None
    total_cost: float
    warranty_expiry_date: date | None = None
    insurance_expiry_date: date | None = None
    return_required: bool = True


class ESSAssignedAssetsResponse(CamelSchema):
    """Asset list summary for ESS."""

    items: list[ESSAssetResponse]
    total_assets: int
    total_asset_value: float


class ESSTrainingProgramSummary(CamelSchema):
    """Training row in ESS."""

    program_id: UUID
    program_code: str
    title: str
    category: str
    mode: str
    trainer_name: str
    start_date: date
    end_date: date
    duration_hours: float
    location: str
    status: str
    nomination_status: str
    attendance_marked: bool
    feedback_submitted: bool
    certificate_provided: bool


class ESSTrainingSummaryResponse(CamelSchema):
    """ESS training summary cards."""

    completed_programs: int
    upcoming_programs: int
    mandatory_programs: int
    feedback_pending: int
    total_hours_completed: float


class ESSTrainingListResponse(CamelSchema):
    """ESS training list payload."""

    summary: ESSTrainingSummaryResponse
    items: list[ESSTrainingProgramSummary]


class ESSTrainingFeedbackDetail(CamelSchema):
    """Employee feedback detail."""

    id: UUID
    overall_rating: float
    content_rating: float
    trainer_rating: float
    facilities_rating: float
    relevance_rating: float
    would_recommend: bool
    strengths: str | None = None
    improvements: str | None = None
    comments: str | None = None
    submitted_on: date


class ESSTrainingDetailResponse(CamelSchema):
    """ESS training program detail."""

    program_id: UUID
    program_code: str
    title: str
    description: str
    category: str
    mode: str
    trainer_type: str
    trainer_name: str
    trainer_contact: str | None = None
    start_date: date
    end_date: date
    duration_hours: float
    location: str
    is_mandatory: bool
    certificate_provided: bool
    nomination_status: str
    attendance_marked: bool
    feedback: ESSTrainingFeedbackDetail | None = None


class ESSPerformanceGoalListResponse(CamelSchema):
    """ESS goals list payload."""

    appraisal: EmployeePerformanceDetailResponse | None = None


class ESSLeaveTypeOption(CamelSchema):
    """Employee-facing leave type option."""

    id: UUID
    code: str
    name: str
    description: str | None = None
    annual_quota: Decimal
    available_balance: Decimal
    used: Decimal
    document_required: bool
    document_required_after_days: int | None = None
    half_day_allowed: bool


class ESSLeaveBalanceRow(CamelSchema):
    """Employee leave balance row."""

    leave_type_id: UUID
    code: str
    name: str
    opening_balance: Decimal
    accrued: Decimal
    carry_forward: Decimal
    used: Decimal
    lapsed: Decimal
    available_balance: Decimal


class ESSLeaveApplicationCreate(CamelSchema):
    """Create an employee-owned leave application."""

    leave_type_id: UUID
    from_date: date
    to_date: date
    is_half_day: bool = False
    half_day_type: str | None = None
    reason: str = Field(..., min_length=10)
    contact_number: str | None = None
    contact_address: str | None = None
    attachments: list[str] | None = None
    comp_off_date: date | None = None


class ESSLeaveApplicationUpdate(CamelSchema):
    """Update an employee-owned pending leave application."""

    from_date: date | None = None
    to_date: date | None = None
    is_half_day: bool | None = None
    half_day_type: str | None = None
    reason: str | None = Field(None, min_length=10)
    contact_number: str | None = None
    contact_address: str | None = None
    attachments: list[str] | None = None


class ESSLeaveCancelRequest(CamelSchema):
    """Cancel an employee-owned leave application."""

    reason: str = Field(..., min_length=10)


class ESSLeaveApplicationResponse(CamelSchema):
    """Employee-facing leave application row."""

    id: UUID
    application_number: str
    leave_type_id: UUID
    leave_type_code: str | None = None
    leave_type_name: str | None = None
    from_date: date
    to_date: date
    is_half_day: bool
    half_day_type: str | None = None
    total_days: Decimal
    working_days: Decimal
    reason: str
    contact_number: str | None = None
    contact_address: str | None = None
    attachments: list[str] | None = None
    status: LeaveApplicationStatus
    approver_remarks: str | None = None
    rejection_reason: str | None = None
    cancellation_reason: str | None = None
    approved_at: date | None = None
    rejected_at: date | None = None
    cancelled_at: date | None = None
    created_at: datetime


class ESSLeaveSummaryResponse(CamelSchema):
    """Leave summary for ESS."""

    balances: list[ESSLeaveBalanceRow]
    applications: list[ESSLeaveApplicationResponse]
    leave_types: list[ESSLeaveTypeOption]
    pending_count: int
    approved_this_year: Decimal


class ESSAttendanceRecordRow(CamelSchema):
    """Employee attendance record row."""

    date: date
    status: str
    in_time: str | None = None
    out_time: str | None = None
    working_hours: float
    shift: str | None = None


class ESSAttendanceRecordsResponse(CamelSchema):
    """Employee attendance records response."""

    items: list[ESSAttendanceRecordRow]


class ESSAttendanceSummaryResponse(CamelSchema):
    """Employee attendance summary response."""

    month: str
    working_days: float
    present: int
    absent: int
    leave: int
    holiday: int
    half_day: int
    work_from_home: int


class ESSRegularizationCreate(CamelSchema):
    """Create attendance regularization request."""

    attendance_date: date
    request_type: str
    reason: str = Field(..., min_length=10)
    requested_first_in: str | None = None
    requested_last_out: str | None = None
    requested_status: str | None = None
    attachments: list[str] | None = None


class ESSRegularizationResponse(CamelSchema):
    """Employee attendance regularization row."""

    id: UUID
    attendance_date: date
    request_type: str
    reason: str
    status: str
    approved_by: str | None = None
    approved_at: str | None = None
    approver_remarks: str | None = None
    rejected_at: str | None = None
    rejection_reason: str | None = None
    created_at: datetime


class ESSRegularizationTypeOption(CamelSchema):
    """Allowed attendance regularization type."""

    code: str
    label: str
    description: str
