"""Workflow definition model - templates for workflows."""

from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import WorkflowEntityType


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.workflow.workflow_instance import WorkflowInstance


class WorkflowDefinition(BaseModel):
    """Workflow definition - template for creating workflow instances."""

    __tablename__ = "wf_workflow_definition"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this workflow belongs to",
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Workflow name e.g., 'Purchase Bill Approval'",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique code e.g., 'PB_APPROVAL'",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the workflow",
    )

    # Entity type this workflow applies to
    entity_type: Mapped[WorkflowEntityType] = mapped_column(
        Enum(WorkflowEntityType),
        nullable=False,
        index=True,
        comment="Type of entity this workflow handles",
    )

    # Priority and default settings
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the default workflow for the entity type?",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Higher priority wins when multiple workflows match",
    )

    # Activation conditions (JSONB)
    activation_conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions for when this workflow applies e.g., {'amount_gte': 100000}",
    )

    # Workflow settings
    allow_parallel_branches: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Allow parallel approval branches",
    )
    require_comments_on_reject: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Require comments when rejecting",
    )
    notify_initiator_on_complete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Notify initiator when workflow completes",
    )
    allow_withdrawal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Allow initiator to withdraw/cancel the workflow",
    )

    # Version tracking for workflow changes
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Workflow version number",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep",
        back_populates="workflow_definition",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowStep.step_number",
    )
    instances: Mapped[List["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        back_populates="workflow_definition",
        lazy="noload",
    )

    __table_args__ = (
        Index("ix_wf_definition_org_entity", "organization_id", "entity_type"),
        Index("ix_wf_definition_org_code", "organization_id", "code", unique=True),
    )

    def __repr__(self) -> str:
        return f"<WorkflowDefinition(code={self.code}, entity_type={self.entity_type})>"
