"""GST Rate repository."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.gst_rate import GSTRate
from app.repositories.base import BaseRepository


class GSTRateRepository(BaseRepository[GSTRate]):
    """Repository for GST Rate operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(GSTRate, session)

    async def get_by_code(self, code: str) -> Optional[GSTRate]:
        """Get GST rate by code."""
        query = select(GSTRate).where(
            and_(
                GSTRate.code == code,
                GSTRate.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_rates(
        self,
        as_of_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GSTRate], int]:
        """Get active GST rates as of a specific date."""
        check_date = as_of_date or date.today()

        base_query = select(GSTRate).where(
            and_(
                GSTRate.is_active == True,
                GSTRate.effective_from <= check_date,
                (GSTRate.effective_to.is_(None) | (GSTRate.effective_to >= check_date)),
            )
        )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(GSTRate.rate).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_all_rates(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[GSTRate], int]:
        """Get all GST rates."""
        base_query = select(GSTRate)
        if not include_inactive:
            base_query = base_query.where(GSTRate.is_active == True)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(GSTRate.rate).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total
