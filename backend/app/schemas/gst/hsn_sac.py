"""HSN/SAC schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.core.constants import HSNSACType


class HSNSACBase(BaseSchema):
    """Base HSN/SAC schema."""

    code: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=1)
    hsn_sac_type: HSNSACType
    chapter: Optional[str] = Field(None, max_length=10)
    section: Optional[str] = Field(None, max_length=10)
    gst_rate_id: Optional[UUID] = None
    unit_of_measurement: Optional[str] = Field(None, max_length=20)


class HSNSACCreate(HSNSACBase):
    """Schema for creating an HSN/SAC code."""

    pass


class HSNSACUpdate(BaseSchema):
    """Schema for updating an HSN/SAC code."""

    description: Optional[str] = None
    chapter: Optional[str] = Field(None, max_length=10)
    section: Optional[str] = Field(None, max_length=10)
    gst_rate_id: Optional[UUID] = None
    unit_of_measurement: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class HSNSACResponse(HSNSACBase):
    """HSN/SAC response schema."""

    id: UUID
    gst_rate_code: Optional[str] = None
    gst_rate_name: Optional[str] = None
    gst_rate_value: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
