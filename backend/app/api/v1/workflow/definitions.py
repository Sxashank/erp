"""Workflow definition API endpoints."""

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
    WorkflowDefinition,
    WorkflowStep,
    ApprovalRule,
    EscalationRule,
    WorkflowEntityType,
)
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionWithStepsResponse,
    WorkflowStepCreate,
    WorkflowStepUpdate,
    WorkflowStepResponse,
    ApprovalRuleCreate,
    EscalationRuleCreate,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[WorkflowDefinitionResponse])
async def list_workflow_definitions(
    organization_id: UUID = Query(...),
    entity_type: Optional[WorkflowEntityType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of workflow definitions."""
    query = (
        select(WorkflowDefinition)
        .where(
            and_(
                WorkflowDefinition.organization_id == organization_id,
                WorkflowDefinition.is_active == True,
            )
        )
    )

    if entity_type:
        query = query.where(WorkflowDefinition.entity_type == entity_type)

    # Count total
    count_query = select(WorkflowDefinition.id).where(
        and_(
            WorkflowDefinition.organization_id == organization_id,
            WorkflowDefinition.is_active == True,
        )
    )
    if entity_type:
        count_query = count_query.where(WorkflowDefinition.entity_type == entity_type)

    count_result = await db.execute(count_query)
    total = len(count_result.fetchall())

    # Get paginated results
    query = query.order_by(
        WorkflowDefinition.entity_type,
        WorkflowDefinition.priority.desc(),
    ).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    definitions = result.scalars().all()

    items = [
        WorkflowDefinitionResponse(
            id=d.id,
            organization_id=d.organization_id,
            name=d.name,
            code=d.code,
            description=d.description,
            entity_type=d.entity_type,
            is_default=d.is_default,
            priority=d.priority,
            activation_conditions=d.activation_conditions,
            allow_parallel_branches=d.allow_parallel_branches,
            require_comments_on_reject=d.require_comments_on_reject,
            notify_initiator_on_complete=d.notify_initiator_on_complete,
            allow_withdrawal=d.allow_withdrawal,
            version=d.version,
            created_at=d.created_at,
            updated_at=d.updated_at,
            is_active=d.is_active,
        )
        for d in definitions
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=WorkflowDefinitionWithStepsResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_definition(
    data: WorkflowDefinitionCreate,
    current_user: User = Depends(RequirePermissions("WORKFLOW_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow definition with steps."""
    # Check for duplicate code
    existing = await db.execute(
        select(WorkflowDefinition).where(
            and_(
                WorkflowDefinition.organization_id == data.organization_id,
                WorkflowDefinition.code == data.code,
                WorkflowDefinition.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with code '{data.code}' already exists",
        )

    # If setting as default, unset other defaults for this entity type
    if data.is_default:
        await db.execute(
            select(WorkflowDefinition)
            .where(
                and_(
                    WorkflowDefinition.organization_id == data.organization_id,
                    WorkflowDefinition.entity_type == data.entity_type,
                    WorkflowDefinition.is_default == True,
                )
            )
        )
        # Update existing defaults
        result = await db.execute(
            select(WorkflowDefinition).where(
                and_(
                    WorkflowDefinition.organization_id == data.organization_id,
                    WorkflowDefinition.entity_type == data.entity_type,
                    WorkflowDefinition.is_default == True,
                )
            )
        )
        for existing_default in result.scalars().all():
            existing_default.is_default = False

    # Create definition
    definition = WorkflowDefinition(
        organization_id=data.organization_id,
        name=data.name,
        code=data.code,
        description=data.description,
        entity_type=data.entity_type,
        is_default=data.is_default,
        priority=data.priority,
        activation_conditions=data.activation_conditions,
        allow_parallel_branches=data.allow_parallel_branches,
        require_comments_on_reject=data.require_comments_on_reject,
        notify_initiator_on_complete=data.notify_initiator_on_complete,
        allow_withdrawal=data.allow_withdrawal,
        created_by=current_user.id,
    )
    db.add(definition)
    await db.flush()

    # Create steps
    for step_data in data.steps:
        step = WorkflowStep(
            workflow_definition_id=definition.id,
            step_number=step_data.step_number,
            name=step_data.name,
            description=step_data.description,
            step_type=step_data.step_type,
            approval_mode=step_data.approval_mode,
            entry_conditions=step_data.entry_conditions,
            exit_conditions=step_data.exit_conditions,
            on_approve_action=step_data.on_approve_action,
            on_reject_action=step_data.on_reject_action,
            allow_delegation=step_data.allow_delegation,
            sla_hours=step_data.sla_hours,
            reminder_hours=step_data.reminder_hours,
            created_by=current_user.id,
        )
        db.add(step)
        await db.flush()

        # Create approval rules
        for rule_data in step_data.approval_rules:
            rule = ApprovalRule(
                workflow_step_id=step.id,
                sequence=rule_data.sequence,
                approver_type=rule_data.approver_type,
                user_id=rule_data.user_id,
                role_id=rule_data.role_id,
                designation=rule_data.designation,
                dynamic_field=rule_data.dynamic_field,
                conditions=rule_data.conditions,
                is_mandatory=rule_data.is_mandatory,
                can_self_approve=rule_data.can_self_approve,
                fallback_to_admin=rule_data.fallback_to_admin,
                created_by=current_user.id,
            )
            db.add(rule)

        # Create escalation rules
        for esc_data in step_data.escalation_rules:
            escalation = EscalationRule(
                workflow_step_id=step.id,
                level=esc_data.level,
                timeout_hours=esc_data.timeout_hours,
                escalation_type=esc_data.escalation_type,
                escalate_to_type=esc_data.escalate_to_type,
                escalate_to_user_id=esc_data.escalate_to_user_id,
                escalate_to_role_id=esc_data.escalate_to_role_id,
                notify_current_approver=esc_data.notify_current_approver,
                notify_initiator=esc_data.notify_initiator,
                notification_template_id=esc_data.notification_template_id,
                created_by=current_user.id,
            )
            db.add(escalation)

    await db.commit()

    # Reload with relationships
    return await get_workflow_definition(definition.id, current_user, db)


@router.get("/{definition_id}", response_model=WorkflowDefinitionWithStepsResponse)
async def get_workflow_definition(
    definition_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a workflow definition with all steps."""
    query = (
        select(WorkflowDefinition)
        .options(
            selectinload(WorkflowDefinition.steps).selectinload(WorkflowStep.approval_rules),
            selectinload(WorkflowDefinition.steps).selectinload(WorkflowStep.escalation_rules),
        )
        .where(
            and_(
                WorkflowDefinition.id == definition_id,
                WorkflowDefinition.is_active == True,
            )
        )
    )

    result = await db.execute(query)
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    return _definition_to_response(definition)


@router.put("/{definition_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow_definition(
    definition_id: UUID,
    data: WorkflowDefinitionUpdate,
    current_user: User = Depends(RequirePermissions("WORKFLOW_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow definition."""
    query = select(WorkflowDefinition).where(
        and_(
            WorkflowDefinition.id == definition_id,
            WorkflowDefinition.is_active == True,
        )
    )
    result = await db.execute(query)
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    # Handle default flag
    if data.is_default and not definition.is_default:
        result = await db.execute(
            select(WorkflowDefinition).where(
                and_(
                    WorkflowDefinition.organization_id == definition.organization_id,
                    WorkflowDefinition.entity_type == definition.entity_type,
                    WorkflowDefinition.is_default == True,
                    WorkflowDefinition.id != definition_id,
                )
            )
        )
        for existing_default in result.scalars().all():
            existing_default.is_default = False

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(definition, field, value)

    definition.updated_by = current_user.id
    definition.version += 1

    await db.commit()

    return WorkflowDefinitionResponse(
        id=definition.id,
        organization_id=definition.organization_id,
        name=definition.name,
        code=definition.code,
        description=definition.description,
        entity_type=definition.entity_type,
        is_default=definition.is_default,
        priority=definition.priority,
        activation_conditions=definition.activation_conditions,
        allow_parallel_branches=definition.allow_parallel_branches,
        require_comments_on_reject=definition.require_comments_on_reject,
        notify_initiator_on_complete=definition.notify_initiator_on_complete,
        allow_withdrawal=definition.allow_withdrawal,
        version=definition.version,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
        is_active=definition.is_active,
    )


@router.delete("/{definition_id}", response_model=MessageResponse)
async def delete_workflow_definition(
    definition_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a workflow definition."""
    query = select(WorkflowDefinition).where(
        and_(
            WorkflowDefinition.id == definition_id,
            WorkflowDefinition.is_active == True,
        )
    )
    result = await db.execute(query)
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    definition.soft_delete(current_user.id)
    await db.commit()

    return MessageResponse(message="Workflow definition deleted successfully")


@router.post("/{definition_id}/set-default", response_model=WorkflowDefinitionResponse)
async def set_default_workflow(
    definition_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Set a workflow as the default for its entity type."""
    query = select(WorkflowDefinition).where(
        and_(
            WorkflowDefinition.id == definition_id,
            WorkflowDefinition.is_active == True,
        )
    )
    result = await db.execute(query)
    definition = result.scalar_one_or_none()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    # Unset other defaults
    result = await db.execute(
        select(WorkflowDefinition).where(
            and_(
                WorkflowDefinition.organization_id == definition.organization_id,
                WorkflowDefinition.entity_type == definition.entity_type,
                WorkflowDefinition.is_default == True,
                WorkflowDefinition.id != definition_id,
            )
        )
    )
    for existing_default in result.scalars().all():
        existing_default.is_default = False

    definition.is_default = True
    definition.updated_by = current_user.id

    await db.commit()

    return WorkflowDefinitionResponse(
        id=definition.id,
        organization_id=definition.organization_id,
        name=definition.name,
        code=definition.code,
        description=definition.description,
        entity_type=definition.entity_type,
        is_default=definition.is_default,
        priority=definition.priority,
        activation_conditions=definition.activation_conditions,
        allow_parallel_branches=definition.allow_parallel_branches,
        require_comments_on_reject=definition.require_comments_on_reject,
        notify_initiator_on_complete=definition.notify_initiator_on_complete,
        allow_withdrawal=definition.allow_withdrawal,
        version=definition.version,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
        is_active=definition.is_active,
    )


def _definition_to_response(definition: WorkflowDefinition) -> WorkflowDefinitionWithStepsResponse:
    """Convert definition model to response with steps."""
    steps = []
    for step in sorted(definition.steps, key=lambda s: s.step_number):
        if not step.is_active:
            continue

        approval_rules = [
            {
                "id": r.id,
                "sequence": r.sequence,
                "approver_type": r.approver_type,
                "user_id": r.user_id,
                "role_id": r.role_id,
                "designation": r.designation,
                "dynamic_field": r.dynamic_field,
                "conditions": r.conditions,
                "is_mandatory": r.is_mandatory,
                "can_self_approve": r.can_self_approve,
                "fallback_to_admin": r.fallback_to_admin,
            }
            for r in sorted(step.approval_rules, key=lambda r: r.sequence)
            if r.is_active
        ]

        escalation_rules = [
            {
                "id": e.id,
                "level": e.level,
                "timeout_hours": e.timeout_hours,
                "escalation_type": e.escalation_type,
                "escalate_to_type": e.escalate_to_type,
                "escalate_to_user_id": e.escalate_to_user_id,
                "escalate_to_role_id": e.escalate_to_role_id,
                "notify_current_approver": e.notify_current_approver,
                "notify_initiator": e.notify_initiator,
                "notification_template_id": e.notification_template_id,
            }
            for e in sorted(step.escalation_rules, key=lambda e: e.level)
            if e.is_active
        ]

        steps.append(WorkflowStepResponse(
            id=step.id,
            step_number=step.step_number,
            name=step.name,
            description=step.description,
            step_type=step.step_type,
            approval_mode=step.approval_mode,
            parent_step_id=step.parent_step_id,
            branch_name=step.branch_name,
            entry_conditions=step.entry_conditions,
            exit_conditions=step.exit_conditions,
            on_approve_step_id=step.on_approve_step_id,
            on_reject_step_id=step.on_reject_step_id,
            on_approve_action=step.on_approve_action,
            on_reject_action=step.on_reject_action,
            allow_delegation=step.allow_delegation,
            sla_hours=step.sla_hours,
            reminder_hours=step.reminder_hours,
            approval_rules=approval_rules,
            escalation_rules=escalation_rules,
        ))

    return WorkflowDefinitionWithStepsResponse(
        id=definition.id,
        organization_id=definition.organization_id,
        name=definition.name,
        code=definition.code,
        description=definition.description,
        entity_type=definition.entity_type,
        is_default=definition.is_default,
        priority=definition.priority,
        activation_conditions=definition.activation_conditions,
        allow_parallel_branches=definition.allow_parallel_branches,
        require_comments_on_reject=definition.require_comments_on_reject,
        notify_initiator_on_complete=definition.notify_initiator_on_complete,
        allow_withdrawal=definition.allow_withdrawal,
        version=definition.version,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
        is_active=definition.is_active,
        steps=steps,
    )
