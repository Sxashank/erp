"""Pydantic schemas for Shift and Holiday models."""

from datetime import date, time
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import ShiftType, HolidayType


# ============================================
# Shift Schemas
# ============================================
class ShiftBase(BaseModel):
    """Base schema for shift."""
    shift_code: str = Field(..., max_length=20)
    shift_name: str = Field(..., max_length=100)
    shift_type: ShiftType = ShiftType.GENERAL

    # Timing
    start_time: time
    end_time: time
    is_overnight: bool = False

    # Break
    break_start_time: Optional[time] = None
    break_end_time: Optional[time] = None
    break_duration_minutes: int = 0

    # Working Hours
    working_hours: int = Field(480, description="Working hours in minutes")
    half_day_hours: int = Field(240, description="Half day hours in minutes")

    # Grace Period
    grace_period_late_minutes: int = 15
    grace_period_early_minutes: int = 15

    # Late Deduction Rules
    late_deduction_rules: Optional[Dict[str, Any]] = None

    # Overtime
    overtime_applicable: bool = False
    overtime_threshold_minutes: int = 30
    overtime_rate_multiplier: Optional[float] = 1.0

    # Week Off
    week_off_days: Optional[List[str]] = Field(default=["SUNDAY"])

    # Status
    is_active: bool = True
    description: Optional[str] = None


class ShiftCreate(ShiftBase):
    """Schema for creating shift."""
    organization_id: UUID


class ShiftUpdate(BaseModel):
    """Schema for updating shift."""
    shift_name: Optional[str] = None
    shift_type: Optional[ShiftType] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_overnight: Optional[bool] = None
    break_start_time: Optional[time] = None
    break_end_time: Optional[time] = None
    break_duration_minutes: Optional[int] = None
    working_hours: Optional[int] = None
    half_day_hours: Optional[int] = None
    grace_period_late_minutes: Optional[int] = None
    grace_period_early_minutes: Optional[int] = None
    late_deduction_rules: Optional[Dict[str, Any]] = None
    overtime_applicable: Optional[bool] = None
    overtime_threshold_minutes: Optional[int] = None
    overtime_rate_multiplier: Optional[float] = None
    week_off_days: Optional[List[str]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class ShiftResponse(ShiftBase):
    """Response schema for shift."""
    id: UUID
    organization_id: UUID
    total_shift_minutes: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================
# Holiday Calendar Schemas
# ============================================
class HolidayCalendarBase(BaseModel):
    """Base schema for holiday calendar."""
    year: int
    calendar_name: str = Field("DEFAULT", max_length=100)
    description: Optional[str] = None
    applicable_unit_ids: Optional[List[UUID]] = None
    is_active: bool = True


class HolidayCalendarCreate(HolidayCalendarBase):
    """Schema for creating holiday calendar."""
    organization_id: UUID


class HolidayCalendarUpdate(BaseModel):
    """Schema for updating holiday calendar."""
    calendar_name: Optional[str] = None
    description: Optional[str] = None
    applicable_unit_ids: Optional[List[UUID]] = None
    is_active: Optional[bool] = None


class HolidayCalendarResponse(HolidayCalendarBase):
    """Response schema for holiday calendar."""
    id: UUID
    organization_id: UUID
    holidays: Optional[List["HolidayResponse"]] = None

    class Config:
        from_attributes = True


# ============================================
# Holiday Schemas
# ============================================
class HolidayBase(BaseModel):
    """Base schema for holiday."""
    holiday_date: date
    holiday_name: str = Field(..., max_length=200)
    holiday_type: HolidayType = HolidayType.COMPANY
    is_optional: bool = False
    max_optional_per_year: Optional[int] = None
    applicable_unit_ids: Optional[List[UUID]] = None
    applicable_department_ids: Optional[List[UUID]] = None
    description: Optional[str] = None


class HolidayCreate(HolidayBase):
    """Schema for creating holiday."""
    calendar_id: UUID


class HolidayBulkCreate(BaseModel):
    """Schema for bulk creating holidays."""
    calendar_id: UUID
    holidays: List[HolidayBase]


class HolidayUpdate(BaseModel):
    """Schema for updating holiday."""
    holiday_date: Optional[date] = None
    holiday_name: Optional[str] = None
    holiday_type: Optional[HolidayType] = None
    is_optional: Optional[bool] = None
    max_optional_per_year: Optional[int] = None
    applicable_unit_ids: Optional[List[UUID]] = None
    applicable_department_ids: Optional[List[UUID]] = None
    description: Optional[str] = None


class HolidayResponse(HolidayBase):
    """Response schema for holiday."""
    id: UUID
    calendar_id: UUID

    class Config:
        from_attributes = True


# Resolve forward reference
HolidayCalendarResponse.model_rebuild()
