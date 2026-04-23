"""Notification module models."""

from app.models.notification.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationCategory,
    Notification,
    NotificationPreference,
    NotificationLog,
)

from app.models.notification.template import (
    NotificationTemplateType,
    NotificationTemplate as SysNotificationTemplate,
    NotificationTemplateVariable,
)

__all__ = [
    # Enums
    "NotificationChannel",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationCategory",
    "NotificationTemplateType",
    # Models
    "Notification",
    "NotificationPreference",
    "NotificationLog",
    "SysNotificationTemplate",
    "NotificationTemplateVariable",
]
