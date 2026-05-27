"""API endpoints for Shift and Holiday management."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.constants import Permissions
from app.models.auth.user import User
from app.schemas.hris.shift import (
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    HolidayCalendarCreate,
    HolidayCalendarUpdate,
    HolidayCalendarResponse,
    HolidayCreate,
    HolidayBulkCreate,
    HolidayUpdate,
    HolidayResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.hris.shift_service import ShiftService, HolidayService
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
# Shifts
# ============================================
@router.get(
    "/shifts", response_model=PaginatedResponse[ShiftResponse], response_model_by_alias=True
)
async def list_shifts(
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SHIFT_VIEW)),
):
    """List shifts for organization."""
    service = ShiftService(db)
    shifts, total = await service.list(
        _require_organization_id(current_user),
        active_only,
        skip,
        limit,
    )
    return PaginatedResponse(items=shifts, total=total, skip=skip, limit=limit)


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SHIFT_CREATE)),
):
    """Create a new shift."""
    service = ShiftService(db)
    organization_id = _require_organization_id(current_user)
    payload = data.model_copy(update={"organization_id": organization_id})

    # Check if shift code already exists
    existing = await service.get_by_code(organization_id, payload.shift_code)
    if existing:
        raise BadRequestException(
            detail="Shift code already exists",
            error_code="SHIFT_CODE_ALREADY_EXISTS",
        )

    shift = await service.create(payload, current_user.id)
    return shift


@router.get("/shifts/{shift_id}", response_model=ShiftResponse, response_model_by_alias=True)
async def get_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SHIFT_VIEW)),
):
    """Get shift by ID."""
    service = ShiftService(db)
    shift = await service.get(shift_id)
    if not shift:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")
    return shift


@router.put("/shifts/{shift_id}", response_model=ShiftResponse, response_model_by_alias=True)
async def update_shift(
    shift_id: UUID,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SHIFT_UPDATE)),
):
    """Update shift."""
    service = ShiftService(db)
    shift = await service.update(shift_id, data, current_user.id)
    if not shift:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")
    return shift


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SHIFT_DELETE)),
):
    """Delete (deactivate) shift."""
    service = ShiftService(db)
    success = await service.delete(shift_id)
    if not success:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")


# ============================================
# Holiday Calendars
# ============================================
@router.get(
    "/holiday-calendars", response_model=List[HolidayCalendarResponse], response_model_by_alias=True
)
async def list_holiday_calendars(
    year: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_VIEW)),
):
    """List holiday calendars for organization."""
    service = HolidayService(db)
    calendars = await service.list_calendars(
        _require_organization_id(current_user),
        year,
        active_only,
    )
    return calendars


@router.post(
    "/holiday-calendars",
    response_model=HolidayCalendarResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_holiday_calendar(
    data: HolidayCalendarCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_CREATE)),
):
    """Create a new holiday calendar."""
    service = HolidayService(db)
    payload = data.model_copy(update={"organization_id": _require_organization_id(current_user)})
    calendar = await service.create_calendar(payload, current_user.id)
    return calendar


@router.get(
    "/holiday-calendars/{calendar_id}",
    response_model=HolidayCalendarResponse,
    response_model_by_alias=True,
)
async def get_holiday_calendar(
    calendar_id: UUID,
    include_holidays: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_VIEW)),
):
    """Get holiday calendar by ID."""
    service = HolidayService(db)
    calendar = await service.get_calendar(calendar_id, include_holidays)
    if not calendar:
        raise NotFoundException(
            detail="Holiday calendar not found",
            error_code="HOLIDAY_CALENDAR_NOT_FOUND",
        )
    return calendar


@router.put(
    "/holiday-calendars/{calendar_id}",
    response_model=HolidayCalendarResponse,
    response_model_by_alias=True,
)
async def update_holiday_calendar(
    calendar_id: UUID,
    data: HolidayCalendarUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_UPDATE)),
):
    """Update holiday calendar."""
    service = HolidayService(db)
    calendar = await service.update_calendar(calendar_id, data, current_user.id)
    if not calendar:
        raise NotFoundException(
            detail="Holiday calendar not found",
            error_code="HOLIDAY_CALENDAR_NOT_FOUND",
        )
    return calendar


@router.delete("/holiday-calendars/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday_calendar(
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_DELETE)),
):
    """Delete (deactivate) holiday calendar."""
    service = HolidayService(db)
    success = await service.delete_calendar(calendar_id)
    if not success:
        raise NotFoundException(
            detail="Holiday calendar not found",
            error_code="HOLIDAY_CALENDAR_NOT_FOUND",
        )


# ============================================
# Holidays
# ============================================
@router.get("/holidays", response_model=List[HolidayResponse], response_model_by_alias=True)
async def list_holidays(
    calendar_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_VIEW)),
):
    """List holidays for a calendar."""
    service = HolidayService(db)
    holidays = await service.list_holidays(calendar_id, from_date, to_date)
    return holidays


@router.post(
    "/holidays",
    response_model=HolidayResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_holiday(
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_CREATE)),
):
    """Create a new holiday."""
    service = HolidayService(db)
    holiday = await service.create_holiday(data, current_user.id)
    return holiday


@router.post(
    "/holidays/bulk",
    response_model=List[HolidayResponse],
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_holidays(
    data: HolidayBulkCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_CREATE)),
):
    """Bulk create holidays."""
    service = HolidayService(db)
    holidays = await service.bulk_create_holidays(data, current_user.id)
    return holidays


@router.get("/holidays/{holiday_id}", response_model=HolidayResponse, response_model_by_alias=True)
async def get_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_VIEW)),
):
    """Get holiday by ID."""
    service = HolidayService(db)
    holiday = await service.get_holiday(holiday_id)
    if not holiday:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")
    return holiday


@router.put("/holidays/{holiday_id}", response_model=HolidayResponse, response_model_by_alias=True)
async def update_holiday(
    holiday_id: UUID,
    data: HolidayUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_UPDATE)),
):
    """Update holiday."""
    service = HolidayService(db)
    holiday = await service.update_holiday(holiday_id, data, current_user.id)
    if not holiday:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")
    return holiday


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_DELETE)),
):
    """Delete holiday."""
    service = HolidayService(db)
    success = await service.delete_holiday(holiday_id)
    if not success:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")


# ============================================
# Utility Endpoints
# ============================================
@router.get(
    "/check-holiday", response_model=Optional[HolidayResponse], response_model_by_alias=True
)
async def check_holiday(
    check_date: date,
    unit_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_HOLIDAY_VIEW)),
):
    """Check if a date is a holiday."""
    service = HolidayService(db)
    holiday = await service.is_holiday(
        _require_organization_id(current_user),
        check_date,
        unit_id,
    )
    return holiday
