"""Approval workflow repositories."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approval.approval import (
    ApprovalWorkflow,
    ApprovalWorkflowLevel,
    ApprovalRequest,
    ApprovalRequestAction,
)
from app.repositories.base import BaseRepository
from app.core.constants import (
    ApprovalWorkflowType,
    ApprovalRequestStatus,
)


class ApprovalWorkflowRepository(BaseRepository[ApprovalWorkflow]):
    """Repository for approval workflow configuration."""

    def __init__(self, session: AsyncSession):
        super().__init__(ApprovalWorkflow, session)

    async def get_by_org_and_type(
        self,
        organization_id: UUID,
        workflow_type: ApprovalWorkflowType,
    ) -> Optional[ApprovalWorkflow]:
        """Get workflow configuration by organization and type."""
        query = select(ApprovalWorkflow).where(
            and_(
                ApprovalWorkflow.organization_id == organization_id,
                ApprovalWorkflow.workflow_type == workflow_type,
                ApprovalWorkflow.is_active == True,
            )
        ).options(
            selectinload(ApprovalWorkflow.levels),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_levels(self, workflow_id: UUID) -> Optional[ApprovalWorkflow]:
        """Get workflow with levels loaded."""
        query = select(ApprovalWorkflow).where(
            and_(
                ApprovalWorkflow.id == workflow_id,
                ApprovalWorkflow.is_active == True,
            )
        ).options(
            selectinload(ApprovalWorkflow.levels),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ApprovalWorkflow], int]:
        """Get all workflows for an organization with pagination."""
        # Count query
        count_query = select(func.count(ApprovalWorkflow.id)).where(
            and_(
                ApprovalWorkflow.organization_id == organization_id,
                ApprovalWorkflow.is_active == True,
            )
        )
        total = (await self.session.execute(count_query)).scalar() or 0

        # Data query
        query = select(ApprovalWorkflow).where(
            and_(
                ApprovalWorkflow.organization_id == organization_id,
                ApprovalWorkflow.is_active == True,
            )
        ).options(
            selectinload(ApprovalWorkflow.levels),
        ).offset(skip).limit(limit).order_by(ApprovalWorkflow.workflow_type)

        result = await self.session.execute(query)
        workflows = list(result.scalars().all())

        return workflows, total

    async def create_level(
        self,
        level_data: dict,
    ) -> ApprovalWorkflowLevel:
        """Create a workflow level."""
        level = ApprovalWorkflowLevel(**level_data)
        self.session.add(level)
        await self.session.flush()
        await self.session.refresh(level)
        return level

    async def delete_levels(self, workflow_id: UUID) -> int:
        """Delete all levels for a workflow."""
        query = select(ApprovalWorkflowLevel).where(
            ApprovalWorkflowLevel.workflow_id == workflow_id
        )
        result = await self.session.execute(query)
        levels = result.scalars().all()
        count = 0
        for level in levels:
            await self.session.delete(level)
            count += 1
        await self.session.flush()
        return count


class ApprovalRequestRepository(BaseRepository[ApprovalRequest]):
    """Repository for approval requests."""

    def __init__(self, session: AsyncSession):
        super().__init__(ApprovalRequest, session)

    async def get_with_details(
        self,
        request_id: UUID,
    ) -> Optional[ApprovalRequest]:
        """Get request with all related details."""
        query = select(ApprovalRequest).where(
            ApprovalRequest.id == request_id
        ).options(
            selectinload(ApprovalRequest.workflow).selectinload(ApprovalWorkflow.levels),
            selectinload(ApprovalRequest.actions),
            selectinload(ApprovalRequest.requester),
            selectinload(ApprovalRequest.resolver),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_request_number(
        self,
        request_number: str,
    ) -> Optional[ApprovalRequest]:
        """Get request by unique request number."""
        query = select(ApprovalRequest).where(
            ApprovalRequest.request_number == request_number
        ).options(
            selectinload(ApprovalRequest.workflow),
            selectinload(ApprovalRequest.actions),
            selectinload(ApprovalRequest.requester),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> Optional[ApprovalRequest]:
        """Get active approval request for an entity."""
        query = select(ApprovalRequest).where(
            and_(
                ApprovalRequest.entity_type == entity_type,
                ApprovalRequest.entity_id == entity_id,
                ApprovalRequest.status == ApprovalRequestStatus.PENDING,
            )
        ).options(
            selectinload(ApprovalRequest.workflow),
            selectinload(ApprovalRequest.actions),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_for_user(
        self,
        user_id: UUID,
        user_role_ids: List[UUID],
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ApprovalRequest], int]:
        """Get pending requests that a user can approve."""
        # This query finds requests where:
        # 1. Status is PENDING
        # 2. Current level approvers include the user or their roles
        # 3. User hasn't already taken action on the current level

        base_conditions = [
            ApprovalRequest.status == ApprovalRequestStatus.PENDING,
        ]
        if organization_id:
            base_conditions.append(
                ApprovalRequest.organization_id == organization_id
            )

        # Count query
        count_query = select(func.count(ApprovalRequest.id)).where(
            and_(*base_conditions)
        )
        total = (await self.session.execute(count_query)).scalar() or 0

        # Data query - we'll filter in memory for complex role/user matching
        query = select(ApprovalRequest).where(
            and_(*base_conditions)
        ).options(
            selectinload(ApprovalRequest.workflow).selectinload(ApprovalWorkflow.levels),
            selectinload(ApprovalRequest.actions),
            selectinload(ApprovalRequest.requester),
        ).offset(skip).limit(limit).order_by(ApprovalRequest.requested_at.desc())

        result = await self.session.execute(query)
        requests = list(result.scalars().all())

        # Filter to only requests where user can approve at current level
        filtered = []
        for req in requests:
            if self._can_user_approve(req, user_id, user_role_ids):
                filtered.append(req)

        return filtered, len(filtered)

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

    async def get_filtered(
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
        """Get filtered approval requests."""
        conditions = [ApprovalRequest.is_active == True]

        if organization_id:
            conditions.append(ApprovalRequest.organization_id == organization_id)
        if workflow_type:
            conditions.append(ApprovalRequest.workflow_type == workflow_type)
        if status:
            conditions.append(ApprovalRequest.status == status)
        if entity_type:
            conditions.append(ApprovalRequest.entity_type == entity_type)
        if requested_by:
            conditions.append(ApprovalRequest.requested_by == requested_by)
        if date_from:
            conditions.append(ApprovalRequest.requested_at >= date_from)
        if date_to:
            conditions.append(ApprovalRequest.requested_at <= date_to)

        # Count query
        count_query = select(func.count(ApprovalRequest.id)).where(
            and_(*conditions)
        )
        total = (await self.session.execute(count_query)).scalar() or 0

        # Data query
        query = select(ApprovalRequest).where(
            and_(*conditions)
        ).options(
            selectinload(ApprovalRequest.workflow),
            selectinload(ApprovalRequest.requester),
        ).offset(skip).limit(limit).order_by(ApprovalRequest.requested_at.desc())

        result = await self.session.execute(query)
        requests = list(result.scalars().all())

        return requests, total

    async def generate_request_number(
        self,
        organization_id: UUID,
        prefix: str = "APR",
    ) -> str:
        """Generate unique request number."""
        today = datetime.now().strftime("%Y%m%d")
        prefix_pattern = f"{prefix}/{today}/%"

        # Count existing requests with this prefix today
        count_query = select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.request_number.like(prefix_pattern)
        )
        count = (await self.session.execute(count_query)).scalar() or 0

        return f"{prefix}/{today}/{count + 1:04d}"

    async def create_action(
        self,
        action_data: dict,
    ) -> ApprovalRequestAction:
        """Create an approval action."""
        action = ApprovalRequestAction(**action_data)
        self.session.add(action)
        await self.session.flush()
        await self.session.refresh(action)
        return action

    async def update_with_version(
        self,
        request_id: UUID,
        current_version: int,
        update_data: dict,
    ) -> bool:
        """Update request with optimistic locking."""
        stmt = (
            update(ApprovalRequest)
            .where(
                and_(
                    ApprovalRequest.id == request_id,
                    ApprovalRequest.version == current_version,
                )
            )
            .values(
                **update_data,
                version=current_version + 1,
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def get_stats_by_organization(
        self,
        organization_id: UUID,
    ) -> dict:
        """Get approval statistics for dashboard."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Pending count
        pending_query = select(func.count(ApprovalRequest.id)).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == ApprovalRequestStatus.PENDING,
            )
        )
        pending_count = (await self.session.execute(pending_query)).scalar() or 0

        # Approved today
        approved_query = select(func.count(ApprovalRequest.id)).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == ApprovalRequestStatus.APPROVED,
                ApprovalRequest.resolved_at >= today_start,
            )
        )
        approved_today = (await self.session.execute(approved_query)).scalar() or 0

        # Rejected today
        rejected_query = select(func.count(ApprovalRequest.id)).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == ApprovalRequestStatus.REJECTED,
                ApprovalRequest.resolved_at >= today_start,
            )
        )
        rejected_today = (await self.session.execute(rejected_query)).scalar() or 0

        # Returned today
        returned_query = select(func.count(ApprovalRequest.id)).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == ApprovalRequestStatus.RETURNED,
                ApprovalRequest.resolved_at >= today_start,
            )
        )
        returned_today = (await self.session.execute(returned_query)).scalar() or 0

        # By workflow type
        type_query = select(
            ApprovalRequest.workflow_type,
            func.count(ApprovalRequest.id),
        ).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == ApprovalRequestStatus.PENDING,
            )
        ).group_by(ApprovalRequest.workflow_type)
        type_result = await self.session.execute(type_query)
        by_type = {str(row[0].value): row[1] for row in type_result}

        return {
            "pending_count": pending_count,
            "approved_today": approved_today,
            "rejected_today": rejected_today,
            "returned_today": returned_today,
            "by_workflow_type": by_type,
        }
