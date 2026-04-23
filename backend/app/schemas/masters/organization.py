"""Organization schemas."""

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator
import re

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import EntityStatus


class OrganizationBase(BaseSchema):
    """Base organization schema."""

    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=200)
    legal_name: str = Field(..., min_length=2, max_length=300)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""

    # Registration
    cin: Optional[str] = Field(None, max_length=25)
    pan: str = Field(..., min_length=10, max_length=10)
    tan: Optional[str] = Field(None, min_length=10, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    rbi_registration: Optional[str] = Field(None, max_length=50)

    # Address
    reg_address_line1: Optional[str] = Field(None, max_length=255)
    reg_address_line2: Optional[str] = Field(None, max_length=255)
    reg_city: Optional[str] = Field(None, max_length=100)
    reg_district: Optional[str] = Field(None, max_length=100)
    reg_state_code: Optional[str] = Field(None, max_length=2)
    reg_pincode: Optional[str] = Field(None, max_length=10)
    reg_country: str = Field(default="India", max_length=50)

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)

    # Financial
    base_currency: str = Field(default="INR", max_length=3)
    financial_year_start_month: int = Field(default=4, ge=1, le=12)

    # Branding
    logo_path: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        """Validate PAN format."""
        pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid PAN format. Expected: AAAAA9999A")
        return v.upper()

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


class OrganizationUpdate(BaseSchema):
    """Organization update schema."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    legal_name: Optional[str] = Field(None, min_length=2, max_length=300)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    # Registration
    tan: Optional[str] = Field(None, min_length=10, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    rbi_registration: Optional[str] = Field(None, max_length=50)

    # Address
    reg_address_line1: Optional[str] = Field(None, max_length=255)
    reg_address_line2: Optional[str] = Field(None, max_length=255)
    reg_city: Optional[str] = Field(None, max_length=100)
    reg_district: Optional[str] = Field(None, max_length=100)
    reg_state_code: Optional[str] = Field(None, max_length=2)
    reg_pincode: Optional[str] = Field(None, max_length=10)

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)

    # Branding
    logo_path: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)

    status: Optional[str] = None


class OrganizationResponse(OrganizationBase, AuditSchema):
    """Organization response schema."""

    id: UUID

    # Registration
    cin: Optional[str] = None
    pan: str
    tan: Optional[str] = None
    gstin: Optional[str] = None
    rbi_registration: Optional[str] = None

    # Address
    reg_address_line1: Optional[str] = None
    reg_address_line2: Optional[str] = None
    reg_city: Optional[str] = None
    reg_district: Optional[str] = None
    reg_state_code: Optional[str] = None
    reg_pincode: Optional[str] = None
    reg_country: str

    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    # Financial
    base_currency: str
    financial_year_start_month: int

    # Branding
    logo_path: Optional[str] = None
    primary_color: Optional[str] = None

    # Status
    status: str
    is_primary: bool

    # Counts
    unit_count: int = 0
    department_count: int = 0
    user_count: int = 0
