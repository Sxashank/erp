"""GST Registration repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.gst_registration import GSTRegistration
from app.repositories.base import BaseRepository


class GSTRegistrationRepository(BaseRepository[GSTRegistration]):
    """Repository for GST Registration operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(GSTRegistration, session)

    async def get_by_gstin(self, gstin: str) -> Optional[GSTRegistration]:
        """Get registration by GSTIN."""
        query = (
            select(GSTRegistration)
            .options(
                selectinload(GSTRegistration.organization),
                selectinload(GSTRegistration.unit),
            )
            .where(
                and_(
                    GSTRegistration.gstin == gstin.upper(),
                    GSTRegistration.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[GSTRegistration], int]:
        """Get all GST registrations for an organization."""
        conditions = [GSTRegistration.organization_id == organization_id]
        if not include_inactive:
            conditions.append(GSTRegistration.is_active == True)

        base_query = (
            select(GSTRegistration)
            .options(
                selectinload(GSTRegistration.organization),
                selectinload(GSTRegistration.unit),
            )
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(GSTRegistration).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(GSTRegistration.gstin).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_unit(
        self,
        unit_id: UUID,
    ) -> Optional[GSTRegistration]:
        """Get GST registration for a specific unit."""
        query = (
            select(GSTRegistration)
            .options(
                selectinload(GSTRegistration.organization),
                selectinload(GSTRegistration.unit),
            )
            .where(
                and_(
                    GSTRegistration.unit_id == unit_id,
                    GSTRegistration.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, id: UUID) -> Optional[GSTRegistration]:
        """Get GST registration with all relationships loaded."""
        query = (
            select(GSTRegistration)
            .options(
                selectinload(GSTRegistration.organization),
                selectinload(GSTRegistration.unit),
            )
            .where(GSTRegistration.id == id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
