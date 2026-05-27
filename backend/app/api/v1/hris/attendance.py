"""API endpoints for Attendance management."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.constants import Permissions, AttendanceStatus, RegularizationStatus
from app.models.auth.user import User
from app.schemas.hris.attendance import (
    AttendancePunchCreate,
    AttendancePunchResponse,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceFilters,
    AttendanceRegularizationCreate,
    AttendanceRegularizationApprove,
    AttendanceRegularizationReject,
    AttendanceRegularizationResponse,
    AttendanceRegularizationFilters,
    MonthlyAttendanceSummaryResponse,
    ProcessDailyAttendanceRequest,
    ProcessMonthlyAttendanceRequest,
    LockAttendanceRequest,
    AttendanceProcessingResult,
)
from app.schemas.common import PaginatedResponse
from app.services.hris.attendance_service import AttendanceService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


# ============================================
# Punches
# ============================================
@router.post(
    "/punch",
    response_model=AttendancePunchResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def record_punch(
    data: AttendancePunchCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_MARK)),
):
    """Record an attendance punch (IN/OUT)."""
    service = AttendanceService(db)
    punch = await service.record_punch(data, current_user.id)
    return punch


@router.get(
    "/punches/{employee_id}",
    response_model=List[AttendancePunchResponse],
    response_model_by_alias=True,
)
async def get_punches(
    employee_id: UUID,
    punch_date: date,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_VIEW)),
):
    """Get punches for an employee on a date."""
    service = AttendanceService(db)
    punches = await service.get_punches(employee_id, punch_date)
    return punches


# ============================================
# Attendance Records
# ============================================
@router.get("", response_model=PaginatedResponse[AttendanceResponse], response_model_by_alias=True)
async def list_attendance(
    employee_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    shift_id: Optional[UUID] = None,
    status: Optional[AttendanceStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    is_processed: Optional[bool] = None,
    is_locked: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_VIEW)),
):
    """List attendance records."""
    service = AttendanceService(db)
    filters = AttendanceFilters(
        organization_id=_require_organization_id(current_user),
        employee_id=employee_id,
        department_id=department_id,
        shift_id=shift_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        is_processed=is_processed,
        is_locked=is_locked,
    )
    records, total = await service.list(filters, skip, limit)

    items = []
    for rec in records:
        items.append(_build_attendance_response(rec))

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


# ============================================
# Regularization
# ============================================
@router.get(
    "/regularizations",
    response_model=PaginatedResponse[AttendanceRegularizationResponse],
    response_model_by_alias=True,
)
async def list_regularizations(
    employee_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    status: Optional[RegularizationStatus] = None,
    request_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_VIEW)),
):
    """List regularization requests."""
    service = AttendanceService(db)
    filters = AttendanceRegularizationFilters(
        organization_id=_require_organization_id(current_user),
        employee_id=employee_id,
        department_id=department_id,
        status=status,
        request_type=request_type,
        from_date=from_date,
        to_date=to_date,
    )
    records, total = await service.list_regularizations(filters, skip, limit)

    items = []
    for rec in records:
        items.append(_build_regularization_response(rec))

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post(
    "/regularizations",
    response_model=AttendanceRegularizationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_regularization(
    data: AttendanceRegularizationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_REGULARIZE)),
):
    """Create regularization request."""
    service = AttendanceService(db)
    regularization = await service.create_regularization(data, current_user.id)
    return _build_regularization_response(regularization)


@router.get(
    "/regularizations/{regularization_id}",
    response_model=AttendanceRegularizationResponse,
    response_model_by_alias=True,
)
async def get_regularization(
    regularization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_VIEW)),
):
    """Get regularization by ID."""
    service = AttendanceService(db)
    regularization = await service.get_regularization(regularization_id)
    if not regularization:
        raise NotFoundException(
            detail="Regularization not found", error_code="REGULARIZATION_NOT_FOUND"
        )
    return _build_regularization_response(regularization)


@router.post(
    "/regularizations/{regularization_id}/approve",
    response_model=AttendanceRegularizationResponse,
    response_model_by_alias=True,
)
async def approve_regularization(
    regularization_id: UUID,
    data: AttendanceRegularizationApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_APPROVE)),
):
    """Approve regularization request."""
    service = AttendanceService(db)
    try:
        regularization = await service.approve_regularization(
            regularization_id, data.remarks, current_user.id
        )
        if not regularization:
            raise NotFoundException(
                detail="Regularization not found",
                error_code="REGULARIZATION_NOT_FOUND",
            )
        return _build_regularization_response(regularization)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/regularizations/{regularization_id}/reject",
    response_model=AttendanceRegularizationResponse,
    response_model_by_alias=True,
)
async def reject_regularization(
    regularization_id: UUID,
    data: AttendanceRegularizationReject,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_APPROVE)),
):
    """Reject regularization request."""
    service = AttendanceService(db)
    try:
        regularization = await service.reject_regularization(
            regularization_id, data.reason, current_user.id
        )
        if not regularization:
            raise NotFoundException(
                detail="Regularization not found",
                error_code="REGULARIZATION_NOT_FOUND",
            )
        return _build_regularization_response(regularization)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Processing
# ============================================
@router.post(
    "/process/daily", response_model=AttendanceProcessingResult, response_model_by_alias=True
)
async def process_daily_attendance(
    data: ProcessDailyAttendanceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_MARK)),
):
    """Process daily attendance from punches."""
    service = AttendanceService(db)
    result = await service.process_daily_attendance(data, current_user.id)
    return result


@router.post(
    "/process/monthly", response_model=AttendanceProcessingResult, response_model_by_alias=True
)
async def process_monthly_summary(
    data: ProcessMonthlyAttendanceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_MARK)),
):
    """Process monthly attendance summary."""
    service = AttendanceService(db)
    result = await service.process_monthly_summary(data, current_user.id)
    return result


@router.post("/lock", response_model=dict, response_model_by_alias=True)
async def lock_attendance(
    data: LockAttendanceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_APPROVE)),
):
    """Lock monthly attendance for payroll."""
    service = AttendanceService(db)
    count = await service.lock_monthly_attendance(
        data.organization_id, data.year, data.month, current_user.id
    )
    return {"locked_count": count, "message": f"Locked {count} attendance records for payroll"}


@router.get("/{attendance_id}", response_model=AttendanceResponse, response_model_by_alias=True)
async def get_attendance(
    attendance_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_VIEW)),
):
    """Get attendance record by ID."""
    service = AttendanceService(db)
    attendance = await service.get_by_id(attendance_id)
    if not attendance:
        raise NotFoundException(
            detail="Attendance record not found",
            error_code="ATTENDANCE_RECORD_NOT_FOUND",
        )
    return _build_attendance_response(attendance)


@router.put("/{attendance_id}", response_model=AttendanceResponse, response_model_by_alias=True)
async def update_attendance(
    attendance_id: UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_ATTENDANCE_MARK)),
):
    """Update attendance record."""
    service = AttendanceService(db)
    try:
        attendance = await service.update(attendance_id, data, current_user.id)
        if not attendance:
            raise NotFoundException(
                detail="Attendance record not found",
                error_code="ATTENDANCE_RECORD_NOT_FOUND",
            )
        return _build_attendance_response(attendance)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Helper Functions
# ============================================
def _build_attendance_response(rec) -> AttendanceResponse:
    """Build attendance response."""
    return AttendanceResponse(
        id=rec.id,
        employee_id=rec.employee_id,
        attendance_date=rec.attendance_date,
        shift_id=rec.shift_id,
        scheduled_in=rec.scheduled_in,
        scheduled_out=rec.scheduled_out,
        first_in=rec.first_in,
        last_out=rec.last_out,
        all_punches=rec.all_punches,
        status=rec.status,
        total_work_minutes=rec.total_work_minutes,
        break_minutes=rec.break_minutes,
        effective_work_minutes=rec.effective_work_minutes,
        late_minutes=rec.late_minutes,
        early_leave_minutes=rec.early_leave_minutes,
        overtime_minutes=rec.overtime_minutes,
        overtime_approved=rec.overtime_approved,
        leave_application_id=rec.leave_application_id,
        leave_type_id=rec.leave_type_id,
        is_holiday=rec.is_holiday,
        holiday_name=rec.holiday_name,
        is_week_off=rec.is_week_off,
        is_regularized=rec.is_regularized,
        regularization_id=rec.regularization_id,
        is_on_duty=rec.is_on_duty,
        on_duty_reference=rec.on_duty_reference,
        is_work_from_home=rec.is_work_from_home,
        is_processed=rec.is_processed,
        is_locked=rec.is_locked,
        remarks=rec.remarks,
        employee_name=rec.employee.full_name if rec.employee else None,
        employee_code=rec.employee.employee_code if rec.employee else None,
        shift_name=rec.shift.shift_name if rec.shift else None,
    )


def _build_regularization_response(rec) -> AttendanceRegularizationResponse:
    """Build regularization response."""
    return AttendanceRegularizationResponse(
        id=rec.id,
        employee_id=rec.employee_id,
        attendance_date=rec.attendance_date,
        request_type=rec.request_type,
        reason=rec.reason,
        original_first_in=rec.original_first_in,
        original_last_out=rec.original_last_out,
        original_status=rec.original_status,
        requested_first_in=rec.requested_first_in,
        requested_last_out=rec.requested_last_out,
        requested_status=rec.requested_status,
        attachments=rec.attachments,
        status=rec.status,
        approved_by=rec.approved_by,
        approved_at=rec.approved_at,
        approver_remarks=rec.approver_remarks,
        rejected_by=rec.rejected_by,
        rejected_at=rec.rejected_at,
        rejection_reason=rec.rejection_reason,
        employee_name=rec.employee.full_name if rec.employee else None,
        employee_code=rec.employee.employee_code if rec.employee else None,
    )
