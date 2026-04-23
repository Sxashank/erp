"""GST Rate schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class GSTRateBase(BaseSchema):
    """Base GST Rate schema."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate: Decimal = Field(..., ge=0, le=100)
    cgst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    sgst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    igst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    cess_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    effective_from: date
    effective_to: Optional[date] = None
    is_composition: bool = False
    is_reverse_charge: bool = False


class GSTRateCreate(GSTRateBase):
    """Schema for creating a GST rate."""

    pass


class GSTRateUpdate(BaseSchema):
    """Schema for updating a GST rate."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    cgst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    sgst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    igst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    cess_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_composition: Optional[bool] = None
    is_reverse_charge: Optional[bool] = None
    is_active: Optional[bool] = None


class GSTRateResponse(GSTRateBase):
    """GST Rate response schema."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
