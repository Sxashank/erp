"""API endpoints for Attendance management."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.constants import Permissions, AttendanceStatus, RegularizationStatus
from app.core.permissions import RequirePermissions
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

router = APIRouter()


# ============================================
# Punches
# ============================================
@router.post("/punch", response_model=AttendancePunchResponse, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_MARK])
async def record_punch(
    data: AttendancePunchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record an attendance punch (IN/OUT)."""
    service = AttendanceService(db)
    punch = await service.record_punch(data, current_user.id)
    return punch


@router.get("/punches/{employee_id}", response_model=List[AttendancePunchResponse])
@RequirePermissions([Permissions.HRIS_ATTENDANCE_VIEW])
async def get_punches(
    employee_id: UUID,
    punch_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get punches for an employee on a date."""
    service = AttendanceService(db)
    punches = await service.get_punches(employee_id, punch_date)
    return punches


# ============================================
# Attendance Records
# ============================================
@router.get("", response_model=PaginatedResponse[AttendanceResponse])
@RequirePermissions([Permissions.HRIS_ATTENDANCE_VIEW])
async def list_attendance(
    organization_id: Optional[UUID] = None,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List attendance records."""
    service = AttendanceService(db)
    filters = AttendanceFilters(
        organization_id=organization_id,
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


@router.get("/{attendance_id}", response_model=AttendanceResponse)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_VIEW])
async def get_attendance(
    attendance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attendance record by ID."""
    service = AttendanceService(db)
    attendance = await service.get_by_id(attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return _build_attendance_response(attendance)


@router.put("/{attendance_id}", response_model=AttendanceResponse)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_MARK])
async def update_attendance(
    attendance_id: UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update attendance record."""
    service = AttendanceService(db)
    try:
        attendance = await service.update(attendance_id, data, current_user.id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return _build_attendance_response(attendance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Regularization
# ============================================
@router.get("/regularizations", response_model=PaginatedResponse[AttendanceRegularizationResponse])
@RequirePermissions([Permissions.HRIS_ATTENDANCE_VIEW])
async def list_regularizations(
    organization_id: Optional[UUID] = None,
    employee_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    status: Optional[RegularizationStatus] = None,
    request_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List regularization requests."""
    service = AttendanceService(db)
    filters = AttendanceRegularizationFilters(
        organization_id=organization_id,
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


@router.post("/regularizations", response_model=AttendanceRegularizationResponse, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_REGULARIZE])
async def create_regularization(
    data: AttendanceRegularizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create regularization request."""
    service = AttendanceService(db)
    regularization = await service.create_regularization(data, current_user.id)
    return _build_regularization_response(regularization)


@router.get("/regularizations/{regularization_id}", response_model=AttendanceRegularizationResponse)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_VIEW])
async def get_regularization(
    regularization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get regularization by ID."""
    service = AttendanceService(db)
    regularization = await service.get_regularization(regularization_id)
    if not regularization:
        raise HTTPException(status_code=404, detail="Regularization not found")
    return _build_regularization_response(regularization)


@router.post("/regularizations/{regularization_id}/approve", response_model=AttendanceRegularizationResponse)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_APPROVE])
async def approve_regularization(
    regularization_id: UUID,
    data: AttendanceRegularizationApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve regularization request."""
    service = AttendanceService(db)
    try:
        regularization = await service.approve_regularization(
            regularization_id, data.remarks, current_user.id
        )
        if not regularization:
            raise HTTPException(status_code=404, detail="Regularization not found")
        return _build_regularization_response(regularization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/regularizations/{regularization_id}/reject", response_model=AttendanceRegularizationResponse)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_APPROVE])
async def reject_regularization(
    regularization_id: UUID,
    data: AttendanceRegularizationReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject regularization request."""
    service = AttendanceService(db)
    try:
        regularization = await service.reject_regularization(
            regularization_id, data.reason, current_user.id
        )
        if not regularization:
            raise HTTPException(status_code=404, detail="Regularization not found")
        return _build_regularization_response(regularization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Processing
# ============================================
@router.post("/process/daily", response_model=AttendanceProcessingResult)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_MARK])
async def process_daily_attendance(
    data: ProcessDailyAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process daily attendance from punches."""
    service = AttendanceService(db)
    result = await service.process_daily_attendance(data, current_user.id)
    return result


@router.post("/process/monthly", response_model=AttendanceProcessingResult)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_MARK])
async def process_monthly_summary(
    data: ProcessMonthlyAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process monthly attendance summary."""
    service = AttendanceService(db)
    result = await service.process_monthly_summary(data, current_user.id)
    return result


@router.post("/lock", response_model=dict)
@RequirePermissions([Permissions.HRIS_ATTENDANCE_APPROVE])
async def lock_attendance(
    data: LockAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lock monthly attendance for payroll."""
    service = AttendanceService(db)
    count = await service.lock_monthly_attendance(
        data.organization_id, data.year, data.month, current_user.id
    )
    return {"locked_count": count, "message": f"Locked {count} attendance records for payroll"}


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
