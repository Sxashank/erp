"""ESS leave self-service endpoints."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.core.constants import LeaveApplicationStatus
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveApplication, LeaveBalance, LeaveType
from app.schemas.ess.operations import (
    ESSLeaveApplicationCreate,
    ESSLeaveApplicationResponse,
    ESSLeaveApplicationUpdate,
    ESSLeaveBalanceRow,
    ESSLeaveCancelRequest,
    ESSLeaveSummaryResponse,
    ESSLeaveTypeOption,
)
from app.schemas.hris.leave import (
    LeaveApplicationCancel,
    LeaveApplicationCreate,
    LeaveApplicationFilters,
    LeaveApplicationUpdate,
)
from app.services.hris.leave_service import LeaveApplicationService

router = APIRouter(prefix="/leave", tags=["ESS Leave"])


async def _get_employee(session: AsyncSession, employee_id: UUID) -> Employee:
    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundException(
            detail="Employee profile not found",
            error_code="EMPLOYEE_NOT_FOUND",
        )
    return employee


async def _get_audit_user_id(session: AsyncSession, employee_id: UUID) -> UUID:
    employee = await _get_employee(session, employee_id)
    if not employee.user_id:
        raise BadRequestException(
            detail="Employee is not linked to an HRMS user account for auditable ESS leave actions",
            error_code="EMPLOYEE_USER_LINK_REQUIRED",
        )
    return employee.user_id


def _leave_application_response(application: LeaveApplication) -> ESSLeaveApplicationResponse:
    return ESSLeaveApplicationResponse(
        id=application.id,
        application_number=application.application_number,
        leave_type_id=application.leave_type_id,
        leave_type_code=application.leave_type.leave_code if application.leave_type else None,
        leave_type_name=application.leave_type.leave_name if application.leave_type else None,
        from_date=application.from_date,
        to_date=application.to_date,
        is_half_day=application.is_half_day,
        half_day_type=application.half_day_type,
        total_days=application.total_days,
        working_days=application.working_days,
        reason=application.reason,
        contact_number=application.contact_number,
        contact_address=application.contact_address,
        attachments=application.attachments,
        status=application.status,
        approver_remarks=application.approver_remarks,
        rejection_reason=application.rejection_reason,
        cancellation_reason=application.cancellation_reason,
        approved_at=application.approved_at,
        rejected_at=application.rejected_at,
        cancelled_at=application.cancelled_at,
        created_at=application.created_at,
    )


async def _get_owned_application(
    service: LeaveApplicationService,
    application_id: UUID,
    employee_id: UUID,
) -> LeaveApplication:
    application = await service.get(application_id)
    if not application or application.employee_id != employee_id:
        raise NotFoundException(
            detail="Leave application not found",
            error_code="LEAVE_APPLICATION_NOT_FOUND",
        )
    return application


async def _leave_balances(
    session: AsyncSession,
    organization_id: UUID,
    employee_id: UUID,
    year: int,
) -> tuple[list[ESSLeaveBalanceRow], list[ESSLeaveTypeOption]]:
    result = await session.execute(
        select(LeaveType, LeaveBalance)
        .outerjoin(
            LeaveBalance,
            (LeaveBalance.leave_type_id == LeaveType.id)
            & (LeaveBalance.employee_id == employee_id)
            & (LeaveBalance.year == year),
        )
        .where(LeaveType.organization_id == organization_id, LeaveType.is_active.is_(True))
        .order_by(LeaveType.display_order, LeaveType.leave_code)
    )

    balances: list[ESSLeaveBalanceRow] = []
    options: list[ESSLeaveTypeOption] = []
    for leave_type, balance in result.all():
        available = balance.available_balance if balance else Decimal("0")
        used = balance.used if balance else Decimal("0")
        balances.append(
            ESSLeaveBalanceRow(
                leave_type_id=leave_type.id,
                code=leave_type.leave_code,
                name=leave_type.leave_name,
                opening_balance=balance.opening_balance if balance else Decimal("0"),
                accrued=balance.accrued if balance else Decimal("0"),
                carry_forward=balance.carry_forward if balance else Decimal("0"),
                used=used,
                lapsed=balance.lapsed if balance else Decimal("0"),
                available_balance=available,
            )
        )
        options.append(
            ESSLeaveTypeOption(
                id=leave_type.id,
                code=leave_type.leave_code,
                name=leave_type.leave_name,
                description=leave_type.description,
                annual_quota=leave_type.annual_quota,
                available_balance=available,
                used=used,
                document_required=leave_type.document_required,
                document_required_after_days=leave_type.document_required_after_days,
                half_day_allowed=leave_type.half_day_allowed,
            )
        )
    return balances, options


@router.get("/summary", response_model=ESSLeaveSummaryResponse, response_model_by_alias=True)
async def get_leave_summary(
    year: int | None = Query(None),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return leave balances, leave types and recent applications for the employee."""
    service = LeaveApplicationService(session)
    selected_year = year or date.today().year
    applications, _ = await service.list(
        LeaveApplicationFilters(employee_id=ess_context.employee_id),
        skip=0,
        limit=50,
    )
    balances, leave_types = await _leave_balances(
        session,
        ess_context.organization_id,
        ess_context.employee_id,
        selected_year,
    )
    approved_this_year = sum(
        (
            application.working_days
            for application in applications
            if application.status == LeaveApplicationStatus.APPROVED
            and application.from_date.year == selected_year
        ),
        Decimal("0"),
    )
    return ESSLeaveSummaryResponse(
        balances=balances,
        applications=[_leave_application_response(application) for application in applications],
        leave_types=leave_types,
        pending_count=sum(
            1 for app in applications if app.status == LeaveApplicationStatus.PENDING
        ),
        approved_this_year=approved_this_year,
    )


@router.get(
    "/applications",
    response_model=list[ESSLeaveApplicationResponse],
    response_model_by_alias=True,
)
async def list_leave_applications(
    status_filter: LeaveApplicationStatus | None = Query(None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """List employee-owned leave applications."""
    service = LeaveApplicationService(session)
    applications, _ = await service.list(
        LeaveApplicationFilters(
            employee_id=ess_context.employee_id,
            status=status_filter,
            from_date=from_date,
            to_date=to_date,
        ),
        skip=offset,
        limit=limit,
    )
    return [_leave_application_response(application) for application in applications]


@router.post(
    "/applications",
    response_model=ESSLeaveApplicationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_application(
    request: ESSLeaveApplicationCreate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Create a leave application for the authenticated employee."""
    audit_user_id = await _get_audit_user_id(session, ess_context.employee_id)
    service = LeaveApplicationService(session)
    try:
        application = await service.create(
            LeaveApplicationCreate(
                employee_id=ess_context.employee_id,
                leave_type_id=request.leave_type_id,
                from_date=request.from_date,
                to_date=request.to_date,
                is_half_day=request.is_half_day,
                half_day_type=request.half_day_type,
                reason=request.reason,
                contact_number=request.contact_number,
                contact_address=request.contact_address,
                attachments=request.attachments,
                comp_off_date=request.comp_off_date,
            ),
            audit_user_id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST")
    application = await service.get(application.id)
    await session.commit()
    return _leave_application_response(application)


@router.get(
    "/applications/{application_id}",
    response_model=ESSLeaveApplicationResponse,
    response_model_by_alias=True,
)
async def get_leave_application(
    application_id: UUID,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get an employee-owned leave application."""
    service = LeaveApplicationService(session)
    application = await _get_owned_application(service, application_id, ess_context.employee_id)
    return _leave_application_response(application)


@router.put(
    "/applications/{application_id}",
    response_model=ESSLeaveApplicationResponse,
    response_model_by_alias=True,
)
async def update_leave_application(
    application_id: UUID,
    request: ESSLeaveApplicationUpdate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Update an employee-owned pending leave application."""
    audit_user_id = await _get_audit_user_id(session, ess_context.employee_id)
    service = LeaveApplicationService(session)
    await _get_owned_application(service, application_id, ess_context.employee_id)
    try:
        application = await service.update(
            application_id,
            LeaveApplicationUpdate(**request.model_dump(exclude_unset=True)),
            audit_user_id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST")
    if not application:
        raise NotFoundException(
            detail="Leave application not found",
            error_code="LEAVE_APPLICATION_NOT_FOUND",
        )
    application = await service.get(application.id)
    await session.commit()
    return _leave_application_response(application)


@router.post(
    "/applications/{application_id}/cancel",
    response_model=ESSLeaveApplicationResponse,
    response_model_by_alias=True,
)
async def cancel_leave_application(
    application_id: UUID,
    request: ESSLeaveCancelRequest,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Cancel an employee-owned pending or approved leave application."""
    audit_user_id = await _get_audit_user_id(session, ess_context.employee_id)
    service = LeaveApplicationService(session)
    await _get_owned_application(service, application_id, ess_context.employee_id)
    try:
        application = await service.cancel(
            application_id,
            LeaveApplicationCancel(reason=request.reason).reason,
            audit_user_id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST")
    if not application:
        raise NotFoundException(
            detail="Leave application not found",
            error_code="LEAVE_APPLICATION_NOT_FOUND",
        )
    application = await service.get(application.id)
    await session.commit()
    return _leave_application_response(application)
