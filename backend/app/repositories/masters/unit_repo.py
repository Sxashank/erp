"""Unit repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.masters.unit import Unit
from app.repositories.base import BaseRepository


class UnitRepository(BaseRepository[Unit]):
    """Repository for Unit operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Unit, session)

    async def get_by_code(self, code: str) -> Optional[Unit]:
        """Get unit by code."""
        return await self.get_by_field("code", code)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[Unit]:
        """Get all units for an organization."""
        query = select(Unit).where(Unit.organization_id == organization_id)
        if not include_inactive:
            query = query.where(Unit.is_active == True)
        query = query.order_by(Unit.level, Unit.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_head_office(self, organization_id: UUID) -> Optional[Unit]:
        """Get head office unit for an organization."""
        query = select(Unit).where(
            and_(
                Unit.organization_id == organization_id,
                Unit.is_head_office == True,
                Unit.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_children(self, parent_unit_id: UUID) -> List[Unit]:
        """Get child units of a parent unit."""
        query = select(Unit).where(
            and_(
                Unit.parent_unit_id == parent_unit_id,
                Unit.is_active == True,
            )
        ).order_by(Unit.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_tree(self, organization_id: UUID) -> List[Unit]:
        """Get unit tree for an organization."""
        query = select(Unit).where(
            and_(
                Unit.organization_id == organization_id,
                Unit.is_active == True,
            )
        ).options(
            selectinload(Unit.child_units)
        ).order_by(Unit.level, Unit.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_root_units(self, organization_id: UUID) -> List[Unit]:
        """Get root level units (no parent) with children loaded recursively."""
        # First get all units for this organization with children eager loaded
        query = select(Unit).where(
            and_(
                Unit.organization_id == organization_id,
                Unit.is_active == True,
            )
        ).options(
            selectinload(Unit.child_units)
        ).order_by(Unit.level, Unit.name)

        result = await self.session.execute(query)
        all_units = list(result.scalars().unique().all())

        # Filter to only root units (those without parent)
        root_units = [u for u in all_units if u.parent_unit_id is None]
        return root_units

    async def code_exists(
        self,
        code: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if unit code already exists."""
        query = select(Unit.id).where(Unit.code == code)
        if exclude_id:
            query = query.where(Unit.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def update_hierarchy(self, unit: Unit) -> Unit:
        """Update hierarchy path and level for a unit."""
        if unit.parent_unit_id:
            parent = await self.get(unit.parent_unit_id)
            if parent:
                unit.level = parent.level + 1
                unit.path = f"{parent.path or ''}/{parent.id}"
            else:
                unit.level = 1
                unit.path = None
        else:
            unit.level = 1
            unit.path = None

        await self.session.flush()
        return unit

    async def has_children(self, unit_id: UUID) -> bool:
        """Check if unit has child units."""
        children = await self.get_children(unit_id)
        return len(children) > 0
