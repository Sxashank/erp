"""Notification template schemas for API request/response."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema

from app.models.notification import (
    NotificationCategory,
    NotificationTemplateType,
)


class TemplateVariableCreate(CamelSchema):
    """Schema for creating a template variable."""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    data_type: str = "string"
    format_pattern: Optional[str] = None
    default_value: Optional[str] = None

    is_required: bool = True
    validation_regex: Optional[str] = None
    sample_value: Optional[str] = None
    display_order: int = 0


class TemplateVariableResponse(CamelSchema):
    """Schema for template variable response."""

    id: UUID
    template_id: UUID
    name: str
    display_name: str
    description: Optional[str] = None

    data_type: str
    format_pattern: Optional[str] = None
    default_value: Optional[str] = None

    is_required: bool
    validation_regex: Optional[str] = None
    sample_value: Optional[str] = None
    display_order: int


class NotificationTemplateCreate(CamelSchema):
    """Schema for creating a notification template."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    template_type: NotificationTemplateType = NotificationTemplateType.TRANSACTIONAL
    category: NotificationCategory = NotificationCategory.SYSTEM

    channels: List[str] = Field(default=["email", "in_app"])

    # Email template
    email_subject: Optional[str] = None
    email_body_html: Optional[str] = None
    email_body_text: Optional[str] = None

    # SMS template
    sms_body: Optional[str] = None

    # Push notification template
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    push_image_url: Optional[str] = None

    # In-app notification template
    in_app_title: Optional[str] = None
    in_app_message: Optional[str] = None

    # WhatsApp template
    whatsapp_template_id: Optional[str] = None
    whatsapp_template_params: Optional[List[str]] = None

    # Variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None

    # Trigger
    trigger_event: Optional[str] = None

    is_active: bool = True

    # Variable definitions
    variable_definitions: Optional[List[TemplateVariableCreate]] = None


class NotificationTemplateUpdate(CamelSchema):
    """Schema for updating a notification template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

    template_type: Optional[NotificationTemplateType] = None
    category: Optional[NotificationCategory] = None

    channels: Optional[List[str]] = None

    # Email template
    email_subject: Optional[str] = None
    email_body_html: Optional[str] = None
    email_body_text: Optional[str] = None

    # SMS template
    sms_body: Optional[str] = None

    # Push notification template
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    push_image_url: Optional[str] = None

    # In-app notification template
    in_app_title: Optional[str] = None
    in_app_message: Optional[str] = None

    # WhatsApp template
    whatsapp_template_id: Optional[str] = None
    whatsapp_template_params: Optional[List[str]] = None

    # Variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None

    # Trigger
    trigger_event: Optional[str] = None

    is_active: Optional[bool] = None


class NotificationTemplateResponse(CamelSchema):
    """Schema for notification template response."""

    id: UUID
    organization_id: Optional[UUID] = None

    code: str
    name: str
    description: Optional[str] = None

    template_type: NotificationTemplateType
    category: NotificationCategory

    channels: List[str]

    # Email template
    email_subject: Optional[str] = None
    email_body_html: Optional[str] = None
    email_body_text: Optional[str] = None

    # SMS template
    sms_body: Optional[str] = None

    # Push notification template
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    push_image_url: Optional[str] = None

    # In-app notification template
    in_app_title: Optional[str] = None
    in_app_message: Optional[str] = None

    # WhatsApp template
    whatsapp_template_id: Optional[str] = None
    whatsapp_template_params: Optional[List[str]] = None

    # Variables
    variables: Optional[List[str]] = None
    default_values: Optional[dict] = None

    trigger_event: Optional[str] = None
    is_active: bool
    usage_count: int

    variable_definitions: List[TemplateVariableResponse] = []

    created_at: datetime
    updated_at: Optional[datetime] = None


class NotificationTemplateListResponse(CamelSchema):
    """Schema for paginated template list response."""

    items: List[NotificationTemplateResponse]
    total: int
    page: int
    page_size: int


class TemplatePreviewRequest(CamelSchema):
    """Schema for template preview request."""

    template_id: Optional[UUID] = None
    template_code: Optional[str] = None
    context: dict = Field(default_factory=dict)
    channel: str = "email"


class TemplatePreviewResponse(CamelSchema):
    """Schema for template preview response."""

    channel: str
    title: Optional[str] = None
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    variables_used: List[str]
    missing_variables: List[str]
