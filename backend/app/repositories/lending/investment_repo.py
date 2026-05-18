"""Treasury investment portfolio repository.

Data-access layer for `trs_investment`. No business logic — the service
owns transactions, derived fields, and validation (CLAUDE.md §3.2).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.treasury_investment import TreasuryInvestment
from app.repositories.base import BaseRepository


class InvestmentRepository(BaseRepository[TreasuryInvestment]):
    """Repository for TreasuryInvestment model."""

    def __init__(self, session: AsyncSession):
        super().__init__(TreasuryInvestment, session)

    async def list_by_org(
        self,
        organization_id: UUID,
        status: str | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TreasuryInvestment], int]:
        """Paginated list of investments for an organization.

        Returns ``(items, total)``. Soft-deleted rows are excluded via
        ``is_active``.
        """
        conditions = [
            TreasuryInvestment.organization_id == organization_id,
            TreasuryInvestment.is_active == True,  # noqa: E712
        ]
        if status:
            conditions.append(TreasuryInvestment.status == status)
        if category:
            conditions.append(TreasuryInvestment.category == category)

        base = select(TreasuryInvestment).where(and_(*conditions))
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            base.order_by(TreasuryInvestment.purchase_date.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_maturing(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TreasuryInvestment]:
        """Investments maturing inside ``[start_date, end_date]`` (inclusive).

        Returns active investments only (MATURED / SOLD excluded). Nullable
        ``maturity_date`` (e.g. mutual funds) is naturally excluded by the
        date filter.
        """
        query = (
            select(TreasuryInvestment)
            .where(
                and_(
                    TreasuryInvestment.organization_id == organization_id,
                    TreasuryInvestment.is_active == True,  # noqa: E712
                    TreasuryInvestment.status == "ACTIVE",
                    TreasuryInvestment.maturity_date.is_not(None),
                    TreasuryInvestment.maturity_date >= start_date,
                    TreasuryInvestment.maturity_date <= end_date,
                )
            )
            .order_by(TreasuryInvestment.maturity_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_all_active(self, organization_id: UUID) -> list[TreasuryInvestment]:
        """All active investments for the organization (used for summary)."""
        query = select(TreasuryInvestment).where(
            and_(
                TreasuryInvestment.organization_id == organization_id,
                TreasuryInvestment.is_active == True,  # noqa: E712
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_year(self, organization_id: UUID, year: int) -> int:
        """Count investments created in a given calendar year (for number gen)."""
        query = (
            select(func.count())
            .select_from(TreasuryInvestment)
            .where(
                and_(
                    TreasuryInvestment.organization_id == organization_id,
                    func.extract("year", TreasuryInvestment.created_at) == year,
                )
            )
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_by_number(
        self, organization_id: UUID, investment_number: str
    ) -> TreasuryInvestment | None:
        """Lookup by business number (for idempotency / uniqueness checks)."""
        query = select(TreasuryInvestment).where(
            and_(
                TreasuryInvestment.organization_id == organization_id,
                TreasuryInvestment.investment_number == investment_number,
                TreasuryInvestment.is_active == True,  # noqa: E712
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
