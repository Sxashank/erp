"""HSN/SAC repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.hsn_sac import HSNSAC
from app.core.constants import HSNSACType
from app.repositories.base import BaseRepository


class HSNSACRepository(BaseRepository[HSNSAC]):
    """Repository for HSN/SAC operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(HSNSAC, session)

    async def get_by_code(self, code: str) -> Optional[HSNSAC]:
        """Get HSN/SAC by code."""
        query = (
            select(HSNSAC)
            .options(selectinload(HSNSAC.gst_rate))
            .where(
                and_(
                    HSNSAC.code == code,
                    HSNSAC.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        search_term: str,
        hsn_sac_type: Optional[HSNSACType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[HSNSAC], int]:
        """Search HSN/SAC by code or description."""
        conditions = [HSNSAC.is_active == True]

        if search_term:
            search_pattern = f"%{search_term}%"
            conditions.append(
                or_(
                    HSNSAC.code.ilike(search_pattern),
                    HSNSAC.description.ilike(search_pattern),
                )
            )

        if hsn_sac_type:
            conditions.append(HSNSAC.hsn_sac_type == hsn_sac_type)

        base_query = (
            select(HSNSAC)
            .options(selectinload(HSNSAC.gst_rate))
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(HSNSAC).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(HSNSAC.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_type(
        self,
        hsn_sac_type: HSNSACType,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[HSNSAC], int]:
        """Get HSN/SAC by type."""
        return await self.search("", hsn_sac_type, skip, limit)
