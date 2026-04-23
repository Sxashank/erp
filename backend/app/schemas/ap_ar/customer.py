"""Customer schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.pii import MaskedPIIModel


class CustomerBase(BaseModel):
    """Base customer schema."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    customer_type: str = Field(default="COMPANY")
    organization_id: UUID

    # Tax & Compliance
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    gst_registration_type: Optional[str] = None
    place_of_supply_state: Optional[str] = Field(None, max_length=2)
    tcs_applicable: bool = False
    tcs_section_id: Optional[UUID] = None

    # Contact & Billing Address
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    billing_address_line1: Optional[str] = Field(None, max_length=200)
    billing_address_line2: Optional[str] = Field(None, max_length=200)
    billing_city: Optional[str] = Field(None, max_length=100)
    billing_state_code: Optional[str] = Field(None, max_length=2)
    billing_pincode: Optional[str] = Field(None, max_length=10)
    billing_country: str = Field(default="India", max_length=50)

    # Shipping Address
    shipping_address_line1: Optional[str] = Field(None, max_length=200)
    shipping_address_line2: Optional[str] = Field(None, max_length=200)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state_code: Optional[str] = Field(None, max_length=2)
    shipping_pincode: Optional[str] = Field(None, max_length=10)
    shipping_country: str = Field(default="India", max_length=50)

    # Banking Details
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    payment_mode_preference: Optional[str] = None

    # Financial Settings
    control_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None
    payment_terms_id: Optional[UUID] = None
    credit_days: int = Field(default=30, ge=0)
    credit_limit: Optional[Decimal] = None
    credit_limit_enabled: bool = False
    currency_code: str = Field(default="INR", max_length=3)

    # Balances
    opening_balance: Decimal = Field(default=Decimal("0"))
    opening_balance_type: Optional[str] = None

    # Notes
    remarks: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    name: Optional[str] = Field(None, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    customer_type: Optional[str] = None

    # Tax & Compliance
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    gst_registration_type: Optional[str] = None
    place_of_supply_state: Optional[str] = Field(None, max_length=2)
    tcs_applicable: Optional[bool] = None
    tcs_section_id: Optional[UUID] = None

    # Contact & Billing Address
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    billing_address_line1: Optional[str] = Field(None, max_length=200)
    billing_address_line2: Optional[str] = Field(None, max_length=200)
    billing_city: Optional[str] = Field(None, max_length=100)
    billing_state_code: Optional[str] = Field(None, max_length=2)
    billing_pincode: Optional[str] = Field(None, max_length=10)
    billing_country: Optional[str] = Field(None, max_length=50)

    # Shipping Address
    shipping_address_line1: Optional[str] = Field(None, max_length=200)
    shipping_address_line2: Optional[str] = Field(None, max_length=200)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state_code: Optional[str] = Field(None, max_length=2)
    shipping_pincode: Optional[str] = Field(None, max_length=10)
    shipping_country: Optional[str] = Field(None, max_length=50)

    # Banking Details
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    payment_mode_preference: Optional[str] = None

    # Financial Settings
    control_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None
    payment_terms_id: Optional[UUID] = None
    credit_days: Optional[int] = Field(None, ge=0)
    credit_limit: Optional[Decimal] = None
    credit_limit_enabled: Optional[bool] = None
    currency_code: Optional[str] = Field(None, max_length=3)

    # Balances
    opening_balance: Optional[Decimal] = None
    opening_balance_type: Optional[str] = None

    # Notes
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(MaskedPIIModel, BaseModel):
    """Schema for customer response."""
    id: UUID
    code: str
    name: str
    display_name: Optional[str]
    customer_type: Optional[str]
    organization_id: UUID

    # Tax & Compliance
    pan: Optional[str]
    gstin: Optional[str]
    gst_registration_type: Optional[str]
    place_of_supply_state: Optional[str]
    tcs_applicable: bool
    tcs_section_id: Optional[UUID]

    # Contact & Billing Address
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    billing_address_line1: Optional[str]
    billing_address_line2: Optional[str]
    billing_city: Optional[str]
    billing_state_code: Optional[str]
    billing_pincode: Optional[str]
    billing_country: str

    # Shipping Address
    shipping_address_line1: Optional[str]
    shipping_address_line2: Optional[str]
    shipping_city: Optional[str]
    shipping_state_code: Optional[str]
    shipping_pincode: Optional[str]
    shipping_country: str

    # Banking Details
    bank_name: Optional[str]
    bank_account_number: Optional[str]
    bank_ifsc_code: Optional[str]
    bank_branch: Optional[str]
    payment_mode_preference: Optional[str]

    # Financial Settings
    control_account_id: Optional[UUID]
    revenue_account_id: Optional[UUID]
    payment_terms_id: Optional[UUID]
    credit_days: int
    credit_limit: Optional[Decimal]
    credit_limit_enabled: bool
    currency_code: str

    # Balances
    opening_balance: Decimal
    opening_balance_type: Optional[str]
    current_balance: Decimal
    current_balance_type: Optional[str]

    # Notes
    remarks: Optional[str]

    # Audit
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Schema for customer list response (lighter)."""
    id: UUID
    code: str
    name: str
    display_name: Optional[str]
    customer_type: Optional[str]
    gstin: Optional[str]
    pan: Optional[str]
    billing_city: Optional[str]
    billing_state_code: Optional[str]
    current_balance: Decimal
    current_balance_type: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
