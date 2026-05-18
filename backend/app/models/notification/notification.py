"""Notification models for system-wide notifications."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationCategory(str, enum.Enum):
    """Notification categories for grouping."""
    SYSTEM = "system"
    WORKFLOW = "workflow"
    LOAN = "loan"
    PAYMENT = "payment"
    COLLECTION = "collection"
    REMINDER = "reminder"
    ALERT = "alert"
    ANNOUNCEMENT = "announcement"
    MARKETING = "marketing"


class Notification(BaseModel):
    """System-wide notification record."""

    __tablename__ = "sys_notification"
    __table_args__ = (
        Index("ix_sys_notification_org_user", "organization_id", "user_id"),
        Index("ix_sys_notification_entity", "entity_type", "entity_id"),
    )

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Recipient
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Target user for the notification",
    )

    # External recipients (for non-user notifications)
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Template reference
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_notification_template.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, native_enum=False),
        default=NotificationCategory.SYSTEM,
        nullable=False,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, native_enum=False),
        default=NotificationPriority.MEDIUM,
        nullable=False,
    )

    # Delivery channels
    channels: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        default=["in_app"],
        nullable=False,
    )

    # Status
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Tracking
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Entity reference (e.g., loan, voucher, etc.)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    entity_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Action URL
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Retry handling
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="selectin")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    logs = relationship("NotificationLog", back_populates="notification", lazy="dynamic")


class NotificationPreference(BaseModel):
    """User notification preferences."""

    __tablename__ = "sys_notification_preference"
    __table_args__ = (
        Index(
            "ix_sys_notification_preference_user_org_category",
            "user_id",
            "organization_id",
            "category",
            unique=True,
        ),
    )

    # User reference
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Organization scope (preferences can differ by org)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Category preferences
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, native_enum=False),
        nullable=False,
    )

    # Channel preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Frequency/timing preferences
    digest_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="If true, batch notifications into digest",
    )
    digest_frequency: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="daily, weekly, etc.",
    )
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Start of quiet hours (HH:MM format)",
    )
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="End of quiet hours (HH:MM format)",
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="selectin")


class NotificationLog(BaseModel):
    """Notification delivery log for tracking."""

    __tablename__ = "sys_notification_log"

    # Notification reference
    notification_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sys_notification.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Delivery attempt details
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False),
        nullable=False,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False),
        nullable=False,
    )

    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Response details
    response_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    response_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Provider info
    provider: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="SMS gateway, email provider, etc.",
    )
    provider_message_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="External provider's message ID",
    )

    # Cost tracking
    cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # Additional metadata
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    notification = relationship("Notification", back_populates="logs")
