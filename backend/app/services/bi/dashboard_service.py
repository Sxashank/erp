"""BI Dashboard service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ConflictException
from app.models.bi.dashboard import Dashboard, DashboardRoleAccess
from app.schemas.bi.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardRoleAccessCreate,
    DashboardRoleAccessUpdate,
)


class DashboardService:
    """Service for BI dashboard management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_dashboard(
        self,
        data: DashboardCreate,
        created_by: Optional[UUID] = None,
    ) -> Dashboard:
        """Create a new dashboard."""
        # Check if code exists in organization
        existing = await self._get_by_code(data.organization_id, data.code)
        if existing:
            raise ConflictException(f"Dashboard code '{data.code}' already exists in this organization")

        dashboard = Dashboard(
            code=data.code,
            name=data.name,
            description=data.description,
            organization_id=data.organization_id,
            is_default=data.is_default,
            is_public=data.is_public,
            layout_config=data.layout_config,
            display_order=data.display_order,
            auto_refresh=data.auto_refresh,
            refresh_interval_seconds=data.refresh_interval_seconds,
            created_by=created_by,
        )

        self.session.add(dashboard)
        await self.session.flush()
        await self.session.refresh(dashboard)
        return dashboard

    async def get_dashboard(self, dashboard_id: UUID) -> Dashboard:
        """Get dashboard by ID."""
        dashboard = await self._get_by_id(dashboard_id)
        if not dashboard:
            raise NotFoundException("Dashboard not found")
        return dashboard

    async def get_dashboards(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Dashboard], int]:
        """Get all dashboards for an organization."""
        query = (
            select(Dashboard)
            .where(
                Dashboard.organization_id == organization_id,
                Dashboard.is_active == True,
            )
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.role_access),
            )
            .order_by(Dashboard.display_order, Dashboard.name)
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        dashboards = result.scalars().all()

        # Get total count
        count_query = select(func.count(Dashboard.id)).where(
            Dashboard.organization_id == organization_id,
            Dashboard.is_active == True,
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return list(dashboards), total

    async def get_landing_dashboards(
        self,
        role_ids: List[UUID],
        organization_id: UUID,
    ) -> List[Dashboard]:
        """Get dashboards that should appear on landing page for given roles."""
        query = (
            select(Dashboard)
            .join(DashboardRoleAccess)
            .where(
                Dashboard.organization_id == organization_id,
                Dashboard.is_active == True,
                DashboardRoleAccess.role_id.in_(role_ids),
                DashboardRoleAccess.can_view == True,
                DashboardRoleAccess.show_on_landing == True,
            )
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.role_access),
            )
            .order_by(DashboardRoleAccess.landing_order, Dashboard.display_order)
            .distinct()
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_accessible_dashboards(
        self,
        role_ids: List[UUID],
        organization_id: UUID,
    ) -> List[Dashboard]:
        """Get dashboards accessible to given roles."""
        # Get public dashboards
        public_query = (
            select(Dashboard)
            .where(
                Dashboard.organization_id == organization_id,
                Dashboard.is_active == True,
                Dashboard.is_public == True,
            )
        )

        # Get dashboards with role access
        role_query = (
            select(Dashboard)
            .join(DashboardRoleAccess)
            .where(
                Dashboard.organization_id == organization_id,
                Dashboard.is_active == True,
                DashboardRoleAccess.role_id.in_(role_ids),
                DashboardRoleAccess.can_view == True,
            )
        )

        # Union and order
        from sqlalchemy import union_all

        combined = union_all(public_query, role_query).subquery()
        final_query = (
            select(Dashboard)
            .where(Dashboard.id.in_(select(combined.c.id)))
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.role_access),
            )
            .order_by(Dashboard.display_order, Dashboard.name)
        )

        result = await self.session.execute(final_query)
        return list(result.scalars().all())

    async def update_dashboard(
        self,
        dashboard_id: UUID,
        data: DashboardUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Dashboard:
        """Update an existing dashboard."""
        dashboard = await self.get_dashboard(dashboard_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        for field, value in update_data.items():
            setattr(dashboard, field, value)

        await self.session.flush()
        await self.session.refresh(dashboard)
        return dashboard

    async def delete_dashboard(
        self,
        dashboard_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Dashboard:
        """Soft delete a dashboard."""
        dashboard = await self.get_dashboard(dashboard_id)
        dashboard.soft_delete(deleted_by)
        await self.session.flush()
        return dashboard

    async def set_default(
        self,
        dashboard_id: UUID,
        organization_id: UUID,
        updated_by: Optional[UUID] = None,
    ) -> Dashboard:
        """Set a dashboard as the default for an organization."""
        # Unset current default
        query = select(Dashboard).where(
            Dashboard.organization_id == organization_id,
            Dashboard.is_default == True,
            Dashboard.is_active == True,
        )
        result = await self.session.execute(query)
        current_default = result.scalar_one_or_none()
        if current_default:
            current_default.is_default = False
            current_default.updated_by = updated_by

        # Set new default
        dashboard = await self.get_dashboard(dashboard_id)
        dashboard.is_default = True
        dashboard.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(dashboard)
        return dashboard

    # Role Access methods
    async def get_role_access(
        self,
        dashboard_id: UUID,
    ) -> List[DashboardRoleAccess]:
        """Get all role access for a dashboard."""
        await self.get_dashboard(dashboard_id)  # Validate dashboard exists

        query = (
            select(DashboardRoleAccess)
            .where(
                DashboardRoleAccess.dashboard_id == dashboard_id,
                DashboardRoleAccess.is_active == True,
            )
            .options(selectinload(DashboardRoleAccess.role))
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_role_access(
        self,
        dashboard_id: UUID,
        data: DashboardRoleAccessCreate,
        created_by: Optional[UUID] = None,
    ) -> DashboardRoleAccess:
        """Create role access for a dashboard."""
        await self.get_dashboard(dashboard_id)  # Validate dashboard exists

        # Check if access already exists
        existing = await self._get_role_access(dashboard_id, data.role_id)
        if existing:
            raise ConflictException("Role access already exists for this dashboard")

        role_access = DashboardRoleAccess(
            dashboard_id=dashboard_id,
            role_id=data.role_id,
            can_view=data.can_view,
            can_edit=data.can_edit,
            show_on_landing=data.show_on_landing,
            landing_order=data.landing_order,
            created_by=created_by,
        )

        self.session.add(role_access)
        await self.session.flush()
        await self.session.refresh(role_access)
        return role_access

    async def update_role_access(
        self,
        access_id: UUID,
        data: DashboardRoleAccessUpdate,
        updated_by: Optional[UUID] = None,
    ) -> DashboardRoleAccess:
        """Update role access for a dashboard."""
        role_access = await self._get_role_access_by_id(access_id)
        if not role_access:
            raise NotFoundException("Role access not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        for field, value in update_data.items():
            setattr(role_access, field, value)

        await self.session.flush()
        await self.session.refresh(role_access)
        return role_access

    async def delete_role_access(
        self,
        access_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> DashboardRoleAccess:
        """Delete role access for a dashboard."""
        role_access = await self._get_role_access_by_id(access_id)
        if not role_access:
            raise NotFoundException("Role access not found")

        role_access.soft_delete(deleted_by)
        await self.session.flush()
        return role_access

    async def _get_by_id(self, dashboard_id: UUID) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        query = (
            select(Dashboard)
            .where(
                Dashboard.id == dashboard_id,
                Dashboard.is_active == True,
            )
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.role_access),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> Optional[Dashboard]:
        """Get dashboard by code within organization."""
        query = select(Dashboard).where(
            Dashboard.organization_id == organization_id,
            Dashboard.code == code,
            Dashboard.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_role_access(
        self,
        dashboard_id: UUID,
        role_id: UUID,
    ) -> Optional[DashboardRoleAccess]:
        """Get role access by dashboard and role."""
        query = select(DashboardRoleAccess).where(
            DashboardRoleAccess.dashboard_id == dashboard_id,
            DashboardRoleAccess.role_id == role_id,
            DashboardRoleAccess.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_role_access_by_id(
        self,
        access_id: UUID,
    ) -> Optional[DashboardRoleAccess]:
        """Get role access by ID."""
        query = (
            select(DashboardRoleAccess)
            .where(
                DashboardRoleAccess.id == access_id,
                DashboardRoleAccess.is_active == True,
            )
            .options(selectinload(DashboardRoleAccess.role))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
