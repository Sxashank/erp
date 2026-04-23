"""BI Dashboard Widgets API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.services.bi.widget_service import WidgetService
from app.schemas.bi.dashboard import (
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardWidgetResponse,
    BulkLayoutUpdateRequest,
    ChartDefinitionBrief,
    DataSourceBrief,
)
from app.schemas.base import MessageResponse

router = APIRouter()


def _to_widget_response(widget) -> DashboardWidgetResponse:
    """Convert widget model to response."""
    chart_brief = None
    if widget.chart_definition:
        chart_brief = ChartDefinitionBrief(
            id=widget.chart_definition.id,
            code=widget.chart_definition.code,
            name=widget.chart_definition.name,
            chart_type=widget.chart_definition.chart_type,
            module=widget.chart_definition.module,
        )

    data_source_brief = None
    if widget.data_source:
        data_source_brief = DataSourceBrief(
            id=widget.data_source.id,
            code=widget.data_source.code,
            name=widget.data_source.name,
        )

    return DashboardWidgetResponse(
        id=widget.id,
        dashboard_id=widget.dashboard_id,
        widget_key=widget.widget_key,
        title=widget.title,
        widget_type=widget.widget_type,
        chart_definition_id=widget.chart_definition_id,
        data_source_id=widget.data_source_id,
        chart_definition=chart_brief,
        data_source=data_source_brief,
        grid_x=widget.grid_x,
        grid_y=widget.grid_y,
        grid_w=widget.grid_w,
        grid_h=widget.grid_h,
        config=widget.config,
        display_order=widget.display_order,
        created_at=widget.created_at,
        updated_at=widget.updated_at,
        created_by=widget.created_by,
        updated_by=widget.updated_by,
        is_active=widget.is_active,
        version=widget.version,
    )


@router.get("/{dashboard_id}/widgets", response_model=List[DashboardWidgetResponse])
async def list_widgets(
    dashboard_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """List all widgets in a dashboard."""
    service = WidgetService(db)
    widgets = await service.get_widgets(dashboard_id)
    return [_to_widget_response(w) for w in widgets]


@router.post("/{dashboard_id}/widgets", response_model=DashboardWidgetResponse)
async def create_widget(
    dashboard_id: UUID,
    data: DashboardWidgetCreate,
    current_user: User = Depends(RequirePermissions("BI_WIDGET_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new widget in a dashboard."""
    service = WidgetService(db)
    widget = await service.create_widget(dashboard_id, data, current_user.id)
    await db.commit()
    return _to_widget_response(widget)


@router.get("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def get_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a widget by ID."""
    service = WidgetService(db)
    widget = await service.get_widget(widget_id)
    return _to_widget_response(widget)


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def update_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    data: DashboardWidgetUpdate,
    current_user: User = Depends(RequirePermissions("BI_WIDGET_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a widget."""
    service = WidgetService(db)
    widget = await service.update_widget(widget_id, data, current_user.id)
    await db.commit()
    return _to_widget_response(widget)


@router.delete("/{dashboard_id}/widgets/{widget_id}", response_model=MessageResponse)
async def delete_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_WIDGET_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a widget."""
    service = WidgetService(db)
    await service.delete_widget(widget_id, current_user.id)
    await db.commit()
    return MessageResponse(message="Widget deleted successfully", success=True)


@router.put("/{dashboard_id}/widgets/layout", response_model=List[DashboardWidgetResponse])
async def update_layout(
    dashboard_id: UUID,
    data: BulkLayoutUpdateRequest,
    current_user: User = Depends(RequirePermissions("BI_WIDGET_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Bulk update widget layouts."""
    service = WidgetService(db)
    widgets = await service.update_layout(dashboard_id, data.layouts, current_user.id)
    await db.commit()
    return [_to_widget_response(w) for w in widgets]
