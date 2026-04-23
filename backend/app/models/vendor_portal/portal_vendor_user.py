"""Vendor Portal User Models.

Handles vendor portal authentication and session management.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Index,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.vendor_portal.enums import (
    VendorPortalUserStatus,
    VendorOTPPurpose,
)

if TYPE_CHECKING:
    from app.models.ap_ar.vendor import Vendor


class PortalVendorUser(BaseModel):
    """Vendor portal user.

    Supports both OTP-based and password authentication.
    Linked to vendor master for AP/PO information access.
    """

    __tablename__ = "portal_vendor_user"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
        index=True,
    )

    # Contact Info (used for login)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    phone: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Authentication
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(100))

    # Role & Permissions
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_pos: Mapped[bool] = mapped_column(Boolean, default=True)
    can_acknowledge_pos: Mapped[bool] = mapped_column(Boolean, default=False)
    can_submit_invoices: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_asn: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_payments: Mapped[bool] = mapped_column(Boolean, default=True)
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_compliance: Mapped[bool] = mapped_column(Boolean, default=False)

    # User Status
    status: Mapped[VendorPortalUserStatus] = mapped_column(
        default=VendorPortalUserStatus.ACTIVE
    )
    status_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    notification_preferences: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # Login tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    last_login_device: Mapped[Optional[str]] = mapped_column(String(100))
    login_count: Mapped[int] = mapped_column(Integer, default=0)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )
    sessions: Mapped[List["PortalVendorSession"]] = relationship(
        "PortalVendorSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_vendor_user_org_vendor", "organization_id", "vendor_id"),
        Index("ix_portal_vendor_user_org_email", "organization_id", "email"),
    )

    @property
    def full_name(self) -> str:
        """Return full name."""
        return f"{self.first_name} {self.last_name}"


class PortalVendorSession(BaseModel):
    """Active vendor portal sessions.

    Tracks active login sessions with device info.
    """

    __tablename__ = "portal_vendor_session"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Token
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Session Info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    device_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Timestamps
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    logout_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    logout_reason: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    user: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser", back_populates="sessions"
    )

    __table_args__ = (
        Index("ix_portal_vendor_session_token", "session_token"),
        Index("ix_portal_vendor_session_user_active", "user_id", "is_active"),
    )


class PortalVendorOTP(BaseModel):
    """OTP management for vendor portal authentication.

    Handles OTP generation, validation, and expiry.
    """

    __tablename__ = "portal_vendor_otp"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Target (email or phone)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(15), index=True)

    # OTP Details
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[VendorOTPPurpose] = mapped_column(nullable=False)

    # Reference (for specific operations)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Delivery
    sent_via: Mapped[str] = mapped_column(String(20), default="EMAIL")  # EMAIL, SMS
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50))
    delivery_vendor_ref: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_portal_vendor_otp_email_purpose", "email", "purpose"),
        Index("ix_portal_vendor_otp_phone_purpose", "phone", "purpose"),
    )
