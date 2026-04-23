"""TDS Section schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class TDSSectionBase(BaseSchema):
    """Base TDS Section schema."""

    section_code: str = Field(..., min_length=1, max_length=20)
    section_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    rate_individual: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    rate_company: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    rate_no_pan: Decimal = Field(default=Decimal("20.00"), ge=0, le=100)
    rate_lower_deduction: Optional[Decimal] = Field(None, ge=0, le=100)
    threshold_single: Decimal = Field(default=Decimal("0.00"), ge=0)
    threshold_annual: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_tcs: bool = False
    surcharge_applicable: bool = False
    cess_rate: Decimal = Field(default=Decimal("4.00"), ge=0, le=100)
    effective_from: date
    effective_to: Optional[date] = None
    return_form: str = Field(default="26Q", max_length=10)
    nature_of_payment_code: Optional[str] = Field(None, max_length=10)


class TDSSectionCreate(TDSSectionBase):
    """Schema for creating a TDS section."""

    pass


class TDSSectionUpdate(BaseSchema):
    """Schema for updating a TDS section."""

    section_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rate_individual: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_company: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_no_pan: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_lower_deduction: Optional[Decimal] = Field(None, ge=0, le=100)
    threshold_single: Optional[Decimal] = Field(None, ge=0)
    threshold_annual: Optional[Decimal] = Field(None, ge=0)
    surcharge_applicable: Optional[bool] = None
    cess_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    return_form: Optional[str] = Field(None, max_length=10)
    nature_of_payment_code: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class TDSSectionResponse(TDSSectionBase):
    """TDS Section response schema."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
