"""Workflow engine enums."""

import enum


class WorkflowEntityType(str, enum.Enum):
    """Types of entities that can have workflows."""

    VOUCHER = "VOUCHER"
    PURCHASE_BILL = "PURCHASE_BILL"
    SALES_INVOICE = "SALES_INVOICE"
    PAYMENT = "PAYMENT"
    JOURNAL_ENTRY = "JOURNAL_ENTRY"
    LOAN_APPLICATION = "LOAN_APPLICATION"
    LOAN_SANCTION = "LOAN_SANCTION"
    LOAN_RATING = "LOAN_RATING"


class WorkflowStepType(str, enum.Enum):
    """Types of workflow steps."""

    APPROVAL = "APPROVAL"
    NOTIFICATION = "NOTIFICATION"
    CONDITIONAL = "CONDITIONAL"
    PARALLEL_GATE = "PARALLEL_GATE"


class ApprovalMode(str, enum.Enum):
    """How approvals are processed at a step."""

    SEQUENTIAL = "SEQUENTIAL"  # One approver at a time in sequence
    PARALLEL_ANY = "PARALLEL_ANY"  # Any one approver can approve
    PARALLEL_ALL = "PARALLEL_ALL"  # All approvers must approve


class ApproverType(str, enum.Enum):
    """Types of approvers that can be assigned."""

    USER = "USER"  # Specific user
    ROLE = "ROLE"  # Users with specific role
    DESIGNATION = "DESIGNATION"  # Users with specific designation
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"  # Head of the department
    REPORTING_MANAGER = "REPORTING_MANAGER"  # Reporting manager of initiator
    DYNAMIC = "DYNAMIC"  # Based on entity field


class EscalationType(str, enum.Enum):
    """Types of escalation actions."""

    NOTIFY = "NOTIFY"  # Send reminder notification
    REASSIGN = "REASSIGN"  # Reassign to different approver
    AUTO_APPROVE = "AUTO_APPROVE"  # Automatically approve
    AUTO_REJECT = "AUTO_REJECT"  # Automatically reject


class WorkflowInstanceStatus(str, enum.Enum):
    """Status of a workflow instance."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class TaskStatus(str, enum.Enum):
    """Status of an individual workflow task."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    SKIPPED = "SKIPPED"


class StepAction(str, enum.Enum):
    """Actions to take after a step completes."""

    NEXT = "NEXT"  # Move to next step
    COMPLETE = "COMPLETE"  # Complete the workflow
    GOTO = "GOTO"  # Go to specific step
    REJECT = "REJECT"  # Reject the workflow
    PREVIOUS = "PREVIOUS"  # Go back to previous step


class WorkflowAction(str, enum.Enum):
    """Actions recorded in workflow history."""

    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    DELEGATED = "DELEGATED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    STEP_ENTERED = "STEP_ENTERED"
    STEP_COMPLETED = "STEP_COMPLETED"
