"""BI Data Source service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.bi.datasource import DataSource
from app.schemas.bi.datasource import DataSourceCreate, DataSourceUpdate


class DataSourceService:
    """Service for BI data source management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_data_source(
        self,
        data: DataSourceCreate,
        created_by: Optional[UUID] = None,
    ) -> DataSource:
        """Create a new data source."""
        # Check if code exists
        existing = await self._get_by_code(data.code)
        if existing:
            raise ConflictException(f"Data source code '{data.code}' already exists")

        data_source = DataSource(
            code=data.code,
            name=data.name,
            description=data.description,
            organization_id=data.organization_id,
            source_type=data.source_type,
            api_endpoint=data.api_endpoint,
            api_method=data.api_method,
            query_template=data.query_template,
            static_data=data.static_data,
            parameters_schema=data.parameters_schema,
            response_transform=data.response_transform,
            cache_ttl_seconds=data.cache_ttl_seconds,
            created_by=created_by,
        )

        self.session.add(data_source)
        await self.session.flush()
        await self.session.refresh(data_source)
        return data_source

    async def get_data_source(self, data_source_id: UUID) -> DataSource:
        """Get data source by ID."""
        data_source = await self._get_by_id(data_source_id)
        if not data_source:
            raise NotFoundException("Data source not found")
        return data_source

    async def get_data_sources(
        self,
        organization_id: Optional[UUID] = None,
        include_system: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[DataSource], int]:
        """Get all data sources."""
        query = select(DataSource).where(DataSource.is_active == True)

        if organization_id:
            if include_system:
                query = query.where(
                    (DataSource.organization_id == organization_id)
                    | (DataSource.organization_id.is_(None))
                )
            else:
                query = query.where(DataSource.organization_id == organization_id)
        elif not include_system:
            query = query.where(DataSource.organization_id.isnot(None))

        query = query.order_by(DataSource.name).offset(skip).limit(limit)

        result = await self.session.execute(query)
        data_sources = result.scalars().all()

        # Get total count
        count_query = select(func.count(DataSource.id)).where(DataSource.is_active == True)
        if organization_id:
            if include_system:
                count_query = count_query.where(
                    (DataSource.organization_id == organization_id)
                    | (DataSource.organization_id.is_(None))
                )
            else:
                count_query = count_query.where(DataSource.organization_id == organization_id)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return list(data_sources), total

    async def update_data_source(
        self,
        data_source_id: UUID,
        data: DataSourceUpdate,
        updated_by: Optional[UUID] = None,
    ) -> DataSource:
        """Update an existing data source."""
        data_source = await self.get_data_source(data_source_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        for field, value in update_data.items():
            setattr(data_source, field, value)

        await self.session.flush()
        await self.session.refresh(data_source)
        return data_source

    async def delete_data_source(
        self,
        data_source_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> DataSource:
        """Soft delete a data source."""
        data_source = await self.get_data_source(data_source_id)
        data_source.soft_delete(deleted_by)
        await self.session.flush()
        return data_source

    async def _get_by_id(self, data_source_id: UUID) -> Optional[DataSource]:
        """Get data source by ID."""
        query = select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_by_code(self, code: str) -> Optional[DataSource]:
        """Get data source by code."""
        query = select(DataSource).where(
            DataSource.code == code,
            DataSource.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_data(
        self,
        data_source_id: UUID,
        parameters: Optional[dict] = None,
    ) -> dict:
        """Fetch data from a supported data source."""
        data_source = await self.get_data_source(data_source_id)

        from app.models.bi.enums import DataSourceType

        if data_source.source_type == DataSourceType.STATIC:
            return data_source.static_data or {}

        if data_source.source_type == DataSourceType.API_ENDPOINT:
            raise BadRequestException(
                "API endpoint BI data sources are not enabled in this release. "
                "Use a STATIC data source for manual-first dashboards."
            )

        if data_source.source_type == DataSourceType.SQL_QUERY:
            raise BadRequestException(
                "SQL-query BI data sources are not enabled in this release. "
                "Use a STATIC data source for manual-first dashboards."
            )

        return {}
