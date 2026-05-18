"""Schemas for Recurring Voucher API."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from app.schemas.base import CamelSchema

from app.core.constants import RecurrenceFrequency, RecurringVoucherStatus


class RecurringVoucherLineTemplate(CamelSchema):
    """Template line item for recurring voucher."""

    account_id: UUID
    debit_amount: Decimal = Decimal("0.00")
    credit_amount: Decimal = Decimal("0.00")
    narration: Optional[str] = None
    cost_center_id: Optional[UUID] = None

    @field_validator("debit_amount", "credit_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class RecurringVoucherCreate(CamelSchema):
    """Schema for creating a recurring voucher template."""

    organization_id: UUID
    voucher_type_id: UUID
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    frequency: RecurrenceFrequency
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_date: date
    end_date: Optional[date] = None
    total_occurrences: Optional[int] = Field(None, gt=0)
    auto_post: bool = False
    auto_approve: bool = False
    narration_template: Optional[str] = None
    notify_on_generation: bool = True
    notify_days_before: int = Field(default=0, ge=0)
    lines: List[RecurringVoucherLineTemplate]

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: List[RecurringVoucherLineTemplate]) -> List[RecurringVoucherLineTemplate]:
        if not v:
            raise ValueError("At least one line item is required")
        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)
        if total_debit != total_credit:
            raise ValueError(f"Debit ({total_debit}) and Credit ({total_credit}) must be equal")
        return v


class RecurringVoucherUpdate(CamelSchema):
    """Schema for updating a recurring voucher template."""

    template_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    frequency: Optional[RecurrenceFrequency] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    end_date: Optional[date] = None
    total_occurrences: Optional[int] = Field(None, gt=0)
    auto_post: Optional[bool] = None
    auto_approve: Optional[bool] = None
    narration_template: Optional[str] = None
    notify_on_generation: Optional[bool] = None
    notify_days_before: Optional[int] = Field(None, ge=0)
    lines: Optional[List[RecurringVoucherLineTemplate]] = None


class RecurringVoucherLineResponse(CamelSchema):
    """Line item in recurring voucher response."""

    account_id: str
    account_code: str
    account_name: str
    debit_amount: Decimal
    credit_amount: Decimal
    narration: Optional[str] = None
    cost_center_id: Optional[str] = None


class RecurringVoucherResponse(CamelSchema):
    """Full recurring voucher response."""

    id: str
    organization_id: str
    organization_name: str
    voucher_type_id: str
    voucher_type_name: str
    template_name: str
    description: Optional[str] = None
    frequency: RecurrenceFrequency
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None
    next_run_date: Optional[date] = None
    last_run_date: Optional[date] = None
    total_occurrences: Optional[int] = None
    completed_occurrences: int
    status: RecurringVoucherStatus
    auto_post: bool
    auto_approve: bool
    narration_template: Optional[str] = None
    total_amount: Decimal
    lines: List[RecurringVoucherLineResponse]
    notify_on_generation: bool
    notify_days_before: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class RecurringVoucherListItem(CamelSchema):
    """List item for recurring voucher."""

    id: str
    template_name: str
    voucher_type_name: str
    frequency: RecurrenceFrequency
    total_amount: Decimal
    next_run_date: Optional[date] = None
    last_run_date: Optional[date] = None
    completed_occurrences: int
    total_occurrences: Optional[int] = None
    status: RecurringVoucherStatus
    auto_post: bool


class RecurringVoucherListResponse(CamelSchema):
    """Paginated list of recurring vouchers."""

    items: List[RecurringVoucherListItem]
    total: int
    page: int
    page_size: int
    pages: int


class RecurringVoucherLogResponse(CamelSchema):
    """Response for recurring voucher log entry."""

    id: str
    recurring_voucher_id: str
    recurring_voucher_name: str
    voucher_id: Optional[str] = None
    voucher_number: Optional[str] = None
    scheduled_date: date
    generated_at: Optional[datetime] = None
    occurrence_number: int
    status: str
    error_message: Optional[str] = None


class RecurringVoucherLogListResponse(CamelSchema):
    """Paginated list of recurring voucher logs."""

    items: List[RecurringVoucherLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class GenerateVoucherRequest(CamelSchema):
    """Request to manually generate voucher from recurring template."""

    voucher_date: Optional[date] = None
    narration_override: Optional[str] = None


class GenerateVoucherResponse(CamelSchema):
    """Response after generating voucher."""

    success: bool
    message: str
    voucher_id: Optional[str] = None
    voucher_number: Optional[str] = None


class PauseResumeRequest(CamelSchema):
    """Request to pause or resume recurring voucher."""

    reason: Optional[str] = None


class UpcomingRecurringVoucher(CamelSchema):
    """Upcoming recurring voucher for dashboard."""

    id: str
    template_name: str
    voucher_type_name: str
    next_run_date: date
    total_amount: Decimal
    days_until_due: int


class RecurringVoucherStats(CamelSchema):
    """Statistics for recurring vouchers."""

    total_active: int
    total_paused: int
    due_today: int
    due_this_week: int
    total_generated_this_month: int
    total_amount_this_month: Decimal
