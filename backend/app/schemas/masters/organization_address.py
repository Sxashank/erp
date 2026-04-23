"""Organization Address schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator
import re

from app.schemas.base import BaseSchema, AuditSchema


class OrganizationAddressBase(BaseSchema):
    """Base organization address schema."""

    address_type: str = Field(..., max_length=30)
    address_label: Optional[str] = Field(None, max_length=100)
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    address_line3: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: str = Field(..., min_length=2, max_length=2)
    state_name: Optional[str] = Field(None, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=10)
    country: str = Field(default="India", max_length=50)

    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v: str) -> str:
        """Validate address type."""
        valid_types = ["REGISTERED", "CORPORATE", "FACTORY", "WAREHOUSE", "BRANCH", "COMMUNICATION", "OTHER"]
        if v.upper() not in valid_types:
            raise ValueError(f"Invalid address type. Must be one of: {', '.join(valid_types)}")
        return v.upper()

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate Indian pincode format."""
        pattern = r"^[1-9][0-9]{5}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid pincode format. Expected 6-digit number starting with non-zero")
        return v

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        """Validate Indian state code."""
        valid_codes = [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
            "31", "32", "33", "34", "35", "36", "37", "38", "97", "99"
        ]
        if v not in valid_codes:
            raise ValueError("Invalid state code")
        return v


class OrganizationAddressCreate(OrganizationAddressBase):
    """Organization address creation schema."""

    organization_id: Optional[UUID] = None  # Populated from path parameter
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    is_primary: bool = False


class OrganizationAddressUpdate(BaseSchema):
    """Organization address update schema."""

    address_type: Optional[str] = Field(None, max_length=30)
    address_label: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    address_line3: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, min_length=2, max_length=2)
    state_name: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    country: Optional[str] = Field(None, max_length=50)
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    is_primary: Optional[bool] = None

    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate address type."""
        if v is None:
            return v
        valid_types = ["REGISTERED", "CORPORATE", "FACTORY", "WAREHOUSE", "BRANCH", "COMMUNICATION", "OTHER"]
        if v.upper() not in valid_types:
            raise ValueError(f"Invalid address type. Must be one of: {', '.join(valid_types)}")
        return v.upper()

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        """Validate Indian pincode format."""
        if v is None:
            return v
        pattern = r"^[1-9][0-9]{5}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid pincode format. Expected 6-digit number starting with non-zero")
        return v

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate Indian state code."""
        if v is None:
            return v
        valid_codes = [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
            "31", "32", "33", "34", "35", "36", "37", "38", "97", "99"
        ]
        if v not in valid_codes:
            raise ValueError("Invalid state code")
        return v


class OrganizationAddressResponse(OrganizationAddressBase, AuditSchema):
    """Organization address response schema."""

    id: UUID
    organization_id: UUID
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_primary: bool
