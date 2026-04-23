"""Financial Year schemas."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema


class FinancialPeriodResponse(BaseSchema):
    """Financial Period response schema."""

    id: UUID
    period_number: int
    name: str
    start_date: date
    end_date: date
    is_closed: bool
    closed_at: Optional[datetime] = None
    # Lock fields
    is_locked: bool = False
    locked_at: Optional[datetime] = None
    lock_reason: Optional[str] = None
    gst_return_filed_date: Optional[date] = None
    is_adjustment_period: bool = False
    is_active: bool = True


class FinancialYearCreate(BaseSchema):
    """Schema for creating a financial year."""

    code: str = Field(..., min_length=1, max_length=20, description="FY code e.g. FY2024-25")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    start_date: date
    end_date: date
    is_current: bool = False
    organization_id: UUID

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v: date, info) -> date:
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class FinancialYearUpdate(BaseSchema):
    """Schema for updating a financial year."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class FinancialYearResponse(AuditSchema):
    """Financial Year response schema."""

    id: UUID
    code: str
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_closed: bool
    closed_at: Optional[datetime] = None
    organization_id: UUID
    organization_name: Optional[str] = None


class FinancialYearWithPeriodsResponse(FinancialYearResponse):
    """Financial Year with periods response schema."""

    periods: List[FinancialPeriodResponse] = []


class ClosePeriodRequest(BaseSchema):
    """Request to close a financial period."""

    period_id: UUID


class CloseYearRequest(BaseSchema):
    """Request to close a financial year."""

    closing_narration: Optional[str] = None
    transfer_profit_to_account_id: Optional[UUID] = None


class LockPeriodRequest(BaseSchema):
    """Request to lock a financial period."""

    period_id: UUID
    reason: str = Field(..., min_length=1, max_length=50, description="Lock reason e.g. GST_RETURN_FILED, AUDIT")


class UnlockPeriodRequest(BaseSchema):
    """Request to unlock a financial period (requires admin)."""

    period_id: UUID
    override_reason: str = Field(..., min_length=1, max_length=200, description="Reason for unlocking")


class SetGSTFiledDateRequest(BaseSchema):
    """Request to set GST return filed date."""

    period_id: UUID
    filed_date: date = Field(..., description="Date until which GST return has been filed")


class ValidateDateRequest(BaseSchema):
    """Request to validate if entries are allowed for a date."""

    organization_id: UUID
    entry_date: date


class ValidateDateResponse(BaseSchema):
    """Response for date validation."""

    allowed: bool
    period_id: Optional[UUID] = None
    period_name: Optional[str] = None
    reason: Optional[str] = None
