"""Designation repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.masters.designation import Designation
from app.repositories.base import BaseRepository


class DesignationRepository(BaseRepository[Designation]):
    """Repository for Designation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Designation, session)

    async def get_by_code(self, code: str) -> Optional[Designation]:
        """Get designation by code."""
        return await self.get_by_field("code", code)

    async def get_by_department(
        self,
        department_id: UUID,
        include_inactive: bool = False,
    ) -> List[Designation]:
        """Get all designations for a department."""
        query = select(Designation).where(Designation.department_id == department_id)
        if not include_inactive:
            query = query.where(Designation.is_active == True)
        query = query.order_by(Designation.level, Designation.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[Designation]:
        """Get all designations with department loaded."""
        query = select(Designation).options(
            selectinload(Designation.department),
            selectinload(Designation.reporting_to),
        )
        if not include_inactive:
            query = query.where(Designation.is_active == True)
        query = query.offset(skip).limit(limit).order_by(Designation.level, Designation.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_reporting_hierarchy(self, designation_id: UUID) -> List[Designation]:
        """Get reporting hierarchy for a designation."""
        hierarchy = []
        current = await self.get(designation_id)

        while current and current.reporting_to_id:
            parent = await self.get(current.reporting_to_id)
            if parent:
                hierarchy.append(parent)
                current = parent
            else:
                break

        return hierarchy

    async def get_reports(self, designation_id: UUID) -> List[Designation]:
        """Get designations that report to this designation."""
        query = select(Designation).where(
            and_(
                Designation.reporting_to_id == designation_id,
                Designation.is_active == True,
            )
        ).order_by(Designation.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def code_exists(
        self,
        code: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if designation code already exists."""
        query = select(Designation.id).where(Designation.code == code)
        if exclude_id:
            query = query.where(Designation.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def has_reports(self, designation_id: UUID) -> bool:
        """Check if designation has reporting designations."""
        reports = await self.get_reports(designation_id)
        return len(reports) > 0
