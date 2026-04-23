"""Approval/Maker-Checker workflow models for enterprise compliance."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import (
    ApprovalWorkflowType,
    ApprovalRequestStatus,
    ApprovalAction,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.auth.user import User


class ApprovalWorkflow(BaseModel):
    """
    Configuration for approval workflows (maker-checker).

    Defines which transaction types require approval, thresholds,
    and the number of approval levels required.
    """

    __tablename__ = "mst_approval_workflow"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "workflow_type",
            name="uq_approval_workflow_org_type",
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Workflow Configuration
    workflow_type: Mapped[ApprovalWorkflowType] = mapped_column(
        SQLEnum(ApprovalWorkflowType),
        nullable=False,
        comment="Type of transaction requiring approval",
    )
    workflow_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name for the workflow",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Threshold Configuration
    threshold_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Minimum amount requiring approval (0 = all transactions)",
    )
    threshold_currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )

    # Approval Levels
    approval_levels: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of approval levels (1, 2, or 3)",
    )

    # Workflow Settings
    is_sequential: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="If True, approvals must be sequential; if False, parallel",
    )
    auto_approve_on_timeout: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Auto-approve if no action within timeout period",
    )
    timeout_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Hours before request expires or auto-approves",
    )
    allow_self_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Can maker also be checker (usually False for compliance)",
    )

    # Notification Settings
    notify_on_submit: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    notify_on_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    notify_on_rejection: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    levels: Mapped[List["ApprovalWorkflowLevel"]] = relationship(
        "ApprovalWorkflowLevel",
        back_populates="workflow",
        lazy="selectin",
        order_by="ApprovalWorkflowLevel.level_number",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflow({self.workflow_type}, levels={self.approval_levels})>"


class ApprovalWorkflowLevel(BaseModel):
    """
    Configuration for each approval level in a workflow.

    Defines who can approve at each level (by role or specific users).
    """

    __tablename__ = "mst_approval_workflow_level"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "level_number",
            name="uq_workflow_level",
        ),
    )

    # Parent Workflow
    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_approval_workflow.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Level Configuration
    level_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Level order (1 = first, 2 = second, etc.)",
    )
    level_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Display name (e.g., 'Department Head', 'Finance Manager')",
    )

    # Approver Configuration (either roles or specific users)
    approver_roles: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of role IDs that can approve at this level",
    )
    approver_users: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of specific user IDs that can approve at this level",
    )

    # Level Settings
    min_approvers: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Minimum approvers required at this level",
    )
    threshold_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Level-specific threshold (overrides workflow threshold)",
    )

    # Escalation
    escalation_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Hours before escalating to next level",
    )
    escalation_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User to escalate to if timeout",
    )

    # Relationships
    workflow: Mapped["ApprovalWorkflow"] = relationship(
        "ApprovalWorkflow",
        back_populates="levels",
        lazy="selectin",
    )
    escalation_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[escalation_user_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflowLevel(level={self.level_number}, name={self.level_name})>"


class ApprovalRequest(BaseModel):
    """
    Individual approval request for a transaction.

    Created when a maker submits a transaction for approval.
    Tracks the approval status through all levels.
    """

    __tablename__ = "txn_approval_request"
    __table_args__ = (
        Index("idx_approval_request_entity", "entity_type", "entity_id"),
        Index("idx_approval_request_status", "status"),
        Index("idx_approval_request_current_level", "current_level"),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Workflow Reference
    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_approval_workflow.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workflow_type: Mapped[ApprovalWorkflowType] = mapped_column(
        SQLEnum(ApprovalWorkflowType),
        nullable=False,
        comment="Denormalized for quick queries",
    )

    # Entity Reference (polymorphic reference to any entity)
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of entity (e.g., 'FixedAsset', 'DepreciationRun')",
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="ID of the entity requiring approval",
    )

    # Request Details
    request_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        comment="Unique request number for tracking",
    )
    request_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Amount involved in the transaction",
    )
    request_summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Brief description of what is being requested",
    )
    request_details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Full details of the request for audit",
    )

    # Maker Details
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Approval Status
    status: Mapped[ApprovalRequestStatus] = mapped_column(
        SQLEnum(ApprovalRequestStatus),
        default=ApprovalRequestStatus.PENDING,
        nullable=False,
    )
    current_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Current approval level (1-based)",
    )
    total_levels: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total approval levels required",
    )

    # Approval Chain (history of all approvals)
    approval_chain: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="History: [{level, user, action, timestamp, comments}]",
    )

    # Final Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    final_comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Version for optimistic locking
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    workflow: Mapped["ApprovalWorkflow"] = relationship(
        "ApprovalWorkflow",
        lazy="selectin",
    )
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by],
        lazy="selectin",
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="selectin",
    )
    actions: Mapped[List["ApprovalRequestAction"]] = relationship(
        "ApprovalRequestAction",
        back_populates="request",
        lazy="selectin",
        order_by="ApprovalRequestAction.created_at",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest({self.request_number}, status={self.status})>"


class ApprovalRequestAction(BaseModel):
    """
    Individual approval/rejection action on a request.

    Records each checker's action with timestamp and comments.
    """

    __tablename__ = "txn_approval_request_action"
    __table_args__ = (
        Index("idx_approval_action_request", "request_id"),
        Index("idx_approval_action_user", "action_by"),
    )

    # Parent Request
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_approval_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Level Info
    level_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="The level at which this action was taken",
    )

    # Action Details
    action: Mapped[ApprovalAction] = mapped_column(
        SQLEnum(ApprovalAction),
        nullable=False,
    )
    action_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Context
    action_context: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context (IP address, device, etc.)",
    )

    # Relationships
    request: Mapped["ApprovalRequest"] = relationship(
        "ApprovalRequest",
        back_populates="actions",
        lazy="selectin",
    )
    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[action_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequestAction(level={self.level_number}, action={self.action})>"
