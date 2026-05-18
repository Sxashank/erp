"""Approval/Maker-Checker workflow service."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    ApprovalWorkflowType,
    ApprovalRequestStatus,
    ApprovalAction,
)
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ConflictException,
    ForbiddenException,
)
from app.models.approval.approval import (
    ApprovalWorkflow,
    ApprovalWorkflowLevel,
    ApprovalRequest,
    ApprovalRequestAction,
)
from app.repositories.approval.approval_repo import (
    ApprovalWorkflowRepository,
    ApprovalRequestRepository,
)
from app.schemas.approval.approval import (
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalRequestCreate,
    ApprovalRequestActionCreate,
    ApprovalCheckResult,
)


class ApprovalService:
    """Service for managing approval workflows and requests."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.workflow_repo = ApprovalWorkflowRepository(session)
        self.request_repo = ApprovalRequestRepository(session)

    # ============================================
    # Workflow Configuration Methods
    # ============================================

    async def create_workflow(
        self,
        data: ApprovalWorkflowCreate,
        created_by: Optional[UUID] = None,
    ) -> ApprovalWorkflow:
        """Create a new approval workflow configuration."""
        # Check if workflow already exists for this type
        existing = await self.workflow_repo.get_by_org_and_type(
            data.organization_id,
            data.workflow_type,
        )
        if existing:
            raise ConflictException(
                f"Approval workflow for {data.workflow_type.value} already exists"
            )

        # Validate levels match approval_levels count
        if len(data.levels) != data.approval_levels:
            raise BadRequestException(
                f"Number of levels ({len(data.levels)}) must match approval_levels ({data.approval_levels})"
            )

        # Create workflow
        workflow_data = {
            "organization_id": data.organization_id,
            "workflow_type": data.workflow_type,
            "workflow_name": data.workflow_name,
            "description": data.description,
            "threshold_amount": data.threshold_amount,
            "threshold_currency": data.threshold_currency,
            "approval_levels": data.approval_levels,
            "is_sequential": data.is_sequential,
            "auto_approve_on_timeout": data.auto_approve_on_timeout,
            "timeout_hours": data.timeout_hours,
            "allow_self_approval": data.allow_self_approval,
            "notify_on_submit": data.notify_on_submit,
            "notify_on_approval": data.notify_on_approval,
            "notify_on_rejection": data.notify_on_rejection,
            "created_by": created_by,
        }
        workflow = await self.workflow_repo.create(workflow_data)

        # Create levels
        for level_data in data.levels:
            await self.workflow_repo.create_level({
                "workflow_id": workflow.id,
                "level_number": level_data.level_number,
                "level_name": level_data.level_name,
                "approver_roles": level_data.approver_roles,
                "approver_users": level_data.approver_users,
                "min_approvers": level_data.min_approvers,
                "threshold_amount": level_data.threshold_amount,
                "escalation_hours": level_data.escalation_hours,
                "escalation_user_id": level_data.escalation_user_id,
                "created_by": created_by,
            })

        await self.session.refresh(workflow)
        return workflow

    async def update_workflow(
        self,
        workflow_id: UUID,
        data: ApprovalWorkflowUpdate,
        updated_by: Optional[UUID] = None,
    ) -> ApprovalWorkflow:
        """Update an approval workflow configuration."""
        workflow = await self.workflow_repo.get_with_levels(workflow_id)
        if not workflow:
            raise NotFoundException("Approval workflow not found")

        # Update workflow fields
        update_data = data.model_dump(exclude_unset=True, exclude={"levels"})
        update_data["updated_by"] = updated_by

        workflow = await self.workflow_repo.update(workflow, update_data)
        if data.levels is not None:
            expected_levels = data.approval_levels or len(data.levels)
            if len(data.levels) != expected_levels:
                raise BadRequestException(
                    f"Number of levels ({len(data.levels)}) must match approval_levels ({expected_levels})"
                )
            await self.workflow_repo.delete_levels(workflow_id)
            for level_data in data.levels:
                await self.workflow_repo.create_level({
                    "workflow_id": workflow.id,
                    "level_number": level_data.level_number,
                    "level_name": level_data.level_name,
                    "approver_roles": level_data.approver_roles,
                    "approver_users": level_data.approver_users,
                    "min_approvers": level_data.min_approvers,
                    "threshold_amount": level_data.threshold_amount,
                    "escalation_hours": level_data.escalation_hours,
                    "escalation_user_id": level_data.escalation_user_id,
                    "created_by": updated_by,
                    "updated_by": updated_by,
                })
            await self.session.refresh(workflow)
        return workflow

    async def get_workflow(
        self,
        workflow_id: UUID,
    ) -> ApprovalWorkflow:
        """Get approval workflow by ID."""
        workflow = await self.workflow_repo.get_with_levels(workflow_id)
        if not workflow:
            raise NotFoundException("Approval workflow not found")
        return workflow

    async def get_workflow_by_type(
        self,
        organization_id: UUID,
        workflow_type: ApprovalWorkflowType,
    ) -> Optional[ApprovalWorkflow]:
        """Get workflow configuration for a specific type."""
        return await self.workflow_repo.get_by_org_and_type(
            organization_id,
            workflow_type,
        )

    async def list_workflows(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ApprovalWorkflow], int]:
        """List all workflows for an organization."""
        return await self.workflow_repo.get_by_organization(
            organization_id,
            skip=skip,
            limit=limit,
        )

    async def delete_workflow(
        self,
        workflow_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an approval workflow."""
        workflow = await self.workflow_repo.get(workflow_id)
        if not workflow:
            raise NotFoundException("Approval workflow not found")

        # Check if there are pending requests
        requests, count = await self.request_repo.get_filtered(
            workflow_type=workflow.workflow_type,
            status=ApprovalRequestStatus.PENDING,
            limit=1,
        )
        if count > 0:
            raise BadRequestException(
                "Cannot delete workflow with pending approval requests"
            )

        await self.workflow_repo.soft_delete(workflow_id, deleted_by)
        return True

    # ============================================
    # Approval Check Methods
    # ============================================

    async def check_approval_required(
        self,
        organization_id: UUID,
        workflow_type: ApprovalWorkflowType,
        amount: Decimal = Decimal("0.00"),
    ) -> ApprovalCheckResult:
        """
        Check if approval is required for a transaction.

        Returns details about whether approval is needed and the workflow config.
        """
        workflow = await self.workflow_repo.get_by_org_and_type(
            organization_id,
            workflow_type,
        )

        if not workflow:
            return ApprovalCheckResult(
                requires_approval=False,
                reason="No approval workflow configured",
            )

        # Check threshold
        if amount < workflow.threshold_amount:
            return ApprovalCheckResult(
                requires_approval=False,
                workflow_id=workflow.id,
                workflow_type=workflow_type,
                threshold_amount=workflow.threshold_amount,
                reason=f"Amount {amount} below threshold {workflow.threshold_amount}",
            )

        return ApprovalCheckResult(
            requires_approval=True,
            workflow_id=workflow.id,
            workflow_type=workflow_type,
            approval_levels=workflow.approval_levels,
            threshold_amount=workflow.threshold_amount,
        )

    # ============================================
    # Approval Request Methods
    # ============================================

    async def submit_for_approval(
        self,
        data: ApprovalRequestCreate,
        requested_by: UUID,
    ) -> ApprovalRequest:
        """
        Submit an entity for approval.

        This creates an approval request and returns it.
        """
        # Get workflow configuration
        workflow = await self.workflow_repo.get_by_org_and_type(
            data.organization_id,
            data.workflow_type,
        )
        if not workflow:
            raise BadRequestException(
                f"No approval workflow configured for {data.workflow_type.value}"
            )

        # Check if entity already has pending request
        existing = await self.request_repo.get_by_entity(
            data.entity_type,
            data.entity_id,
        )
        if existing:
            raise ConflictException(
                f"Entity already has pending approval request: {existing.request_number}"
            )

        # Generate request number
        request_number = await self.request_repo.generate_request_number(
            data.organization_id,
            prefix="APR",
        )

        # Calculate expiry
        expires_at = None
        if workflow.timeout_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=workflow.timeout_hours
            )

        # Create request
        request_data = {
            "organization_id": data.organization_id,
            "workflow_id": workflow.id,
            "workflow_type": data.workflow_type,
            "entity_type": data.entity_type,
            "entity_id": data.entity_id,
            "request_number": request_number,
            "request_amount": data.request_amount,
            "request_summary": data.request_summary,
            "request_details": data.request_details,
            "requested_by": requested_by,
            "requested_at": datetime.now(timezone.utc),
            "status": ApprovalRequestStatus.PENDING,
            "current_level": 1,
            "total_levels": workflow.approval_levels,
            "approval_chain": [],
            "expires_at": expires_at,
            "created_by": requested_by,
        }

        request = await self.request_repo.create(request_data)
        await self.session.refresh(request)
        return request

    async def take_action(
        self,
        request_id: UUID,
        action_data: ApprovalRequestActionCreate,
        action_by: UUID,
        user_role_ids: List[UUID],
    ) -> ApprovalRequest:
        """
        Take action (approve/reject/return) on an approval request.
        """
        request = await self.request_repo.get_with_details(request_id)
        if not request:
            raise NotFoundException("Approval request not found")

        if request.status != ApprovalRequestStatus.PENDING:
            raise BadRequestException(
                f"Cannot take action on request with status: {request.status.value}"
            )

        # Check if user can approve at current level
        if not self._can_user_approve(request, action_by, user_role_ids):
            raise ForbiddenException(
                "You are not authorized to approve at this level"
            )

        # Check self-approval
        if (request.requested_by == action_by and
            not request.workflow.allow_self_approval):
            raise ForbiddenException(
                "Self-approval is not allowed for this workflow"
            )

        # Create action record
        action_record = await self.request_repo.create_action({
            "request_id": request.id,
            "level_number": request.current_level,
            "action": action_data.action,
            "action_by": action_by,
            "action_at": datetime.now(timezone.utc),
            "comments": action_data.comments,
            "created_by": action_by,
        })

        # Update approval chain
        approval_chain = request.approval_chain or []
        approval_chain.append({
            "level": request.current_level,
            "user_id": str(action_by),
            "action": action_data.action.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comments": action_data.comments,
        })

        # Process action
        update_data = {
            "approval_chain": approval_chain,
        }

        if action_data.action == ApprovalAction.APPROVE:
            # Check if more levels needed
            if request.current_level < request.total_levels:
                update_data["current_level"] = request.current_level + 1
            else:
                # Final approval
                update_data["status"] = ApprovalRequestStatus.APPROVED
                update_data["resolved_at"] = datetime.now(timezone.utc)
                update_data["resolved_by"] = action_by
                update_data["final_comments"] = action_data.comments

        elif action_data.action == ApprovalAction.REJECT:
            update_data["status"] = ApprovalRequestStatus.REJECTED
            update_data["resolved_at"] = datetime.now(timezone.utc)
            update_data["resolved_by"] = action_by
            update_data["final_comments"] = action_data.comments

        elif action_data.action == ApprovalAction.RETURN:
            update_data["status"] = ApprovalRequestStatus.RETURNED
            update_data["resolved_at"] = datetime.now(timezone.utc)
            update_data["resolved_by"] = action_by
            update_data["final_comments"] = action_data.comments

        # Update with optimistic locking
        success = await self.request_repo.update_with_version(
            request.id,
            request.version,
            update_data,
        )
        if not success:
            raise ConflictException(
                "Request was modified by another user. Please refresh and try again."
            )

        # Refresh and return
        request = await self.request_repo.get_with_details(request_id)
        if request and request.status == ApprovalRequestStatus.APPROVED:
            await self._execute_final_approved_request(request, action_by)
        return request

    def _can_user_approve(
        self,
        request: ApprovalRequest,
        user_id: UUID,
        user_role_ids: List[UUID],
    ) -> bool:
        """Check if user can approve this request at its current level."""
        if not request.workflow or not request.workflow.levels:
            return False

        # Find current level configuration
        current_level_config = None
        for level in request.workflow.levels:
            if level.level_number == request.current_level:
                current_level_config = level
                break

        if not current_level_config:
            return False

        # Check if user already acted on this level
        for action in request.actions or []:
            if (action.level_number == request.current_level and
                action.action_by == user_id):
                return False

        # Check if user is in approver_users
        if current_level_config.approver_users:
            if str(user_id) in [str(uid) for uid in current_level_config.approver_users]:
                return True

        # Check if user's roles match approver_roles
        if current_level_config.approver_roles:
            user_role_strs = [str(rid) for rid in user_role_ids]
            approver_role_strs = [str(rid) for rid in current_level_config.approver_roles]
            if any(rid in approver_role_strs for rid in user_role_strs):
                return True

        return False

    async def cancel_request(
        self,
        request_id: UUID,
        cancelled_by: UUID,
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        """Cancel an approval request (by the requester)."""
        request = await self.request_repo.get_with_details(request_id)
        if not request:
            raise NotFoundException("Approval request not found")

        if request.status != ApprovalRequestStatus.PENDING:
            raise BadRequestException(
                f"Cannot cancel request with status: {request.status.value}"
            )

        if request.requested_by != cancelled_by:
            raise ForbiddenException(
                "Only the requester can cancel an approval request"
            )

        update_data = {
            "status": ApprovalRequestStatus.CANCELLED,
            "resolved_at": datetime.now(timezone.utc),
            "resolved_by": cancelled_by,
            "final_comments": comments or "Cancelled by requester",
        }

        success = await self.request_repo.update_with_version(
            request.id,
            request.version,
            update_data,
        )
        if not success:
            raise ConflictException(
                "Request was modified by another user. Please refresh and try again."
            )

        request = await self.request_repo.get_with_details(request_id)
        return request

    async def get_request(
        self,
        request_id: UUID,
    ) -> ApprovalRequest:
        """Get approval request by ID."""
        request = await self.request_repo.get_with_details(request_id)
        if not request:
            raise NotFoundException("Approval request not found")
        return request

    async def get_request_by_number(
        self,
        request_number: str,
    ) -> ApprovalRequest:
        """Get approval request by request number."""
        request = await self.request_repo.get_by_request_number(request_number)
        if not request:
            raise NotFoundException("Approval request not found")
        return request

    async def get_request_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> Optional[ApprovalRequest]:
        """Get pending approval request for an entity."""
        return await self.request_repo.get_by_entity(entity_type, entity_id)

    async def list_pending_for_user(
        self,
        user_id: UUID,
        user_role_ids: List[UUID],
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ApprovalRequest], int]:
        """List pending requests that a user can approve."""
        return await self.request_repo.get_pending_for_user(
            user_id=user_id,
            user_role_ids=user_role_ids,
            organization_id=organization_id,
            skip=skip,
            limit=limit,
        )

    async def list_requests(
        self,
        organization_id: Optional[UUID] = None,
        workflow_type: Optional[ApprovalWorkflowType] = None,
        status: Optional[ApprovalRequestStatus] = None,
        entity_type: Optional[str] = None,
        requested_by: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ApprovalRequest], int]:
        """List approval requests with filters."""
        return await self.request_repo.get_filtered(
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

    async def get_dashboard_stats(
        self,
        organization_id: UUID,
        user_id: UUID,
        user_role_ids: List[UUID],
    ) -> dict:
        """Get dashboard statistics for approvals."""
        # Get org-level stats
        stats = await self.request_repo.get_stats_by_organization(organization_id)

        # Get user's pending approvals
        pending_requests, _ = await self.list_pending_for_user(
            user_id=user_id,
            user_role_ids=user_role_ids,
            organization_id=organization_id,
            limit=10,
        )

        # Calculate aging
        now = datetime.now(timezone.utc)
        aging = {"0-1": 0, "2-5": 0, "5+": 0}
        for req in pending_requests:
            days = (now - req.requested_at.replace(tzinfo=timezone.utc)).days
            if days <= 1:
                aging["0-1"] += 1
            elif days <= 5:
                aging["2-5"] += 1
            else:
                aging["5+"] += 1

        stats["my_pending_count"] = len(pending_requests)
        stats["aging"] = aging

        return stats

    # ============================================
    # Integration Helper Methods
    # ============================================

    async def is_approved(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> bool:
        """Check if an entity has been approved."""
        request = await self.request_repo.get_by_entity(entity_type, entity_id)
        # No pending request means either approved or no approval required
        if not request:
            # Check if there's an approved request
            requests, _ = await self.request_repo.get_filtered(
                entity_type=entity_type,
                status=ApprovalRequestStatus.APPROVED,
                limit=1,
            )
            # Filter by entity_id in memory since it's not directly filterable
            for req in requests:
                if req.entity_id == entity_id:
                    return True
            # No approval request exists - might not require approval
            return True
        return False

    async def get_approval_status(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> dict:
        """Get approval status for an entity."""
        request = await self.request_repo.get_by_entity(entity_type, entity_id)

        if not request:
            return {
                "requires_approval": False,
                "status": None,
                "request_number": None,
            }

        return {
            "requires_approval": True,
            "status": request.status.value,
            "request_number": request.request_number,
            "current_level": request.current_level,
            "total_levels": request.total_levels,
            "requested_at": request.requested_at.isoformat(),
        }

    async def _execute_final_approved_request(
        self,
        request: ApprovalRequest,
        action_by: UUID,
    ) -> None:
        """Execute domain-side effects for approved requests that declare a target."""
        request_details = request.request_details or {}
        execution_target = request_details.get("execution_target")
        if not execution_target:
            return

        if execution_target == "fixed_assets_disposal":
            from app.services.fixed_assets.disposal_service import DisposalService

            service = DisposalService(self.session)
            await service.finalize_approved_request(request, approved_by=action_by)
            return

        if execution_target == "fixed_assets_depreciation_post":
            from app.services.fixed_assets.depreciation_service import DepreciationService

            service = DepreciationService(self.session)
            await service.execute_approved_posting_request(request, posted_by=action_by)
