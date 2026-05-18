"""BI Dashboards API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.bi.dashboard_service import DashboardService
from app.schemas.bi.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListResponse,
    DashboardRoleAccessCreate,
    DashboardRoleAccessUpdate,
    DashboardRoleAccessResponse,
    DashboardWidgetResponse,
    LandingDashboardResponse,
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


def _to_role_access_response(access) -> DashboardRoleAccessResponse:
    """Convert role access model to response."""
    return DashboardRoleAccessResponse(
        id=access.id,
        dashboard_id=access.dashboard_id,
        role_id=access.role_id,
        role_name=access.role.name if access.role else None,
        role_code=access.role.code if access.role else None,
        can_view=access.can_view,
        can_edit=access.can_edit,
        show_on_landing=access.show_on_landing,
        landing_order=access.landing_order,
        created_at=access.created_at,
        updated_at=access.updated_at,
        created_by=access.created_by,
        updated_by=access.updated_by,
        is_active=access.is_active,
        version=access.version,
    )


def _to_response(dashboard) -> DashboardResponse:
    """Convert dashboard model to response."""
    return DashboardResponse(
        id=dashboard.id,
        code=dashboard.code,
        name=dashboard.name,
        description=dashboard.description,
        organization_id=dashboard.organization_id,
        is_default=dashboard.is_default,
        is_public=dashboard.is_public,
        layout_config=dashboard.layout_config,
        display_order=dashboard.display_order,
        auto_refresh=dashboard.auto_refresh,
        refresh_interval_seconds=dashboard.refresh_interval_seconds,
        widgets=[_to_widget_response(w) for w in (dashboard.widgets or [])],
        role_access=[_to_role_access_response(ra) for ra in (dashboard.role_access or [])],
        created_at=dashboard.created_at,
        updated_at=dashboard.updated_at,
        created_by=dashboard.created_by,
        updated_by=dashboard.updated_by,
        is_active=dashboard.is_active,
        version=dashboard.version,
    )


def _to_list_response(dashboard) -> DashboardListResponse:
    """Convert dashboard model to list response."""
    return DashboardListResponse(
        id=dashboard.id,
        code=dashboard.code,
        name=dashboard.name,
        description=dashboard.description,
        is_default=dashboard.is_default,
        is_public=dashboard.is_public,
        display_order=dashboard.display_order,
        widget_count=len(dashboard.widgets) if dashboard.widgets else 0,
        is_active=dashboard.is_active,
    )


def _to_landing_response(dashboard, landing_order: int = 0) -> LandingDashboardResponse:
    """Convert dashboard to landing page response."""
    return LandingDashboardResponse(
        id=dashboard.id,
        code=dashboard.code,
        name=dashboard.name,
        description=dashboard.description,
        display_order=dashboard.display_order,
        landing_order=landing_order,
        auto_refresh=dashboard.auto_refresh,
        refresh_interval_seconds=dashboard.refresh_interval_seconds,
        widgets=[_to_widget_response(w) for w in (dashboard.widgets or [])],
    )


@router.get("", response_model=List[DashboardListResponse], response_model_by_alias=True)
async def list_dashboards(
    organization_id: Optional[UUID] = None,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List all dashboards for the organization."""
    service = DashboardService(db)
    org_id = organization_id or current_user.organization_id
    dashboards, _ = await service.get_dashboards(org_id)
    return [_to_list_response(d) for d in dashboards]


@router.get("/landing", response_model=List[LandingDashboardResponse], response_model_by_alias=True)
async def get_landing_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get dashboards for current user's landing page."""
    if not current_user.organization_id:
        return []

    service = DashboardService(db)
    role_ids = [ur.role_id for ur in current_user.user_roles]
    dashboards = await service.get_landing_dashboards(
        role_ids=role_ids,
        organization_id=current_user.organization_id,
    )

    # Get landing order from role access
    results = []
    for d in dashboards:
        landing_order = 0
        for ra in (d.role_access or []):
            if ra.role_id in role_ids and ra.show_on_landing:
                landing_order = ra.landing_order
                break
        results.append(_to_landing_response(d, landing_order))

    return sorted(results, key=lambda x: (x.landing_order, x.display_order))


@router.get("/accessible", response_model=List[DashboardListResponse], response_model_by_alias=True)
async def list_accessible_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List dashboards accessible to current user."""
    if not current_user.organization_id:
        return []

    service = DashboardService(db)
    role_ids = [ur.role_id for ur in current_user.user_roles]
    dashboards = await service.get_accessible_dashboards(
        role_ids=role_ids,
        organization_id=current_user.organization_id,
    )
    return [_to_list_response(d) for d in dashboards]


@router.post("", response_model=DashboardResponse, response_model_by_alias=True)
async def create_dashboard(
    data: DashboardCreate,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new dashboard."""
    service = DashboardService(db)
    dashboard = await service.create_dashboard(data, current_user.id)
    await db.commit()
    return _to_response(dashboard)


@router.get("/{dashboard_id}", response_model=DashboardResponse, response_model_by_alias=True)
async def get_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get a dashboard by ID."""
    service = DashboardService(db)
    dashboard = await service.get_dashboard(dashboard_id)
    return _to_response(dashboard)


@router.put("/{dashboard_id}", response_model=DashboardResponse, response_model_by_alias=True)
async def update_dashboard(
    dashboard_id: UUID,
    data: DashboardUpdate,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a dashboard."""
    service = DashboardService(db)
    dashboard = await service.update_dashboard(dashboard_id, data, current_user.id)
    await db.commit()
    return _to_response(dashboard)


@router.delete("/{dashboard_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a dashboard."""
    service = DashboardService(db)
    await service.delete_dashboard(dashboard_id, current_user.id)
    await db.commit()
    return MessageResponse(message="Dashboard deleted successfully", success=True)


@router.post("/{dashboard_id}/set-default", response_model=DashboardResponse, response_model_by_alias=True)
async def set_default_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Set a dashboard as default for the organization."""
    service = DashboardService(db)
    dashboard = await service.get_dashboard(dashboard_id)
    dashboard = await service.set_default(
        dashboard_id,
        dashboard.organization_id,
        current_user.id,
    )
    await db.commit()
    return _to_response(dashboard)


# Role Access endpoints
@router.get("/{dashboard_id}/access", response_model=List[DashboardRoleAccessResponse], response_model_by_alias=True)
async def list_dashboard_access(
    dashboard_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_ACCESS_MANAGE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List role access for a dashboard."""
    service = DashboardService(db)
    access_list = await service.get_role_access(dashboard_id)
    return [_to_role_access_response(a) for a in access_list]


@router.post("/{dashboard_id}/access", response_model=DashboardRoleAccessResponse, response_model_by_alias=True)
async def create_dashboard_access(
    dashboard_id: UUID,
    data: DashboardRoleAccessCreate,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_ACCESS_MANAGE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create role access for a dashboard."""
    service = DashboardService(db)
    access = await service.create_role_access(dashboard_id, data, current_user.id)
    await db.commit()
    return _to_role_access_response(access)


@router.put("/{dashboard_id}/access/{access_id}", response_model=DashboardRoleAccessResponse, response_model_by_alias=True)
async def update_dashboard_access(
    dashboard_id: UUID,
    access_id: UUID,
    data: DashboardRoleAccessUpdate,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_ACCESS_MANAGE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update role access for a dashboard."""
    service = DashboardService(db)
    access = await service.update_role_access(access_id, data, current_user.id)
    await db.commit()
    return _to_role_access_response(access)


@router.delete("/{dashboard_id}/access/{access_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_dashboard_access(
    dashboard_id: UUID,
    access_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DASHBOARD_ACCESS_MANAGE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete role access for a dashboard."""
    service = DashboardService(db)
    await service.delete_role_access(access_id, current_user.id)
    await db.commit()
    return MessageResponse(message="Role access deleted successfully", success=True)
