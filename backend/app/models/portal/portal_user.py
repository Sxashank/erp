"""Portal User Models.

Handles customer portal authentication and session management.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.portal.enums import (
    ConsentType,
    DeviceType,
    OTPPurpose,
    PortalActorRole,
    PortalRegistrationStatus,
    PortalUserStatus,
)

if TYPE_CHECKING:
    from app.models.portal.portal_user_entity import PortalUserEntity


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

    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("mst_customer.id"),
        nullable=True,
        index=True,
    )

    # Borrower-portal registration lifecycle.
    # ACTIVE for legacy customer-portal rows (back-compat default in the
    # alembic migration); PENDING_APPROVAL / REJECTED used by borrower
    # registration (WI-2). ``get_portal_user`` rejects any session whose
    # user is not ACTIVE.
    registration_status: Mapped[PortalRegistrationStatus] = mapped_column(
        SAEnum(
            PortalRegistrationStatus,
            name="portal_registration_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=PortalRegistrationStatus.ACTIVE,
        nullable=False,
    )

    # Self-asserted IDs captured at registration time. None of these are
    # trusted until an admin verifies them; they are kept on the user
    # row so the admin-review screen can render the request without
    # rejoining anywhere.
    registration_requested_pan: Mapped[str | None] = mapped_column(String(20))
    registration_requested_cin: Mapped[str | None] = mapped_column(String(30))
    registration_requested_gstin: Mapped[str | None] = mapped_column(String(20))
    registration_requested_llpin: Mapped[str | None] = mapped_column(String(20))
    registration_requested_loan_account_number: Mapped[str | None] = mapped_column(String(80))
    registration_requested_sanctioned_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2)
    )
    registration_authorized_signatory_name: Mapped[str | None] = mapped_column(String(200))

    registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500))

    # Auto-generated REG/{YYYY}/{NNNNNN}. Unique so the unauth status
    # endpoint can look it up by (reference, mobile).
    registration_reference: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
    )

    # Contact Info (used for OTP)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    mobile_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mobile_verified_at: Mapped[datetime | None] = mapped_column(DateTime)

    email: Mapped[str | None] = mapped_column(String(255), index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime)

    # User Status — stored as VARCHAR (DB has no PG ENUM type for this);
    # python-side enum coerces on read/write.
    status: Mapped[PortalUserStatus] = mapped_column(
        String(20),
        default=PortalUserStatus.ACTIVE.value,
    )
    status_reason: Mapped[str | None] = mapped_column(String(500))
    actor_role: Mapped[PortalActorRole] = mapped_column(
        String(50),
        default=PortalActorRole.SCHEME_BORROWER.value,
        nullable=False,
    )

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    notification_preferences: Mapped[str | None] = mapped_column(
        Text
    )  # JSON: {sms: true, email: true, push: true}

    # Login tracking
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_login_ip: Mapped[str | None] = mapped_column(String(45))
    last_login_device: Mapped[str | None] = mapped_column(String(50))
    login_count: Mapped[int] = mapped_column(default=0)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(100))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invited_by: Mapped[UUID | None] = mapped_column(
        SAUUID(),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    invite_token_hash: Mapped[str | None] = mapped_column(String(255))
    invite_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reset_token_hash: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    sessions: Mapped[list[PortalSession]] = relationship(
        "PortalSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    devices: Mapped[list[PortalDevice]] = relationship(
        "PortalDevice",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    consents: Mapped[list[PortalConsent]] = relationship(
        "PortalConsent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # Borrower-portal: many lending entities per portal user.
    entities: Mapped[list[PortalUserEntity]] = relationship(
        "PortalUserEntity",
        back_populates="portal_user",
        cascade="all, delete-orphan",
        foreign_keys="PortalUserEntity.portal_user_id",
        lazy="selectin",
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
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Session Info
    device_id: Mapped[UUID | None] = mapped_column(ForeignKey("portal_device.id"))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    logout_at: Mapped[datetime | None] = mapped_column(DateTime)
    logout_reason: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    user: Mapped[PortalUser] = relationship("PortalUser", back_populates="sessions")

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
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Unique device identifier
    device_type: Mapped[DeviceType] = mapped_column(String(20), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(100))
    device_model: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(50))
    app_version: Mapped[str | None] = mapped_column(String(20))

    # Push Notifications
    fcm_token: Mapped[str | None] = mapped_column(Text)
    apns_token: Mapped[str | None] = mapped_column(Text)

    # Trust Status
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Activity
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    login_count: Mapped[int] = mapped_column(default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime)
    block_reason: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    user: Mapped[PortalUser] = relationship("PortalUser", back_populates="devices")

    __table_args__ = (Index("ix_portal_device_user_device", "user_id", "device_id"),)


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
    mobile: Mapped[str | None] = mapped_column(String(15), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)

    # OTP Details
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # Hashed OTP for validation
    purpose: Mapped[OTPPurpose] = mapped_column(String(30), nullable=False)

    # Reference (for payment OTP etc.)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[UUID | None] = mapped_column()

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)

    # Delivery
    sent_via: Mapped[str] = mapped_column(String(20), default="SMS")  # SMS, EMAIL
    delivery_status: Mapped[str | None] = mapped_column(String(50))
    delivery_vendor_ref: Mapped[str | None] = mapped_column(String(100))

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
    consent_type: Mapped[ConsentType] = mapped_column(String(40), nullable=False)
    consent_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Version of T&C/policy

    # Status
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    revocation_reason: Mapped[str | None] = mapped_column(String(500))

    # Capture Info
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    capture_method: Mapped[str] = mapped_column(
        String(50), default="PORTAL"
    )  # PORTAL, MOBILE_APP, API

    # Relationships
    user: Mapped[PortalUser] = relationship("PortalUser", back_populates="consents")

    __table_args__ = (Index("ix_portal_consent_user_type", "user_id", "consent_type"),)
