"""BI Dashboard Widget service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ConflictException
from app.models.bi.dashboard import Dashboard, DashboardWidget
from app.schemas.bi.dashboard import (
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardWidgetLayoutUpdate,
)


class WidgetService:
    """Service for BI dashboard widget management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_widget(
        self,
        dashboard_id: UUID,
        data: DashboardWidgetCreate,
        created_by: Optional[UUID] = None,
    ) -> DashboardWidget:
        """Create a new widget in a dashboard."""
        # Validate dashboard exists
        dashboard = await self._get_dashboard(dashboard_id)
        if not dashboard:
            raise NotFoundException("Dashboard not found")

        # Check if widget_key exists in dashboard
        existing = await self._get_widget_by_key(dashboard_id, data.widget_key)
        if existing:
            raise ConflictException(f"Widget key '{data.widget_key}' already exists in this dashboard")

        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            widget_key=data.widget_key,
            title=data.title,
            widget_type=data.widget_type,
            chart_definition_id=data.chart_definition_id,
            data_source_id=data.data_source_id,
            grid_x=data.grid_x,
            grid_y=data.grid_y,
            grid_w=data.grid_w,
            grid_h=data.grid_h,
            config=data.config,
            display_order=data.display_order,
            created_by=created_by,
        )

        self.session.add(widget)
        await self.session.flush()
        await self.session.refresh(widget)
        return widget

    async def get_widget(self, widget_id: UUID) -> DashboardWidget:
        """Get widget by ID."""
        widget = await self._get_widget_by_id(widget_id)
        if not widget:
            raise NotFoundException("Widget not found")
        return widget

    async def get_widgets(self, dashboard_id: UUID) -> List[DashboardWidget]:
        """Get all widgets for a dashboard."""
        # Validate dashboard exists
        dashboard = await self._get_dashboard(dashboard_id)
        if not dashboard:
            raise NotFoundException("Dashboard not found")

        query = (
            select(DashboardWidget)
            .where(
                DashboardWidget.dashboard_id == dashboard_id,
                DashboardWidget.is_active == True,
            )
            .options(
                selectinload(DashboardWidget.chart_definition),
                selectinload(DashboardWidget.data_source),
            )
            .order_by(DashboardWidget.display_order, DashboardWidget.grid_y, DashboardWidget.grid_x)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_widget(
        self,
        widget_id: UUID,
        data: DashboardWidgetUpdate,
        updated_by: Optional[UUID] = None,
    ) -> DashboardWidget:
        """Update an existing widget."""
        widget = await self.get_widget(widget_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        for field, value in update_data.items():
            setattr(widget, field, value)

        await self.session.flush()
        await self.session.refresh(widget)
        return widget

    async def delete_widget(
        self,
        widget_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> DashboardWidget:
        """Soft delete a widget."""
        widget = await self.get_widget(widget_id)
        widget.soft_delete(deleted_by)
        await self.session.flush()
        return widget

    async def update_layout(
        self,
        dashboard_id: UUID,
        layouts: List[DashboardWidgetLayoutUpdate],
        updated_by: Optional[UUID] = None,
    ) -> List[DashboardWidget]:
        """Bulk update widget layouts."""
        # Validate dashboard exists
        dashboard = await self._get_dashboard(dashboard_id)
        if not dashboard:
            raise NotFoundException("Dashboard not found")

        updated_widgets = []

        for layout in layouts:
            widget = await self._get_widget_by_id(layout.widget_id)
            if widget and widget.dashboard_id == dashboard_id:
                widget.grid_x = layout.grid_x
                widget.grid_y = layout.grid_y
                widget.grid_w = layout.grid_w
                widget.grid_h = layout.grid_h
                widget.updated_by = updated_by
                updated_widgets.append(widget)

        await self.session.flush()

        # Refresh all widgets
        for widget in updated_widgets:
            await self.session.refresh(widget)

        return updated_widgets

    async def _get_dashboard(self, dashboard_id: UUID) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        query = select(Dashboard).where(
            Dashboard.id == dashboard_id,
            Dashboard.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_widget_by_id(self, widget_id: UUID) -> Optional[DashboardWidget]:
        """Get widget by ID."""
        query = (
            select(DashboardWidget)
            .where(
                DashboardWidget.id == widget_id,
                DashboardWidget.is_active == True,
            )
            .options(
                selectinload(DashboardWidget.chart_definition),
                selectinload(DashboardWidget.data_source),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_widget_by_key(
        self,
        dashboard_id: UUID,
        widget_key: str,
    ) -> Optional[DashboardWidget]:
        """Get widget by key within dashboard."""
        query = select(DashboardWidget).where(
            DashboardWidget.dashboard_id == dashboard_id,
            DashboardWidget.widget_key == widget_key,
            DashboardWidget.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
