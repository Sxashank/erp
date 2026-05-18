"""Financial Year API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.financial_year_service import FinancialYearService
from app.services.finance.period_service import PeriodService
from app.schemas.finance.financial_year import (
    FinancialYearCreate,
    FinancialYearUpdate,
    FinancialYearResponse,
    FinancialYearWithPeriodsResponse,
    FinancialPeriodResponse,
    ClosePeriodRequest,
    LockPeriodRequest,
    UnlockPeriodRequest,
    SetGSTFiledDateRequest,
    ValidateDateRequest,
    ValidateDateResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[FinancialYearResponse], response_model_by_alias=True)
async def list_financial_years(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_FY_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of financial years.
    Requires FIN_FY_VIEW permission.
    """
    service = FinancialYearService(db)
    skip = (page - 1) * page_size
    fys, total = await service.get_all(current_user.organization_id, skip, page_size, include_inactive)

    items = [
        FinancialYearResponse(
            id=fy.id,
            code=fy.code,
            name=fy.name,
            start_date=fy.start_date,
            end_date=fy.end_date,
            is_current=fy.is_current,
            is_closed=fy.is_closed,
            closed_at=fy.closed_at,
            organization_id=fy.organization_id,
            organization_name=fy.organization.name if fy.organization else None,
            created_at=fy.created_at,
            updated_at=fy.updated_at,
            is_active=fy.is_active,
        )
        for fy in fys
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=FinancialYearWithPeriodsResponse, response_model_by_alias=True)
async def create_financial_year(
    data: FinancialYearCreate,
    current_user: User = Depends(RequirePermissions("FIN_FY_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new financial year with periods.
    Requires FIN_FY_CREATE permission.
    """
    service = FinancialYearService(db)
    fy = await service.create(data, current_user.id)

    # Reload with periods
    fy = await service.get(fy.id)

    return _fy_to_response_with_periods(fy)


@router.get("/current", response_model=Optional[FinancialYearResponse], response_model_by_alias=True)
async def get_current_financial_year(
    current_user: User = Depends(RequirePermissions("FIN_FY_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get the current financial year.
    Requires FIN_FY_VIEW permission.
    """
    service = FinancialYearService(db)
    fy = await service.get_current(current_user.organization_id)

    if not fy:
        return None

    return _fy_to_response(fy)


@router.get("/{fy_id}", response_model=FinancialYearWithPeriodsResponse, response_model_by_alias=True)
async def get_financial_year(
    fy_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_FY_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get financial year by ID with periods.
    Requires FIN_FY_VIEW permission.
    """
    service = FinancialYearService(db)
    fy = await service.get(fy_id)

    return _fy_to_response_with_periods(fy)


@router.put("/{fy_id}", response_model=FinancialYearResponse, response_model_by_alias=True)
async def update_financial_year(
    fy_id: UUID,
    data: FinancialYearUpdate,
    current_user: User = Depends(RequirePermissions("FIN_FY_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update a financial year.
    Requires FIN_FY_UPDATE permission.
    """
    service = FinancialYearService(db)
    fy = await service.update(fy_id, data, current_user.id)

    return _fy_to_response(fy)


@router.post("/{fy_id}/close-period", response_model=FinancialPeriodResponse, response_model_by_alias=True)
async def close_period(
    fy_id: UUID,
    data: ClosePeriodRequest,
    current_user: User = Depends(RequirePermissions("FIN_FY_CLOSE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Close a financial period.
    Requires FIN_FY_CLOSE permission.
    """
    service = PeriodService(db)
    period = await service.close_period(data.period_id, current_user.id)
    return _period_to_response(period)


@router.post("/{fy_id}/lock-period", response_model=FinancialPeriodResponse, response_model_by_alias=True)
async def lock_period(
    fy_id: UUID,
    data: LockPeriodRequest,
    current_user: User = Depends(RequirePermissions("FIN_FY_CLOSE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Lock a financial period (soft lock - prevents new entries).
    Requires FIN_FY_CLOSE permission.
    """
    service = PeriodService(db)
    period = await service.lock_period(data.period_id, data.reason, current_user.id)
    return _period_to_response(period)


@router.post("/{fy_id}/unlock-period", response_model=FinancialPeriodResponse, response_model_by_alias=True)
async def unlock_period(
    fy_id: UUID,
    data: UnlockPeriodRequest,
    current_user: User = Depends(RequirePermissions("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Unlock a financial period.
    Requires SUPER_ADMIN permission.
    """
    service = PeriodService(db)
    period = await service.unlock_period(data.period_id, current_user.id, data.override_reason)
    return _period_to_response(period)


@router.post("/{fy_id}/gst-filed", response_model=FinancialPeriodResponse, response_model_by_alias=True)
async def set_gst_filed_date(
    fy_id: UUID,
    data: SetGSTFiledDateRequest,
    current_user: User = Depends(RequirePermissions("FIN_FY_CLOSE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Set GST return filed date for a period.
    Entries on or before this date will be locked.
    Requires FIN_FY_CLOSE permission.
    """
    service = PeriodService(db)
    period = await service.set_gst_filed_date(data.period_id, data.filed_date, current_user.id)
    return _period_to_response(period)


@router.post("/validate-date", response_model=ValidateDateResponse, response_model_by_alias=True)
async def validate_entry_date(
    data: ValidateDateRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Validate if entries are allowed for a given date.
    Returns validation result with details about why entries may be blocked.
    """
    service = PeriodService(db)
    result = await service.validate_entry_date(current_user.organization_id, data.entry_date)
    return ValidateDateResponse(
        allowed=result.allowed,
        period_id=result.period_id,
        period_name=result.period_name,
        reason=result.reason,
    )


@router.post("/{fy_id}/reopen-period", response_model=FinancialPeriodResponse, response_model_by_alias=True)
async def reopen_period(
    fy_id: UUID,
    data: UnlockPeriodRequest,
    current_user: User = Depends(RequirePermissions("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Reopen a closed financial period.
    Requires SUPER_ADMIN permission.
    """
    service = PeriodService(db)
    period = await service.reopen_period(data.period_id, current_user.id, data.override_reason)
    return _period_to_response(period)


@router.post("/{fy_id}/close", response_model=FinancialYearResponse, response_model_by_alias=True)
async def close_financial_year(
    fy_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_FY_CLOSE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Close a financial year.
    Requires FIN_FY_CLOSE permission.
    """
    service = FinancialYearService(db)
    fy = await service.close_year(fy_id, current_user.id)

    return _fy_to_response(fy)


@router.delete("/{fy_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_financial_year(
    fy_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_FY_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a financial year.
    Requires FIN_FY_DELETE permission.
    """
    service = FinancialYearService(db)
    await service.delete(fy_id, current_user.id)

    return MessageResponse(message="Financial year deleted successfully")


def _period_to_response(period) -> FinancialPeriodResponse:
    """Convert FinancialPeriod model to response."""
    return FinancialPeriodResponse(
        id=period.id,
        period_number=period.period_number,
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_closed=period.is_closed,
        closed_at=period.closed_at,
        is_locked=period.is_locked,
        locked_at=period.locked_at,
        lock_reason=period.lock_reason,
        gst_return_filed_date=period.gst_return_filed_date,
        is_adjustment_period=period.is_adjustment_period,
        is_active=period.is_active,
    )


def _fy_to_response(fy) -> FinancialYearResponse:
    """Convert FinancialYear model to response."""
    return FinancialYearResponse(
        id=fy.id,
        code=fy.code,
        name=fy.name,
        start_date=fy.start_date,
        end_date=fy.end_date,
        is_current=fy.is_current,
        is_closed=fy.is_closed,
        closed_at=fy.closed_at,
        organization_id=fy.organization_id,
        organization_name=fy.organization.name if fy.organization else None,
        created_at=fy.created_at,
        updated_at=fy.updated_at,
        is_active=fy.is_active,
    )


def _fy_to_response_with_periods(fy) -> FinancialYearWithPeriodsResponse:
    """Convert FinancialYear model to response with periods."""
    return FinancialYearWithPeriodsResponse(
        id=fy.id,
        code=fy.code,
        name=fy.name,
        start_date=fy.start_date,
        end_date=fy.end_date,
        is_current=fy.is_current,
        is_closed=fy.is_closed,
        closed_at=fy.closed_at,
        organization_id=fy.organization_id,
        organization_name=fy.organization.name if fy.organization else None,
        created_at=fy.created_at,
        updated_at=fy.updated_at,
        is_active=fy.is_active,
        periods=[_period_to_response(p) for p in fy.periods],
    )
