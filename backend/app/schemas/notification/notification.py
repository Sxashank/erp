"""Notification schemas for API request/response."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationCategory,
)


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""

    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    html_content: Optional[str] = None

    user_id: Optional[UUID] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

    category: NotificationCategory = NotificationCategory.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[str] = Field(default=["in_app"])

    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    entity_reference: Optional[str] = None

    action_url: Optional[str] = None
    action_label: Optional[str] = None

    template_id: Optional[UUID] = None
    metadata: Optional[dict] = None

    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = None
    status: Optional[NotificationStatus] = None
    metadata: Optional[dict] = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: UUID
    organization_id: UUID
    user_id: Optional[UUID] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

    template_id: Optional[UUID] = None

    title: str
    message: str
    html_content: Optional[str] = None

    category: NotificationCategory
    priority: NotificationPriority
    channels: List[str]
    status: NotificationStatus

    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    entity_reference: Optional[str] = None

    action_url: Optional[str] = None
    action_label: Optional[str] = None

    metadata: Optional[dict] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    retry_count: int
    max_retries: int

    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list response."""

    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int = 0


class NotificationPreferenceCreate(BaseModel):
    """Schema for creating notification preference."""

    category: NotificationCategory
    organization_id: Optional[UUID] = None

    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True
    whatsapp_enabled: bool = False

    digest_mode: bool = False
    digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preference."""

    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None

    digest_mode: Optional[bool] = None
    digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response."""

    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    category: NotificationCategory

    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    whatsapp_enabled: bool

    digest_mode: bool
    digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationLogResponse(BaseModel):
    """Schema for notification log response."""

    id: UUID
    notification_id: UUID
    channel: NotificationChannel
    status: NotificationStatus
    attempt_number: int
    attempted_at: datetime
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None
    cost: Optional[float] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics."""

    total_notifications: int
    unread_count: int
    read_count: int
    sent_count: int
    failed_count: int
    pending_count: int

    by_category: dict
    by_channel: dict
    by_priority: dict


class MarkReadRequest(BaseModel):
    """Schema for marking notifications as read."""

    notification_ids: Optional[List[UUID]] = None
    mark_all: bool = False


class SendNotificationRequest(BaseModel):
    """Schema for sending a notification from template."""

    template_code: str
    context: dict = Field(default_factory=dict)

    user_id: Optional[UUID] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    entity_reference: Optional[str] = None


class BulkNotificationRequest(BaseModel):
    """Schema for sending bulk notifications."""

    title: str
    message: str
    category: NotificationCategory = NotificationCategory.ANNOUNCEMENT
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[str] = Field(default=["in_app"])

    user_ids: Optional[List[UUID]] = None
    department_ids: Optional[List[UUID]] = None
    role_ids: Optional[List[UUID]] = None
    all_users: bool = False

    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[dict] = None
    scheduled_at: Optional[datetime] = None
