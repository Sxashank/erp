"""Workflow instance API endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.models.workflow import (
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowEntityType,
)
from app.services.workflow import WorkflowEngine
from app.schemas.workflow import (
    WorkflowInstanceResponse,
    WorkflowInstanceDetailResponse,
    WorkflowHistoryResponse,
    WorkflowTaskResponse,
    CancelWorkflowRequest,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[WorkflowInstanceResponse])
async def list_workflow_instances(
    organization_id: UUID = Query(...),
    entity_type: Optional[WorkflowEntityType] = Query(None),
    status_filter: Optional[WorkflowInstanceStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of workflow instances."""
    query = (
        select(WorkflowInstance)
        .options(
            selectinload(WorkflowInstance.workflow_definition),
            selectinload(WorkflowInstance.current_step),
            selectinload(WorkflowInstance.initiator),
        )
        .where(
            and_(
                WorkflowInstance.organization_id == organization_id,
                WorkflowInstance.is_active == True,
            )
        )
    )

    if entity_type:
        query = query.where(WorkflowInstance.entity_type == entity_type)
    if status_filter:
        query = query.where(WorkflowInstance.status == status_filter)

    # Count total
    count_query = select(WorkflowInstance.id).where(
        and_(
            WorkflowInstance.organization_id == organization_id,
            WorkflowInstance.is_active == True,
        )
    )
    if entity_type:
        count_query = count_query.where(WorkflowInstance.entity_type == entity_type)
    if status_filter:
        count_query = count_query.where(WorkflowInstance.status == status_filter)

    count_result = await db.execute(count_query)
    total = len(count_result.fetchall())

    # Get paginated results
    query = query.order_by(
        WorkflowInstance.started_at.desc()
    ).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    instances = result.scalars().all()

    items = [
        WorkflowInstanceResponse(
            id=i.id,
            workflow_definition_id=i.workflow_definition_id,
            workflow_name=i.workflow_definition.name if i.workflow_definition else None,
            organization_id=i.organization_id,
            entity_type=i.entity_type,
            entity_id=i.entity_id,
            entity_reference=i.entity_reference,
            current_step_id=i.current_step_id,
            current_step_name=i.current_step.name if i.current_step else None,
            current_step_number=i.current_step_number,
            status=i.status,
            started_at=i.started_at,
            started_by=i.started_by,
            initiator_name=i.initiator.full_name if i.initiator else None,
            completed_at=i.completed_at,
            completed_by=i.completed_by,
            cancelled_at=i.cancelled_at,
            cancelled_by=i.cancelled_by,
            cancellation_reason=i.cancellation_reason,
            created_at=i.created_at,
            updated_at=i.updated_at,
            is_active=i.is_active,
        )
        for i in instances
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/{instance_id}", response_model=WorkflowInstanceDetailResponse)
async def get_workflow_instance(
    instance_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a workflow instance with full details."""
    query = (
        select(WorkflowInstance)
        .options(
            selectinload(WorkflowInstance.workflow_definition),
            selectinload(WorkflowInstance.current_step),
            selectinload(WorkflowInstance.initiator),
            selectinload(WorkflowInstance.tasks).selectinload("workflow_step"),
            selectinload(WorkflowInstance.tasks).selectinload("assignee"),
            selectinload(WorkflowInstance.history).selectinload("actor"),
            selectinload(WorkflowInstance.history).selectinload("from_step"),
            selectinload(WorkflowInstance.history).selectinload("to_step"),
        )
        .where(
            and_(
                WorkflowInstance.id == instance_id,
                WorkflowInstance.is_active == True,
            )
        )
    )

    result = await db.execute(query)
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow instance not found",
        )

    return _instance_to_detail_response(instance)


@router.get("/{instance_id}/history", response_model=List[WorkflowHistoryResponse])
async def get_workflow_history(
    instance_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get full history for a workflow instance."""
    engine = WorkflowEngine(db)
    history = await engine.get_instance_history(instance_id)

    return [
        WorkflowHistoryResponse(
            id=h.id,
            action=h.action,
            action_by=h.action_by,
            actor_name=h.actor.full_name if h.actor else None,
            action_at=h.action_at,
            from_step_id=h.from_step_id,
            from_step_name=h.from_step.name if h.from_step else None,
            to_step_id=h.to_step_id,
            to_step_name=h.to_step.name if h.to_step else None,
            from_status=h.from_status,
            to_status=h.to_status,
            comments=h.comments,
            action_metadata=h.action_metadata,
        )
        for h in history
    ]


@router.post("/{instance_id}/cancel", response_model=WorkflowInstanceResponse)
async def cancel_workflow(
    instance_id: UUID,
    data: CancelWorkflowRequest,
    current_user: User = Depends(RequirePermissions("WORKFLOW_CANCEL")),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active workflow."""
    engine = WorkflowEngine(db)

    try:
        instance = await engine.cancel_workflow(
            instance_id=instance_id,
            reason=data.reason,
            cancelled_by=current_user.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return WorkflowInstanceResponse(
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
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        is_active=instance.is_active,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=Optional[WorkflowInstanceResponse])
async def get_entity_workflow(
    entity_type: WorkflowEntityType,
    entity_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get active workflow for a specific entity."""
    query = (
        select(WorkflowInstance)
        .options(
            selectinload(WorkflowInstance.workflow_definition),
            selectinload(WorkflowInstance.current_step),
            selectinload(WorkflowInstance.initiator),
        )
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

    result = await db.execute(query)
    instance = result.scalar_one_or_none()

    if not instance:
        return None

    return WorkflowInstanceResponse(
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
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        is_active=instance.is_active,
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
        WorkflowHistoryResponse(
            id=h.id,
            action=h.action,
            action_by=h.action_by,
            actor_name=h.actor.full_name if h.actor else None,
            action_at=h.action_at,
            from_step_id=h.from_step_id,
            from_step_name=h.from_step.name if h.from_step else None,
            to_step_id=h.to_step_id,
            to_step_name=h.to_step.name if h.to_step else None,
            from_status=h.from_status,
            to_status=h.to_status,
            comments=h.comments,
            action_metadata=h.action_metadata,
        )
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
