"""Workflow task API endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.workflow import WorkflowEngine
from app.schemas.workflow import (
    WorkflowTaskResponse,
    ApprovalActionRequest,
    DelegateTaskRequest,
    WorkflowInstanceDetailResponse,
)
from app.schemas.base import MessageResponse
from app.core.exceptions import BadRequestException

router = APIRouter()


@router.get("/pending", response_model=List[WorkflowTaskResponse], response_model_by_alias=True)
async def get_pending_tasks(
    organization_id: Optional[UUID] = Query(None),
    current_user: User = Depends(RequirePermissions("WORKFLOW_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all pending approval tasks for the current user."""
    engine = WorkflowEngine(db)
    tasks = await engine.get_pending_tasks(
        user_id=current_user.id,
        organization_id=organization_id,
    )

    return [
        WorkflowTaskResponse(
            id=task.id,
            workflow_instance_id=task.workflow_instance_id,
            workflow_step_id=task.workflow_step_id,
            step_name=task.workflow_step.name if task.workflow_step else None,
            step_number=task.workflow_step.step_number if task.workflow_step else None,
            assigned_to=task.assigned_to,
            assignee_name=task.assignee.full_name if task.assignee else None,
            assigned_at=task.assigned_at,
            status=task.status,
            action_taken=task.action_taken,
            comments=task.comments,
            acted_at=task.acted_at,
            delegated_from=task.delegated_from,
            delegated_reason=task.delegated_reason,
            delegated_at=task.delegated_at,
            escalation_level=task.escalation_level,
            escalated_at=task.escalated_at,
            due_at=task.due_at,
            is_overdue=task.is_overdue,
            sequence=task.sequence,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_active=task.is_active,
        )
        for task in tasks
    ]


@router.post("/{task_id}/approve", response_model=WorkflowInstanceDetailResponse, response_model_by_alias=True)
async def approve_task(
    task_id: UUID,
    data: ApprovalActionRequest,
    current_user: User = Depends(RequirePermissions("WORKFLOW_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Approve or reject a workflow task."""
    engine = WorkflowEngine(db)

    try:
        instance = await engine.process_approval(
            task_id=task_id,
            action=data.action,
            comments=data.comments,
            action_by=current_user.id,
        )
    except Exception as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return _instance_to_detail_response(instance)


@router.post("/{task_id}/delegate", response_model=WorkflowTaskResponse, response_model_by_alias=True)
async def delegate_task(
    task_id: UUID,
    data: DelegateTaskRequest,
    current_user: User = Depends(RequirePermissions("WORKFLOW_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delegate a task to another user."""
    engine = WorkflowEngine(db)

    try:
        task = await engine.delegate_task(
            task_id=task_id,
            delegate_to=data.delegate_to,
            reason=data.reason,
            delegated_by=current_user.id,
        )
    except Exception as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return WorkflowTaskResponse(
        id=task.id,
        workflow_instance_id=task.workflow_instance_id,
        workflow_step_id=task.workflow_step_id,
        step_name=task.workflow_step.name if task.workflow_step else None,
        step_number=task.workflow_step.step_number if task.workflow_step else None,
        assigned_to=task.assigned_to,
        assignee_name=task.assignee.full_name if task.assignee else None,
        assigned_at=task.assigned_at,
        status=task.status,
        action_taken=task.action_taken,
        comments=task.comments,
        acted_at=task.acted_at,
        delegated_from=task.delegated_from,
        delegated_reason=task.delegated_reason,
        delegated_at=task.delegated_at,
        escalation_level=task.escalation_level,
        escalated_at=task.escalated_at,
        due_at=task.due_at,
        is_overdue=task.is_overdue,
        sequence=task.sequence,
        created_at=task.created_at,
        updated_at=task.updated_at,
        is_active=task.is_active,
    )


def _instance_to_detail_response(instance) -> WorkflowInstanceDetailResponse:
    """Convert instance model to detailed response."""
    tasks = [
        WorkflowTaskResponse(
            id=t.id,
            workflow_instance_id=t.workflow_instance_id,
            workflow_step_id=t.workflow_step_id,
            step_name=t.workflow_step.name if t.workflow_step else None,
            step_number=t.workflow_step.step_number if t.workflow_step else None,
            assigned_to=t.assigned_to,
            assignee_name=t.assignee.full_name if t.assignee else None,
            assigned_at=t.assigned_at,
            status=t.status,
            action_taken=t.action_taken,
            comments=t.comments,
            acted_at=t.acted_at,
            delegated_from=t.delegated_from,
            delegated_reason=t.delegated_reason,
            delegated_at=t.delegated_at,
            escalation_level=t.escalation_level,
            escalated_at=t.escalated_at,
            due_at=t.due_at,
            is_overdue=t.is_overdue,
            sequence=t.sequence,
            created_at=t.created_at,
            updated_at=t.updated_at,
            is_active=t.is_active,
        )
        for t in instance.tasks
    ]

    history = [
        {
            "id": h.id,
            "action": h.action,
            "action_by": h.action_by,
            "actor_name": h.actor.full_name if h.actor else None,
            "action_at": h.action_at,
            "from_step_id": h.from_step_id,
            "from_step_name": h.from_step.name if h.from_step else None,
            "to_step_id": h.to_step_id,
            "to_step_name": h.to_step.name if h.to_step else None,
            "from_status": h.from_status,
            "to_status": h.to_status,
            "comments": h.comments,
            "action_metadata": h.action_metadata,
        }
        for h in instance.history
    ]

    return WorkflowInstanceDetailResponse(
        id=instance.id,
        workflow_definition_id=instance.workflow_definition_id,
        workflow_name=instance.workflow_definition.name if instance.workflow_definition else None,
        organization_id=instance.organization_id,
        entity_type=instance.entity_type,
        entity_id=instance.entity_id,
        entity_reference=instance.entity_reference,
        current_step_id=instance.current_step_id,
        current_step_name=instance.current_step.name if instance.current_step else None,
        current_step_number=instance.current_step_number,
        status=instance.status,
        started_at=instance.started_at,
        started_by=instance.started_by,
        initiator_name=instance.initiator.full_name if instance.initiator else None,
        completed_at=instance.completed_at,
        completed_by=instance.completed_by,
        cancelled_at=instance.cancelled_at,
        cancelled_by=instance.cancelled_by,
        cancellation_reason=instance.cancellation_reason,
        context_data=instance.context_data,
        tasks=tasks,
        history=history,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        is_active=instance.is_active,
    )
