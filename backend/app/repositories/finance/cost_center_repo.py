"""Cost Center repository."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.cost_center import CostCenter
from app.models.finance.gl_entry import GLEntry
from app.repositories.base import BaseRepository


class CostCenterRepository(BaseRepository[CostCenter]):
    """Repository for Cost Center operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CostCenter, session)

    async def get_with_details(self, id: UUID) -> Optional[CostCenter]:
        """Get cost center with parent loaded."""
        query = (
            select(CostCenter)
            .options(
                selectinload(CostCenter.parent),
                selectinload(CostCenter.organization),
            )
            .where(
                and_(
                    CostCenter.id == id,
                    CostCenter.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_children(self, id: UUID) -> Optional[CostCenter]:
        """Get cost center with children loaded."""
        query = (
            select(CostCenter)
            .options(
                selectinload(CostCenter.children),
            )
            .where(
                and_(
                    CostCenter.id == id,
                    CostCenter.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
        parent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[CostCenter], int]:
        """Get cost centers for an organization."""
        conditions = [CostCenter.organization_id == organization_id]

        if not include_inactive:
            conditions.append(CostCenter.is_active == True)

        if parent_id is not None:
            conditions.append(CostCenter.parent_id == parent_id)

        base_query = (
            select(CostCenter)
            .options(selectinload(CostCenter.parent))
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(CostCenter).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(CostCenter.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_root_cost_centers(
        self,
        organization_id: UUID,
    ) -> List[CostCenter]:
        """Get root level cost centers (no parent)."""
        query = (
            select(CostCenter)
            .options(selectinload(CostCenter.children))
            .where(
                and_(
                    CostCenter.organization_id == organization_id,
                    CostCenter.parent_id.is_(None),
                    CostCenter.is_active == True,
                )
            )
            .order_by(CostCenter.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_children(
        self,
        parent_id: UUID,
    ) -> List[CostCenter]:
        """Get child cost centers."""
        query = (
            select(CostCenter)
            .options(selectinload(CostCenter.children))
            .where(
                and_(
                    CostCenter.parent_id == parent_id,
                    CostCenter.is_active == True,
                )
            )
            .order_by(CostCenter.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> Optional[CostCenter]:
        """Get cost center by code within an organization."""
        query = (
            select(CostCenter)
            .options(selectinload(CostCenter.parent))
            .where(
                and_(
                    CostCenter.organization_id == organization_id,
                    CostCenter.code == code,
                    CostCenter.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def code_exists(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a cost center code exists in the organization."""
        query = select(CostCenter.id).where(
            and_(
                CostCenter.code == code,
                CostCenter.organization_id == organization_id,
                CostCenter.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(CostCenter.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_allocatable(
        self,
        organization_id: UUID,
    ) -> List[CostCenter]:
        """Get cost centers that can have expenses allocated."""
        query = (
            select(CostCenter)
            .where(
                and_(
                    CostCenter.organization_id == organization_id,
                    CostCenter.is_allocatable == True,
                    CostCenter.is_active == True,
                )
            )
            .order_by(CostCenter.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_budgets(
        self,
        organization_id: UUID,
    ) -> List[CostCenter]:
        """Get cost centers with budget tracking enabled."""
        query = (
            select(CostCenter)
            .where(
                and_(
                    CostCenter.organization_id == organization_id,
                    CostCenter.has_budget == True,
                    CostCenter.is_active == True,
                )
            )
            .order_by(CostCenter.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        organization_id: UUID,
        query_str: str,
        limit: int = 20,
    ) -> List[CostCenter]:
        """Search cost centers by code or name."""
        query = (
            select(CostCenter)
            .options(selectinload(CostCenter.parent))
            .where(
                and_(
                    CostCenter.organization_id == organization_id,
                    CostCenter.is_active == True,
                    (
                        CostCenter.code.ilike(f"%{query_str}%")
                        | CostCenter.name.ilike(f"%{query_str}%")
                    ),
                )
            )
            .order_by(CostCenter.code)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expense_summary(
        self,
        cost_center_id: UUID,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Get expense summary for a cost center in a period."""
        query = (
            select(
                func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
                func.count(GLEntry.id).label("transaction_count"),
            )
            .where(
                and_(
                    GLEntry.cost_center_id == cost_center_id,
                    GLEntry.voucher_date >= from_date,
                    GLEntry.voucher_date <= to_date,
                    GLEntry.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_debit": row.total_debit,
            "total_credit": row.total_credit,
            "net_expense": row.total_debit - row.total_credit,
            "transaction_count": row.transaction_count,
        }

    async def get_all_descendants(
        self,
        parent_id: UUID,
    ) -> List[CostCenter]:
        """Get all descendant cost centers recursively."""
        # Get immediate children
        children = await self.get_children(parent_id)
        descendants = list(children)

        # Recursively get descendants of each child
        for child in children:
            child_descendants = await self.get_all_descendants(child.id)
            descendants.extend(child_descendants)

        return descendants

    async def has_transactions(
        self,
        cost_center_id: UUID,
    ) -> bool:
        """Check if cost center has any GL transactions."""
        query = select(func.count(GLEntry.id)).where(
            and_(
                GLEntry.cost_center_id == cost_center_id,
                GLEntry.is_active == True,
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0
