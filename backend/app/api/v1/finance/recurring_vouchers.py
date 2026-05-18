"""Recurring Voucher API endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.recurring_service import RecurringVoucherService
from app.core.constants import RecurrenceFrequency, RecurringVoucherStatus
from app.schemas.finance.recurring_voucher import (
    RecurringVoucherCreate,
    RecurringVoucherUpdate,
    RecurringVoucherResponse,
    RecurringVoucherListResponse,
    RecurringVoucherLogListResponse,
    GenerateVoucherRequest,
    GenerateVoucherResponse,
    PauseResumeRequest,
    UpcomingRecurringVoucher,
    RecurringVoucherStats,
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


@router.get(
    "",
    response_model=RecurringVoucherListResponse, response_model_by_alias=True,
)
async def list_recurring_vouchers(
    organization_id: UUID,
    status: Optional[RecurringVoucherStatus] = None,
    frequency: Optional[RecurrenceFrequency] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List recurring voucher templates."""
    service = RecurringVoucherService(db)
    return await service.list(
        organization_id=organization_id,
        status=status,
        frequency=frequency,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/upcoming",
    response_model=list[UpcomingRecurringVoucher], response_model_by_alias=True,
)
async def get_upcoming_vouchers(
    organization_id: UUID,
    days_ahead: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get upcoming recurring vouchers due in the next N days."""
    service = RecurringVoucherService(db)
    return await service.get_upcoming(organization_id, days_ahead)


@router.get(
    "/stats",
    response_model=RecurringVoucherStats, response_model_by_alias=True,
)
async def get_recurring_stats(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get statistics for recurring vouchers."""
    service = RecurringVoucherService(db)
    return await service.get_stats(organization_id)


@router.get(
    "/{recurring_id}",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
)
async def get_recurring_voucher(
    recurring_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get a recurring voucher template by ID."""
    service = RecurringVoucherService(db)
    result = await service.get_with_lines(recurring_id)
    if not result:
        raise NotFoundException(
            detail=f"Recurring voucher {recurring_id} not found",
            error_code="RECURRING_VOUCHER_NOT_FOUND",
        )
    return result


@router.post(
    "",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_voucher(
    data: RecurringVoucherCreate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new recurring voucher template."""
    service = RecurringVoucherService(db)
    try:
        recurring = await service.create(data, current_user.id)
        await db.commit()
        return await service.get_with_lines(recurring.id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put(
    "/{recurring_id}",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
)
async def update_recurring_voucher(
    recurring_id: UUID,
    data: RecurringVoucherUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a recurring voucher template."""
    service = RecurringVoucherService(db)
    try:
        recurring = await service.update(recurring_id, data, current_user.id)
        await db.commit()
        return await service.get_with_lines(recurring.id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.delete(
    "/{recurring_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recurring_voucher(
    recurring_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete (soft) a recurring voucher template."""
    service = RecurringVoucherService(db)
    success = await service.delete(recurring_id, current_user.id)
    if not success:
        raise NotFoundException(
            detail=f"Recurring voucher {recurring_id} not found",
            error_code="RECURRING_VOUCHER_NOT_FOUND",
        )
    await db.commit()


@router.post(
    "/{recurring_id}/pause",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
)
async def pause_recurring_voucher(
    recurring_id: UUID,
    request: PauseResumeRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Pause a recurring voucher."""
    service = RecurringVoucherService(db)
    try:
        await service.pause(recurring_id, current_user.id, request.reason)
        await db.commit()
        return await service.get_with_lines(recurring_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{recurring_id}/resume",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
)
async def resume_recurring_voucher(
    recurring_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Resume a paused recurring voucher."""
    service = RecurringVoucherService(db)
    try:
        await service.resume(recurring_id, current_user.id)
        await db.commit()
        return await service.get_with_lines(recurring_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{recurring_id}/cancel",
    response_model=RecurringVoucherResponse, response_model_by_alias=True,
)
async def cancel_recurring_voucher(
    recurring_id: UUID,
    request: PauseResumeRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Cancel a recurring voucher (cannot be undone)."""
    service = RecurringVoucherService(db)
    try:
        await service.cancel(recurring_id, current_user.id, request.reason)
        await db.commit()
        return await service.get_with_lines(recurring_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{recurring_id}/generate",
    response_model=GenerateVoucherResponse, response_model_by_alias=True,
)
async def generate_voucher_from_template(
    recurring_id: UUID,
    request: GenerateVoucherRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Manually generate a voucher from a recurring template."""
    service = RecurringVoucherService(db)
    result = await service.generate_voucher(
        recurring_id,
        current_user.id,
        request.voucher_date,
        request.narration_override,
    )
    if result.success:
        await db.commit()
    return result


@router.post(
    "/process-due",
    response_model=list[GenerateVoucherResponse], response_model_by_alias=True,
)
async def process_due_vouchers(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Process all due recurring vouchers and generate vouchers."""
    service = RecurringVoucherService(db)
    results = await service.process_due_vouchers(organization_id, current_user.id)
    await db.commit()
    return results


@router.get(
    "/{recurring_id}/logs",
    response_model=RecurringVoucherLogListResponse, response_model_by_alias=True,
)
async def get_recurring_voucher_logs(
    recurring_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get generation logs for a recurring voucher."""
    service = RecurringVoucherService(db)
    return await service.get_logs(recurring_id, page, page_size)
