"""Schemas for Voucher Template API."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator
from app.schemas.base import CamelSchema


class VoucherTemplateLineItem(CamelSchema):
    """Template line item for voucher template."""

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


class VoucherTemplateCreate(CamelSchema):
    """Schema for creating a voucher template."""

    organization_id: UUID
    voucher_type_id: UUID
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    default_narration: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_favorite: bool = False
    lines: List[VoucherTemplateLineItem]

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: List[VoucherTemplateLineItem]) -> List[VoucherTemplateLineItem]:
        if not v:
            raise ValueError("At least one line item is required")
        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)
        if total_debit != total_credit:
            raise ValueError(f"Debit ({total_debit}) and Credit ({total_credit}) must be equal")
        return v


class VoucherTemplateUpdate(CamelSchema):
    """Schema for updating a voucher template."""

    template_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    default_narration: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_favorite: Optional[bool] = None
    is_active: Optional[bool] = None
    lines: Optional[List[VoucherTemplateLineItem]] = None


class VoucherTemplateLineResponse(CamelSchema):
    """Line item in template response."""

    account_id: str
    account_code: str
    account_name: str
    debit_amount: Decimal
    credit_amount: Decimal
    narration: Optional[str] = None
    cost_center_id: Optional[str] = None


class VoucherTemplateResponse(CamelSchema):
    """Full voucher template response."""

    id: str
    organization_id: str
    organization_name: str
    voucher_type_id: str
    voucher_type_name: str
    voucher_type_code: str
    template_name: str
    description: Optional[str] = None
    default_narration: Optional[str] = None
    total_amount: Decimal
    lines: List[VoucherTemplateLineResponse]
    is_active: bool
    is_favorite: bool
    category: Optional[str] = None
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class VoucherTemplateListItem(CamelSchema):
    """List item for voucher template."""

    id: str
    template_name: str
    voucher_type_name: str
    voucher_type_code: str
    total_amount: Decimal
    category: Optional[str] = None
    is_active: bool
    is_favorite: bool
    usage_count: int
    last_used_at: Optional[datetime] = None


class VoucherTemplateListResponse(CamelSchema):
    """Paginated list of voucher templates."""

    items: List[VoucherTemplateListItem]
    total: int
    page: int
    page_size: int
    pages: int


class UseTemplateRequest(CamelSchema):
    """Request to create a voucher from template."""

    voucher_date: str
    narration_override: Optional[str] = None
    amount_multiplier: Optional[Decimal] = Field(None, gt=0)


class UseTemplateResponse(CamelSchema):
    """Response after creating voucher from template."""

    success: bool
    message: str
    voucher_id: Optional[str] = None
    voucher_number: Optional[str] = None


class TemplateCategory(CamelSchema):
    """Template category with count."""

    category: str
    count: int


class VoucherTemplateStats(CamelSchema):
    """Statistics for voucher templates."""

    total_templates: int
    active_templates: int
    favorite_templates: int
    categories: List[TemplateCategory]
    most_used: List[VoucherTemplateListItem]
