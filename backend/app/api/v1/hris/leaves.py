"""API endpoints for Leave management."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.constants import Permissions, LeaveApplicationStatus
from app.models.auth.user import User
from app.schemas.hris.leave import (
    LeaveTypeCreate,
    LeaveTypeUpdate,
    LeaveTypeResponse,
    LeaveBalanceCreate,
    LeaveBalanceResponse,
    LeaveBalanceSummary,
    LeaveApplicationCreate,
    LeaveApplicationUpdate,
    LeaveApplicationApprove,
    LeaveApplicationReject,
    LeaveApplicationCancel,
    LeaveApplicationResponse,
    LeaveApplicationFilters,
)
from app.schemas.common import PaginatedResponse
from app.services.hris.leave_service import (
    LeaveTypeService,
    LeaveBalanceService,
    LeaveApplicationService,
)
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
# Leave Types
# ============================================
@router.get("/types", response_model=List[LeaveTypeResponse], response_model_by_alias=True)
async def list_leave_types(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_VIEW)),
):
    """List leave types for organization."""
    service = LeaveTypeService(db)
    leave_types = await service.list(
        _require_organization_id(current_user),
        active_only,
    )
    return leave_types


@router.post(
    "/types",
    response_model=LeaveTypeResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_type(
    data: LeaveTypeCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_CREATE)),
):
    """Create a new leave type."""
    service = LeaveTypeService(db)
    organization_id = _require_organization_id(current_user)
    payload = data.model_copy(update={"organization_id": organization_id})

    # Check if leave code already exists
    existing = await service.get_by_code(organization_id, payload.leave_code)
    if existing:
        raise BadRequestException(
            detail="Leave code already exists",
            error_code="LEAVE_CODE_ALREADY_EXISTS",
        )

    leave_type = await service.create(payload, current_user.id)
    return leave_type


@router.get(
    "/types/{leave_type_id}", response_model=LeaveTypeResponse, response_model_by_alias=True
)
async def get_leave_type(
    leave_type_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_VIEW)),
):
    """Get leave type by ID."""
    service = LeaveTypeService(db)
    leave_type = await service.get(leave_type_id)
    if not leave_type:
        raise NotFoundException(detail="Leave type not found", error_code="LEAVE_TYPE_NOT_FOUND")
    return leave_type


@router.put(
    "/types/{leave_type_id}", response_model=LeaveTypeResponse, response_model_by_alias=True
)
async def update_leave_type(
    leave_type_id: UUID,
    data: LeaveTypeUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_UPDATE)),
):
    """Update leave type."""
    service = LeaveTypeService(db)
    leave_type = await service.update(leave_type_id, data, current_user.id)
    if not leave_type:
        raise NotFoundException(detail="Leave type not found", error_code="LEAVE_TYPE_NOT_FOUND")
    return leave_type


@router.delete("/types/{leave_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave_type(
    leave_type_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_DELETE)),
):
    """Delete (deactivate) leave type."""
    service = LeaveTypeService(db)
    success = await service.delete(leave_type_id)
    if not success:
        raise NotFoundException(detail="Leave type not found", error_code="LEAVE_TYPE_NOT_FOUND")


# ============================================
# Leave Balances
# ============================================
@router.get(
    "/balances/{employee_id}", response_model=LeaveBalanceSummary, response_model_by_alias=True
)
async def get_leave_balances(
    employee_id: UUID,
    year: int,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_VIEW)),
):
    """Get leave balances for an employee."""
    service = LeaveBalanceService(db)
    balances = await service.get_all_balances(employee_id, year)

    items = []
    for bal in balances:
        items.append(
            LeaveBalanceResponse(
                id=bal.id,
                employee_id=bal.employee_id,
                leave_type_id=bal.leave_type_id,
                year=bal.year,
                opening_balance=bal.opening_balance,
                accrued=bal.accrued,
                carry_forward=bal.carry_forward,
                adjustment=bal.adjustment,
                used=bal.used,
                encashed=bal.encashed,
                lapsed=bal.lapsed,
                available_balance=bal.available_balance,
                leave_type_name=bal.leave_type.leave_name if bal.leave_type else None,
                leave_type_code=bal.leave_type.leave_code if bal.leave_type else None,
            )
        )

    return LeaveBalanceSummary(
        employee_id=employee_id,
        year=year,
        balances=items,
    )


@router.post("/balances", response_model=LeaveBalanceResponse, response_model_by_alias=True)
async def create_or_update_balance(
    data: LeaveBalanceCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_UPDATE)),
):
    """Create or update leave balance (for admin adjustments)."""
    service = LeaveBalanceService(db)
    balance = await service.create_or_update(data, current_user.id)
    return LeaveBalanceResponse(
        id=balance.id,
        employee_id=balance.employee_id,
        leave_type_id=balance.leave_type_id,
        year=balance.year,
        opening_balance=balance.opening_balance,
        accrued=balance.accrued,
        carry_forward=balance.carry_forward,
        adjustment=balance.adjustment,
        used=balance.used,
        encashed=balance.encashed,
        lapsed=balance.lapsed,
        available_balance=balance.available_balance,
    )


@router.post(
    "/balances/initialize/{employee_id}",
    response_model=List[LeaveBalanceResponse],
    response_model_by_alias=True,
)
async def initialize_balances(
    employee_id: UUID,
    year: int,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_TYPE_UPDATE)),
):
    """Initialize leave balances for a new year."""
    service = LeaveBalanceService(db)
    balances = await service.initialize_balances(
        employee_id,
        _require_organization_id(current_user),
        year,
        current_user.id,
    )
    return balances


# ============================================
# Leave Applications
# ============================================
@router.get(
    "/applications",
    response_model=PaginatedResponse[LeaveApplicationResponse],
    response_model_by_alias=True,
)
async def list_leave_applications(
    employee_id: Optional[UUID] = None,
    leave_type_id: Optional[UUID] = None,
    status: Optional[LeaveApplicationStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    department_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_VIEW)),
):
    """List leave applications."""
    service = LeaveApplicationService(db)
    filters = LeaveApplicationFilters(
        organization_id=_require_organization_id(current_user),
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        department_id=department_id,
    )
    applications, total = await service.list(filters, skip, limit)

    items = []
    for app in applications:
        items.append(_build_application_response(app))

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/applications/pending-approval",
    response_model=PaginatedResponse[LeaveApplicationResponse],
    response_model_by_alias=True,
)
async def get_pending_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_APPROVE)),
):
    """Get leave applications pending for current user's approval."""
    service = LeaveApplicationService(db)
    applications, total = await service.get_pending_for_approval(current_user.id, skip, limit)

    items = []
    for app in applications:
        items.append(_build_application_response(app))

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post(
    "/applications",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_application(
    data: LeaveApplicationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_APPLY)),
):
    """Create a new leave application."""
    service = LeaveApplicationService(db)
    try:
        application = await service.create(data, current_user.id)
        return _build_application_response(application)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/applications/{application_id}",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
)
async def get_leave_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_VIEW)),
):
    """Get leave application by ID."""
    service = LeaveApplicationService(db)
    application = await service.get(application_id)
    if not application:
        raise NotFoundException(
            detail="Leave application not found",
            error_code="LEAVE_APPLICATION_NOT_FOUND",
        )
    return _build_application_response(application)


@router.put(
    "/applications/{application_id}",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
)
async def update_leave_application(
    application_id: UUID,
    data: LeaveApplicationUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_APPLY)),
):
    """Update leave application (only if pending)."""
    service = LeaveApplicationService(db)
    try:
        application = await service.update(application_id, data, current_user.id)
        if not application:
            raise NotFoundException(
                detail="Leave application not found",
                error_code="LEAVE_APPLICATION_NOT_FOUND",
            )
        return _build_application_response(application)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/applications/{application_id}/approve",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
)
async def approve_leave_application(
    application_id: UUID,
    data: LeaveApplicationApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_APPROVE)),
):
    """Approve leave application."""
    service = LeaveApplicationService(db)
    try:
        application = await service.approve(application_id, data.remarks, current_user.id)
        if not application:
            raise NotFoundException(
                detail="Leave application not found",
                error_code="LEAVE_APPLICATION_NOT_FOUND",
            )
        return _build_application_response(application)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/applications/{application_id}/reject",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
)
async def reject_leave_application(
    application_id: UUID,
    data: LeaveApplicationReject,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_APPROVE)),
):
    """Reject leave application."""
    service = LeaveApplicationService(db)
    try:
        application = await service.reject(application_id, data.reason, current_user.id)
        if not application:
            raise NotFoundException(
                detail="Leave application not found",
                error_code="LEAVE_APPLICATION_NOT_FOUND",
            )
        return _build_application_response(application)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/applications/{application_id}/cancel",
    response_model=LeaveApplicationResponse,
    response_model_by_alias=True,
)
async def cancel_leave_application(
    application_id: UUID,
    data: LeaveApplicationCancel,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_LEAVE_CANCEL)),
):
    """Cancel leave application."""
    service = LeaveApplicationService(db)
    try:
        application = await service.cancel(application_id, data.reason, current_user.id)
        if not application:
            raise NotFoundException(
                detail="Leave application not found",
                error_code="LEAVE_APPLICATION_NOT_FOUND",
            )
        return _build_application_response(application)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Helper Functions
# ============================================
def _build_application_response(app) -> LeaveApplicationResponse:
    """Build leave application response."""
    return LeaveApplicationResponse(
        id=app.id,
        employee_id=app.employee_id,
        leave_type_id=app.leave_type_id,
        application_number=app.application_number,
        from_date=app.from_date,
        to_date=app.to_date,
        is_half_day=app.is_half_day,
        half_day_type=app.half_day_type,
        total_days=app.total_days,
        working_days=app.working_days,
        reason=app.reason,
        contact_number=app.contact_number,
        contact_address=app.contact_address,
        attachments=app.attachments,
        comp_off_date=app.comp_off_date,
        status=app.status,
        approved_by=app.approved_by,
        approved_at=app.approved_at,
        approver_remarks=app.approver_remarks,
        rejected_by=app.rejected_by,
        rejected_at=app.rejected_at,
        rejection_reason=app.rejection_reason,
        cancelled_at=app.cancelled_at,
        cancellation_reason=app.cancellation_reason,
        employee_name=app.employee.full_name if app.employee else None,
        employee_code=app.employee.employee_code if app.employee else None,
        leave_type_name=app.leave_type.leave_name if app.leave_type else None,
        leave_type_code=app.leave_type.leave_code if app.leave_type else None,
    )
