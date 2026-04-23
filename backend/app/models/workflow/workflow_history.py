"""Workflow history model - audit trail of all workflow actions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


if TYPE_CHECKING:
    from app.models.workflow.workflow_instance import WorkflowInstance
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.auth.user import User


class WorkflowHistory(BaseModel):
    """Audit trail entry for workflow actions."""

    __tablename__ = "wf_workflow_history"

    # Parent instance
    workflow_instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow instance",
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action: STARTED, APPROVED, REJECTED, ESCALATED, etc.",
    )
    action_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=False,
        comment="User who performed the action",
    )
    action_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When action was performed",
    )

    # Step context
    from_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Step before the action",
    )
    to_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Step after the action",
    )

    # Status transition
    from_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Status before the action",
    )
    to_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Status after the action",
    )

    # Additional context
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comments provided with action",
    )
    action_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional action metadata",
    )

    # Task reference (if action was on a specific task)
    task_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_task.id", ondelete="SET NULL"),
        nullable=True,
        comment="Related task if action was on a task",
    )

    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance",
        back_populates="history",
        lazy="selectin",
    )
    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[action_by],
        lazy="selectin",
    )
    from_step: Mapped[Optional["WorkflowStep"]] = relationship(
        "WorkflowStep",
        foreign_keys=[from_step_id],
        lazy="selectin",
    )
    to_step: Mapped[Optional["WorkflowStep"]] = relationship(
        "WorkflowStep",
        foreign_keys=[to_step_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_wf_history_instance_action", "workflow_instance_id", "action_at"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowHistory(action={self.action}, action_at={self.action_at})>"
