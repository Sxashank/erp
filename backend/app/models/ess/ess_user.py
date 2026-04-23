"""ESS Portal User and Session models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.ess.enums import (
    ESSUserStatus,
    ProfileUpdateType,
    ProfileUpdateStatus,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee
    from app.models.ess.reimbursement import ReimbursementClaim
    from app.models.ess.helpdesk import HelpdeskTicket
    from app.models.ess.it_declaration import ITDeclaration


class ESSUser(BaseModel):
    """ESS Portal user linked to employee."""

    __tablename__ = "ess_user"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "employee_id", name="uq_ess_user_org_employee"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link to Employee
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Authentication
    mobile: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_mobile_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Password (optional - primarily OTP based)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)

    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Security
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ESSUserStatus, name="ess_user_status_enum", create_type=False),
        default=ESSUserStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", lazy="selectin"
    )
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="selectin"
    )
    sessions: Mapped[List["ESSSession"]] = relationship(
        "ESSSession", back_populates="ess_user", lazy="selectin"
    )
    devices: Mapped[List["ESSDevice"]] = relationship(
        "ESSDevice", back_populates="ess_user", lazy="selectin"
    )
    reimbursement_claims: Mapped[List["ReimbursementClaim"]] = relationship(
        "ReimbursementClaim", lazy="selectin"
    )
    helpdesk_tickets: Mapped[List["HelpdeskTicket"]] = relationship(
        "HelpdeskTicket", lazy="selectin"
    )
    it_declarations: Mapped[List["ITDeclaration"]] = relationship(
        "ITDeclaration", lazy="selectin"
    )
    profile_update_requests: Mapped[List["ProfileUpdateRequest"]] = relationship(
        "ProfileUpdateRequest", lazy="selectin"
    )


class ESSSession(BaseModel):
    """ESS Portal active sessions."""

    __tablename__ = "ess_session"

    # User Reference
    ess_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Details
    session_token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Device Info
    device_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_device.id", ondelete="SET NULL"),
        nullable=True,
    )
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mobile, web, tablet
    device_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    os_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Location
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Timestamps
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="sessions", lazy="selectin"
    )
    device: Mapped[Optional["ESSDevice"]] = relationship(
        "ESSDevice", back_populates="sessions", lazy="selectin"
    )


class ESSDevice(BaseModel):
    """ESS Portal registered devices."""

    __tablename__ = "ess_device"

    # User Reference
    ess_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Device Identification
    device_uuid: Mapped[str] = mapped_column(String(100), nullable=False)
    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mobile, web, tablet

    # Device Details
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Push Notifications
    fcm_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    apns_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Trust
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Last Activity
    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="devices", lazy="selectin"
    )
    sessions: Mapped[List["ESSSession"]] = relationship(
        "ESSSession", back_populates="device", lazy="selectin"
    )


class ESSOTP(BaseModel):
    """OTP management for ESS Portal."""

    __tablename__ = "ess_otp"

    # User Reference
    ess_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # OTP Target (for registration before user exists)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OTP Details
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    otp_type: Mapped[str] = mapped_column(String(20), nullable=False)  # LOGIN, REGISTRATION, RESET, VERIFY
    purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Validity
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Attempts
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)


class ProfileUpdateRequest(BaseModel):
    """Profile update requests from ESS Portal."""

    __tablename__ = "ess_profile_update_request"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User Reference
    ess_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee Reference
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request Details
    request_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    update_type: Mapped[str] = mapped_column(
        SQLEnum(ProfileUpdateType, name="profile_update_type_enum", create_type=False),
        nullable=False,
    )

    # Changes
    current_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    requested_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Supporting Documents
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Approval
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("auth_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewer_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ProfileUpdateStatus, name="profile_update_status_enum", create_type=False),
        default=ProfileUpdateStatus.PENDING,
        nullable=False,
    )

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="profile_update_requests", lazy="selectin"
    )
