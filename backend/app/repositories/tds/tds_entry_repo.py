"""TDS Entry repository."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, extract
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_entry import TDSEntry
from app.models.finance.financial_year import FinancialYear
from app.core.constants import TDSChallanStatus
from app.repositories.base import BaseRepository


class TDSEntryRepository(BaseRepository[TDSEntry]):
    """Repository for TDS Entry operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TDSEntry, session)

    async def get_with_details(self, id: UUID) -> Optional[TDSEntry]:
        """Get TDS entry with all relationships loaded."""
        query = (
            select(TDSEntry)
            .options(
                selectinload(TDSEntry.tds_section),
                selectinload(TDSEntry.voucher),
                selectinload(TDSEntry.organization),
            )
            .where(TDSEntry.id == id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        challan_status: Optional[TDSChallanStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSEntry], int]:
        """Get TDS entries for an organization with filters."""
        conditions = [
            TDSEntry.organization_id == organization_id,
            TDSEntry.is_active == True,
        ]

        if from_date:
            conditions.append(TDSEntry.deduction_date >= from_date)
        if to_date:
            conditions.append(TDSEntry.deduction_date <= to_date)
        if challan_status:
            conditions.append(TDSEntry.challan_status == challan_status)

        base_query = (
            select(TDSEntry)
            .options(
                selectinload(TDSEntry.tds_section),
                selectinload(TDSEntry.voucher),
            )
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(TDSEntry).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(TDSEntry.deduction_date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pending_challans(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSEntry], int]:
        """Get TDS entries with pending challans."""
        return await self.get_by_organization(
            organization_id,
            challan_status=TDSChallanStatus.PENDING,
            skip=skip,
            limit=limit,
        )

    async def get_by_quarter(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> List[TDSEntry]:
        """Get TDS entries for a specific quarter for return filing."""
        # Determine quarter dates based on Indian financial year (Apr-Mar)
        year_start = int(financial_year.split("-")[0])

        quarter_dates = {
            "Q1": (date(year_start, 4, 1), date(year_start, 6, 30)),
            "Q2": (date(year_start, 7, 1), date(year_start, 9, 30)),
            "Q3": (date(year_start, 10, 1), date(year_start, 12, 31)),
            "Q4": (date(year_start + 1, 1, 1), date(year_start + 1, 3, 31)),
        }

        from_date, to_date = quarter_dates.get(quarter, (None, None))
        if not from_date:
            return []

        query = (
            select(TDSEntry)
            .options(
                selectinload(TDSEntry.tds_section),
                selectinload(TDSEntry.voucher),
            )
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.is_active == True,
                    TDSEntry.deduction_date >= from_date,
                    TDSEntry.deduction_date <= to_date,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_summary_by_section(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[dict]:
        """Get TDS summary grouped by section."""
        query = (
            select(
                TDSEntry.tds_section_id,
                func.count(TDSEntry.id).label("entry_count"),
                func.sum(TDSEntry.base_amount).label("total_base"),
                func.sum(TDSEntry.total_tds).label("total_tds"),
            )
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.is_active == True,
                    TDSEntry.deduction_date >= from_date,
                    TDSEntry.deduction_date <= to_date,
                )
            )
            .group_by(TDSEntry.tds_section_id)
        )
        result = await self.session.execute(query)
        return [
            {
                "tds_section_id": row.tds_section_id,
                "entry_count": row.entry_count,
                "total_base": row.total_base,
                "total_tds": row.total_tds,
            }
            for row in result.all()
        ]

    async def get_vendor_aggregate(
        self,
        organization_id: UUID,
        vendor_id: UUID,
        tds_section_id: UUID,
        financial_year_id: UUID,
    ) -> Decimal:
        """Get total TDS base amount for vendor in current FY for a section.

        Used for aggregate threshold checking per Section 194C etc.
        """
        query = select(func.coalesce(func.sum(TDSEntry.base_amount), 0)).where(
            and_(
                TDSEntry.organization_id == organization_id,
                TDSEntry.vendor_id == vendor_id,
                TDSEntry.tds_section_id == tds_section_id,
                TDSEntry.financial_year_id == financial_year_id,
                TDSEntry.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return Decimal(str(result.scalar() or 0))

    async def get_financial_year_for_date(
        self,
        organization_id: UUID,
        entry_date: date,
    ) -> Optional[FinancialYear]:
        """Get financial year that contains the given date."""
        query = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.start_date <= entry_date,
                FinancialYear.end_date >= entry_date,
                FinancialYear.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_vendor_entries_in_fy(
        self,
        organization_id: UUID,
        vendor_id: UUID,
        tds_section_id: UUID,
        financial_year_id: UUID,
    ) -> List[TDSEntry]:
        """Get all TDS entries for a vendor in a financial year."""
        query = (
            select(TDSEntry)
            .options(selectinload(TDSEntry.tds_section))
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.vendor_id == vendor_id,
                    TDSEntry.tds_section_id == tds_section_id,
                    TDSEntry.financial_year_id == financial_year_id,
                    TDSEntry.is_active == True,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
