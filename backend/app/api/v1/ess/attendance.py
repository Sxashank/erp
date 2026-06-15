"""ESS attendance self-service endpoints."""

from __future__ import annotations

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.hris.employee import Employee
from app.schemas.ess.operations import (
    ESSAttendanceRecordRow,
    ESSAttendanceRecordsResponse,
    ESSAttendanceSummaryResponse,
    ESSRegularizationCreate,
    ESSRegularizationResponse,
    ESSRegularizationTypeOption,
)
from app.schemas.hris.attendance import (
    AttendanceRegularizationCreate,
    AttendanceRegularizationFilters,
)
from app.services.ess.profile_service import ESSProfileService
from app.services.hris.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["ESS Attendance"])

REGULARIZATION_TYPE_OPTIONS = [
    ESSRegularizationTypeOption(
        code="MISSED_PUNCH",
        label="Missed Punch",
        description="Check-in or check-out was missed and needs correction.",
    ),
    ESSRegularizationTypeOption(
        code="CORRECTION",
        label="Time Correction",
        description="Recorded attendance time is incorrect.",
    ),
    ESSRegularizationTypeOption(
        code="ON_DUTY",
        label="On Duty",
        description="Official work outside office or branch premises.",
    ),
    ESSRegularizationTypeOption(
        code="WFH",
        label="Work From Home",
        description="Approved work-from-home day to be regularized.",
    ),
]


async def _get_employee_user_id(session: AsyncSession, employee_id: UUID) -> UUID | None:
    result = await session.execute(select(Employee.user_id).where(Employee.id == employee_id))
    return result.scalar_one_or_none()


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        hour, minute = value.split(":", 1)
        return time(hour=int(hour), minute=int(minute[:2]))
    except (TypeError, ValueError) as exc:
        raise BadRequestException(
            detail="Time values must be in HH:MM format",
            error_code="INVALID_TIME_FORMAT",
        ) from exc


def _regularization_response(regularization) -> ESSRegularizationResponse:
    return ESSRegularizationResponse(
        id=regularization.id,
        attendance_date=regularization.attendance_date,
        request_type=regularization.request_type,
        reason=regularization.reason,
        status=regularization.status,
        approved_by=str(regularization.approved_by) if regularization.approved_by else None,
        approved_at=regularization.approved_at.isoformat() if regularization.approved_at else None,
        approver_remarks=regularization.approver_remarks,
        rejected_at=regularization.rejected_at.isoformat() if regularization.rejected_at else None,
        rejection_reason=regularization.rejection_reason,
        created_at=regularization.created_at,
    )


@router.get("/records", response_model=ESSAttendanceRecordsResponse, response_model_by_alias=True)
async def get_attendance_records(
    from_date: date = Query(..., alias="fromDate"),
    to_date: date = Query(..., alias="toDate"),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return attendance records for the authenticated employee."""
    service = ESSProfileService(session)
    records = await service.get_attendance(ess_context.employee_id, from_date, to_date)
    return ESSAttendanceRecordsResponse(
        items=[
            ESSAttendanceRecordRow(
                date=record.attendance_date,
                status=record.status,
                in_time=record.first_in.isoformat() if record.first_in else None,
                out_time=record.last_out.isoformat() if record.last_out else None,
                working_hours=(
                    round(record.effective_work_minutes / 60, 2)
                    if record.effective_work_minutes
                    else 0
                ),
                shift=None,
            )
            for record in records
        ]
    )


@router.get(
    "/summary",
    response_model=ESSAttendanceSummaryResponse,
    response_model_by_alias=True,
)
async def get_attendance_summary(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return attendance summary for the authenticated employee."""
    service = ESSProfileService(session)
    summary = await service.get_attendance_summary(ess_context.employee_id, month)
    return ESSAttendanceSummaryResponse(**summary)


@router.get(
    "/regularization-types",
    response_model=list[ESSRegularizationTypeOption],
    response_model_by_alias=True,
)
async def list_regularization_types(
    _session: AsyncSession = Depends(get_ess_db_with_tenant),
    _ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return supported HRMS attendance regularization request types."""
    return REGULARIZATION_TYPE_OPTIONS


@router.post(
    "/regularizations",
    response_model=ESSRegularizationResponse,
    response_model_by_alias=True,
)
async def create_regularization(
    request: ESSRegularizationCreate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Create an employee-owned attendance regularization request."""
    service = AttendanceService(session)
    if request.request_type not in {option.code for option in REGULARIZATION_TYPE_OPTIONS}:
        raise BadRequestException(
            detail="Unsupported attendance regularization type",
            error_code="INVALID_REGULARIZATION_TYPE",
        )
    created_by = await _get_employee_user_id(session, ess_context.employee_id)
    try:
        regularization = await service.create_regularization(
            AttendanceRegularizationCreate(
                employee_id=ess_context.employee_id,
                attendance_date=request.attendance_date,
                request_type=request.request_type,
                reason=request.reason,
                requested_first_in=_parse_time(request.requested_first_in),
                requested_last_out=_parse_time(request.requested_last_out),
                requested_status=request.requested_status,
                attachments=request.attachments,
            ),
            created_by or ess_context.employee_id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST")
    await session.commit()
    return _regularization_response(regularization)


@router.get(
    "/regularizations",
    response_model=list[ESSRegularizationResponse],
    response_model_by_alias=True,
)
async def list_regularizations(
    status_filter: str | None = Query(None, alias="status"),
    from_date: date | None = Query(None, alias="fromDate"),
    to_date: date | None = Query(None, alias="toDate"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """List employee-owned attendance regularization requests."""
    service = AttendanceService(session)
    regularizations, _ = await service.list_regularizations(
        AttendanceRegularizationFilters(
            organization_id=ess_context.organization_id,
            employee_id=ess_context.employee_id,
            status=status_filter,
            from_date=from_date,
            to_date=to_date,
        ),
        skip=offset,
        limit=limit,
    )
    return [_regularization_response(row) for row in regularizations]
