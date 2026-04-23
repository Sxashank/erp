"""Payment Terms repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.payment_terms import PaymentTerms
from app.repositories.base import BaseRepository


class PaymentTermsRepository(BaseRepository[PaymentTerms]):
    """Repository for Payment Terms operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PaymentTerms, session)

    async def get_by_code(self, code: str, organization_id: UUID) -> Optional[PaymentTerms]:
        """Get payment terms by code within an organization."""
        query = select(PaymentTerms).where(
            and_(
                PaymentTerms.code == code,
                PaymentTerms.organization_id == organization_id,
                PaymentTerms.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[PaymentTerms], int]:
        """Get all payment terms for an organization."""
        base_query = select(PaymentTerms).where(
            PaymentTerms.organization_id == organization_id
        )
        if not include_inactive:
            base_query = base_query.where(PaymentTerms.is_active == True)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(PaymentTerms.days, PaymentTerms.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_active_terms(
        self,
        organization_id: UUID,
    ) -> List[PaymentTerms]:
        """Get all active payment terms for dropdown lists."""
        query = select(PaymentTerms).where(
            and_(
                PaymentTerms.organization_id == organization_id,
                PaymentTerms.is_active == True,
            )
        ).order_by(PaymentTerms.days, PaymentTerms.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())
