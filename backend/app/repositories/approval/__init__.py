"""Approval repositories."""

from app.repositories.approval.approval_repo import (
    ApprovalWorkflowRepository,
    ApprovalRequestRepository,
)

__all__ = [
    "ApprovalWorkflowRepository",
    "ApprovalRequestRepository",
]
