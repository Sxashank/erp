"""Approval/Maker-Checker workflow schemas."""

from app.schemas.approval.approval import (
    # Workflow Configuration
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalWorkflowResponse,
    ApprovalWorkflowLevelCreate,
    ApprovalWorkflowLevelResponse,
    # Approval Requests
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalRequestListResponse,
    ApprovalRequestActionCreate,
    ApprovalRequestActionResponse,
    # Query/Filter
    ApprovalRequestFilter,
    PendingApprovalResponse,
    # Dashboard
    ApprovalDashboardResponse,
)

__all__ = [
    # Workflow Configuration
    "ApprovalWorkflowCreate",
    "ApprovalWorkflowUpdate",
    "ApprovalWorkflowResponse",
    "ApprovalWorkflowLevelCreate",
    "ApprovalWorkflowLevelResponse",
    # Approval Requests
    "ApprovalRequestCreate",
    "ApprovalRequestResponse",
    "ApprovalRequestListResponse",
    "ApprovalRequestActionCreate",
    "ApprovalRequestActionResponse",
    # Query/Filter
    "ApprovalRequestFilter",
    "PendingApprovalResponse",
    # Dashboard
    "ApprovalDashboardResponse",
]
