"""Notification template models."""

import enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.notification.notification import NotificationCategory, NotificationChannel


class NotificationTemplateType(str, enum.Enum):
    """Template types for different purposes."""
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    SYSTEM = "system"
    REMINDER = "reminder"
    ALERT = "alert"


class NotificationTemplate(BaseModel):
    """Notification template for reusable notification content."""

    __tablename__ = "mst_notification_template"

    # Organization scope (null = global template)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Template identification
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Unique template code for reference",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template type and category
    template_type: Mapped[NotificationTemplateType] = mapped_column(
        Enum(NotificationTemplateType),
        default=NotificationTemplateType.TRANSACTIONAL,
        nullable=False,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory),
        default=NotificationCategory.SYSTEM,
        nullable=False,
    )

    # Supported channels
    channels: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        default=["email", "in_app"],
        nullable=False,
    )

    # Email template
    email_subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SMS template
    sms_body: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="SMS content (max ~160 chars for single SMS)",
    )

    # Push notification template
    push_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    push_body: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    push_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # In-app notification template
    in_app_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    in_app_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # WhatsApp template (for approved templates)
    whatsapp_template_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="WhatsApp Business API template ID",
    )
    whatsapp_template_params: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="Parameter names for WhatsApp template",
    )

    # Template variables
    variables: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="List of variable placeholders used in template",
    )

    # Default values for variables
    default_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Default values for template variables",
    )

    # Trigger configuration
    trigger_event: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Event that triggers this notification",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    organization = relationship("Organization", lazy="selectin")
    variable_definitions = relationship(
        "NotificationTemplateVariable",
        back_populates="template",
        lazy="selectin",
    )


class NotificationTemplateVariable(BaseModel):
    """Variable definitions for notification templates."""

    __tablename__ = "mst_notification_template_variable"

    # Template reference
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_notification_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Variable details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Variable name (e.g., customer_name)",
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human readable name",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Data type
    data_type: Mapped[str] = mapped_column(
        String(50),
        default="string",
        nullable=False,
        comment="string, number, date, currency, etc.",
    )

    # Formatting
    format_pattern: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Format pattern (e.g., date format, currency format)",
    )

    # Default value
    default_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Validation
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_regex: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Sample value for preview
    sample_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Ordering
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    template = relationship("NotificationTemplate", back_populates="variable_definitions")
