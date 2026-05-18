"""Workflow engine - core workflow processing service."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowTask,
    WorkflowHistory,
    WorkflowEntityType,
    WorkflowInstanceStatus,
    TaskStatus,
    ApprovalMode,
    StepAction,
    WorkflowAction,
)


class WorkflowEngine:
    """Core workflow processing engine."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_workflow(
        self,
        entity_type: WorkflowEntityType,
        entity_id: UUID,
        entity_reference: str,
        organization_id: UUID,
        context: Dict[str, Any],
        started_by: UUID,
    ) -> WorkflowInstance:
        """
        Start a new workflow instance for an entity.

        Args:
            entity_type: Type of entity (VOUCHER, PURCHASE_BILL, etc.)
            entity_id: ID of the entity
            entity_reference: Human-readable reference (voucher number, etc.)
            organization_id: Organization ID
            context: Entity context data for condition evaluation
            started_by: User starting the workflow

        Returns:
            Created WorkflowInstance
        """
        # Find matching workflow definition
        definition = await self._find_matching_workflow(
            organization_id, entity_type, context
        )
        if not definition:
            raise NotFoundException(
                f"No workflow definition found for {entity_type.value}"
            )

        # Check if workflow already exists for this entity
        existing = await self._get_active_instance(entity_type, entity_id)
        if existing:
            raise ConflictException(
                f"Active workflow already exists for {entity_reference}"
            )

        # Create workflow instance
        now = datetime.now(timezone.utc)
        instance = WorkflowInstance(
            workflow_definition_id=definition.id,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            status=WorkflowInstanceStatus.IN_PROGRESS,
            context_data=context,
            started_at=now,
            started_by=started_by,
            current_step_number=1,
            created_by=started_by,
        )
        self.session.add(instance)
        await self.session.flush()

        # Get first step
        first_step = await self._get_step_by_number(definition.id, 1)
        if not first_step:
            raise BadRequestException("Workflow has no steps defined")

        # Check if first step conditions are met
        if not await self._evaluate_entry_conditions(first_step, context):
            # Skip to next applicable step
            first_step = await self._find_next_applicable_step(
                definition.id, 1, context
            )

        if first_step:
            instance.current_step_id = first_step.id
            instance.current_step_number = first_step.step_number

            # Create tasks for first step
            await self._create_tasks_for_step(instance, first_step, started_by)

        # Record history
        await self._record_history(
            instance=instance,
            action=WorkflowAction.STARTED,
            action_by=started_by,
            to_status=WorkflowInstanceStatus.IN_PROGRESS.value,
            to_step=first_step,
            comments=f"Workflow started for {entity_reference}",
        )

        await self.session.flush()
        return instance

    async def process_approval(
        self,
        task_id: UUID,
        action: str,  # "APPROVE" or "REJECT"
        comments: Optional[str],
        action_by: UUID,
    ) -> WorkflowInstance:
        """
        Process an approval action on a task.

        Args:
            task_id: ID of the task to process
            action: "APPROVE" or "REJECT"
            comments: Optional comments
            action_by: User performing the action

        Returns:
            Updated WorkflowInstance
        """
        # Get task with related data
        task = await self._get_task(task_id)
        if not task:
            raise NotFoundException("Task not found")

        if task.status != TaskStatus.PENDING:
            raise BadRequestException(f"Task is not pending (status: {task.status})")

        if task.assigned_to != action_by:
            raise BadRequestException("You are not assigned to this task")

        instance = task.workflow_instance
        if instance.status not in [
            WorkflowInstanceStatus.IN_PROGRESS,
            WorkflowInstanceStatus.PENDING,
        ]:
            raise BadRequestException(
                f"Workflow is not in progress (status: {instance.status})"
            )

        step = task.workflow_step
        definition = instance.workflow_definition

        # Check if comments required for rejection
        if action == "REJECT" and definition.require_comments_on_reject and not comments:
            raise BadRequestException("Comments are required when rejecting")

        # Update task
        now = datetime.now(timezone.utc)
        task.status = TaskStatus.APPROVED if action == "APPROVE" else TaskStatus.REJECTED
        task.action_taken = action
        task.comments = comments
        task.acted_at = now
        task.updated_by = action_by

        # Record task history
        await self._record_history(
            instance=instance,
            action=WorkflowAction.APPROVED if action == "APPROVE" else WorkflowAction.REJECTED,
            action_by=action_by,
            from_step=step,
            to_step=step,
            from_status=instance.status.value,
            to_status=instance.status.value,
            comments=comments,
            task=task,
        )

        # Check if step is complete
        is_approved = action == "APPROVE"
        step_complete = await self._check_step_completion(instance, step, is_approved)

        if step_complete:
            # Determine next action
            if is_approved:
                await self._handle_step_approval(instance, step, action_by)
            else:
                await self._handle_step_rejection(instance, step, action_by, comments)

        await self.session.flush()

        # Reload instance with fresh data
        return await self._get_instance(instance.id)

    async def cancel_workflow(
        self,
        instance_id: UUID,
        reason: str,
        cancelled_by: UUID,
    ) -> WorkflowInstance:
        """Cancel an active workflow."""
        instance = await self._get_instance(instance_id)
        if not instance:
            raise NotFoundException("Workflow instance not found")

        if instance.status not in [
            WorkflowInstanceStatus.PENDING,
            WorkflowInstanceStatus.IN_PROGRESS,
        ]:
            raise BadRequestException("Workflow cannot be cancelled")

        definition = instance.workflow_definition
        if not definition.allow_withdrawal:
            raise BadRequestException("This workflow does not allow cancellation")

        # Cancel all pending tasks
        for task in instance.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.SKIPPED
                task.comments = "Workflow cancelled"
                task.updated_by = cancelled_by

        # Update instance
        now = datetime.now(timezone.utc)
        instance.status = WorkflowInstanceStatus.CANCELLED
        instance.cancelled_at = now
        instance.cancelled_by = cancelled_by
        instance.cancellation_reason = reason
        instance.updated_by = cancelled_by

        # Record history
        await self._record_history(
            instance=instance,
            action=WorkflowAction.CANCELLED,
            action_by=cancelled_by,
            from_status=WorkflowInstanceStatus.IN_PROGRESS.value,
            to_status=WorkflowInstanceStatus.CANCELLED.value,
            comments=reason,
        )

        await self.session.flush()
        return instance

    async def delegate_task(
        self,
        task_id: UUID,
        delegate_to: UUID,
        reason: str,
        delegated_by: UUID,
    ) -> WorkflowTask:
        """Delegate a task to another user."""
        task = await self._get_task(task_id)
        if not task:
            raise NotFoundException("Task not found")

        if task.status != TaskStatus.PENDING:
            raise BadRequestException("Only pending tasks can be delegated")

        if task.assigned_to != delegated_by:
            raise BadRequestException("You are not assigned to this task")

        step = task.workflow_step
        if not step.allow_delegation:
            raise BadRequestException("Delegation is not allowed for this step")

        # Update task
        now = datetime.now(timezone.utc)
        task.delegated_from = task.assigned_to
        task.assigned_to = delegate_to
        task.delegated_reason = reason
        task.delegated_at = now
        task.updated_by = delegated_by

        # Record history
        await self._record_history(
            instance=task.workflow_instance,
            action=WorkflowAction.DELEGATED,
            action_by=delegated_by,
            from_status=task.workflow_instance.status.value,
            to_status=task.workflow_instance.status.value,
            comments=f"Delegated to user: {delegate_to}. Reason: {reason}",
            task=task,
        )

        await self.session.flush()
        return task

    async def get_pending_tasks(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> List[WorkflowTask]:
        """Get all pending tasks for a user."""
        query = (
            select(WorkflowTask)
            .options(
                selectinload(WorkflowTask.workflow_instance),
                selectinload(WorkflowTask.workflow_step),
            )
            .where(
                and_(
                    WorkflowTask.assigned_to == user_id,
                    WorkflowTask.status == TaskStatus.PENDING,
                    WorkflowTask.is_active == True,
                )
            )
        )

        if organization_id:
            query = query.join(WorkflowInstance).where(
                WorkflowInstance.organization_id == organization_id
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_instance_history(
        self,
        instance_id: UUID,
    ) -> List[WorkflowHistory]:
        """Get full history for a workflow instance."""
        query = (
            select(WorkflowHistory)
            .options(
                selectinload(WorkflowHistory.actor),
                selectinload(WorkflowHistory.from_step),
                selectinload(WorkflowHistory.to_step),
            )
            .where(WorkflowHistory.workflow_instance_id == instance_id)
            .order_by(WorkflowHistory.action_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Private helper methods

    async def _find_matching_workflow(
        self,
        organization_id: UUID,
        entity_type: WorkflowEntityType,
        context: Dict[str, Any],
    ) -> Optional[WorkflowDefinition]:
        """Find the best matching workflow definition."""
        query = (
            select(WorkflowDefinition)
            .options(selectinload(WorkflowDefinition.steps))
            .where(
                and_(
                    WorkflowDefinition.organization_id == organization_id,
                    WorkflowDefinition.entity_type == entity_type,
                    WorkflowDefinition.is_active == True,
                )
            )
            .order_by(
                WorkflowDefinition.priority.desc(),
                WorkflowDefinition.is_default.desc(),
            )
        )

        result = await self.session.execute(query)
        definitions = list(result.scalars().all())

        # Find first definition whose conditions match
        for definition in definitions:
            if await self._evaluate_conditions(
                definition.activation_conditions, context
            ):
                return definition

        # Return default if no specific match
        for definition in definitions:
            if definition.is_default:
                return definition

        return definitions[0] if definitions else None

    async def _evaluate_conditions(
        self,
        conditions: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate JSONB conditions against context."""
        if not conditions:
            return True

        for key, value in conditions.items():
            # Handle comparison operators
            if key.endswith("_gte"):
                field = key[:-4]
                if field not in context:
                    return False
                if Decimal(str(context[field])) < Decimal(str(value)):
                    return False
            elif key.endswith("_gt"):
                field = key[:-3]
                if field not in context:
                    return False
                if Decimal(str(context[field])) <= Decimal(str(value)):
                    return False
            elif key.endswith("_lte"):
                field = key[:-4]
                if field not in context:
                    return False
                if Decimal(str(context[field])) > Decimal(str(value)):
                    return False
            elif key.endswith("_lt"):
                field = key[:-3]
                if field not in context:
                    return False
                if Decimal(str(context[field])) >= Decimal(str(value)):
                    return False
            elif key.endswith("_in"):
                field = key[:-3]
                if field not in context:
                    return False
                if context[field] not in value:
                    return False
            elif key.endswith("_ne"):
                field = key[:-3]
                if field in context and context[field] == value:
                    return False
            else:
                # Exact match
                if key not in context:
                    return False
                if context[key] != value:
                    return False

        return True

    async def _evaluate_entry_conditions(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> bool:
        """Check if step entry conditions are met."""
        return await self._evaluate_conditions(step.entry_conditions, context)

    async def _get_step_by_number(
        self,
        definition_id: UUID,
        step_number: int,
    ) -> Optional[WorkflowStep]:
        """Get a workflow step by its number."""
        query = (
            select(WorkflowStep)
            .options(
                selectinload(WorkflowStep.approval_rules),
                selectinload(WorkflowStep.escalation_rules),
            )
            .where(
                and_(
                    WorkflowStep.workflow_definition_id == definition_id,
                    WorkflowStep.step_number == step_number,
                    WorkflowStep.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _find_next_applicable_step(
        self,
        definition_id: UUID,
        current_step_number: int,
        context: Dict[str, Any],
    ) -> Optional[WorkflowStep]:
        """Find the next step whose entry conditions are met."""
        query = (
            select(WorkflowStep)
            .options(
                selectinload(WorkflowStep.approval_rules),
                selectinload(WorkflowStep.escalation_rules),
            )
            .where(
                and_(
                    WorkflowStep.workflow_definition_id == definition_id,
                    WorkflowStep.step_number > current_step_number,
                    WorkflowStep.is_active == True,
                )
            )
            .order_by(WorkflowStep.step_number)
        )
        result = await self.session.execute(query)
        steps = list(result.scalars().all())

        for step in steps:
            if await self._evaluate_entry_conditions(step, context):
                return step

        return None

    async def _create_tasks_for_step(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        created_by: UUID,
    ) -> List[WorkflowTask]:
        """Create approval tasks for a workflow step."""
        from app.services.workflow.approval_resolver import ApprovalResolver

        resolver = ApprovalResolver(self.session)
        tasks = []
        now = datetime.now(timezone.utc)

        for rule in step.approval_rules:
            # Check rule conditions
            if not await self._evaluate_conditions(
                rule.conditions, instance.context_data or {}
            ):
                continue

            # Resolve approvers
            approvers = await resolver.resolve_approvers(
                rule=rule,
                context=instance.context_data or {},
                organization_id=instance.organization_id,
                initiator_id=instance.started_by,
            )

            for i, approver_id in enumerate(approvers):
                # Check self-approval
                if approver_id == instance.started_by and not rule.can_self_approve:
                    continue

                due_at = None
                if step.sla_hours:
                    due_at = now + timedelta(hours=step.sla_hours)

                task = WorkflowTask(
                    workflow_instance_id=instance.id,
                    workflow_step_id=step.id,
                    assigned_to=approver_id,
                    assigned_at=now,
                    status=TaskStatus.PENDING,
                    due_at=due_at,
                    sequence=rule.sequence + i,
                    created_by=created_by,
                )
                self.session.add(task)
                tasks.append(task)

        await self.session.flush()
        return tasks

    async def _check_step_completion(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        is_approved: bool,
    ) -> bool:
        """Check if the current step is complete based on approval mode."""
        # Get all tasks for this step
        query = select(WorkflowTask).where(
            and_(
                WorkflowTask.workflow_instance_id == instance.id,
                WorkflowTask.workflow_step_id == step.id,
                WorkflowTask.is_active == True,
            )
        )
        result = await self.session.execute(query)
        tasks = list(result.scalars().all())

        if step.approval_mode == ApprovalMode.SEQUENTIAL:
            # All tasks in sequence must be approved
            pending = [t for t in tasks if t.status == TaskStatus.PENDING]
            rejected = [t for t in tasks if t.status == TaskStatus.REJECTED]
            if rejected:
                return True  # Rejected - step failed
            return len(pending) == 0  # Complete when no pending tasks

        elif step.approval_mode == ApprovalMode.PARALLEL_ANY:
            # Any one approval completes the step
            approved = [t for t in tasks if t.status == TaskStatus.APPROVED]
            rejected = [t for t in tasks if t.status == TaskStatus.REJECTED]
            if approved:
                # Skip remaining pending tasks
                for task in tasks:
                    if task.status == TaskStatus.PENDING:
                        task.status = TaskStatus.SKIPPED
                return True
            # All rejected means step failed
            pending = [t for t in tasks if t.status == TaskStatus.PENDING]
            return len(pending) == 0 and len(approved) == 0

        elif step.approval_mode == ApprovalMode.PARALLEL_ALL:
            # All tasks must be approved
            pending = [t for t in tasks if t.status == TaskStatus.PENDING]
            rejected = [t for t in tasks if t.status == TaskStatus.REJECTED]
            if rejected:
                return True  # Any rejection fails the step
            return len(pending) == 0  # Complete when all have acted

        return False

    async def _handle_step_approval(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        action_by: UUID,
    ):
        """Handle successful step completion."""
        context = instance.context_data or {}

        # Determine next action
        if step.on_approve_action == StepAction.COMPLETE:
            await self._complete_workflow(instance, True, action_by)

        elif step.on_approve_action == StepAction.GOTO and step.on_approve_step_id:
            next_step = await self._get_step_by_id(step.on_approve_step_id)
            if next_step:
                await self._move_to_step(instance, next_step, action_by)

        else:  # NEXT
            next_step = await self._find_next_applicable_step(
                instance.workflow_definition_id,
                step.step_number,
                context,
            )
            if next_step:
                await self._move_to_step(instance, next_step, action_by)
            else:
                # No more steps - complete workflow
                await self._complete_workflow(instance, True, action_by)

    async def _handle_step_rejection(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        action_by: UUID,
        comments: Optional[str],
    ):
        """Handle step rejection."""
        if step.on_reject_action == StepAction.REJECT:
            await self._complete_workflow(instance, False, action_by, comments)

        elif step.on_reject_action == StepAction.GOTO and step.on_reject_step_id:
            next_step = await self._get_step_by_id(step.on_reject_step_id)
            if next_step:
                await self._move_to_step(instance, next_step, action_by)
            else:
                await self._complete_workflow(instance, False, action_by, comments)

        elif step.on_reject_action == StepAction.PREVIOUS:
            if step.step_number > 1:
                prev_step = await self._get_step_by_number(
                    instance.workflow_definition_id,
                    step.step_number - 1,
                )
                if prev_step:
                    await self._move_to_step(instance, prev_step, action_by)
                    return
            await self._complete_workflow(instance, False, action_by, comments)

        else:
            await self._complete_workflow(instance, False, action_by, comments)

    async def _move_to_step(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        action_by: UUID,
    ):
        """Move workflow to a new step."""
        old_step = instance.current_step

        instance.current_step_id = step.id
        instance.current_step_number = step.step_number
        instance.updated_by = action_by

        # Create tasks for new step
        await self._create_tasks_for_step(instance, step, action_by)

        # Record history
        await self._record_history(
            instance=instance,
            action=WorkflowAction.STEP_ENTERED,
            action_by=action_by,
            from_step=old_step,
            to_step=step,
            from_status=instance.status.value,
            to_status=instance.status.value,
        )

    async def _complete_workflow(
        self,
        instance: WorkflowInstance,
        approved: bool,
        completed_by: UUID,
        comments: Optional[str] = None,
    ):
        """Complete the workflow."""
        now = datetime.now(timezone.utc)
        old_status = instance.status

        instance.status = (
            WorkflowInstanceStatus.APPROVED if approved
            else WorkflowInstanceStatus.REJECTED
        )
        instance.completed_at = now
        instance.completed_by = completed_by
        instance.updated_by = completed_by

        # Record history
        await self._record_history(
            instance=instance,
            action=WorkflowAction.COMPLETED,
            action_by=completed_by,
            from_status=old_status.value,
            to_status=instance.status.value,
            comments=comments,
        )

    async def _record_history(
        self,
        instance: WorkflowInstance,
        action: WorkflowAction,
        action_by: UUID,
        from_status: Optional[str] = None,
        to_status: str = None,
        from_step: Optional[WorkflowStep] = None,
        to_step: Optional[WorkflowStep] = None,
        comments: Optional[str] = None,
        task: Optional[WorkflowTask] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record an action in workflow history."""
        history = WorkflowHistory(
            workflow_instance_id=instance.id,
            action=action.value,
            action_by=action_by,
            action_at=datetime.now(timezone.utc),
            from_step_id=from_step.id if from_step else None,
            to_step_id=to_step.id if to_step else None,
            from_status=from_status,
            to_status=to_status or instance.status.value,
            comments=comments,
            action_metadata=metadata,
            task_id=task.id if task else None,
            created_by=action_by,
        )
        self.session.add(history)

    async def _get_task(self, task_id: UUID) -> Optional[WorkflowTask]:
        """Get a task with related data."""
        query = (
            select(WorkflowTask)
            .options(
                selectinload(WorkflowTask.workflow_instance).selectinload(
                    WorkflowInstance.workflow_definition
                ),
                selectinload(WorkflowTask.workflow_step),
            )
            .where(
                and_(
                    WorkflowTask.id == task_id,
                    WorkflowTask.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_instance(self, instance_id: UUID) -> Optional[WorkflowInstance]:
        """Get a workflow instance with related data."""
        query = (
            select(WorkflowInstance)
            .options(
                selectinload(WorkflowInstance.workflow_definition),
                selectinload(WorkflowInstance.current_step),
                selectinload(WorkflowInstance.tasks),
                selectinload(WorkflowInstance.history),
            )
            .where(
                and_(
                    WorkflowInstance.id == instance_id,
                    WorkflowInstance.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_active_instance(
        self,
        entity_type: WorkflowEntityType,
        entity_id: UUID,
    ) -> Optional[WorkflowInstance]:
        """Get active workflow instance for an entity."""
        query = (
            select(WorkflowInstance)
            .where(
                and_(
                    WorkflowInstance.entity_type == entity_type,
                    WorkflowInstance.entity_id == entity_id,
                    WorkflowInstance.status.in_([
                        WorkflowInstanceStatus.PENDING,
                        WorkflowInstanceStatus.IN_PROGRESS,
                    ]),
                    WorkflowInstance.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_step_by_id(self, step_id: UUID) -> Optional[WorkflowStep]:
        """Get a workflow step by ID."""
        query = (
            select(WorkflowStep)
            .options(
                selectinload(WorkflowStep.approval_rules),
                selectinload(WorkflowStep.escalation_rules),
            )
            .where(
                and_(
                    WorkflowStep.id == step_id,
                    WorkflowStep.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
