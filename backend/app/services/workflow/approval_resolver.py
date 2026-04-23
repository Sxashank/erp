"""Approval resolver - resolves approvers from rules."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import ApprovalRule, ApproverType
from app.models.auth.user import User
from app.models.auth.role import UserRole


class ApprovalResolver:
    """Service for resolving approvers from approval rules."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve_approvers(
        self,
        rule: ApprovalRule,
        context: Dict[str, Any],
        organization_id: UUID,
        initiator_id: Optional[UUID] = None,
    ) -> List[UUID]:
        """
        Resolve actual user IDs from an approval rule.

        Args:
            rule: The approval rule defining who can approve
            context: Entity context for dynamic resolution
            organization_id: Organization ID for scoping
            initiator_id: User who initiated the workflow (for self-approval check)

        Returns:
            List of user IDs who can approve
        """
        approver_type = rule.approver_type
        approvers: List[UUID] = []

        if approver_type == ApproverType.USER:
            if rule.user_id:
                # Verify user is active
                if await self._is_user_active(rule.user_id):
                    approvers.append(rule.user_id)

        elif approver_type == ApproverType.ROLE:
            if rule.role_id:
                approvers = await self._resolve_role_users(
                    rule.role_id, organization_id
                )

        elif approver_type == ApproverType.DESIGNATION:
            if rule.designation:
                approvers = await self._resolve_designation_users(
                    rule.designation, organization_id
                )

        elif approver_type == ApproverType.DEPARTMENT_HEAD:
            # Get department from context
            department_id = context.get("department_id")
            if department_id:
                head = await self._resolve_department_head(department_id)
                if head:
                    approvers.append(head)

        elif approver_type == ApproverType.REPORTING_MANAGER:
            # Get initiator's reporting manager
            if initiator_id:
                manager = await self._resolve_reporting_manager(initiator_id)
                if manager:
                    approvers.append(manager)

        elif approver_type == ApproverType.DYNAMIC:
            if rule.dynamic_field:
                dynamic_approver = await self._resolve_dynamic_field(
                    rule.dynamic_field, context
                )
                if dynamic_approver:
                    approvers.append(dynamic_approver)

        # Fallback to admin if no approvers found and fallback enabled
        if not approvers and rule.fallback_to_admin:
            admin_users = await self._get_admin_users(organization_id)
            approvers.extend(admin_users)

        return approvers

    async def _is_user_active(self, user_id: UUID) -> bool:
        """Check if a user is active."""
        query = select(User).where(
            and_(
                User.id == user_id,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def _resolve_role_users(
        self,
        role_id: UUID,
        organization_id: UUID,
    ) -> List[UUID]:
        """Get all active users with a given role in the organization."""
        query = (
            select(UserRole.user_id)
            .join(User, User.id == UserRole.user_id)
            .where(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.is_active == True,
                    User.is_active == True,
                    User.organization_id == organization_id,
                )
            )
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def _resolve_designation_users(
        self,
        designation: str,
        organization_id: UUID,
    ) -> List[UUID]:
        """Get all active users with a given designation."""
        query = select(User.id).where(
            and_(
                User.designation == designation,
                User.organization_id == organization_id,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def _resolve_department_head(
        self,
        department_id: UUID,
    ) -> Optional[UUID]:
        """Get the department head user ID."""
        from app.models.masters.department import Department

        query = select(Department.head_id).where(
            and_(
                Department.id == department_id,
                Department.is_active == True,
            )
        )
        result = await self.session.execute(query)
        row = result.fetchone()
        return row[0] if row and row[0] else None

    async def _resolve_reporting_manager(
        self,
        user_id: UUID,
    ) -> Optional[UUID]:
        """Get a user's reporting manager."""
        query = select(User.reporting_manager_id).where(
            and_(
                User.id == user_id,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        row = result.fetchone()
        manager_id = row[0] if row else None

        # Verify manager is active
        if manager_id and await self._is_user_active(manager_id):
            return manager_id
        return None

    async def _resolve_dynamic_field(
        self,
        field_path: str,
        context: Dict[str, Any],
    ) -> Optional[UUID]:
        """
        Resolve user from a dynamic field path.

        Example field paths:
        - "vendor.account_manager_id"
        - "created_by.manager_id"
        - "project_owner_id"
        """
        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

            if value is None:
                return None

        # Value should be a UUID string or UUID
        if isinstance(value, str):
            try:
                from uuid import UUID as UUIDType
                user_id = UUIDType(value)
            except ValueError:
                return None
        elif isinstance(value, UUID):
            user_id = value
        else:
            return None

        # Verify user is active
        if await self._is_user_active(user_id):
            return user_id
        return None

    async def _get_admin_users(
        self,
        organization_id: UUID,
    ) -> List[UUID]:
        """Get admin users for fallback."""
        # Look for users with admin role
        from app.models.auth.role import Role

        # Find admin role
        admin_query = select(Role.id).where(
            and_(
                Role.code.in_(["ADMIN", "SUPER_ADMIN", "ORG_ADMIN"]),
                Role.is_active == True,
            )
        )
        result = await self.session.execute(admin_query)
        admin_role_ids = [row[0] for row in result.fetchall()]

        if not admin_role_ids:
            return []

        # Get users with admin roles
        user_query = (
            select(UserRole.user_id)
            .distinct()
            .join(User, User.id == UserRole.user_id)
            .where(
                and_(
                    UserRole.role_id.in_(admin_role_ids),
                    UserRole.is_active == True,
                    User.is_active == True,
                    User.organization_id == organization_id,
                )
            )
        )
        result = await self.session.execute(user_query)
        return [row[0] for row in result.fetchall()]
