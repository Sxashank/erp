"""Approval/Maker-Checker workflow API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import (
    Permissions,
    ApprovalWorkflowType,
    ApprovalRequestStatus,
)
from app.core.exceptions import BadRequestException
from app.core.permissions import PermissionChecker
from app.schemas.approval.approval import (
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalWorkflowResponse,
    ApprovalWorkflowLevelResponse,
    ApprovalRequestResponse,
    ApprovalRequestListResponse,
    ApprovalRequestActionCreate,
    ApprovalRequestActionResponse,
)
from app.schemas.base import MessageResponse
from app.services.approval.approval_service import ApprovalService

router = APIRouter()


# ============================================
# Helper Functions
# ============================================


def _workflow_to_response(workflow) -> ApprovalWorkflowResponse:
    """Convert workflow model to response schema."""
    levels = [
        ApprovalWorkflowLevelResponse(
            id=level.id,
            workflow_id=level.workflow_id,
            level_number=level.level_number,
            level_name=level.level_name,
            approver_roles=level.approver_roles,
            approver_users=level.approver_users,
            min_approvers=level.min_approvers,
            threshold_amount=level.threshold_amount,
            escalation_hours=level.escalation_hours,
            escalation_user_id=level.escalation_user_id,
            created_at=level.created_at,
            updated_at=level.updated_at,
            is_active=level.is_active,
        )
        for level in (workflow.levels or [])
    ]

    return ApprovalWorkflowResponse(
        id=workflow.id,
        organization_id=workflow.organization_id,
        workflow_type=workflow.workflow_type,
        workflow_name=workflow.workflow_name,
        description=workflow.description,
        threshold_amount=workflow.threshold_amount,
        threshold_currency=workflow.threshold_currency,
        approval_levels=workflow.approval_levels,
        is_sequential=workflow.is_sequential,
        auto_approve_on_timeout=workflow.auto_approve_on_timeout,
        timeout_hours=workflow.timeout_hours,
        allow_self_approval=workflow.allow_self_approval,
        notify_on_submit=workflow.notify_on_submit,
        notify_on_approval=workflow.notify_on_approval,
        notify_on_rejection=workflow.notify_on_rejection,
        levels=levels,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        is_active=workflow.is_active,
    )


def _request_to_response(
    request,
    current_user_id: Optional[UUID] = None,
    user_role_ids: Optional[List[UUID]] = None,
) -> ApprovalRequestResponse:
    """Convert request model to response schema."""
    actions = [
        ApprovalRequestActionResponse(
            id=action.id,
            request_id=action.request_id,
            level_number=action.level_number,
            action=action.action,
            action_by=action.action_by,
            action_at=action.action_at,
            comments=action.comments,
            actor_name=action.actor.full_name if action.actor else None,
            created_at=action.created_at,
            updated_at=action.updated_at,
            is_active=action.is_active,
        )
        for action in (request.actions or [])
    ]

    # Determine if current user can approve
    can_approve = False
    if current_user_id and user_role_ids and request.status == ApprovalRequestStatus.PENDING:
        can_approve = _check_can_approve(request, current_user_id, user_role_ids)

    return ApprovalRequestResponse(
        id=request.id,
        organization_id=request.organization_id,
        workflow_id=request.workflow_id,
        workflow_type=request.workflow_type,
        workflow_name=request.workflow.workflow_name if request.workflow else None,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        request_number=request.request_number,
        request_amount=request.request_amount,
        request_summary=request.request_summary,
        request_details=request.request_details,
        requested_by=request.requested_by,
        requester_name=request.requester.full_name if request.requester else None,
        requested_at=request.requested_at,
        status=request.status,
        current_level=request.current_level,
        total_levels=request.total_levels,
        resolved_at=request.resolved_at,
        resolved_by=request.resolved_by,
        resolver_name=request.resolver.full_name if request.resolver else None,
        final_comments=request.final_comments,
        expires_at=request.expires_at,
        version=request.version,
        actions=actions,
        can_approve=can_approve,
        created_at=request.created_at,
        updated_at=request.updated_at,
        is_active=request.is_active,
    )


def _check_can_approve(request, user_id: UUID, user_role_ids: List[UUID]) -> bool:
    """Check if user can approve at current level."""
    if not request.workflow or not request.workflow.levels:
        return False

    # Find current level config
    current_level_config = None
    for level in request.workflow.levels:
        if level.level_number == request.current_level:
            current_level_config = level
            break

    if not current_level_config:
        return False

    # Check if user already acted
    for action in request.actions or []:
        if action.level_number == request.current_level and action.action_by == user_id:
            return False

    # Check approver_users
    if current_level_config.approver_users:
        if str(user_id) in [str(uid) for uid in current_level_config.approver_users]:
            return True

    # Check approver_roles
    if current_level_config.approver_roles:
        user_role_strs = [str(rid) for rid in user_role_ids]
        approver_role_strs = [str(rid) for rid in current_level_config.approver_roles]
        if any(rid in approver_role_strs for rid in user_role_strs):
            return True

    return False


def _get_user_role_ids(user: User) -> List[UUID]:
    """Extract role IDs from user object."""
    role_ids = []
    if hasattr(user, "user_roles") and user.user_roles:
        for user_role in user.user_roles:
            if hasattr(user_role, "role_id"):
                role_ids.append(user_role.role_id)
    return role_ids


# ============================================
# Workflow Configuration Endpoints
# ============================================


@router.post(
    "/workflows",
    response_model=ApprovalWorkflowResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    request: Request,
    data: ApprovalWorkflowCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_CREATE])),
):
    """Create a new approval workflow configuration."""
    service = ApprovalService(db)
    workflow = await service.create_workflow(data, created_by=current_user.id)
    await db.commit()
    return _workflow_to_response(workflow)


@router.get("/workflows", response_model=dict, response_model_by_alias=True)
async def list_workflows(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_VIEW])),
):
    """List approval workflows for an organization."""
    organization_id = current_user.organization_id
    if not organization_id:
        raise BadRequestException("Current user is not mapped to an organization")
    service = ApprovalService(db)
    workflows, total = await service.list_workflows(organization_id, skip=skip, limit=limit)

    return {
        "items": [_workflow_to_response(w) for w in workflows],
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.get(
    "/workflows/{workflow_id}",
    response_model=ApprovalWorkflowResponse,
    response_model_by_alias=True,
)
async def get_workflow(
    request: Request,
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_VIEW])),
):
    """Get approval workflow by ID."""
    service = ApprovalService(db)
    workflow = await service.get_workflow(workflow_id)
    return _workflow_to_response(workflow)


@router.get(
    "/workflows/by-type/{workflow_type}",
    response_model=Optional[ApprovalWorkflowResponse],
    response_model_by_alias=True,
)
async def get_workflow_by_type(
    request: Request,
    workflow_type: ApprovalWorkflowType,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_VIEW])),
):
    """Get workflow configuration for a specific type."""
    organization_id = current_user.organization_id
    if not organization_id:
        raise BadRequestException("Current user is not mapped to an organization")
    service = ApprovalService(db)
    workflow = await service.get_workflow_by_type(organization_id, workflow_type)
    if not workflow:
        return None
    return _workflow_to_response(workflow)


@router.put(
    "/workflows/{workflow_id}",
    response_model=ApprovalWorkflowResponse,
    response_model_by_alias=True,
)
async def update_workflow(
    request: Request,
    workflow_id: UUID,
    data: ApprovalWorkflowUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_UPDATE])),
):
    """Update an approval workflow configuration."""
    service = ApprovalService(db)
    workflow = await service.update_workflow(workflow_id, data, updated_by=current_user.id)
    await db.commit()
    return _workflow_to_response(workflow)


@router.delete(
    "/workflows/{workflow_id}", response_model=MessageResponse, response_model_by_alias=True
)
async def delete_workflow(
    request: Request,
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_CONFIG_DELETE])),
):
    """Delete an approval workflow configuration."""
    service = ApprovalService(db)
    await service.delete_workflow(workflow_id, deleted_by=current_user.id)
    await db.commit()
    return MessageResponse(message="Workflow deleted successfully")


# ============================================
# Approval Request Endpoints
# ============================================


@router.get("/requests", response_model=dict, response_model_by_alias=True)
async def list_requests(
    request: Request,
    organization_id: Optional[UUID] = None,
    workflow_type: Optional[ApprovalWorkflowType] = None,
    status: Optional[ApprovalRequestStatus] = None,
    entity_type: Optional[str] = None,
    requested_by: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_REQUEST_VIEW])),
):
    """List approval requests with filters."""
    service = ApprovalService(db)
    requests, total = await service.list_requests(
        organization_id=organization_id,
        workflow_type=workflow_type,
        status=status,
        entity_type=entity_type,
        requested_by=requested_by,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [
            ApprovalRequestListResponse(
                id=r.id,
                request_number=r.request_number,
                workflow_type=r.workflow_type,
                workflow_name=r.workflow.workflow_name if r.workflow else None,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                request_amount=r.request_amount,
                request_summary=r.request_summary,
                requested_by=r.requested_by,
                requester_name=r.requester.full_name if r.requester else None,
                requested_at=r.requested_at,
                status=r.status,
                current_level=r.current_level,
                total_levels=r.total_levels,
                expires_at=r.expires_at,
            )
            for r in requests
        ],
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.get("/requests/pending", response_model=dict, response_model_by_alias=True)
async def list_pending_for_me(
    request: Request,
    organization_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_PENDING_VIEW])),
):
    """List pending approval requests that I can approve."""
    service = ApprovalService(db)
    user_role_ids = _get_user_role_ids(current_user)

    requests, total = await service.list_pending_for_user(
        user_id=current_user.id,
        user_role_ids=user_role_ids,
        organization_id=organization_id,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [_request_to_response(r, current_user.id, user_role_ids) for r in requests],
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.get(
    "/requests/{request_id}", response_model=ApprovalRequestResponse, response_model_by_alias=True
)
async def get_request(
    request: Request,
    request_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_REQUEST_VIEW])),
):
    """Get approval request by ID."""
    service = ApprovalService(db)
    approval_request = await service.get_request(request_id)
    user_role_ids = _get_user_role_ids(current_user)
    return _request_to_response(approval_request, current_user.id, user_role_ids)


@router.get(
    "/requests/by-number/{request_number}",
    response_model=ApprovalRequestResponse,
    response_model_by_alias=True,
)
async def get_request_by_number(
    request: Request,
    request_number: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_REQUEST_VIEW])),
):
    """Get approval request by request number."""
    service = ApprovalService(db)
    approval_request = await service.get_request_by_number(request_number)
    user_role_ids = _get_user_role_ids(current_user)
    return _request_to_response(approval_request, current_user.id, user_role_ids)


@router.post(
    "/requests/{request_id}/action",
    response_model=ApprovalRequestResponse,
    response_model_by_alias=True,
)
async def take_action(
    request: Request,
    request_id: UUID,
    action_data: ApprovalRequestActionCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_REQUEST_APPROVE])),
):
    """Take action (approve/reject/return) on an approval request."""
    service = ApprovalService(db)
    user_role_ids = _get_user_role_ids(current_user)

    approval_request = await service.take_action(
        request_id=request_id,
        action_data=action_data,
        action_by=current_user.id,
        user_role_ids=user_role_ids,
    )
    await db.commit()
    return _request_to_response(approval_request, current_user.id, user_role_ids)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=ApprovalRequestResponse,
    response_model_by_alias=True,
)
async def cancel_request(
    request: Request,
    request_id: UUID,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_REQUEST_CANCEL])),
):
    """Cancel an approval request (by requester)."""
    service = ApprovalService(db)
    approval_request = await service.cancel_request(
        request_id=request_id,
        cancelled_by=current_user.id,
        comments=comments,
    )
    await db.commit()
    user_role_ids = _get_user_role_ids(current_user)
    return _request_to_response(approval_request, current_user.id, user_role_ids)


# ============================================
# Dashboard Endpoints
# ============================================


@router.get("/dashboard", response_model=dict, response_model_by_alias=True)
async def get_dashboard(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.APPROVAL_PENDING_VIEW])),
):
    """Get approval dashboard statistics."""
    service = ApprovalService(db)
    user_role_ids = _get_user_role_ids(current_user)

    stats = await service.get_dashboard_stats(
        organization_id=organization_id,
        user_id=current_user.id,
        user_role_ids=user_role_ids,
    )

    return stats


# ============================================
# Utility Endpoints
# ============================================


@router.get("/check/{workflow_type}", response_model=dict, response_model_by_alias=True)
async def check_approval_required(
    request: Request,
    workflow_type: ApprovalWorkflowType,
    organization_id: UUID,
    amount: float = Query(0.0, ge=0),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Check if approval is required for a transaction."""
    from decimal import Decimal

    service = ApprovalService(db)
    result = await service.check_approval_required(
        organization_id=organization_id,
        workflow_type=workflow_type,
        amount=Decimal(str(amount)),
    )
    return result.model_dump()


@router.get("/status/{entity_type}/{entity_id}", response_model=dict, response_model_by_alias=True)
async def get_entity_approval_status(
    request: Request,
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get approval status for a specific entity."""
    service = ApprovalService(db)
    status = await service.get_approval_status(entity_type, entity_id)
    return status
