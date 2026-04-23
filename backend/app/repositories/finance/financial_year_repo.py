"""Financial Year repository."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.finance.financial_year import FinancialYear, FinancialPeriod


class FinancialYearRepository(BaseRepository[FinancialYear]):
    """Repository for Financial Year operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(FinancialYear, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[FinancialYear]:
        """Get all financial years for an organization."""
        query = select(FinancialYear).where(
            FinancialYear.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(FinancialYear.is_active == True)
        query = query.order_by(FinancialYear.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_periods(self, id: UUID) -> Optional[FinancialYear]:
        """Get financial year with its periods."""
        query = (
            select(FinancialYear)
            .options(selectinload(FinancialYear.periods))
            .where(
                and_(
                    FinancialYear.id == id,
                    FinancialYear.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_current(self, organization_id: UUID) -> Optional[FinancialYear]:
        """Get the current active financial year for an organization."""
        query = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.is_current == True,
                FinancialYear.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_date(
        self,
        organization_id: UUID,
        check_date: date,
    ) -> Optional[FinancialYear]:
        """Get financial year containing the given date."""
        query = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.start_date <= check_date,
                FinancialYear.end_date >= check_date,
                FinancialYear.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def code_exists(
        self,
        code: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a financial year code already exists."""
        query = select(FinancialYear.id).where(
            and_(
                FinancialYear.code == code,
                FinancialYear.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(FinancialYear.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def clear_current(self, organization_id: UUID) -> None:
        """Clear current flag for all financial years in organization."""
        query = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.is_current == True,
            )
        )
        result = await self.session.execute(query)
        for fy in result.scalars().all():
            fy.is_current = False
        await self.session.flush()


class FinancialPeriodRepository(BaseRepository[FinancialPeriod]):
    """Repository for Financial Period operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(FinancialPeriod, session)

    async def get_by_financial_year(
        self,
        financial_year_id: UUID,
    ) -> List[FinancialPeriod]:
        """Get all periods for a financial year."""
        query = (
            select(FinancialPeriod)
            .where(
                and_(
                    FinancialPeriod.financial_year_id == financial_year_id,
                    FinancialPeriod.is_active == True,
                )
            )
            .order_by(FinancialPeriod.period_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date(
        self,
        financial_year_id: UUID,
        check_date: date,
    ) -> Optional[FinancialPeriod]:
        """Get the period containing the given date."""
        query = select(FinancialPeriod).where(
            and_(
                FinancialPeriod.financial_year_id == financial_year_id,
                FinancialPeriod.start_date <= check_date,
                FinancialPeriod.end_date >= check_date,
                FinancialPeriod.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_open_periods(
        self,
        financial_year_id: UUID,
    ) -> List[FinancialPeriod]:
        """Get all open (not closed) periods for a financial year."""
        query = (
            select(FinancialPeriod)
            .where(
                and_(
                    FinancialPeriod.financial_year_id == financial_year_id,
                    FinancialPeriod.is_closed == False,
                    FinancialPeriod.is_active == True,
                )
            )
            .order_by(FinancialPeriod.period_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
