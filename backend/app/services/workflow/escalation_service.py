"""Workflow escalation service for handling timeouts and escalations."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workflow import (
    WorkflowTask,
    WorkflowInstance,
    WorkflowStep,
    EscalationRule,
    WorkflowHistory,
    TaskStatus,
    WorkflowInstanceStatus,
    EscalationType,
)
from app.services.workflow.notification_service import NotificationService
from app.services.workflow.approval_resolver import ApprovalResolver

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for handling workflow escalations and timeouts."""

    def __init__(self, db: AsyncSession):
        """Initialize escalation service."""
        self.db = db
        self.notification_service = NotificationService(db)
        self.approval_resolver = ApprovalResolver(db)

    async def check_and_escalate(self) -> int:
        """
        Check all pending tasks for escalation.

        This should be run periodically (e.g., every 15 minutes).

        Returns:
            Number of tasks escalated
        """
        logger.info("Starting escalation check...")

        escalated_count = 0

        # Get all pending tasks that are overdue
        pending_tasks = await self._get_overdue_tasks()
        logger.info(f"Found {len(pending_tasks)} overdue tasks to check")

        for task in pending_tasks:
            try:
                escalated = await self._process_task_escalation(task)
                if escalated:
                    escalated_count += 1
            except Exception as e:
                logger.error(f"Error processing escalation for task {task.id}: {e}")

        await self.db.commit()
        logger.info(f"Escalation check complete. Escalated {escalated_count} tasks.")
        return escalated_count

    async def _get_overdue_tasks(self) -> List[WorkflowTask]:
        """Get all pending tasks that are past their due date."""
        now = datetime.utcnow()

        query = (
            select(WorkflowTask)
            .options(
                selectinload(WorkflowTask.workflow_instance),
                selectinload(WorkflowTask.workflow_step).selectinload(
                    WorkflowStep.escalation_rules
                ),
            )
            .where(
                and_(
                    WorkflowTask.status == TaskStatus.PENDING,
                    WorkflowTask.is_active == True,
                    WorkflowTask.due_at < now,
                )
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _process_task_escalation(self, task: WorkflowTask) -> bool:
        """
        Process escalation for a single task.

        Returns:
            True if task was escalated
        """
        if not task.workflow_step:
            logger.warning(f"Task {task.id} has no workflow step")
            return False

        # Get escalation rules for this step
        escalation_rules = sorted(
            task.workflow_step.escalation_rules,
            key=lambda r: r.level
        )

        if not escalation_rules:
            # No escalation rules - just mark as overdue
            task.is_overdue = True
            return False

        # Find the appropriate escalation rule based on current level
        current_level = task.escalation_level
        next_rule = None

        for rule in escalation_rules:
            if rule.level > current_level:
                # Check if enough time has passed for this escalation level
                hours_overdue = self._hours_since(task.due_at)
                if hours_overdue >= rule.timeout_hours:
                    next_rule = rule
                    break

        if not next_rule:
            # Not yet time for next escalation
            task.is_overdue = True
            return False

        # Apply escalation
        return await self._apply_escalation(task, next_rule)

    async def _apply_escalation(
        self,
        task: WorkflowTask,
        rule: EscalationRule
    ) -> bool:
        """Apply an escalation rule to a task."""
        logger.info(
            f"Applying escalation level {rule.level} to task {task.id}: "
            f"{rule.escalation_type.value}"
        )

        instance = task.workflow_instance
        original_assignee = task.assigned_to

        if rule.escalation_type == EscalationType.NOTIFY:
            # Just send notification, don't change assignment
            await self._send_reminder(task, instance, rule)
            task.escalation_level = rule.level
            task.escalated_at = datetime.utcnow()
            task.is_overdue = True

        elif rule.escalation_type == EscalationType.REASSIGN:
            # Reassign to escalation target
            new_assignee = await self._resolve_escalation_target(rule, instance)
            if new_assignee:
                task.assigned_to = new_assignee
                task.assigned_at = datetime.utcnow()
                task.escalation_level = rule.level
                task.escalated_at = datetime.utcnow()
                task.is_overdue = False  # Reset overdue since reassigned

                # Send notification to new assignee
                await self.notification_service.send_escalation_notice(
                    task=task,
                    instance=instance,
                    escalate_to=new_assignee,
                    original_approver_id=original_assignee,
                    escalation_level=rule.level,
                )

                # Notify original assignee if configured
                if rule.notify_current_approver:
                    await self._notify_escalation_to_original(
                        task, instance, original_assignee, rule.level
                    )
            else:
                logger.warning(
                    f"Could not resolve escalation target for rule {rule.id}"
                )
                return False

        elif rule.escalation_type == EscalationType.AUTO_APPROVE:
            # Auto-approve the task
            task.status = TaskStatus.APPROVED
            task.action_taken = "AUTO_APPROVED"
            task.comments = f"Auto-approved due to timeout (escalation level {rule.level})"
            task.acted_at = datetime.utcnow()
            task.escalation_level = rule.level
            task.escalated_at = datetime.utcnow()

            # Record in history
            await self._record_escalation_history(
                instance, task, "AUTO_APPROVED", rule.level
            )

            # Trigger next step processing (would need WorkflowEngine)
            logger.info(f"Task {task.id} auto-approved due to escalation")

        elif rule.escalation_type == EscalationType.AUTO_REJECT:
            # Auto-reject the task
            task.status = TaskStatus.REJECTED
            task.action_taken = "AUTO_REJECTED"
            task.comments = f"Auto-rejected due to timeout (escalation level {rule.level})"
            task.acted_at = datetime.utcnow()
            task.escalation_level = rule.level
            task.escalated_at = datetime.utcnow()

            # Update instance status
            instance.status = WorkflowInstanceStatus.REJECTED
            instance.completed_at = datetime.utcnow()

            # Record in history
            await self._record_escalation_history(
                instance, task, "AUTO_REJECTED", rule.level
            )

            # Notify initiator
            await self.notification_service.send_approval_complete(
                instance=instance,
                action="REJECTED",
                action_by=task.assigned_to,
                comments=task.comments,
            )

        return True

    async def _resolve_escalation_target(
        self,
        rule: EscalationRule,
        instance: WorkflowInstance
    ) -> Optional[UUID]:
        """Resolve the user ID for escalation target."""
        if rule.escalate_to_user_id:
            return rule.escalate_to_user_id

        if rule.escalate_to_role_id:
            # Get any user with this role in the organization
            users = await self.approval_resolver.resolve_role_users(
                rule.escalate_to_role_id,
                instance.organization_id,
            )
            if users:
                return users[0]  # Return first available user

        if rule.escalate_to_type:
            # Resolve based on type (similar to approval resolver)
            from app.models.workflow import ApproverType

            if rule.escalate_to_type == ApproverType.DESIGNATION:
                users = await self.approval_resolver.resolve_designation_users(
                    rule.escalate_to_designation or "",
                    instance.organization_id,
                )
                if users:
                    return users[0]

        return None

    async def _send_reminder(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance,
        rule: EscalationRule
    ) -> None:
        """Send reminder notification for overdue task."""
        # Send to current assignee
        await self.notification_service.send_approval_request(
            task=task,
            instance=instance,
        )

        # Notify initiator if configured
        if rule.notify_initiator:
            # Would implement initiator notification here
            pass

    async def _notify_escalation_to_original(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance,
        original_assignee: UUID,
        escalation_level: int,
    ) -> None:
        """Notify original assignee that task was escalated."""
        # This would send a notification informing them the task was reassigned
        # Implementation similar to escalation notice but for original assignee
        pass

    async def _record_escalation_history(
        self,
        instance: WorkflowInstance,
        task: WorkflowTask,
        action: str,
        escalation_level: int,
    ) -> None:
        """Record escalation action in workflow history."""
        history = WorkflowHistory(
            workflow_instance_id=instance.id,
            action=action,
            action_by=task.assigned_to,  # System action, use assigned user
            action_at=datetime.utcnow(),
            from_step_id=task.workflow_step_id,
            to_step_id=task.workflow_step_id,
            from_status=TaskStatus.PENDING.value,
            to_status=action,
            comments=f"Escalation level {escalation_level}",
            action_metadata={"escalation_level": escalation_level},
        )
        self.db.add(history)

    def _hours_since(self, dt: datetime) -> float:
        """Calculate hours since a given datetime."""
        if not dt:
            return 0
        delta = datetime.utcnow() - dt
        return delta.total_seconds() / 3600

    async def send_daily_digest(self) -> int:
        """
        Send daily digest of pending approvals to all users with pending tasks.

        Returns:
            Number of digest emails sent
        """
        logger.info("Starting daily digest...")

        # Get all pending tasks grouped by assignee
        query = (
            select(WorkflowTask)
            .options(
                selectinload(WorkflowTask.workflow_instance),
                selectinload(WorkflowTask.workflow_step),
                selectinload(WorkflowTask.assignee),
            )
            .where(
                and_(
                    WorkflowTask.status == TaskStatus.PENDING,
                    WorkflowTask.is_active == True,
                )
            )
            .order_by(WorkflowTask.assigned_to, WorkflowTask.created_at)
        )

        result = await self.db.execute(query)
        tasks = list(result.scalars().all())

        # Group by assignee
        tasks_by_user = {}
        for task in tasks:
            user_id = task.assigned_to
            if user_id not in tasks_by_user:
                tasks_by_user[user_id] = []
            tasks_by_user[user_id].append(task)

        sent_count = 0
        for user_id, user_tasks in tasks_by_user.items():
            try:
                if await self._send_user_digest(user_id, user_tasks):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending digest to user {user_id}: {e}")

        logger.info(f"Daily digest complete. Sent {sent_count} emails.")
        return sent_count

    async def _send_user_digest(
        self,
        user_id: UUID,
        tasks: List[WorkflowTask]
    ) -> bool:
        """Send digest email to a user."""
        from app.models.auth.user import User
        from app.services.email import email_service

        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.email:
            return False

        # Build digest HTML
        task_rows = ""
        for task in tasks:
            instance = task.workflow_instance
            overdue_badge = '<span style="color: red;">[OVERDUE]</span>' if task.is_overdue else ""
            task_rows += f"""
            <tr>
                <td>{instance.entity_reference if instance else 'N/A'}</td>
                <td>{instance.entity_type.value if instance and instance.entity_type else 'N/A'}</td>
                <td>{task.workflow_step.name if task.workflow_step else 'N/A'}</td>
                <td>{task.assigned_at.strftime('%Y-%m-%d') if task.assigned_at else 'N/A'}</td>
                <td>{overdue_badge}</td>
            </tr>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #2563eb; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>Daily Approval Digest</h2>
            <p>Hello {user.full_name},</p>
            <p>You have <strong>{len(tasks)}</strong> pending approval(s):</p>

            <table>
                <tr>
                    <th>Reference</th>
                    <th>Type</th>
                    <th>Step</th>
                    <th>Assigned</th>
                    <th>Status</th>
                </tr>
                {task_rows}
            </table>

            <p style="margin-top: 20px;">
                <a href="http://localhost:3000/workflows/tasks/pending"
                   style="padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px;">
                    View All Pending Tasks
                </a>
            </p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated daily digest from SMFC ERP.
            </p>
        </body>
        </html>
        """

        return await email_service.send_email(
            to=[user.email],
            subject=f"[SMFC ERP] Daily Digest: {len(tasks)} Pending Approval(s)",
            html_body=html_body,
        )

    async def cleanup_old_instances(self, days_old: int = 90) -> int:
        """
        Archive/cleanup old completed workflow instances.

        Args:
            days_old: Archive instances older than this many days

        Returns:
            Number of instances archived
        """
        logger.info(f"Starting cleanup of instances older than {days_old} days...")

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Soft delete old completed instances
        stmt = (
            update(WorkflowInstance)
            .where(
                and_(
                    WorkflowInstance.status.in_([
                        WorkflowInstanceStatus.APPROVED,
                        WorkflowInstanceStatus.REJECTED,
                        WorkflowInstanceStatus.CANCELLED,
                    ]),
                    WorkflowInstance.completed_at < cutoff_date,
                    WorkflowInstance.is_active == True,
                )
            )
            .values(is_active=False)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        count = result.rowcount
        logger.info(f"Cleanup complete. Archived {count} old instances.")
        return count
