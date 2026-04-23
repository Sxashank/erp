"""Workflow instance model - running instance of a workflow."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import WorkflowEntityType, WorkflowInstanceStatus


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.workflow.workflow_definition import WorkflowDefinition
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.workflow.workflow_task import WorkflowTask
    from app.models.workflow.workflow_history import WorkflowHistory
    from app.models.auth.user import User


class WorkflowInstance(BaseModel):
    """Running instance of a workflow for a specific entity."""

    __tablename__ = "wf_workflow_instance"

    # Parent workflow definition
    workflow_definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_definition.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Workflow definition this instance is based on",
    )

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this instance belongs to",
    )

    # Entity being processed
    entity_type: Mapped[WorkflowEntityType] = mapped_column(
        Enum(WorkflowEntityType),
        nullable=False,
        index=True,
        comment="Type of entity being processed",
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the entity being processed",
    )
    entity_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable reference e.g., 'VCH-2024-001234'",
    )

    # Current state
    current_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Current step in the workflow",
    )
    current_step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Current step number",
    )
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        Enum(WorkflowInstanceStatus),
        nullable=False,
        default=WorkflowInstanceStatus.PENDING,
        index=True,
        comment="Current status of the workflow",
    )

    # Context data (snapshot of entity at workflow start)
    context_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Entity data snapshot at workflow start",
    )

    # Parallel processing support
    active_parallel_branches: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Currently active parallel branches",
    )
    completed_parallel_branches: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Completed parallel branches",
    )

    # Tracking timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When workflow was started",
    )
    started_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=False,
        comment="User who started the workflow",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When workflow was completed",
    )
    completed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who completed the workflow",
    )

    # Cancellation tracking
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When workflow was cancelled",
    )
    cancelled_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who cancelled the workflow",
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Reason for cancellation",
    )

    # Relationships
    workflow_definition: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="instances",
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    current_step: Mapped[Optional["WorkflowStep"]] = relationship(
        "WorkflowStep",
        foreign_keys=[current_step_id],
        lazy="selectin",
    )
    tasks: Mapped[List["WorkflowTask"]] = relationship(
        "WorkflowTask",
        back_populates="workflow_instance",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowTask.assigned_at",
    )
    history: Mapped[List["WorkflowHistory"]] = relationship(
        "WorkflowHistory",
        back_populates="workflow_instance",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowHistory.action_at",
    )
    initiator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[started_by],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_wf_instance_entity", "entity_type", "entity_id"),
        Index("ix_wf_instance_org_status", "organization_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowInstance(entity_ref={self.entity_reference}, status={self.status})>"
