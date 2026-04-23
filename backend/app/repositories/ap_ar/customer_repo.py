"""Customer repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Customer, db)

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        search: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> Tuple[List[Customer], int]:
        """Get all customers with filters."""
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.deleted_at.is_(None),
        )

        if not include_inactive:
            query = query.where(Customer.is_active == True)

        if search:
            search_filter = or_(
                Customer.code.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%"),
                Customer.gstin.ilike(f"%{search}%"),
                Customer.pan.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        if customer_type:
            query = query.where(Customer.customer_type == customer_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Customer.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        customers = list(result.scalars().all())

        return customers, total

    async def get_active(self, organization_id: UUID) -> List[Customer]:
        """Get active customers for dropdown lists."""
        query = (
            select(Customer)
            .where(
                Customer.organization_id == organization_id,
                Customer.is_active == True,
                Customer.deleted_at.is_(None),
            )
            .order_by(Customer.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_code(
        self, organization_id: UUID, code: str
    ) -> Optional[Customer]:
        """Get customer by code within organization."""
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.code == code,
            Customer.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_gstin(
        self, organization_id: UUID, gstin: str
    ) -> Optional[Customer]:
        """Get customer by GSTIN within organization."""
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.gstin == gstin,
            Customer.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_next_code(self, organization_id: UUID) -> str:
        """Generate next customer code."""
        query = (
            select(Customer.code)
            .where(
                Customer.organization_id == organization_id,
                Customer.code.like("C%"),
            )
            .order_by(Customer.code.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        last_code = result.scalar_one_or_none()

        if last_code:
            try:
                num = int(last_code[1:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"C{num:04d}"
