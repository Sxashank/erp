"""BI Chart Definition service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.bi.chart import ChartDefinition, ChartRoleAccess
from app.models.bi.enums import BIModule
from app.schemas.bi.chart import ChartDefinitionCreate, ChartDefinitionUpdate


class ChartService:
    """Service for BI chart definition management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chart(
        self,
        data: ChartDefinitionCreate,
        created_by: Optional[UUID] = None,
    ) -> ChartDefinition:
        """Create a new chart definition."""
        # Check if code exists
        existing = await self._get_by_code(data.code)
        if existing:
            raise ConflictException(f"Chart code '{data.code}' already exists")

        chart = ChartDefinition(
            code=data.code,
            name=data.name,
            description=data.description,
            organization_id=data.organization_id,
            module=data.module,
            chart_type=data.chart_type,
            default_data_source_id=data.default_data_source_id,
            config=data.config,
            data_mapping=data.data_mapping,
            is_system=data.is_system,
            created_by=created_by,
        )

        self.session.add(chart)
        await self.session.flush()

        # Add role access if provided
        if data.role_ids:
            for role_id in data.role_ids:
                role_access = ChartRoleAccess(
                    chart_definition_id=chart.id,
                    role_id=role_id,
                    created_by=created_by,
                )
                self.session.add(role_access)

        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    async def get_chart(self, chart_id: UUID) -> ChartDefinition:
        """Get chart definition by ID."""
        chart = await self._get_by_id(chart_id)
        if not chart:
            raise NotFoundException("Chart definition not found")
        return chart

    async def get_charts(
        self,
        organization_id: Optional[UUID] = None,
        module: Optional[BIModule] = None,
        include_system: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[ChartDefinition], int]:
        """Get all chart definitions."""
        query = select(ChartDefinition).where(ChartDefinition.is_active == True)

        if organization_id:
            if include_system:
                query = query.where(
                    (ChartDefinition.organization_id == organization_id)
                    | (ChartDefinition.organization_id.is_(None))
                )
            else:
                query = query.where(ChartDefinition.organization_id == organization_id)
        elif not include_system:
            query = query.where(ChartDefinition.organization_id.isnot(None))

        if module:
            query = query.where(ChartDefinition.module == module)

        query = query.options(selectinload(ChartDefinition.role_access))
        query = query.order_by(ChartDefinition.module, ChartDefinition.name)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        charts = result.scalars().all()

        # Get total count
        count_query = select(func.count(ChartDefinition.id)).where(ChartDefinition.is_active == True)
        if organization_id:
            if include_system:
                count_query = count_query.where(
                    (ChartDefinition.organization_id == organization_id)
                    | (ChartDefinition.organization_id.is_(None))
                )
            else:
                count_query = count_query.where(ChartDefinition.organization_id == organization_id)
        if module:
            count_query = count_query.where(ChartDefinition.module == module)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return list(charts), total

    async def get_charts_for_roles(
        self,
        role_ids: List[UUID],
        organization_id: Optional[UUID] = None,
        module: Optional[BIModule] = None,
    ) -> List[ChartDefinition]:
        """Get charts accessible to given roles."""
        query = (
            select(ChartDefinition)
            .join(ChartRoleAccess)
            .where(
                ChartDefinition.is_active == True,
                ChartRoleAccess.role_id.in_(role_ids),
            )
        )

        if organization_id:
            query = query.where(
                (ChartDefinition.organization_id == organization_id)
                | (ChartDefinition.organization_id.is_(None))
            )

        if module:
            query = query.where(ChartDefinition.module == module)

        query = query.options(selectinload(ChartDefinition.role_access))
        query = query.order_by(ChartDefinition.module, ChartDefinition.name)
        query = query.distinct()

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_chart(
        self,
        chart_id: UUID,
        data: ChartDefinitionUpdate,
        updated_by: Optional[UUID] = None,
    ) -> ChartDefinition:
        """Update an existing chart definition."""
        chart = await self.get_chart(chart_id)

        if chart.is_system:
            raise BadRequestException("Cannot modify system chart definition")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        for field, value in update_data.items():
            setattr(chart, field, value)

        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    async def delete_chart(
        self,
        chart_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> ChartDefinition:
        """Soft delete a chart definition."""
        chart = await self.get_chart(chart_id)

        if chart.is_system:
            raise BadRequestException("Cannot delete system chart definition")

        chart.soft_delete(deleted_by)
        await self.session.flush()
        return chart

    async def set_role_access(
        self,
        chart_id: UUID,
        role_ids: List[UUID],
        updated_by: Optional[UUID] = None,
    ) -> ChartDefinition:
        """Set role access for a chart (replaces existing)."""
        chart = await self.get_chart(chart_id)

        # Delete existing role access
        delete_query = select(ChartRoleAccess).where(
            ChartRoleAccess.chart_definition_id == chart_id
        )
        result = await self.session.execute(delete_query)
        existing_access = result.scalars().all()
        for access in existing_access:
            await self.session.delete(access)

        # Add new role access
        for role_id in role_ids:
            role_access = ChartRoleAccess(
                chart_definition_id=chart_id,
                role_id=role_id,
                created_by=updated_by,
            )
            self.session.add(role_access)

        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    async def _get_by_id(self, chart_id: UUID) -> Optional[ChartDefinition]:
        """Get chart by ID."""
        query = (
            select(ChartDefinition)
            .where(
                ChartDefinition.id == chart_id,
                ChartDefinition.is_active == True,
            )
            .options(selectinload(ChartDefinition.role_access))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_by_code(self, code: str) -> Optional[ChartDefinition]:
        """Get chart by code."""
        query = select(ChartDefinition).where(
            ChartDefinition.code == code,
            ChartDefinition.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
