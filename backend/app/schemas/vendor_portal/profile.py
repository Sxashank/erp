"""Vendor Profile Schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, EmailStr

from app.schemas.base import BaseSchema
from app.core.pii import MaskedPIIModel
from app.models.vendor_portal.enums import VendorPortalUserStatus


class VendorProfileResponse(MaskedPIIModel, BaseSchema):
    """Vendor profile response."""

    # Vendor Master Info
    id: UUID
    code: str
    name: str
    display_name: Optional[str] = None
    vendor_type: str

    # Tax Info
    pan: Optional[str] = None
    gstin: Optional[str] = None
    msme_registered: bool
    msme_number: Optional[str] = None
    msme_type: Optional[str] = None

    # Contact
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    pincode: Optional[str] = None
    country: str

    # Financial
    credit_days: int
    credit_limit: Decimal
    current_balance: Decimal
    current_balance_type: Optional[str] = None

    # Bank Accounts
    bank_accounts: List["VendorBankAccountResponse"] = []

    # Portal Users
    portal_users: List["VendorUserResponse"] = []


class VendorProfileUpdate(BaseSchema):
    """Update vendor profile."""

    display_name: Optional[str] = Field(None, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)


class VendorBankAccountCreate(BaseSchema):
    """Create bank account."""

    bank_name: str = Field(..., max_length=100)
    bank_branch: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    account_holder_name: Optional[str] = Field(None, max_length=200)
    is_primary: bool = False


class VendorBankAccountUpdate(BaseSchema):
    """Update bank account."""

    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    ifsc_code: Optional[str] = Field(None, max_length=11)
    account_holder_name: Optional[str] = Field(None, max_length=200)
    is_primary: Optional[bool] = None


class VendorBankAccountResponse(MaskedPIIModel, BaseSchema):
    """Bank account response."""

    id: UUID
    bank_name: str
    bank_branch: str
    account_number: str
    ifsc_code: str
    account_holder_name: Optional[str] = None
    is_primary: bool
    is_verified: bool
    verified_at: Optional[datetime] = None


class VendorContactCreate(BaseSchema):
    """Create vendor contact."""

    name: str = Field(..., max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False


class VendorContactUpdate(BaseSchema):
    """Update vendor contact."""

    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None


class VendorContactResponse(BaseSchema):
    """Vendor contact response."""

    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool
    created_at: datetime


class VendorUserCreate(BaseSchema):
    """Create portal user invitation."""

    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)

    # Permissions
    can_view_pos: bool = True
    can_acknowledge_pos: bool = False
    can_submit_invoices: bool = False
    can_create_asn: bool = False
    can_view_payments: bool = True
    can_manage_users: bool = False
    can_manage_compliance: bool = False


class VendorUserUpdate(BaseSchema):
    """Update portal user."""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    status: Optional[VendorPortalUserStatus] = None

    # Permissions
    can_view_pos: Optional[bool] = None
    can_acknowledge_pos: Optional[bool] = None
    can_submit_invoices: Optional[bool] = None
    can_create_asn: Optional[bool] = None
    can_view_payments: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_manage_compliance: Optional[bool] = None


class VendorUserResponse(BaseSchema):
    """Portal user response."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    is_primary_contact: bool
    status: VendorPortalUserStatus
    email_verified: bool
    phone_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    # Permissions
    can_view_pos: bool
    can_acknowledge_pos: bool
    can_submit_invoices: bool
    can_create_asn: bool
    can_view_payments: bool
    can_manage_users: bool
    can_manage_compliance: bool


class PortalUserPermissions(BaseSchema):
    """Portal user permissions update."""

    can_view_pos: Optional[bool] = None
    can_acknowledge_pos: Optional[bool] = None
    can_submit_invoices: Optional[bool] = None
    can_create_asn: Optional[bool] = None
    can_view_payments: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_manage_compliance: Optional[bool] = None


# Aliases for backward compatibility
PortalUserCreate = VendorUserCreate
PortalUserUpdate = VendorUserUpdate
PortalUserResponse = VendorUserResponse


class PortalUserListResponse(BaseSchema):
    """Portal user list response."""

    total: int
    users: List[VendorUserResponse] = []


# Fix forward references
VendorProfileResponse.model_rebuild()
