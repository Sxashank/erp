"""Escalation rule model - defines timeout and escalation behavior."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import EscalationType, ApproverType


if TYPE_CHECKING:
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.workflow.notification_template import WorkflowNotificationTemplate
    from app.models.auth.user import User
    from app.models.auth.role import Role


class EscalationRule(BaseModel):
    """Rule defining escalation behavior for a workflow step."""

    __tablename__ = "wf_escalation_rule"

    # Parent step
    workflow_step_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow step",
    )

    # Escalation level (1, 2, 3...)
    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Escalation level - higher levels trigger after lower",
    )

    # Timeout configuration
    timeout_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Hours before this escalation triggers",
    )

    # Escalation type
    escalation_type: Mapped[EscalationType] = mapped_column(
        Enum(EscalationType),
        nullable=False,
        comment="Type of escalation action",
    )

    # Escalation target (for REASSIGN type)
    escalate_to_type: Mapped[Optional[ApproverType]] = mapped_column(
        Enum(ApproverType),
        nullable=True,
        comment="Type of user to escalate to",
    )
    escalate_to_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Specific user to escalate to",
    )
    escalate_to_role_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="SET NULL"),
        nullable=True,
        comment="Role to escalate to",
    )

    # Notification settings
    notify_current_approver: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Notify current approver about escalation",
    )
    notify_initiator: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Notify workflow initiator about escalation",
    )
    notification_template_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_notification_template.id", ondelete="SET NULL"),
        nullable=True,
        comment="Template for escalation notification",
    )

    # Relationships
    workflow_step: Mapped["WorkflowStep"] = relationship(
        "WorkflowStep",
        back_populates="escalation_rules",
        lazy="selectin",
    )
    escalate_to_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[escalate_to_user_id],
        lazy="selectin",
    )
    escalate_to_role: Mapped[Optional["Role"]] = relationship(
        "Role",
        foreign_keys=[escalate_to_role_id],
        lazy="selectin",
    )
    notification_template: Mapped[Optional["WorkflowNotificationTemplate"]] = relationship(
        "WorkflowNotificationTemplate",
        foreign_keys=[notification_template_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<EscalationRule(level={self.level}, type={self.escalation_type})>"
