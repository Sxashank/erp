"""TDS Section schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class TDSSectionBase(CamelSchema):
    """Base TDS Section schema."""

    section_code: str = Field(..., min_length=1, max_length=20)
    section_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    rate_individual: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    rate_company: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    rate_no_pan: Decimal = Field(default=Decimal("20.00"), ge=0, le=100)
    rate_lower_deduction: Decimal | None = Field(None, ge=0, le=100)
    threshold_single: Decimal = Field(default=Decimal("0.00"), ge=0)
    threshold_annual: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_tcs: bool = False
    surcharge_applicable: bool = False
    cess_rate: Decimal = Field(default=Decimal("4.00"), ge=0, le=100)
    effective_from: date
    effective_to: date | None = None
    return_form: str = Field(default="26Q", max_length=10)
    nature_of_payment_code: str | None = Field(None, max_length=10)


class TDSSectionCreate(TDSSectionBase):
    """Schema for creating a TDS section."""

    pass


class TDSSectionUpdate(CamelSchema):
    """Schema for updating a TDS section."""

    section_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    rate_individual: Decimal | None = Field(None, ge=0, le=100)
    rate_company: Decimal | None = Field(None, ge=0, le=100)
    rate_no_pan: Decimal | None = Field(None, ge=0, le=100)
    rate_lower_deduction: Decimal | None = Field(None, ge=0, le=100)
    threshold_single: Decimal | None = Field(None, ge=0)
    threshold_annual: Decimal | None = Field(None, ge=0)
    surcharge_applicable: bool | None = None
    cess_rate: Decimal | None = Field(None, ge=0, le=100)
    effective_from: date | None = None
    effective_to: date | None = None
    return_form: str | None = Field(None, max_length=10)
    nature_of_payment_code: str | None = Field(None, max_length=10)
    is_active: bool | None = None


class TDSSectionResponse(TDSSectionBase):
    """TDS Section response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True
