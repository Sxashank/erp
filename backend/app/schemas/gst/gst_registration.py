"""GST Registration schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
import re

from app.schemas.base import BaseSchema
from app.core.constants import GSTRegistrationType


class GSTRegistrationBase(BaseSchema):
    """Base GST Registration schema."""

    gstin: str = Field(..., min_length=15, max_length=15)
    legal_name: str = Field(..., min_length=1, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    registration_type: GSTRegistrationType = GSTRegistrationType.REGULAR
    state_code: str = Field(..., min_length=2, max_length=2)
    state_name: str = Field(..., min_length=1, max_length=50)
    address: Optional[str] = None
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    is_e_invoice_enabled: bool = False
    e_invoice_username: Optional[str] = Field(None, max_length=100)
    is_e_way_bill_enabled: bool = False
    organization_id: UUID
    unit_id: Optional[UUID] = None

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        """Validate GSTIN format."""
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid GSTIN format")
        return v.upper()

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        """Validate state code."""
        valid_codes = [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "26", "27", "28", "29", "30", "31",
            "32", "33", "34", "35", "36", "37", "38", "97", "99"
        ]
        if v not in valid_codes:
            raise ValueError("Invalid state code")
        return v


class GSTRegistrationCreate(GSTRegistrationBase):
    """Schema for creating a GST registration."""

    e_invoice_password: Optional[str] = Field(None, max_length=100)


class GSTRegistrationUpdate(BaseSchema):
    """Schema for updating a GST registration."""

    legal_name: Optional[str] = Field(None, min_length=1, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    registration_type: Optional[GSTRegistrationType] = None
    address: Optional[str] = None
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    is_e_invoice_enabled: Optional[bool] = None
    e_invoice_username: Optional[str] = Field(None, max_length=100)
    e_invoice_password: Optional[str] = Field(None, max_length=100)
    is_e_way_bill_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class GSTRegistrationResponse(BaseSchema):
    """GST Registration response schema."""

    id: UUID
    gstin: str
    legal_name: str
    trade_name: Optional[str] = None
    registration_type: GSTRegistrationType
    state_code: str
    state_name: str
    address: Optional[str] = None
    pincode: Optional[str] = None
    is_e_invoice_enabled: bool
    e_invoice_username: Optional[str] = None
    is_e_way_bill_enabled: bool
    organization_id: UUID
    organization_name: Optional[str] = None
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
