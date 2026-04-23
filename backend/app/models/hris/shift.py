"""Shift and Holiday models for HRIS module."""

from datetime import date, time
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import ShiftType, HolidayType

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee


class Shift(BaseModel):
    """Work shift master model."""

    __tablename__ = "hris_shift"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "shift_code", name="uq_shift_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Shift Details
    shift_code: Mapped[str] = mapped_column(String(20), nullable=False)
    shift_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_type: Mapped[str] = mapped_column(
        SQLEnum(ShiftType, name="shift_type_enum", create_type=False),
        nullable=False,
        default=ShiftType.GENERAL,
    )

    # Timing
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_overnight: Mapped[bool] = mapped_column(Boolean, default=False)  # Shift spans midnight

    # Break
    break_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    break_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Working Hours
    working_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=480)  # In minutes (8 hours)
    half_day_hours: Mapped[int] = mapped_column(Integer, default=240)  # In minutes (4 hours)

    # Grace Period
    grace_period_late_minutes: Mapped[int] = mapped_column(Integer, default=15)
    grace_period_early_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # Late Deduction Rules (JSONB for flexibility)
    # e.g., {"ranges": [{"from": 16, "to": 30, "deduction_minutes": 30}, {"from": 31, "to": 60, "deduction_minutes": 60}]}
    late_deduction_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Overtime Rules
    overtime_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    overtime_threshold_minutes: Mapped[int] = mapped_column(Integer, default=30)  # Min OT to count
    overtime_rate_multiplier: Mapped[Optional[float]] = mapped_column(Integer, default=1)  # 1x, 1.5x, 2x

    # Week Off (default for this shift)
    week_off_days: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=["SUNDAY"])

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship()

    @property
    def total_shift_minutes(self) -> int:
        """Calculate total shift duration in minutes."""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if self.is_overnight:
            return (24 * 60 - start_minutes) + end_minutes
        return end_minutes - start_minutes


class HolidayCalendar(BaseModel):
    """Holiday calendar master model."""

    __tablename__ = "hris_holiday_calendar"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "year", "calendar_name", name="uq_holiday_calendar_org_year"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    calendar_name: Mapped[str] = mapped_column(String(100), nullable=False, default="DEFAULT")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Applicable units (null means all)
    applicable_unit_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship()
    holidays: Mapped[List["Holiday"]] = relationship(
        back_populates="calendar", cascade="all, delete-orphan"
    )


class Holiday(BaseModel):
    """Individual holiday entry model."""

    __tablename__ = "hris_holiday"
    __table_args__ = (
        UniqueConstraint(
            "calendar_id", "holiday_date", name="uq_holiday_calendar_date"
        ),
    )

    # Calendar Reference
    calendar_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_holiday_calendar.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Holiday Details
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False)
    holiday_name: Mapped[str] = mapped_column(String(200), nullable=False)
    holiday_type: Mapped[str] = mapped_column(
        SQLEnum(HolidayType, name="holiday_type_enum", create_type=False),
        nullable=False,
        default=HolidayType.COMPANY,
    )

    # For restricted/optional holidays
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    max_optional_per_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Applicable to specific units or departments (null means all)
    applicable_unit_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    applicable_department_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    calendar: Mapped["HolidayCalendar"] = relationship(back_populates="holidays")
