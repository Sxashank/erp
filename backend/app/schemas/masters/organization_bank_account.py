"""Organization Bank Account schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
import re

from app.schemas.base import BaseSchema, AuditSchema


class OrganizationBankAccountBase(BaseSchema):
    """Base organization bank account schema."""

    account_name: str = Field(..., min_length=2, max_length=200)
    account_number: str = Field(..., min_length=5, max_length=30)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    bank_name: str = Field(..., min_length=2, max_length=200)
    branch_name: Optional[str] = Field(None, max_length=200)
    branch_address: Optional[str] = None
    micr_code: Optional[str] = Field(None, max_length=9)
    swift_code: Optional[str] = Field(None, max_length=11)
    account_type: str = Field(default="CURRENT", max_length=20)

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        """Validate IFSC code format."""
        pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid IFSC code format. Expected: XXXX0XXXXXX")
        return v.upper()

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        """Validate account type."""
        valid_types = ["CURRENT", "SAVINGS", "OD", "CC", "FIXED_DEPOSIT"]
        if v.upper() not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of: {', '.join(valid_types)}")
        return v.upper()


class OrganizationBankAccountCreate(OrganizationBankAccountBase):
    """Organization bank account creation schema."""

    organization_id: Optional[UUID] = None  # Populated from path parameter
    ledger_account_id: Optional[UUID] = None
    sanctioned_limit: Optional[Decimal] = Field(None, ge=0)
    drawing_power: Optional[Decimal] = Field(None, ge=0)
    is_primary: bool = False
    allow_payments: bool = True
    allow_receipts: bool = True


class OrganizationBankAccountUpdate(BaseSchema):
    """Organization bank account update schema."""

    account_name: Optional[str] = Field(None, min_length=2, max_length=200)
    ifsc_code: Optional[str] = Field(None, min_length=11, max_length=11)
    bank_name: Optional[str] = Field(None, min_length=2, max_length=200)
    branch_name: Optional[str] = Field(None, max_length=200)
    branch_address: Optional[str] = None
    micr_code: Optional[str] = Field(None, max_length=9)
    swift_code: Optional[str] = Field(None, max_length=11)
    account_type: Optional[str] = Field(None, max_length=20)
    ledger_account_id: Optional[UUID] = None
    sanctioned_limit: Optional[Decimal] = Field(None, ge=0)
    drawing_power: Optional[Decimal] = Field(None, ge=0)
    is_primary: Optional[bool] = None
    allow_payments: Optional[bool] = None
    allow_receipts: Optional[bool] = None

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: Optional[str]) -> Optional[str]:
        """Validate IFSC code format."""
        if v is None:
            return v
        pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid IFSC code format. Expected: XXXX0XXXXXX")
        return v.upper()

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate account type."""
        if v is None:
            return v
        valid_types = ["CURRENT", "SAVINGS", "OD", "CC", "FIXED_DEPOSIT"]
        if v.upper() not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of: {', '.join(valid_types)}")
        return v.upper()


class OrganizationBankAccountResponse(OrganizationBankAccountBase, AuditSchema):
    """Organization bank account response schema."""

    id: UUID
    organization_id: UUID
    ledger_account_id: Optional[UUID] = None
    sanctioned_limit: Optional[Decimal] = None
    drawing_power: Optional[Decimal] = None
    is_primary: bool
    allow_payments: bool
    allow_receipts: bool
