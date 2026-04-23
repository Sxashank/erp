"""Notification template schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.workflow.enums import WorkflowEntityType


class NotificationTemplateCreate(BaseSchema):
    """Schema for creating a notification template."""

    organization_id: UUID
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: Optional[WorkflowEntityType] = None
    email_subject: str = Field(..., min_length=1, max_length=500)
    email_body: str = Field(..., min_length=1)
    notification_title: Optional[str] = Field(default=None, max_length=200)
    notification_body: Optional[str] = None
    available_variables: Optional[List[str]] = None


class NotificationTemplateUpdate(BaseSchema):
    """Schema for updating a notification template."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email_subject: Optional[str] = Field(default=None, min_length=1, max_length=500)
    email_body: Optional[str] = Field(default=None, min_length=1)
    notification_title: Optional[str] = Field(default=None, max_length=200)
    notification_body: Optional[str] = None
    available_variables: Optional[List[str]] = None


class NotificationTemplateResponse(AuditSchema):
    """Schema for notification template response."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    entity_type: Optional[WorkflowEntityType] = None
    email_subject: str
    email_body: str
    notification_title: Optional[str] = None
    notification_body: Optional[str] = None
    available_variables: Optional[List[str]] = None


class TemplatePreviewRequest(BaseSchema):
    """Schema for template preview request."""

    context: dict = Field(default_factory=dict)


class TemplatePreviewResponse(BaseSchema):
    """Schema for template preview response."""

    subject: str
    body: str
