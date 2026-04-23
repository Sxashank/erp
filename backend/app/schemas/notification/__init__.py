"""Notification schemas."""

from app.schemas.notification.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationLogResponse,
    NotificationStatsResponse,
    MarkReadRequest,
    SendNotificationRequest,
    BulkNotificationRequest,
)

from app.schemas.notification.template import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    NotificationTemplateListResponse,
    TemplateVariableCreate,
    TemplateVariableResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)

__all__ = [
    # Notification schemas
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationPreferenceCreate",
    "NotificationPreferenceUpdate",
    "NotificationPreferenceResponse",
    "NotificationLogResponse",
    "NotificationStatsResponse",
    "MarkReadRequest",
    "SendNotificationRequest",
    "BulkNotificationRequest",
    # Template schemas
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "NotificationTemplateListResponse",
    "TemplateVariableCreate",
    "TemplateVariableResponse",
    "TemplatePreviewRequest",
    "TemplatePreviewResponse",
]
