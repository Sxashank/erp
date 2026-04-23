"""TDS Section repository."""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_section import TDSSection
from app.repositories.base import BaseRepository


class TDSSectionRepository(BaseRepository[TDSSection]):
    """Repository for TDS Section operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TDSSection, session)

    async def get_by_code(self, section_code: str) -> Optional[TDSSection]:
        """Get TDS section by code."""
        query = select(TDSSection).where(
            and_(
                TDSSection.section_code == section_code,
                TDSSection.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_sections(
        self,
        as_of_date: Optional[date] = None,
        is_tcs: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSSection], int]:
        """Get active TDS/TCS sections as of a specific date."""
        check_date = as_of_date or date.today()

        conditions = [
            TDSSection.is_active == True,
            TDSSection.is_tcs == is_tcs,
            TDSSection.effective_from <= check_date,
            (TDSSection.effective_to.is_(None) | (TDSSection.effective_to >= check_date)),
        ]

        base_query = select(TDSSection).where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(TDSSection.section_code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_all_sections(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        return_form: Optional[str] = None,
    ) -> Tuple[List[TDSSection], int]:
        """Get all TDS sections."""
        conditions = []
        if not include_inactive:
            conditions.append(TDSSection.is_active == True)
        if return_form:
            conditions.append(TDSSection.return_form == return_form)

        base_query = select(TDSSection)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(TDSSection.section_code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total
