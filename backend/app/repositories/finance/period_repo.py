"""Period Repository for financial period queries."""

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.financial_year import FinancialPeriod, FinancialYear


class PeriodRepository:
    """Repository for financial period operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_date(
        self,
        financial_year_id: UUID,
        entry_date: date,
    ) -> Optional[FinancialPeriod]:
        """Get the financial period for a specific date within a financial year."""
        query = (
            select(FinancialPeriod)
            .where(
                and_(
                    FinancialPeriod.financial_year_id == financial_year_id,
                    FinancialPeriod.start_date <= entry_date,
                    FinancialPeriod.end_date >= entry_date,
                    FinancialPeriod.is_active == True,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, period_id: UUID) -> Optional[FinancialPeriod]:
        """Get a financial period by ID."""
        query = select(FinancialPeriod).where(FinancialPeriod.id == period_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_current_period(
        self,
        organization_id: UUID,
    ) -> Optional[FinancialPeriod]:
        """Get the current financial period for an organization."""
        today = date.today()
        query = (
            select(FinancialPeriod)
            .join(FinancialYear)
            .where(
                and_(
                    FinancialYear.organization_id == organization_id,
                    FinancialPeriod.start_date <= today,
                    FinancialPeriod.end_date >= today,
                    FinancialPeriod.is_active == True,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
