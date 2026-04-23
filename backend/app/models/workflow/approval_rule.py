"""Approval rule model - defines who can approve at each step."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.workflow.enums import ApproverType


if TYPE_CHECKING:
    from app.models.workflow.workflow_step import WorkflowStep
    from app.models.auth.user import User
    from app.models.auth.role import Role


class ApprovalRule(BaseModel):
    """Rule defining who can approve at a workflow step."""

    __tablename__ = "wf_approval_rule"

    # Parent step
    workflow_step_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow step",
    )

    # Sequence for ordered approvals
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Order for sequential approval",
    )

    # Approver type
    approver_type: Mapped[ApproverType] = mapped_column(
        Enum(ApproverType),
        nullable=False,
        comment="Type of approver",
    )

    # Approver references (based on type)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Specific user (for USER type)",
    )
    role_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="SET NULL"),
        nullable=True,
        comment="Role (for ROLE type)",
    )
    designation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Designation name (for DESIGNATION type)",
    )
    dynamic_field: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Field path for DYNAMIC type e.g., 'vendor.account_manager_id'",
    )

    # Conditions for this rule (JSONB)
    conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional conditions e.g., {'amount_gte': 50000}",
    )

    # Rule settings
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Must this approver act?",
    )
    can_self_approve: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Can initiator approve their own request?",
    )
    fallback_to_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Fallback to admin if no approver found",
    )

    # Relationships
    workflow_step: Mapped["WorkflowStep"] = relationship(
        "WorkflowStep",
        back_populates="approval_rules",
        lazy="selectin",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        foreign_keys=[role_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ApprovalRule(sequence={self.sequence}, type={self.approver_type})>"
