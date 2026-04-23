"""Portal User Models.

Handles customer portal authentication and session management.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.portal.enums import (
    PortalUserStatus,
    DeviceType,
    OTPPurpose,
    ConsentType,
)


class PortalUser(BaseModel):
    """Customer portal user.

    Supports OTP-based authentication without passwords.
    Linked to customer master for loan information.
    """

    __tablename__ = "portal_user"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_customer.id"),
        nullable=False,
        index=True,
    )

    # Contact Info (used for OTP)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    mobile_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mobile_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # User Status
    status: Mapped[PortalUserStatus] = mapped_column(
        default=PortalUserStatus.ACTIVE
    )
    status_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    notification_preferences: Mapped[Optional[str]] = mapped_column(
        Text
    )  # JSON: {sms: true, email: true, push: true}

    # Login tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    last_login_device: Mapped[Optional[str]] = mapped_column(String(50))
    login_count: Mapped[int] = mapped_column(default=0)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    sessions: Mapped[List["PortalSession"]] = relationship(
        "PortalSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    devices: Mapped[List["PortalDevice"]] = relationship(
        "PortalDevice",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    consents: Mapped[List["PortalConsent"]] = relationship(
        "PortalConsent",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_user_org_customer", "organization_id", "customer_id"),
        Index("ix_portal_user_org_mobile", "organization_id", "mobile"),
    )


class PortalSession(BaseModel):
    """Active portal sessions.

    Tracks active login sessions with device info.
    """

    __tablename__ = "portal_session"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Token
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Session Info
    device_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("portal_device.id")
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    logout_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    logout_reason: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    user: Mapped["PortalUser"] = relationship(
        "PortalUser", back_populates="sessions"
    )

    __table_args__ = (
        Index("ix_portal_session_token", "session_token"),
        Index("ix_portal_session_user_active", "user_id", "is_active"),
    )


class PortalDevice(BaseModel):
    """Registered devices for portal access.

    Tracks devices used to access the portal.
    """

    __tablename__ = "portal_device"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Device Info
    device_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Unique device identifier
    device_type: Mapped[DeviceType] = mapped_column(nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    device_model: Mapped[Optional[str]] = mapped_column(String(100))
    os_version: Mapped[Optional[str]] = mapped_column(String(50))
    app_version: Mapped[Optional[str]] = mapped_column(String(20))

    # Push Notifications
    fcm_token: Mapped[Optional[str]] = mapped_column(Text)
    apns_token: Mapped[Optional[str]] = mapped_column(Text)

    # Trust Status
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Activity
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    login_count: Mapped[int] = mapped_column(default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    blocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    block_reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    user: Mapped["PortalUser"] = relationship(
        "PortalUser", back_populates="devices"
    )

    __table_args__ = (
        Index("ix_portal_device_user_device", "user_id", "device_id"),
    )


class PortalOTP(BaseModel):
    """OTP management for portal authentication.

    Handles OTP generation, validation, and expiry.
    """

    __tablename__ = "portal_otp"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Target (mobile or email)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # OTP Details
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    otp_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Hashed OTP for validation
    purpose: Mapped[OTPPurpose] = mapped_column(nullable=False)

    # Reference (for payment OTP etc.)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[UUID]] = mapped_column()

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)

    # Delivery
    sent_via: Mapped[str] = mapped_column(String(20), default="SMS")  # SMS, EMAIL
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50))
    delivery_vendor_ref: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_portal_otp_mobile_purpose", "mobile", "purpose"),
        Index("ix_portal_otp_email_purpose", "email", "purpose"),
    )


class PortalConsent(BaseModel):
    """Customer consent tracking.

    Records consent for terms, privacy, marketing, etc.
    """

    __tablename__ = "portal_consent"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Consent Details
    consent_type: Mapped[ConsentType] = mapped_column(nullable=False)
    consent_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Version of T&C/policy

    # Status
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Capture Info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    capture_method: Mapped[str] = mapped_column(
        String(50), default="PORTAL"
    )  # PORTAL, MOBILE_APP, API

    # Relationships
    user: Mapped["PortalUser"] = relationship(
        "PortalUser", back_populates="consents"
    )

    __table_args__ = (
        Index("ix_portal_consent_user_type", "user_id", "consent_type"),
    )
