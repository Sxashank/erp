"""Workflow models package."""

from app.models.workflow.enums import (
    WorkflowEntityType,
    WorkflowStepType,
    ApprovalMode,
    ApproverType,
    EscalationType,
    WorkflowInstanceStatus,
    TaskStatus,
    StepAction,
    WorkflowAction,
)
from app.models.workflow.workflow_definition import WorkflowDefinition
from app.models.workflow.workflow_step import WorkflowStep
from app.models.workflow.approval_rule import ApprovalRule
from app.models.workflow.escalation_rule import EscalationRule
from app.models.workflow.notification_template import WorkflowNotificationTemplate
# Alias for backward compatibility
NotificationTemplate = WorkflowNotificationTemplate
from app.models.workflow.workflow_instance import WorkflowInstance
from app.models.workflow.workflow_task import WorkflowTask
from app.models.workflow.workflow_history import WorkflowHistory

__all__ = [
    # Enums
    "WorkflowEntityType",
    "WorkflowStepType",
    "ApprovalMode",
    "ApproverType",
    "EscalationType",
    "WorkflowInstanceStatus",
    "TaskStatus",
    "StepAction",
    "WorkflowAction",
    # Models
    "WorkflowDefinition",
    "WorkflowStep",
    "ApprovalRule",
    "EscalationRule",
    "WorkflowNotificationTemplate",
    "NotificationTemplate",  # Alias for backward compatibility
    "WorkflowInstance",
    "WorkflowTask",
    "WorkflowHistory",
]
