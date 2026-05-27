"""BI Chart Definitions API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.bi.enums import BIModule
from app.services.bi.chart_service import ChartService
from app.schemas.bi.chart import (
    ChartDefinitionCreate,
    ChartDefinitionUpdate,
    ChartDefinitionResponse,
    ChartDefinitionListResponse,
    ChartRoleAccessResponse,
    SetChartRoleAccessRequest,
)
from app.schemas.base import MessageResponse

router = APIRouter()


def _to_role_access_response(access) -> ChartRoleAccessResponse:
    """Convert role access model to response."""
    return ChartRoleAccessResponse(
        id=access.id,
        chart_definition_id=access.chart_definition_id,
        role_id=access.role_id,
        role_name=access.role.name if access.role else None,
        role_code=access.role.code if access.role else None,
        created_at=access.created_at,
        updated_at=access.updated_at,
        created_by=access.created_by,
        updated_by=access.updated_by,
        is_active=access.is_active,
        version=access.version,
    )


def _to_response(chart) -> ChartDefinitionResponse:
    """Convert chart definition model to response."""
    return ChartDefinitionResponse(
        id=chart.id,
        code=chart.code,
        name=chart.name,
        description=chart.description,
        organization_id=chart.organization_id,
        module=chart.module,
        chart_type=chart.chart_type,
        default_data_source_id=chart.default_data_source_id,
        config=chart.config,
        data_mapping=chart.data_mapping,
        is_system=chart.is_system,
        role_access=[_to_role_access_response(ra) for ra in (chart.role_access or [])],
        created_at=chart.created_at,
        updated_at=chart.updated_at,
        created_by=chart.created_by,
        updated_by=chart.updated_by,
        is_active=chart.is_active,
        version=chart.version,
    )


def _to_list_response(chart) -> ChartDefinitionListResponse:
    """Convert chart definition model to list response."""
    return ChartDefinitionListResponse(
        id=chart.id,
        code=chart.code,
        name=chart.name,
        description=chart.description,
        module=chart.module,
        chart_type=chart.chart_type,
        is_system=chart.is_system,
        has_data_source=bool(chart.default_data_source_id),
        is_active=chart.is_active,
    )


@router.get("", response_model=List[ChartDefinitionListResponse], response_model_by_alias=True)
async def list_chart_definitions(
    organization_id: Optional[UUID] = None,
    module: Optional[BIModule] = None,
    include_system: bool = True,
    current_user: User = Depends(RequirePermissions("BI_CHART_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List all chart definitions."""
    service = ChartService(db)
    org_id = organization_id or current_user.organization_id
    charts, _ = await service.get_charts(
        organization_id=org_id,
        module=module,
        include_system=include_system,
    )
    return [_to_list_response(c) for c in charts]


@router.get(
    "/accessible", response_model=List[ChartDefinitionListResponse], response_model_by_alias=True
)
async def list_accessible_charts(
    module: Optional[BIModule] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List chart definitions accessible to current user's roles."""
    service = ChartService(db)
    role_ids = [ur.role_id for ur in current_user.user_roles]
    charts = await service.get_charts_for_roles(
        role_ids=role_ids,
        organization_id=current_user.organization_id,
        module=module,
    )
    return [_to_list_response(c) for c in charts]


@router.post("", response_model=ChartDefinitionResponse, response_model_by_alias=True)
async def create_chart_definition(
    data: ChartDefinitionCreate,
    current_user: User = Depends(RequirePermissions("BI_CHART_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new chart definition."""
    service = ChartService(db)
    chart = await service.create_chart(data, current_user.id)
    await db.commit()
    return _to_response(chart)


@router.get("/{chart_id}", response_model=ChartDefinitionResponse, response_model_by_alias=True)
async def get_chart_definition(
    chart_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_CHART_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get a chart definition by ID."""
    service = ChartService(db)
    chart = await service.get_chart(chart_id)
    return _to_response(chart)


@router.put("/{chart_id}", response_model=ChartDefinitionResponse, response_model_by_alias=True)
async def update_chart_definition(
    chart_id: UUID,
    data: ChartDefinitionUpdate,
    current_user: User = Depends(RequirePermissions("BI_CHART_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a chart definition."""
    service = ChartService(db)
    chart = await service.update_chart(chart_id, data, current_user.id)
    await db.commit()
    return _to_response(chart)


@router.delete("/{chart_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_chart_definition(
    chart_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_CHART_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a chart definition."""
    service = ChartService(db)
    await service.delete_chart(chart_id, current_user.id)
    await db.commit()
    return MessageResponse(message="Chart definition deleted successfully", success=True)


@router.put(
    "/{chart_id}/role-access", response_model=ChartDefinitionResponse, response_model_by_alias=True
)
async def set_chart_role_access(
    chart_id: UUID,
    data: SetChartRoleAccessRequest,
    current_user: User = Depends(RequirePermissions("BI_CHART_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Set role access for a chart definition."""
    service = ChartService(db)
    chart = await service.set_role_access(chart_id, data.role_ids, current_user.id)
    await db.commit()
    return _to_response(chart)
