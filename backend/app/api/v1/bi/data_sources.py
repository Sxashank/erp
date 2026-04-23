"""BI Data Sources API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.services.bi.datasource_service import DataSourceService
from app.schemas.bi.datasource import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataSourceListResponse,
    DataSourceFetchRequest,
    DataSourceFetchResponse,
)
from app.schemas.base import MessageResponse

router = APIRouter()


def _to_response(ds) -> DataSourceResponse:
    """Convert data source model to response."""
    return DataSourceResponse(
        id=ds.id,
        code=ds.code,
        name=ds.name,
        description=ds.description,
        organization_id=ds.organization_id,
        source_type=ds.source_type,
        api_endpoint=ds.api_endpoint,
        api_method=ds.api_method,
        query_template=ds.query_template,
        static_data=ds.static_data,
        parameters_schema=ds.parameters_schema,
        response_transform=ds.response_transform,
        cache_ttl_seconds=ds.cache_ttl_seconds,
        created_at=ds.created_at,
        updated_at=ds.updated_at,
        created_by=ds.created_by,
        updated_by=ds.updated_by,
        is_active=ds.is_active,
        version=ds.version,
    )


def _to_list_response(ds) -> DataSourceListResponse:
    """Convert data source model to list response."""
    return DataSourceListResponse(
        id=ds.id,
        code=ds.code,
        name=ds.name,
        description=ds.description,
        source_type=ds.source_type,
        organization_id=ds.organization_id,
        is_active=ds.is_active,
    )


@router.get("", response_model=List[DataSourceListResponse])
async def list_data_sources(
    organization_id: Optional[UUID] = None,
    include_system: bool = True,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """List all data sources."""
    service = DataSourceService(db)
    org_id = organization_id or current_user.organization_id
    data_sources, _ = await service.get_data_sources(
        organization_id=org_id,
        include_system=include_system,
    )
    return [_to_list_response(ds) for ds in data_sources]


@router.post("", response_model=DataSourceResponse)
async def create_data_source(
    data: DataSourceCreate,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new data source."""
    service = DataSourceService(db)
    data_source = await service.create_data_source(data, current_user.id)
    await db.commit()
    return _to_response(data_source)


@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(
    data_source_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a data source by ID."""
    service = DataSourceService(db)
    data_source = await service.get_data_source(data_source_id)
    return _to_response(data_source)


@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source(
    data_source_id: UUID,
    data: DataSourceUpdate,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a data source."""
    service = DataSourceService(db)
    data_source = await service.update_data_source(data_source_id, data, current_user.id)
    await db.commit()
    return _to_response(data_source)


@router.delete("/{data_source_id}", response_model=MessageResponse)
async def delete_data_source(
    data_source_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a data source."""
    service = DataSourceService(db)
    await service.delete_data_source(data_source_id, current_user.id)
    await db.commit()
    return MessageResponse(message="Data source deleted successfully", success=True)


@router.post("/{data_source_id}/fetch", response_model=DataSourceFetchResponse)
async def fetch_data(
    data_source_id: UUID,
    request: DataSourceFetchRequest,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Fetch data from a data source."""
    service = DataSourceService(db)
    data = await service.fetch_data(data_source_id, request.parameters)
    return DataSourceFetchResponse(data=data, cached=False)


@router.get("/{data_source_id}/preview", response_model=DataSourceFetchResponse)
async def preview_data_source(
    data_source_id: UUID,
    current_user: User = Depends(RequirePermissions("BI_DATASOURCE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Preview data from a data source (no parameters)."""
    service = DataSourceService(db)
    data = await service.fetch_data(data_source_id, None)
    return DataSourceFetchResponse(data=data, cached=False)
