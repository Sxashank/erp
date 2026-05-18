"""Customer schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.core.pii import MaskedPIIModel
from app.schemas.base import CamelSchema


class CustomerBase(CamelSchema):
    """Base customer schema."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    display_name: str | None = Field(None, max_length=200)
    customer_type: str = Field(default="COMPANY")
    organization_id: UUID

    # Tax & Compliance
    pan: str | None = Field(None, max_length=10)
    gstin: str | None = Field(None, max_length=15)
    gst_registration_type: str | None = None
    place_of_supply_state: str | None = Field(None, max_length=2)
    tcs_applicable: bool = False
    tcs_section_id: UUID | None = None

    # Contact & Billing Address
    contact_person: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    mobile: str | None = Field(None, max_length=20)
    billing_address_line1: str | None = Field(None, max_length=200)
    billing_address_line2: str | None = Field(None, max_length=200)
    billing_city: str | None = Field(None, max_length=100)
    billing_state_code: str | None = Field(None, max_length=2)
    billing_pincode: str | None = Field(None, max_length=10)
    billing_country: str = Field(default="India", max_length=50)

    # Shipping Address
    shipping_address_line1: str | None = Field(None, max_length=200)
    shipping_address_line2: str | None = Field(None, max_length=200)
    shipping_city: str | None = Field(None, max_length=100)
    shipping_state_code: str | None = Field(None, max_length=2)
    shipping_pincode: str | None = Field(None, max_length=10)
    shipping_country: str = Field(default="India", max_length=50)

    # Banking Details
    bank_name: str | None = Field(None, max_length=100)
    bank_account_number: str | None = Field(None, max_length=50)
    bank_ifsc_code: str | None = Field(None, max_length=11)
    bank_branch: str | None = Field(None, max_length=100)
    payment_mode_preference: str | None = None

    # Financial Settings
    control_account_id: UUID | None = None
    revenue_account_id: UUID | None = None
    payment_terms_id: UUID | None = None
    credit_days: int = Field(default=30, ge=0)
    credit_limit: Decimal | None = None
    credit_limit_enabled: bool = False
    currency_code: str = Field(default="INR", max_length=3)

    # Balances
    opening_balance: Decimal = Field(default=Decimal("0"))
    opening_balance_type: str | None = None

    # Notes
    remarks: str | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerUpdate(CamelSchema):
    """Schema for updating a customer."""
    name: str | None = Field(None, max_length=200)
    display_name: str | None = Field(None, max_length=200)
    customer_type: str | None = None

    # Tax & Compliance
    pan: str | None = Field(None, max_length=10)
    gstin: str | None = Field(None, max_length=15)
    gst_registration_type: str | None = None
    place_of_supply_state: str | None = Field(None, max_length=2)
    tcs_applicable: bool | None = None
    tcs_section_id: UUID | None = None

    # Contact & Billing Address
    contact_person: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    mobile: str | None = Field(None, max_length=20)
    billing_address_line1: str | None = Field(None, max_length=200)
    billing_address_line2: str | None = Field(None, max_length=200)
    billing_city: str | None = Field(None, max_length=100)
    billing_state_code: str | None = Field(None, max_length=2)
    billing_pincode: str | None = Field(None, max_length=10)
    billing_country: str | None = Field(None, max_length=50)

    # Shipping Address
    shipping_address_line1: str | None = Field(None, max_length=200)
    shipping_address_line2: str | None = Field(None, max_length=200)
    shipping_city: str | None = Field(None, max_length=100)
    shipping_state_code: str | None = Field(None, max_length=2)
    shipping_pincode: str | None = Field(None, max_length=10)
    shipping_country: str | None = Field(None, max_length=50)

    # Banking Details
    bank_name: str | None = Field(None, max_length=100)
    bank_account_number: str | None = Field(None, max_length=50)
    bank_ifsc_code: str | None = Field(None, max_length=11)
    bank_branch: str | None = Field(None, max_length=100)
    payment_mode_preference: str | None = None

    # Financial Settings
    control_account_id: UUID | None = None
    revenue_account_id: UUID | None = None
    payment_terms_id: UUID | None = None
    credit_days: int | None = Field(None, ge=0)
    credit_limit: Decimal | None = None
    credit_limit_enabled: bool | None = None
    currency_code: str | None = Field(None, max_length=3)

    # Balances
    opening_balance: Decimal | None = None
    opening_balance_type: str | None = None

    # Notes
    remarks: str | None = None
    is_active: bool | None = None


class CustomerResponse(MaskedPIIModel):
    """Schema for customer response."""
    id: UUID
    code: str
    name: str
    display_name: str | None
    customer_type: str | None
    organization_id: UUID

    # Tax & Compliance
    pan: str | None
    gstin: str | None
    gst_registration_type: str | None
    place_of_supply_state: str | None
    tcs_applicable: bool
    tcs_section_id: UUID | None

    # Contact & Billing Address
    contact_person: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    billing_address_line1: str | None
    billing_address_line2: str | None
    billing_city: str | None
    billing_state_code: str | None
    billing_pincode: str | None
    billing_country: str

    # Shipping Address
    shipping_address_line1: str | None
    shipping_address_line2: str | None
    shipping_city: str | None
    shipping_state_code: str | None
    shipping_pincode: str | None
    shipping_country: str

    # Banking Details
    bank_name: str | None
    bank_account_number: str | None
    bank_ifsc_code: str | None
    bank_branch: str | None
    payment_mode_preference: str | None

    # Financial Settings
    control_account_id: UUID | None
    revenue_account_id: UUID | None
    payment_terms_id: UUID | None
    credit_days: int
    credit_limit: Decimal | None
    credit_limit_enabled: bool
    currency_code: str

    # Balances
    opening_balance: Decimal
    opening_balance_type: str | None
    current_balance: Decimal
    current_balance_type: str | None

    # Notes
    remarks: str | None

    # Audit
    created_at: datetime
    updated_at: datetime | None
    is_active: bool


class CustomerListResponse(CamelSchema):
    """Schema for customer list response (lighter)."""
    id: UUID
    code: str
    name: str
    display_name: str | None
    customer_type: str | None
    gstin: str | None
    pan: str | None
    billing_city: str | None
    billing_state_code: str | None
    current_balance: Decimal
    current_balance_type: str | None
    is_active: bool
