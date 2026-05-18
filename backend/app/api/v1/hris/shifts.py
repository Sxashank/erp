"""API endpoints for Shift and Holiday management."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.core.constants import Permissions
from app.core.permissions import RequirePermissions
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


# ============================================
# Shifts
# ============================================
@router.get("/shifts", response_model=PaginatedResponse[ShiftResponse], response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_SHIFT_VIEW])
async def list_shifts(
    organization_id: UUID,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List shifts for organization."""
    service = ShiftService(db)
    shifts, total = await service.list(organization_id, active_only, skip, limit)
    return PaginatedResponse(items=shifts, total=total, skip=skip, limit=limit)


@router.post("/shifts", response_model=ShiftResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_SHIFT_CREATE])
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new shift."""
    service = ShiftService(db)

    # Check if shift code already exists
    existing = await service.get_by_code(data.organization_id, data.shift_code)
    if existing:
        raise BadRequestException(
            detail="Shift code already exists",
            error_code="SHIFT_CODE_ALREADY_EXISTS",
        )

    shift = await service.create(data, current_user.id)
    return shift


@router.get("/shifts/{shift_id}", response_model=ShiftResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_SHIFT_VIEW])
async def get_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get shift by ID."""
    service = ShiftService(db)
    shift = await service.get(shift_id)
    if not shift:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")
    return shift


@router.put("/shifts/{shift_id}", response_model=ShiftResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_SHIFT_UPDATE])
async def update_shift(
    shift_id: UUID,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update shift."""
    service = ShiftService(db)
    shift = await service.update(shift_id, data, current_user.id)
    if not shift:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")
    return shift


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
@RequirePermissions([Permissions.HRIS_SHIFT_DELETE])
async def delete_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) shift."""
    service = ShiftService(db)
    success = await service.delete(shift_id)
    if not success:
        raise NotFoundException(detail="Shift not found", error_code="SHIFT_NOT_FOUND")


# ============================================
# Holiday Calendars
# ============================================
@router.get("/holiday-calendars", response_model=List[HolidayCalendarResponse], response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_VIEW])
async def list_holiday_calendars(
    organization_id: UUID,
    year: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List holiday calendars for organization."""
    service = HolidayService(db)
    calendars = await service.list_calendars(organization_id, year, active_only)
    return calendars


@router.post("/holiday-calendars", response_model=HolidayCalendarResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_HOLIDAY_CREATE])
async def create_holiday_calendar(
    data: HolidayCalendarCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new holiday calendar."""
    service = HolidayService(db)
    calendar = await service.create_calendar(data, current_user.id)
    return calendar


@router.get("/holiday-calendars/{calendar_id}", response_model=HolidayCalendarResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_VIEW])
async def get_holiday_calendar(
    calendar_id: UUID,
    include_holidays: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
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


@router.put("/holiday-calendars/{calendar_id}", response_model=HolidayCalendarResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_UPDATE])
async def update_holiday_calendar(
    calendar_id: UUID,
    data: HolidayCalendarUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
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
@RequirePermissions([Permissions.HRIS_HOLIDAY_DELETE])
async def delete_holiday_calendar(
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
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
@RequirePermissions([Permissions.HRIS_HOLIDAY_VIEW])
async def list_holidays(
    calendar_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List holidays for a calendar."""
    service = HolidayService(db)
    holidays = await service.list_holidays(calendar_id, from_date, to_date)
    return holidays


@router.post("/holidays", response_model=HolidayResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_HOLIDAY_CREATE])
async def create_holiday(
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new holiday."""
    service = HolidayService(db)
    holiday = await service.create_holiday(data, current_user.id)
    return holiday


@router.post("/holidays/bulk", response_model=List[HolidayResponse], response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
@RequirePermissions([Permissions.HRIS_HOLIDAY_CREATE])
async def bulk_create_holidays(
    data: HolidayBulkCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Bulk create holidays."""
    service = HolidayService(db)
    holidays = await service.bulk_create_holidays(data, current_user.id)
    return holidays


@router.get("/holidays/{holiday_id}", response_model=HolidayResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_VIEW])
async def get_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get holiday by ID."""
    service = HolidayService(db)
    holiday = await service.get_holiday(holiday_id)
    if not holiday:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")
    return holiday


@router.put("/holidays/{holiday_id}", response_model=HolidayResponse, response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_UPDATE])
async def update_holiday(
    holiday_id: UUID,
    data: HolidayUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update holiday."""
    service = HolidayService(db)
    holiday = await service.update_holiday(holiday_id, data, current_user.id)
    if not holiday:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")
    return holiday


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
@RequirePermissions([Permissions.HRIS_HOLIDAY_DELETE])
async def delete_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete holiday."""
    service = HolidayService(db)
    success = await service.delete_holiday(holiday_id)
    if not success:
        raise NotFoundException(detail="Holiday not found", error_code="HOLIDAY_NOT_FOUND")


# ============================================
# Utility Endpoints
# ============================================
@router.get("/check-holiday", response_model=Optional[HolidayResponse], response_model_by_alias=True)
@RequirePermissions([Permissions.HRIS_HOLIDAY_VIEW])
async def check_holiday(
    organization_id: UUID,
    check_date: date,
    unit_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Check if a date is a holiday."""
    service = HolidayService(db)
    holiday = await service.is_holiday(organization_id, check_date, unit_id)
    return holiday
