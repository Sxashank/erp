"""Workflow schemas package."""

from app.schemas.workflow.workflow_definition import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionWithStepsResponse,
    WorkflowStepCreate,
    WorkflowStepUpdate,
    WorkflowStepResponse,
    ApprovalRuleCreate,
    ApprovalRuleResponse,
    EscalationRuleCreate,
    EscalationRuleResponse,
)
from app.schemas.workflow.workflow_instance import (
    WorkflowInstanceResponse,
    WorkflowInstanceDetailResponse,
    WorkflowTaskResponse,
    WorkflowHistoryResponse,
    ApprovalActionRequest,
    DelegateTaskRequest,
    CancelWorkflowRequest,
)
from app.schemas.workflow.notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)

__all__ = [
    # Definition schemas
    "WorkflowDefinitionCreate",
    "WorkflowDefinitionUpdate",
    "WorkflowDefinitionResponse",
    "WorkflowDefinitionWithStepsResponse",
    "WorkflowStepCreate",
    "WorkflowStepUpdate",
    "WorkflowStepResponse",
    "ApprovalRuleCreate",
    "ApprovalRuleResponse",
    "EscalationRuleCreate",
    "EscalationRuleResponse",
    # Instance schemas
    "WorkflowInstanceResponse",
    "WorkflowInstanceDetailResponse",
    "WorkflowTaskResponse",
    "WorkflowHistoryResponse",
    "ApprovalActionRequest",
    "DelegateTaskRequest",
    "CancelWorkflowRequest",
    # Template schemas
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "TemplatePreviewRequest",
    "TemplatePreviewResponse",
]
