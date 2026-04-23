"""Payment Terms schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class PaymentTermsBase(BaseSchema):
    """Base Payment Terms schema."""

    code: str = Field(..., min_length=1, max_length=20, description="Payment terms code")
    name: str = Field(..., min_length=1, max_length=100, description="Payment terms name")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    days: int = Field(default=0, ge=0, le=365, description="Payment due in days from invoice date")
    discount_days: int = Field(default=0, ge=0, le=365, description="Early payment discount valid for days")
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Early payment discount percentage")


class PaymentTermsCreate(PaymentTermsBase):
    """Schema for creating payment terms."""

    organization_id: UUID = Field(..., description="Organization ID")


class PaymentTermsUpdate(BaseSchema):
    """Schema for updating payment terms."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    days: Optional[int] = Field(None, ge=0, le=365)
    discount_days: Optional[int] = Field(None, ge=0, le=365)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class PaymentTermsResponse(PaymentTermsBase):
    """Payment Terms response schema."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
