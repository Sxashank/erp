"""Workflow task model - individual approval tasks assigned to users."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import TaskStatus


if TYPE_CHECKING:
    from app.models.workflow.workflow_instance import WorkflowInstance
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.auth.user import User


class WorkflowTask(BaseModel):
    """Individual approval task assigned to a user."""

    __tablename__ = "wf_workflow_task"

    # Parent instance and step
    workflow_instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow instance",
    )
    workflow_step_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workflow step this task belongs to",
    )

    # Assignment
    assigned_to: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User assigned to this task",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When task was assigned",
    )

    # Status
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
        comment="Current status of the task",
    )
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Action taken: APPROVED, REJECTED",
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comments provided with action",
    )
    acted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When action was taken",
    )

    # Delegation tracking
    delegated_from: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original assignee if delegated",
    )
    delegated_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Reason for delegation",
    )
    delegated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When task was delegated",
    )

    # Escalation tracking
    escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current escalation level (0 = not escalated)",
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When task was last escalated",
    )
    escalated_from: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Previous assignee before escalation",
    )

    # SLA tracking
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Due date/time for this task",
    )
    is_overdue: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this task overdue?",
    )
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When last reminder was sent",
    )

    # Sequence for multiple approvers in same step
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Sequence number for ordered approvals",
    )

    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance",
        back_populates="tasks",
        lazy="selectin",
    )
    workflow_step: Mapped["WorkflowStep"] = relationship(
        "WorkflowStep",
        lazy="selectin",
    )
    assignee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_to],
        lazy="selectin",
    )
    original_assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[delegated_from],
        lazy="selectin",
    )
    previous_assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[escalated_from],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_wf_task_assignee_status", "assigned_to", "status"),
        Index("ix_wf_task_due", "due_at"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowTask(instance_id={self.workflow_instance_id}, status={self.status})>"
