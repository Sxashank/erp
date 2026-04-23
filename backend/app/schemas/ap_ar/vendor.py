"""Vendor schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema
from app.core.pii import MaskedPIIModel


class VendorBase(BaseSchema):
    """Base Vendor schema."""

    name: str = Field(..., min_length=1, max_length=200, description="Legal name")
    display_name: Optional[str] = Field(None, max_length=200, description="Trade/Display name")
    vendor_type: str = Field(default="SUPPLIER", description="Type: SUPPLIER/CONTRACTOR/SERVICE_PROVIDER/OTHERS")

    # Tax & Compliance
    pan: Optional[str] = Field(None, max_length=10, description="PAN number")
    gstin: Optional[str] = Field(None, max_length=15, description="GSTIN")
    gst_registration_type: Optional[str] = Field(None, description="GST registration type")
    msme_registered: bool = Field(default=False)
    msme_number: Optional[str] = Field(None, max_length=20)
    tds_applicable: bool = Field(default=True)
    tds_section_id: Optional[UUID] = None
    tds_rate_override: Optional[Decimal] = Field(None, ge=0, le=100)

    # Contact & Address
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="India", max_length=50)

    # Banking Details
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    payment_mode_preference: Optional[str] = Field(None, description="CHEQUE/NEFT/RTGS/UPI/CASH")

    # Financial Settings
    control_account_id: Optional[UUID] = None
    expense_account_id: Optional[UUID] = None
    payment_terms_id: Optional[UUID] = None
    credit_days: int = Field(default=30, ge=0, le=365)
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency_code: str = Field(default="INR", max_length=3)

    # Balances
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    opening_balance_type: Optional[str] = Field(None, description="DR/CR")

    # Remarks
    remarks: Optional[str] = None

    @field_validator('pan')
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper().strip()
            if len(v) != 10:
                raise ValueError('PAN must be 10 characters')
        return v

    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper().strip()
            if len(v) != 15:
                raise ValueError('GSTIN must be 15 characters')
        return v


class VendorCreate(VendorBase):
    """Schema for creating a vendor."""

    code: str = Field(..., min_length=1, max_length=20, description="Vendor code")
    organization_id: UUID = Field(..., description="Organization ID")


class VendorUpdate(BaseSchema):
    """Schema for updating a vendor."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    vendor_type: Optional[str] = None

    # Tax & Compliance
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    gst_registration_type: Optional[str] = None
    msme_registered: Optional[bool] = None
    msme_number: Optional[str] = Field(None, max_length=20)
    tds_applicable: Optional[bool] = None
    tds_section_id: Optional[UUID] = None
    tds_rate_override: Optional[Decimal] = Field(None, ge=0, le=100)

    # Contact & Address
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=50)

    # Banking Details
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    payment_mode_preference: Optional[str] = None

    # Financial Settings
    control_account_id: Optional[UUID] = None
    expense_account_id: Optional[UUID] = None
    payment_terms_id: Optional[UUID] = None
    credit_days: Optional[int] = Field(None, ge=0, le=365)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    currency_code: Optional[str] = Field(None, max_length=3)

    # Balances
    opening_balance: Optional[Decimal] = Field(None, ge=0)
    opening_balance_type: Optional[str] = None

    # Remarks
    remarks: Optional[str] = None

    # Status
    is_active: Optional[bool] = None


class VendorResponse(MaskedPIIModel, VendorBase):
    """Vendor response schema."""

    id: UUID
    code: str
    organization_id: UUID
    current_balance: Decimal = Decimal("0.00")
    current_balance_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class VendorListResponse(BaseSchema):
    """Vendor list item response schema."""

    id: UUID
    code: str
    name: str
    display_name: Optional[str] = None
    vendor_type: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    current_balance: Decimal = Decimal("0.00")
    current_balance_type: Optional[str] = None
    is_active: bool = True
