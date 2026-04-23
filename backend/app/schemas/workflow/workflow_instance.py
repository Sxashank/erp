"""Workflow instance and task schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.workflow.enums import (
    WorkflowEntityType,
    WorkflowInstanceStatus,
    TaskStatus,
)


# Request Schemas
class ApprovalActionRequest(BaseSchema):
    """Schema for approval action request."""

    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    comments: Optional[str] = Field(default=None, max_length=2000)


class DelegateTaskRequest(BaseSchema):
    """Schema for task delegation request."""

    delegate_to: UUID
    reason: str = Field(..., min_length=1, max_length=500)


class CancelWorkflowRequest(BaseSchema):
    """Schema for workflow cancellation request."""

    reason: str = Field(..., min_length=1, max_length=500)


# Response Schemas
class WorkflowTaskResponse(AuditSchema):
    """Schema for workflow task response."""

    id: UUID
    workflow_instance_id: UUID
    workflow_step_id: UUID
    step_name: Optional[str] = None
    step_number: Optional[int] = None

    assigned_to: UUID
    assignee_name: Optional[str] = None
    assigned_at: datetime

    status: TaskStatus
    action_taken: Optional[str] = None
    comments: Optional[str] = None
    acted_at: Optional[datetime] = None

    delegated_from: Optional[UUID] = None
    delegated_reason: Optional[str] = None
    delegated_at: Optional[datetime] = None

    escalation_level: int
    escalated_at: Optional[datetime] = None

    due_at: Optional[datetime] = None
    is_overdue: bool
    sequence: int


class WorkflowHistoryResponse(BaseSchema):
    """Schema for workflow history response."""

    id: UUID
    action: str
    action_by: UUID
    actor_name: Optional[str] = None
    action_at: datetime

    from_step_id: Optional[UUID] = None
    from_step_name: Optional[str] = None
    to_step_id: Optional[UUID] = None
    to_step_name: Optional[str] = None

    from_status: Optional[str] = None
    to_status: str
    comments: Optional[str] = None
    action_metadata: Optional[Dict[str, Any]] = None


class WorkflowInstanceResponse(AuditSchema):
    """Schema for workflow instance response."""

    id: UUID
    workflow_definition_id: UUID
    workflow_name: Optional[str] = None
    organization_id: UUID

    entity_type: WorkflowEntityType
    entity_id: UUID
    entity_reference: str

    current_step_id: Optional[UUID] = None
    current_step_name: Optional[str] = None
    current_step_number: int
    status: WorkflowInstanceStatus

    started_at: datetime
    started_by: UUID
    initiator_name: Optional[str] = None

    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None

    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[UUID] = None
    cancellation_reason: Optional[str] = None


class WorkflowInstanceDetailResponse(WorkflowInstanceResponse):
    """Schema for detailed workflow instance response."""

    context_data: Optional[Dict[str, Any]] = None
    tasks: List[WorkflowTaskResponse] = []
    history: List[WorkflowHistoryResponse] = []


class PendingTaskSummary(BaseSchema):
    """Summary of pending tasks for a user."""

    total_pending: int
    overdue_count: int
    due_today_count: int
    tasks: List[WorkflowTaskResponse] = []
