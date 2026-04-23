"""Workflow notification service."""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import User
from app.models.workflow import (
    WorkflowInstance,
    WorkflowTask,
    NotificationTemplate,
    WorkflowEntityType,
)
from app.services.email import email_service

logger = logging.getLogger(__name__)


# Default email templates
DEFAULT_TEMPLATES = {
    "APPROVAL_PENDING": {
        "subject": "[{app_name}] Approval Required: {entity_type} - {entity_reference}",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2563eb; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        .btn-reject { background-color: #dc2626; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Approval Required</h1>
        </div>
        <div class="content">
            <p>Hello {approver_name},</p>
            <p>A new {entity_type} requires your approval.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Amount:</strong> {amount}</p>
                <p><strong>Submitted By:</strong> {initiator_name}</p>
                <p><strong>Step:</strong> {step_name}</p>
                <p><strong>Due By:</strong> {due_date}</p>
            </div>

            <p>Please review and take appropriate action.</p>

            <p style="text-align: center;">
                <a href="{app_url}/workflows/tasks/{task_id}" class="btn">Review & Approve</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message from {app_name}.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    },
    "APPROVAL_APPROVED": {
        "subject": "[{app_name}] Approved: {entity_type} - {entity_reference}",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #16a34a; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Approval Completed</h1>
        </div>
        <div class="content">
            <p>Hello {initiator_name},</p>
            <p>Your {entity_type} has been <strong style="color: #16a34a;">approved</strong>.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Amount:</strong> {amount}</p>
                <p><strong>Approved By:</strong> {approver_name}</p>
                <p><strong>Comments:</strong> {comments}</p>
            </div>

            <p>The {entity_type} will now be processed accordingly.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from {app_name}.</p>
        </div>
    </div>
</body>
</html>
"""
    },
    "APPROVAL_REJECTED": {
        "subject": "[{app_name}] Rejected: {entity_type} - {entity_reference}",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #dc2626; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Approval Rejected</h1>
        </div>
        <div class="content">
            <p>Hello {initiator_name},</p>
            <p>Your {entity_type} has been <strong style="color: #dc2626;">rejected</strong>.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Amount:</strong> {amount}</p>
                <p><strong>Rejected By:</strong> {approver_name}</p>
                <p><strong>Reason:</strong> {comments}</p>
            </div>

            <p>Please review the comments and make necessary corrections before resubmitting.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from {app_name}.</p>
        </div>
    </div>
</body>
</html>
"""
    },
    "ESCALATION_NOTICE": {
        "subject": "[{app_name}] ESCALATION: {entity_type} - {entity_reference} requires attention",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f59e0b; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #f59e0b; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Escalation Notice</h1>
        </div>
        <div class="content">
            <p>Hello {escalate_to_name},</p>
            <p>A {entity_type} approval has been <strong style="color: #f59e0b;">escalated</strong> to you due to timeout.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Amount:</strong> {amount}</p>
                <p><strong>Original Approver:</strong> {original_approver}</p>
                <p><strong>Escalation Level:</strong> {escalation_level}</p>
                <p><strong>Pending Since:</strong> {pending_since}</p>
            </div>

            <p>Please review and take action immediately.</p>

            <p style="text-align: center;">
                <a href="{app_url}/workflows/tasks/{task_id}" class="btn">Review Now</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated escalation from {app_name}.</p>
        </div>
    </div>
</body>
</html>
"""
    },
    "DELEGATION_NOTICE": {
        "subject": "[{app_name}] Task Delegated: {entity_type} - {entity_reference}",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #8b5cf6; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #8b5cf6; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Task Delegated to You</h1>
        </div>
        <div class="content">
            <p>Hello {delegate_to_name},</p>
            <p>An approval task has been <strong>delegated</strong> to you.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Entity Type:</strong> {entity_type}</p>
                <p><strong>Amount:</strong> {amount}</p>
                <p><strong>Delegated By:</strong> {delegated_by_name}</p>
                <p><strong>Reason:</strong> {delegation_reason}</p>
            </div>

            <p>Please review and take action.</p>

            <p style="text-align: center;">
                <a href="{app_url}/workflows/tasks/{task_id}" class="btn">Review Task</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message from {app_name}.</p>
        </div>
    </div>
</body>
</html>
"""
    },
    "WORKFLOW_CANCELLED": {
        "subject": "[{app_name}] Workflow Cancelled: {entity_type} - {entity_reference}",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6b7280; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9fafb; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Workflow Cancelled</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>The workflow for {entity_type} has been <strong>cancelled</strong>.</p>

            <div class="details">
                <p><strong>Reference:</strong> {entity_reference}</p>
                <p><strong>Cancelled By:</strong> {cancelled_by_name}</p>
                <p><strong>Reason:</strong> {cancellation_reason}</p>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated message from {app_name}.</p>
        </div>
    </div>
</body>
</html>
"""
    },
}


class NotificationService:
    """Service for sending workflow notifications."""

    def __init__(self, db: AsyncSession):
        """Initialize notification service."""
        self.db = db
        self.app_name = "SMFC ERP"
        self.app_url = "http://localhost:3000"  # TODO: Get from config

    async def send_approval_request(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance,
    ) -> bool:
        """
        Send approval request notification to assignee.

        Args:
            task: The workflow task
            instance: The workflow instance

        Returns:
            True if notification was sent
        """
        try:
            # Get assignee
            assignee = await self._get_user(task.assigned_to)
            if not assignee or not assignee.email:
                logger.warning(f"No email found for assignee {task.assigned_to}")
                return False

            # Get initiator
            initiator = await self._get_user(instance.started_by)

            # Get template
            template = await self._get_template(
                "APPROVAL_PENDING",
                instance.entity_type,
                instance.organization_id,
            )

            # Build context
            context = self._build_context(
                instance=instance,
                task=task,
                approver=assignee,
                initiator=initiator,
            )

            # Send email
            return await email_service.send_template_email(
                to=[assignee.email],
                subject_template=template["subject"],
                body_template=template["body"],
                context=context,
            )

        except Exception as e:
            logger.error(f"Error sending approval request: {e}")
            return False

    async def send_approval_complete(
        self,
        instance: WorkflowInstance,
        action: str,
        action_by: UUID,
        comments: Optional[str] = None,
    ) -> bool:
        """
        Send approval completion notification to initiator.

        Args:
            instance: The workflow instance
            action: APPROVED or REJECTED
            action_by: User who took action
            comments: Optional comments

        Returns:
            True if notification was sent
        """
        try:
            # Get initiator
            initiator = await self._get_user(instance.started_by)
            if not initiator or not initiator.email:
                logger.warning(f"No email found for initiator {instance.started_by}")
                return False

            # Get approver
            approver = await self._get_user(action_by)

            # Get template based on action
            template_code = "APPROVAL_APPROVED" if action == "APPROVED" else "APPROVAL_REJECTED"
            template = await self._get_template(
                template_code,
                instance.entity_type,
                instance.organization_id,
            )

            # Build context
            context = self._build_context(
                instance=instance,
                approver=approver,
                initiator=initiator,
            )
            context["comments"] = comments or "No comments provided"

            # Send email
            return await email_service.send_template_email(
                to=[initiator.email],
                subject_template=template["subject"],
                body_template=template["body"],
                context=context,
            )

        except Exception as e:
            logger.error(f"Error sending approval complete notification: {e}")
            return False

    async def send_escalation_notice(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance,
        escalate_to: UUID,
        original_approver_id: UUID,
        escalation_level: int,
    ) -> bool:
        """
        Send escalation notification.

        Args:
            task: The workflow task
            instance: The workflow instance
            escalate_to: User being escalated to
            original_approver_id: Original approver
            escalation_level: Current escalation level

        Returns:
            True if notification was sent
        """
        try:
            # Get escalation target
            escalate_to_user = await self._get_user(escalate_to)
            if not escalate_to_user or not escalate_to_user.email:
                logger.warning(f"No email found for escalation target {escalate_to}")
                return False

            # Get original approver
            original_approver = await self._get_user(original_approver_id)
            initiator = await self._get_user(instance.started_by)

            # Get template
            template = await self._get_template(
                "ESCALATION_NOTICE",
                instance.entity_type,
                instance.organization_id,
            )

            # Build context
            context = self._build_context(
                instance=instance,
                task=task,
                initiator=initiator,
            )
            context["escalate_to_name"] = escalate_to_user.full_name
            context["original_approver"] = original_approver.full_name if original_approver else "Unknown"
            context["escalation_level"] = escalation_level
            context["pending_since"] = task.assigned_at.strftime("%Y-%m-%d %H:%M") if task.assigned_at else "N/A"

            # Send email
            return await email_service.send_template_email(
                to=[escalate_to_user.email],
                subject_template=template["subject"],
                body_template=template["body"],
                context=context,
            )

        except Exception as e:
            logger.error(f"Error sending escalation notice: {e}")
            return False

    async def send_delegation_notice(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance,
        delegate_to: UUID,
        delegated_by: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Send delegation notification.

        Args:
            task: The workflow task
            instance: The workflow instance
            delegate_to: User being delegated to
            delegated_by: User who delegated
            reason: Delegation reason

        Returns:
            True if notification was sent
        """
        try:
            # Get delegate
            delegate_user = await self._get_user(delegate_to)
            if not delegate_user or not delegate_user.email:
                logger.warning(f"No email found for delegate {delegate_to}")
                return False

            # Get delegator
            delegator = await self._get_user(delegated_by)
            initiator = await self._get_user(instance.started_by)

            # Get template
            template = await self._get_template(
                "DELEGATION_NOTICE",
                instance.entity_type,
                instance.organization_id,
            )

            # Build context
            context = self._build_context(
                instance=instance,
                task=task,
                initiator=initiator,
            )
            context["delegate_to_name"] = delegate_user.full_name
            context["delegated_by_name"] = delegator.full_name if delegator else "Unknown"
            context["delegation_reason"] = reason or "No reason provided"

            # Send email
            return await email_service.send_template_email(
                to=[delegate_user.email],
                subject_template=template["subject"],
                body_template=template["body"],
                context=context,
            )

        except Exception as e:
            logger.error(f"Error sending delegation notice: {e}")
            return False

    async def send_cancellation_notice(
        self,
        instance: WorkflowInstance,
        cancelled_by: UUID,
        reason: Optional[str] = None,
        notify_users: Optional[List[UUID]] = None,
    ) -> bool:
        """
        Send workflow cancellation notification.

        Args:
            instance: The workflow instance
            cancelled_by: User who cancelled
            reason: Cancellation reason
            notify_users: List of user IDs to notify

        Returns:
            True if notifications were sent
        """
        try:
            # Default to notifying initiator
            if not notify_users:
                notify_users = [instance.started_by]

            # Get canceller
            canceller = await self._get_user(cancelled_by)

            # Get template
            template = await self._get_template(
                "WORKFLOW_CANCELLED",
                instance.entity_type,
                instance.organization_id,
            )

            # Build context
            context = self._build_context(instance=instance)
            context["cancelled_by_name"] = canceller.full_name if canceller else "Unknown"
            context["cancellation_reason"] = reason or "No reason provided"

            success = True
            for user_id in notify_users:
                user = await self._get_user(user_id)
                if user and user.email:
                    result = await email_service.send_template_email(
                        to=[user.email],
                        subject_template=template["subject"],
                        body_template=template["body"],
                        context=context,
                    )
                    success = success and result

            return success

        except Exception as e:
            logger.error(f"Error sending cancellation notice: {e}")
            return False

    async def _get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_template(
        self,
        code: str,
        entity_type: WorkflowEntityType,
        organization_id: UUID,
    ) -> dict:
        """
        Get notification template.

        First checks for org-specific template, then entity-specific,
        then falls back to default templates.
        """
        # Try org + entity specific template
        result = await self.db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.organization_id == organization_id,
                NotificationTemplate.code == code,
                NotificationTemplate.entity_type == entity_type,
                NotificationTemplate.is_active == True,
            )
        )
        template = result.scalar_one_or_none()

        if not template:
            # Try org specific generic template
            result = await self.db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.organization_id == organization_id,
                    NotificationTemplate.code == code,
                    NotificationTemplate.entity_type.is_(None),
                    NotificationTemplate.is_active == True,
                )
            )
            template = result.scalar_one_or_none()

        if template:
            return {
                "subject": template.email_subject,
                "body": template.email_body,
            }

        # Fall back to default templates
        if code in DEFAULT_TEMPLATES:
            return DEFAULT_TEMPLATES[code]

        # Ultimate fallback
        return {
            "subject": f"[{self.app_name}] Workflow Notification",
            "body": "<p>A workflow event has occurred.</p>",
        }

    def _build_context(
        self,
        instance: WorkflowInstance,
        task: Optional[WorkflowTask] = None,
        approver: Optional[User] = None,
        initiator: Optional[User] = None,
    ) -> dict:
        """Build template context from workflow objects."""
        context = {
            "app_name": self.app_name,
            "app_url": self.app_url,
            "entity_type": instance.entity_type.value if instance.entity_type else "",
            "entity_reference": instance.entity_reference or "",
            "entity_id": str(instance.entity_id),
            "workflow_instance_id": str(instance.id),
        }

        # Add amount from context data
        if instance.context_data:
            context["amount"] = instance.context_data.get("amount", "N/A")
        else:
            context["amount"] = "N/A"

        if task:
            context["task_id"] = str(task.id)
            context["step_name"] = ""  # Will be filled if step is loaded
            context["due_date"] = task.due_at.strftime("%Y-%m-%d %H:%M") if task.due_at else "N/A"

        if approver:
            context["approver_name"] = approver.full_name

        if initiator:
            context["initiator_name"] = initiator.full_name

        return context
