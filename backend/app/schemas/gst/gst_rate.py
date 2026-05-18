"""GST Rate schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class GSTRateBase(CamelSchema):
    """Base GST Rate schema."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    rate: Decimal = Field(..., ge=0, le=100)
    cgst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    sgst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    igst_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    cess_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    effective_from: date
    effective_to: date | None = None
    is_composition: bool = False
    is_reverse_charge: bool = False


class GSTRateCreate(GSTRateBase):
    """Schema for creating a GST rate."""

    pass


class GSTRateUpdate(CamelSchema):
    """Schema for updating a GST rate."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    rate: Decimal | None = Field(None, ge=0, le=100)
    cgst_rate: Decimal | None = Field(None, ge=0, le=100)
    sgst_rate: Decimal | None = Field(None, ge=0, le=100)
    igst_rate: Decimal | None = Field(None, ge=0, le=100)
    cess_rate: Decimal | None = Field(None, ge=0, le=100)
    effective_from: date | None = None
    effective_to: date | None = None
    is_composition: bool | None = None
    is_reverse_charge: bool | None = None
    is_active: bool | None = None


class GSTRateResponse(GSTRateBase):
    """GST Rate response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True
