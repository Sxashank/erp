"""Unit schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator
import re

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import UnitType, EntityStatus


class UnitBase(BaseSchema):
    """Base unit schema."""

    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    unit_type: str = Field(default=UnitType.BRANCH.value)


class UnitCreate(UnitBase):
    """Unit creation schema."""

    organization_id: UUID
    parent_unit_id: Optional[UUID] = None

    # Accounting
    is_separate_accounting: bool = False

    # GST
    gstin: Optional[str] = Field(None, max_length=15)
    gst_state_code: Optional[str] = Field(None, max_length=2)

    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="India", max_length=50)

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    manager_name: Optional[str] = Field(None, max_length=200)

    is_head_office: bool = False

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        """Validate GSTIN format."""
        if v is None:
            return v
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid GSTIN format")
        return v.upper()


class UnitUpdate(BaseSchema):
    """Unit update schema."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    unit_type: Optional[str] = None
    parent_unit_id: Optional[UUID] = None

    # Accounting
    is_separate_accounting: Optional[bool] = None

    # GST
    gstin: Optional[str] = Field(None, max_length=15)
    gst_state_code: Optional[str] = Field(None, max_length=2)

    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    manager_name: Optional[str] = Field(None, max_length=200)

    status: Optional[str] = None


class UnitResponse(UnitBase, AuditSchema):
    """Unit response schema."""

    id: UUID
    organization_id: UUID
    parent_unit_id: Optional[UUID] = None
    level: int
    path: Optional[str] = None

    # Accounting
    is_separate_accounting: bool

    # GST
    gstin: Optional[str] = None
    gst_state_code: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state_code: Optional[str] = None
    pincode: Optional[str] = None
    country: str

    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_name: Optional[str] = None

    status: str
    is_head_office: bool

    # Related
    organization_name: Optional[str] = None
    parent_unit_name: Optional[str] = None


class UnitTreeResponse(BaseSchema):
    """Unit tree node response schema."""

    id: UUID
    code: str
    name: str
    unit_type: str
    level: int
    is_head_office: bool
    status: str
    children: List["UnitTreeResponse"] = []


# Rebuild model for forward reference
UnitTreeResponse.model_rebuild()
