"""Shift and Holiday service for HRIS module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hris.shift import Shift, HolidayCalendar, Holiday
from app.schemas.hris.shift import (
    ShiftCreate,
    ShiftUpdate,
    HolidayCalendarCreate,
    HolidayCalendarUpdate,
    HolidayCreate,
    HolidayBulkCreate,
    HolidayUpdate,
)


class ShiftService:
    """Service for shift operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ShiftCreate, created_by: UUID) -> Shift:
        """Create a new shift."""
        shift = Shift(**data.model_dump(), created_by=created_by)
        self.db.add(shift)
        await self.db.flush()
        await self.db.refresh(shift)
        return shift

    async def get(self, shift_id: UUID) -> Optional[Shift]:
        """Get shift by ID."""
        result = await self.db.execute(
            select(Shift).where(Shift.id == shift_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, organization_id: UUID, shift_code: str) -> Optional[Shift]:
        """Get shift by code."""
        result = await self.db.execute(
            select(Shift).where(
                Shift.organization_id == organization_id,
                Shift.shift_code == shift_code,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Shift], int]:
        """List shifts for organization."""
        query = select(Shift).where(Shift.organization_id == organization_id)
        if active_only:
            query = query.where(Shift.is_active == True)

        # Count total
        count_query = select(func.count(Shift.id)).where(
            Shift.organization_id == organization_id
        )
        if active_only:
            count_query = count_query.where(Shift.is_active == True)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(Shift.shift_code).offset(skip).limit(limit)
        result = await self.db.execute(query)
        shifts = list(result.scalars().all())

        return shifts, total

    async def update(self, shift_id: UUID, data: ShiftUpdate, updated_by: UUID) -> Optional[Shift]:
        """Update shift."""
        shift = await self.get(shift_id)
        if not shift:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shift, field, value)

        shift.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(shift)
        return shift

    async def delete(self, shift_id: UUID) -> bool:
        """Soft delete shift (set is_active to False)."""
        shift = await self.get(shift_id)
        if not shift:
            return False

        shift.is_active = False
        await self.db.flush()
        return True


class HolidayService:
    """Service for holiday calendar and holidays."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Holiday Calendar Operations
    # ============================================
    async def create_calendar(self, data: HolidayCalendarCreate, created_by: UUID) -> HolidayCalendar:
        """Create a new holiday calendar."""
        calendar = HolidayCalendar(**data.model_dump(), created_by=created_by)
        self.db.add(calendar)
        await self.db.flush()
        await self.db.refresh(calendar)
        return calendar

    async def get_calendar(self, calendar_id: UUID, include_holidays: bool = False) -> Optional[HolidayCalendar]:
        """Get holiday calendar by ID."""
        query = select(HolidayCalendar).where(HolidayCalendar.id == calendar_id)
        if include_holidays:
            query = query.options(selectinload(HolidayCalendar.holidays))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_calendar_by_year(
        self,
        organization_id: UUID,
        year: int,
        calendar_name: str = "DEFAULT",
    ) -> Optional[HolidayCalendar]:
        """Get holiday calendar by year."""
        result = await self.db.execute(
            select(HolidayCalendar)
            .options(selectinload(HolidayCalendar.holidays))
            .where(
                HolidayCalendar.organization_id == organization_id,
                HolidayCalendar.year == year,
                HolidayCalendar.calendar_name == calendar_name,
            )
        )
        return result.scalar_one_or_none()

    async def list_calendars(
        self,
        organization_id: UUID,
        year: Optional[int] = None,
        active_only: bool = True,
    ) -> List[HolidayCalendar]:
        """List holiday calendars."""
        query = select(HolidayCalendar).where(
            HolidayCalendar.organization_id == organization_id
        )
        if year:
            query = query.where(HolidayCalendar.year == year)
        if active_only:
            query = query.where(HolidayCalendar.is_active == True)

        query = query.order_by(HolidayCalendar.year.desc(), HolidayCalendar.calendar_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_calendar(
        self, calendar_id: UUID, data: HolidayCalendarUpdate, updated_by: UUID
    ) -> Optional[HolidayCalendar]:
        """Update holiday calendar."""
        calendar = await self.get_calendar(calendar_id)
        if not calendar:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(calendar, field, value)

        calendar.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(calendar)
        return calendar

    async def delete_calendar(self, calendar_id: UUID) -> bool:
        """Soft delete calendar (set is_active to False)."""
        calendar = await self.get_calendar(calendar_id)
        if not calendar:
            return False

        calendar.is_active = False
        await self.db.flush()
        return True

    # ============================================
    # Holiday Operations
    # ============================================
    async def create_holiday(self, data: HolidayCreate, created_by: UUID) -> Holiday:
        """Create a new holiday."""
        holiday = Holiday(**data.model_dump(), created_by=created_by)
        self.db.add(holiday)
        await self.db.flush()
        await self.db.refresh(holiday)
        return holiday

    async def bulk_create_holidays(
        self, data: HolidayBulkCreate, created_by: UUID
    ) -> List[Holiday]:
        """Bulk create holidays."""
        holidays = []
        for holiday_data in data.holidays:
            holiday = Holiday(
                calendar_id=data.calendar_id,
                **holiday_data.model_dump(),
                created_by=created_by,
            )
            self.db.add(holiday)
            holidays.append(holiday)

        await self.db.flush()
        for holiday in holidays:
            await self.db.refresh(holiday)

        return holidays

    async def get_holiday(self, holiday_id: UUID) -> Optional[Holiday]:
        """Get holiday by ID."""
        result = await self.db.execute(
            select(Holiday).where(Holiday.id == holiday_id)
        )
        return result.scalar_one_or_none()

    async def list_holidays(
        self,
        calendar_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Holiday]:
        """List holidays for a calendar."""
        query = select(Holiday).where(Holiday.calendar_id == calendar_id)

        if from_date:
            query = query.where(Holiday.holiday_date >= from_date)
        if to_date:
            query = query.where(Holiday.holiday_date <= to_date)

        query = query.order_by(Holiday.holiday_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_holiday(
        self, holiday_id: UUID, data: HolidayUpdate, updated_by: UUID
    ) -> Optional[Holiday]:
        """Update holiday."""
        holiday = await self.get_holiday(holiday_id)
        if not holiday:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(holiday, field, value)

        holiday.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(holiday)
        return holiday

    async def delete_holiday(self, holiday_id: UUID) -> bool:
        """Delete holiday."""
        holiday = await self.get_holiday(holiday_id)
        if not holiday:
            return False

        await self.db.delete(holiday)
        await self.db.flush()
        return True

    async def is_holiday(
        self,
        organization_id: UUID,
        check_date: date,
        unit_id: Optional[UUID] = None,
    ) -> Optional[Holiday]:
        """Check if a date is a holiday."""
        year = check_date.year
        calendar = await self.get_calendar_by_year(organization_id, year)
        if not calendar:
            return None

        result = await self.db.execute(
            select(Holiday).where(
                Holiday.calendar_id == calendar.id,
                Holiday.holiday_date == check_date,
            )
        )
        holiday = result.scalar_one_or_none()

        if holiday and unit_id:
            # Check if holiday applies to this unit
            if holiday.applicable_unit_ids and str(unit_id) not in [
                str(uid) for uid in holiday.applicable_unit_ids
            ]:
                return None

        return holiday

    async def get_holidays_between(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
        unit_id: Optional[UUID] = None,
    ) -> List[Holiday]:
        """Get all holidays between two dates."""
        # Get calendars for the years involved
        years = set()
        current = from_date
        while current <= to_date:
            years.add(current.year)
            current = date(current.year + 1, 1, 1)

        holidays = []
        for year in years:
            calendar = await self.get_calendar_by_year(organization_id, year)
            if calendar:
                year_holidays = await self.list_holidays(
                    calendar.id, from_date, to_date
                )
                for holiday in year_holidays:
                    if unit_id and holiday.applicable_unit_ids:
                        if str(unit_id) in [str(uid) for uid in holiday.applicable_unit_ids]:
                            holidays.append(holiday)
                    else:
                        holidays.append(holiday)

        return sorted(holidays, key=lambda h: h.holiday_date)
