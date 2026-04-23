"""Notification template model - email and notification templates."""

from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import WorkflowEntityType


if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class WorkflowNotificationTemplate(BaseModel):
    """Template for workflow notifications and emails."""

    __tablename__ = "wf_notification_template"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this template belongs to",
    )

    # Template identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Template code e.g., 'APPROVAL_PENDING'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Template name",
    )

    # Entity type (null = generic template)
    entity_type: Mapped[Optional[WorkflowEntityType]] = mapped_column(
        Enum(WorkflowEntityType),
        nullable=True,
        comment="Entity type this template is for (null = generic)",
    )

    # Email content
    email_subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Email subject with {placeholders}",
    )
    email_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Email body (HTML) with {placeholders}",
    )

    # In-app notification content (for future use)
    notification_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="In-app notification title",
    )
    notification_body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="In-app notification body",
    )

    # Available variables documentation
    available_variables: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="List of available placeholder variables",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkflowNotificationTemplate(code={self.code}, name={self.name})>"
