"""Workflow definition schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.workflow.enums import (
    WorkflowEntityType,
    WorkflowStepType,
    ApprovalMode,
    ApproverType,
    EscalationType,
    StepAction,
)


# Approval Rule Schemas
class ApprovalRuleCreate(BaseSchema):
    """Schema for creating an approval rule."""

    sequence: int = Field(default=1, ge=1)
    approver_type: ApproverType
    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    designation: Optional[str] = None
    dynamic_field: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_mandatory: bool = True
    can_self_approve: bool = False
    fallback_to_admin: bool = True


class ApprovalRuleResponse(BaseSchema):
    """Schema for approval rule response."""

    id: UUID
    sequence: int
    approver_type: ApproverType
    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    designation: Optional[str] = None
    dynamic_field: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_mandatory: bool
    can_self_approve: bool
    fallback_to_admin: bool


# Escalation Rule Schemas
class EscalationRuleCreate(BaseSchema):
    """Schema for creating an escalation rule."""

    level: int = Field(default=1, ge=1)
    timeout_hours: int = Field(..., ge=1)
    escalation_type: EscalationType
    escalate_to_type: Optional[ApproverType] = None
    escalate_to_user_id: Optional[UUID] = None
    escalate_to_role_id: Optional[UUID] = None
    notify_current_approver: bool = True
    notify_initiator: bool = False
    notification_template_id: Optional[UUID] = None


class EscalationRuleResponse(BaseSchema):
    """Schema for escalation rule response."""

    id: UUID
    level: int
    timeout_hours: int
    escalation_type: EscalationType
    escalate_to_type: Optional[ApproverType] = None
    escalate_to_user_id: Optional[UUID] = None
    escalate_to_role_id: Optional[UUID] = None
    notify_current_approver: bool
    notify_initiator: bool
    notification_template_id: Optional[UUID] = None


# Workflow Step Schemas
class WorkflowStepCreate(BaseSchema):
    """Schema for creating a workflow step."""

    step_number: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    step_type: WorkflowStepType = WorkflowStepType.APPROVAL
    approval_mode: ApprovalMode = ApprovalMode.SEQUENTIAL

    parent_step_id: Optional[UUID] = None
    branch_name: Optional[str] = None

    entry_conditions: Optional[Dict[str, Any]] = None
    exit_conditions: Optional[Dict[str, Any]] = None

    on_approve_step_id: Optional[UUID] = None
    on_reject_step_id: Optional[UUID] = None
    on_approve_action: StepAction = StepAction.NEXT
    on_reject_action: StepAction = StepAction.REJECT

    allow_delegation: bool = False
    sla_hours: Optional[int] = Field(default=None, ge=1)
    reminder_hours: Optional[int] = Field(default=None, ge=1)

    approval_rules: List[ApprovalRuleCreate] = []
    escalation_rules: List[EscalationRuleCreate] = []


class WorkflowStepUpdate(BaseSchema):
    """Schema for updating a workflow step."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    step_type: Optional[WorkflowStepType] = None
    approval_mode: Optional[ApprovalMode] = None

    entry_conditions: Optional[Dict[str, Any]] = None
    exit_conditions: Optional[Dict[str, Any]] = None

    on_approve_action: Optional[StepAction] = None
    on_reject_action: Optional[StepAction] = None
    on_approve_step_id: Optional[UUID] = None
    on_reject_step_id: Optional[UUID] = None

    allow_delegation: Optional[bool] = None
    sla_hours: Optional[int] = Field(default=None, ge=1)
    reminder_hours: Optional[int] = Field(default=None, ge=1)


class WorkflowStepResponse(BaseSchema):
    """Schema for workflow step response."""

    id: UUID
    step_number: int
    name: str
    description: Optional[str] = None
    step_type: WorkflowStepType
    approval_mode: ApprovalMode

    parent_step_id: Optional[UUID] = None
    branch_name: Optional[str] = None

    entry_conditions: Optional[Dict[str, Any]] = None
    exit_conditions: Optional[Dict[str, Any]] = None

    on_approve_step_id: Optional[UUID] = None
    on_reject_step_id: Optional[UUID] = None
    on_approve_action: StepAction
    on_reject_action: StepAction

    allow_delegation: bool
    sla_hours: Optional[int] = None
    reminder_hours: Optional[int] = None

    approval_rules: List[ApprovalRuleResponse] = []
    escalation_rules: List[EscalationRuleResponse] = []


# Workflow Definition Schemas
class WorkflowDefinitionCreate(BaseSchema):
    """Schema for creating a workflow definition."""

    organization_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    entity_type: WorkflowEntityType
    is_default: bool = False
    priority: int = Field(default=0, ge=0)
    activation_conditions: Optional[Dict[str, Any]] = None
    allow_parallel_branches: bool = False
    require_comments_on_reject: bool = True
    notify_initiator_on_complete: bool = True
    allow_withdrawal: bool = True

    steps: List[WorkflowStepCreate] = []


class WorkflowDefinitionUpdate(BaseSchema):
    """Schema for updating a workflow definition."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0)
    activation_conditions: Optional[Dict[str, Any]] = None
    allow_parallel_branches: Optional[bool] = None
    require_comments_on_reject: Optional[bool] = None
    notify_initiator_on_complete: Optional[bool] = None
    allow_withdrawal: Optional[bool] = None


class WorkflowDefinitionResponse(AuditSchema):
    """Schema for workflow definition response."""

    id: UUID
    organization_id: UUID
    name: str
    code: str
    description: Optional[str] = None
    entity_type: WorkflowEntityType
    is_default: bool
    priority: int
    activation_conditions: Optional[Dict[str, Any]] = None
    allow_parallel_branches: bool
    require_comments_on_reject: bool
    notify_initiator_on_complete: bool
    allow_withdrawal: bool
    version: int


class WorkflowDefinitionWithStepsResponse(WorkflowDefinitionResponse):
    """Schema for workflow definition with steps."""

    steps: List[WorkflowStepResponse] = []
