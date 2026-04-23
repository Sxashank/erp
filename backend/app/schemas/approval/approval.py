"""Approval/Maker-Checker workflow schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import (
    ApprovalWorkflowType,
    ApprovalRequestStatus,
    ApprovalAction,
)


# ============================================
# Workflow Level Schemas
# ============================================

class ApprovalWorkflowLevelCreate(BaseSchema):
    """Schema for creating an approval workflow level."""

    level_number: int = Field(..., ge=1, le=5, description="Level order (1-5)")
    level_name: str = Field(..., max_length=50, description="Display name")
    approver_roles: Optional[List[UUID]] = Field(
        None,
        description="Role IDs that can approve at this level",
    )
    approver_users: Optional[List[UUID]] = Field(
        None,
        description="Specific user IDs that can approve",
    )
    min_approvers: int = Field(
        1,
        ge=1,
        description="Minimum approvers required",
    )
    threshold_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Level-specific threshold override",
    )
    escalation_hours: Optional[int] = Field(
        None,
        ge=1,
        description="Hours before escalation",
    )
    escalation_user_id: Optional[UUID] = Field(
        None,
        description="User to escalate to",
    )


class ApprovalWorkflowLevelResponse(AuditSchema):
    """Response schema for approval workflow level."""

    id: UUID
    workflow_id: UUID
    level_number: int
    level_name: str
    approver_roles: Optional[List[UUID]] = None
    approver_users: Optional[List[UUID]] = None
    min_approvers: int
    threshold_amount: Optional[Decimal] = None
    escalation_hours: Optional[int] = None
    escalation_user_id: Optional[UUID] = None


# ============================================
# Workflow Configuration Schemas
# ============================================

class ApprovalWorkflowCreate(BaseSchema):
    """Schema for creating an approval workflow."""

    organization_id: UUID
    workflow_type: ApprovalWorkflowType
    workflow_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    threshold_amount: Decimal = Field(
        Decimal("0.00"),
        ge=0,
        description="Minimum amount requiring approval (0 = all)",
    )
    threshold_currency: str = Field("INR", max_length=3)
    approval_levels: int = Field(1, ge=1, le=3)
    is_sequential: bool = True
    auto_approve_on_timeout: bool = False
    timeout_hours: Optional[int] = Field(None, ge=1)
    allow_self_approval: bool = False
    notify_on_submit: bool = True
    notify_on_approval: bool = True
    notify_on_rejection: bool = True
    levels: List[ApprovalWorkflowLevelCreate] = Field(
        ...,
        min_length=1,
        description="Approval level configurations",
    )


class ApprovalWorkflowUpdate(BaseSchema):
    """Schema for updating an approval workflow."""

    workflow_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    threshold_amount: Optional[Decimal] = Field(None, ge=0)
    threshold_currency: Optional[str] = Field(None, max_length=3)
    approval_levels: Optional[int] = Field(None, ge=1, le=3)
    is_sequential: Optional[bool] = None
    auto_approve_on_timeout: Optional[bool] = None
    timeout_hours: Optional[int] = Field(None, ge=1)
    allow_self_approval: Optional[bool] = None
    notify_on_submit: Optional[bool] = None
    notify_on_approval: Optional[bool] = None
    notify_on_rejection: Optional[bool] = None
    is_active: Optional[bool] = None


class ApprovalWorkflowResponse(AuditSchema):
    """Response schema for approval workflow."""

    id: UUID
    organization_id: UUID
    workflow_type: ApprovalWorkflowType
    workflow_name: str
    description: Optional[str] = None
    threshold_amount: Decimal
    threshold_currency: str
    approval_levels: int
    is_sequential: bool
    auto_approve_on_timeout: bool
    timeout_hours: Optional[int] = None
    allow_self_approval: bool
    notify_on_submit: bool
    notify_on_approval: bool
    notify_on_rejection: bool
    levels: List[ApprovalWorkflowLevelResponse] = []


# ============================================
# Approval Request Schemas
# ============================================

class ApprovalRequestCreate(BaseSchema):
    """Schema for creating an approval request (internal use)."""

    organization_id: UUID
    workflow_type: ApprovalWorkflowType
    entity_type: str = Field(..., max_length=50)
    entity_id: UUID
    request_amount: Decimal = Field(Decimal("0.00"), ge=0)
    request_summary: str = Field(..., max_length=500)
    request_details: Optional[dict] = None


class ApprovalRequestActionCreate(BaseSchema):
    """Schema for taking action on an approval request."""

    action: ApprovalAction
    comments: Optional[str] = Field(None, max_length=1000)


class ApprovalRequestActionResponse(AuditSchema):
    """Response schema for approval action."""

    id: UUID
    request_id: UUID
    level_number: int
    action: ApprovalAction
    action_by: UUID
    action_at: datetime
    comments: Optional[str] = None
    actor_name: Optional[str] = None


class ApprovalRequestResponse(AuditSchema):
    """Response schema for approval request."""

    id: UUID
    organization_id: UUID
    workflow_id: UUID
    workflow_type: ApprovalWorkflowType
    workflow_name: Optional[str] = None
    entity_type: str
    entity_id: UUID
    request_number: str
    request_amount: Decimal
    request_summary: str
    request_details: Optional[dict] = None
    requested_by: UUID
    requester_name: Optional[str] = None
    requested_at: datetime
    status: ApprovalRequestStatus
    current_level: int
    total_levels: int
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolver_name: Optional[str] = None
    final_comments: Optional[str] = None
    expires_at: Optional[datetime] = None
    version: int
    actions: List[ApprovalRequestActionResponse] = []
    can_approve: Optional[bool] = None  # Set based on current user


class ApprovalRequestListResponse(BaseSchema):
    """List response for approval requests."""

    id: UUID
    request_number: str
    workflow_type: ApprovalWorkflowType
    workflow_name: Optional[str] = None
    entity_type: str
    entity_id: UUID
    request_amount: Decimal
    request_summary: str
    requested_by: UUID
    requester_name: Optional[str] = None
    requested_at: datetime
    status: ApprovalRequestStatus
    current_level: int
    total_levels: int
    expires_at: Optional[datetime] = None


# ============================================
# Query/Filter Schemas
# ============================================

class ApprovalRequestFilter(BaseSchema):
    """Filter parameters for approval requests."""

    organization_id: Optional[UUID] = None
    workflow_type: Optional[ApprovalWorkflowType] = None
    status: Optional[ApprovalRequestStatus] = None
    entity_type: Optional[str] = None
    requested_by: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    pending_for_user: Optional[UUID] = Field(
        None,
        description="Filter requests pending for specific user",
    )


class PendingApprovalResponse(BaseSchema):
    """Response for pending approvals summary."""

    request_id: UUID
    request_number: str
    workflow_type: ApprovalWorkflowType
    workflow_name: str
    entity_type: str
    entity_id: UUID
    request_amount: Decimal
    request_summary: str
    requester_name: str
    requested_at: datetime
    current_level: int
    level_name: str
    expires_at: Optional[datetime] = None
    days_pending: int


# ============================================
# Dashboard Schemas
# ============================================

class ApprovalDashboardResponse(BaseSchema):
    """Dashboard response for approval overview."""

    # Summary counts
    pending_count: int
    approved_today: int
    rejected_today: int
    returned_today: int

    # By workflow type
    by_workflow_type: dict  # {workflow_type: count}

    # My pending (for current user)
    my_pending: List[PendingApprovalResponse]

    # Recent activity
    recent_actions: List[ApprovalRequestActionResponse]

    # Aging (pending requests by days)
    aging: dict  # {"0-1": count, "2-5": count, "5+": count}


# ============================================
# Approval Check Result (Internal Use)
# ============================================

class ApprovalCheckResult(BaseSchema):
    """Result of checking if approval is required."""

    requires_approval: bool
    workflow_id: Optional[UUID] = None
    workflow_type: Optional[ApprovalWorkflowType] = None
    approval_levels: int = 0
    threshold_amount: Decimal = Decimal("0.00")
    reason: Optional[str] = None
