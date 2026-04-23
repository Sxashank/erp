"""Vendor Portal Authentication Schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, EmailStr

from app.schemas.base import BaseSchema
from app.models.vendor_portal.enums import VendorPortalUserStatus, VendorOTPPurpose


class VendorLoginRequest(BaseSchema):
    """Vendor login request."""

    email: EmailStr
    password: Optional[str] = None
    otp: Optional[str] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None


class VendorLoginResponse(BaseSchema):
    """Vendor login response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "VendorUserProfile"


class VendorOTPRequest(BaseSchema):
    """Request OTP for vendor portal."""

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    purpose: VendorOTPPurpose = VendorOTPPurpose.LOGIN


class VendorOTPVerify(BaseSchema):
    """Verify OTP for vendor portal."""

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    otp: str = Field(..., min_length=4, max_length=10)
    purpose: VendorOTPPurpose = VendorOTPPurpose.LOGIN


class VendorPasswordReset(BaseSchema):
    """Password reset request."""

    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8)


class VendorTokenRefresh(BaseSchema):
    """Token refresh request."""

    refresh_token: str


class VendorUserProfile(BaseSchema):
    """Vendor user profile response."""

    id: UUID
    vendor_id: UUID
    organization_id: UUID
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    is_primary_contact: bool
    status: VendorPortalUserStatus

    # Permissions
    can_view_pos: bool
    can_acknowledge_pos: bool
    can_submit_invoices: bool
    can_create_asn: bool
    can_view_payments: bool
    can_manage_users: bool
    can_manage_compliance: bool

    # Vendor Info (populated from vendor master)
    vendor_name: Optional[str] = None
    vendor_code: Optional[str] = None

    email_verified: bool
    phone_verified: bool
    last_login_at: Optional[datetime] = None


class VendorUserProfileUpdate(BaseSchema):
    """Vendor user profile update."""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=5)
    notification_preferences: Optional[dict] = None


class VendorPasswordChange(BaseSchema):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


# Aliases for route compatibility
VendorOTPVerifyRequest = VendorOTPVerify
VendorPasswordResetRequest = VendorPasswordReset
VendorChangePasswordRequest = VendorPasswordChange
VendorRefreshTokenRequest = VendorTokenRefresh


# Fix forward references
VendorLoginResponse.model_rebuild()
