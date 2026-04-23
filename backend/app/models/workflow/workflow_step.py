"""Workflow step model - individual steps within a workflow."""

from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import WorkflowStepType, ApprovalMode, StepAction


if TYPE_CHECKING:
    from app.models.workflow.workflow_definition import WorkflowDefinition
    from app.models.workflow.approval_rule import ApprovalRule
    from app.models.workflow.escalation_rule import EscalationRule


class WorkflowStep(BaseModel):
    """Individual step within a workflow definition."""

    __tablename__ = "wf_workflow_step"

    # Parent workflow
    workflow_definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_definition.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow definition",
    )

    # Step ordering
    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order of this step in the workflow",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Step name e.g., 'Manager Approval'",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Step description",
    )

    # Step type and approval mode
    step_type: Mapped[WorkflowStepType] = mapped_column(
        Enum(WorkflowStepType),
        nullable=False,
        default=WorkflowStepType.APPROVAL,
        comment="Type of step",
    )
    approval_mode: Mapped[ApprovalMode] = mapped_column(
        Enum(ApprovalMode),
        nullable=False,
        default=ApprovalMode.SEQUENTIAL,
        comment="How approvals are processed",
    )

    # Parallel branching support
    parent_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent step for parallel branches",
    )
    branch_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Branch identifier e.g., 'finance_branch'",
    )

    # Conditions (JSONB)
    entry_conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions to enter this step e.g., {'amount_gte': 50000}",
    )
    exit_conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions for step completion",
    )

    # Next step routing
    on_approve_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Step to go to on approval (for GOTO action)",
    )
    on_reject_step_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="SET NULL"),
        nullable=True,
        comment="Step to go to on rejection (for GOTO action)",
    )
    on_approve_action: Mapped[StepAction] = mapped_column(
        Enum(StepAction),
        nullable=False,
        default=StepAction.NEXT,
        comment="Action on approval: NEXT, COMPLETE, GOTO",
    )
    on_reject_action: Mapped[StepAction] = mapped_column(
        Enum(StepAction),
        nullable=False,
        default=StepAction.REJECT,
        comment="Action on rejection: REJECT, GOTO, PREVIOUS",
    )

    # Step settings
    allow_delegation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Allow task delegation to another user",
    )
    sla_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected completion time in hours",
    )
    reminder_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Send reminder after these many hours",
    )

    # Relationships
    workflow_definition: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="steps",
        lazy="selectin",
    )
    approval_rules: Mapped[List["ApprovalRule"]] = relationship(
        "ApprovalRule",
        back_populates="workflow_step",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ApprovalRule.sequence",
    )
    escalation_rules: Mapped[List["EscalationRule"]] = relationship(
        "EscalationRule",
        back_populates="workflow_step",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="EscalationRule.level",
    )
    parent_step: Mapped[Optional["WorkflowStep"]] = relationship(
        "WorkflowStep",
        remote_side="WorkflowStep.id",
        foreign_keys=[parent_step_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkflowStep(step_number={self.step_number}, name={self.name})>"
