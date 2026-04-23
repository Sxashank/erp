"""TDS Challan repository."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_challan import TDSChallan, ChallanStatus
from app.models.tds.tds_entry import TDSEntry
from app.repositories.base import BaseRepository


class TDSChallanRepository(BaseRepository[TDSChallan]):
    """Repository for TDS Challan operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TDSChallan, session)

    async def get_with_details(self, id: UUID) -> Optional[TDSChallan]:
        """Get TDS challan with all relationships loaded."""
        query = (
            select(TDSChallan)
            .options(
                selectinload(TDSChallan.tds_section),
                selectinload(TDSChallan.organization),
                selectinload(TDSChallan.financial_year),
                selectinload(TDSChallan.entries),
            )
            .where(TDSChallan.id == id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_entries(self, id: UUID) -> Optional[TDSChallan]:
        """Get TDS challan with entries loaded."""
        query = (
            select(TDSChallan)
            .options(
                selectinload(TDSChallan.tds_section),
                selectinload(TDSChallan.entries).selectinload(TDSEntry.tds_section),
            )
            .where(
                and_(
                    TDSChallan.id == id,
                    TDSChallan.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[ChallanStatus] = None,
        tds_section_id: Optional[UUID] = None,
        financial_year_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSChallan], int]:
        """Get TDS challans for an organization with filters."""
        conditions = [
            TDSChallan.organization_id == organization_id,
            TDSChallan.is_active == True,
        ]

        if from_date:
            conditions.append(TDSChallan.period_from >= from_date)
        if to_date:
            conditions.append(TDSChallan.period_to <= to_date)
        if status:
            conditions.append(TDSChallan.status == status)
        if tds_section_id:
            conditions.append(TDSChallan.tds_section_id == tds_section_id)
        if financial_year_id:
            conditions.append(TDSChallan.financial_year_id == financial_year_id)

        base_query = (
            select(TDSChallan)
            .options(selectinload(TDSChallan.tds_section))
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(TDSChallan).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(TDSChallan.period_from.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pending_challans(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSChallan], int]:
        """Get challans pending payment."""
        return await self.get_by_organization(
            organization_id,
            status=ChallanStatus.PENDING,
            skip=skip,
            limit=limit,
        )

    async def get_by_challan_number(
        self,
        challan_number: str,
    ) -> Optional[TDSChallan]:
        """Get challan by CIN (Challan Identification Number)."""
        query = (
            select(TDSChallan)
            .options(
                selectinload(TDSChallan.tds_section),
                selectinload(TDSChallan.entries),
            )
            .where(
                and_(
                    TDSChallan.challan_number == challan_number,
                    TDSChallan.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_for_period_section(
        self,
        organization_id: UUID,
        tds_section_id: UUID,
        period_from: date,
        period_to: date,
    ) -> Optional[TDSChallan]:
        """Get existing challan for a period and section (avoid duplicates)."""
        query = (
            select(TDSChallan)
            .where(
                and_(
                    TDSChallan.organization_id == organization_id,
                    TDSChallan.tds_section_id == tds_section_id,
                    TDSChallan.period_from == period_from,
                    TDSChallan.period_to == period_to,
                    TDSChallan.is_active == True,
                    TDSChallan.status.in_([ChallanStatus.DRAFT, ChallanStatus.PENDING]),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_summary(
        self,
        organization_id: UUID,
        financial_year_id: Optional[UUID] = None,
    ) -> dict:
        """Get challan summary statistics."""
        conditions = [
            TDSChallan.organization_id == organization_id,
            TDSChallan.is_active == True,
        ]
        if financial_year_id:
            conditions.append(TDSChallan.financial_year_id == financial_year_id)

        # Get counts by status
        query = (
            select(
                TDSChallan.status,
                func.count(TDSChallan.id).label("count"),
                func.sum(TDSChallan.total_amount).label("total_amount"),
            )
            .where(and_(*conditions))
            .group_by(TDSChallan.status)
        )
        result = await self.session.execute(query)
        rows = result.all()

        summary = {
            "total_challans": 0,
            "draft_count": 0,
            "pending_count": 0,
            "paid_count": 0,
            "verified_count": 0,
            "cancelled_count": 0,
            "total_amount_due": Decimal("0"),
            "total_amount_paid": Decimal("0"),
        }

        for row in rows:
            summary["total_challans"] += row.count
            if row.status == ChallanStatus.DRAFT:
                summary["draft_count"] = row.count
            elif row.status == ChallanStatus.PENDING:
                summary["pending_count"] = row.count
                summary["total_amount_due"] += row.total_amount or Decimal("0")
            elif row.status == ChallanStatus.PAID:
                summary["paid_count"] = row.count
                summary["total_amount_paid"] += row.total_amount or Decimal("0")
            elif row.status == ChallanStatus.VERIFIED:
                summary["verified_count"] = row.count
                summary["total_amount_paid"] += row.total_amount or Decimal("0")
            elif row.status == ChallanStatus.CANCELLED:
                summary["cancelled_count"] = row.count

        # Count late challans
        today = date.today()
        late_query = select(func.count(TDSChallan.id)).where(
            and_(
                TDSChallan.organization_id == organization_id,
                TDSChallan.is_active == True,
                TDSChallan.status.in_([ChallanStatus.DRAFT, ChallanStatus.PENDING]),
                # Due date is 7th of month after period_to
            )
        )
        # Late calculation would need more complex logic
        summary["late_challans_count"] = 0

        return summary

    async def get_due_for_payment(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> List[TDSChallan]:
        """Get challans that are due for payment."""
        if as_of_date is None:
            as_of_date = date.today()

        query = (
            select(TDSChallan)
            .options(selectinload(TDSChallan.tds_section))
            .where(
                and_(
                    TDSChallan.organization_id == organization_id,
                    TDSChallan.is_active == True,
                    TDSChallan.status.in_([ChallanStatus.DRAFT, ChallanStatus.PENDING]),
                )
            )
            .order_by(TDSChallan.period_to)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_for_return(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        quarter: str,
    ) -> List[TDSChallan]:
        """Get challans for TDS return filing."""
        query = (
            select(TDSChallan)
            .options(
                selectinload(TDSChallan.tds_section),
                selectinload(TDSChallan.entries),
            )
            .where(
                and_(
                    TDSChallan.organization_id == organization_id,
                    TDSChallan.financial_year_id == financial_year_id,
                    TDSChallan.return_quarter == quarter,
                    TDSChallan.is_active == True,
                    TDSChallan.status.in_([ChallanStatus.PAID, ChallanStatus.VERIFIED]),
                )
            )
            .order_by(TDSChallan.payment_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_return_status(
        self,
        challan_ids: List[UUID],
        return_id: UUID,
        quarter: str,
    ) -> int:
        """Mark challans as included in a return."""
        stmt = (
            update(TDSChallan)
            .where(TDSChallan.id.in_(challan_ids))
            .values(
                is_included_in_return=True,
                return_id=return_id,
                return_quarter=quarter,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_entries_for_challan(
        self,
        challan_id: UUID,
    ) -> List[TDSEntry]:
        """Get all TDS entries linked to a challan."""
        query = (
            select(TDSEntry)
            .options(selectinload(TDSEntry.tds_section))
            .where(
                and_(
                    TDSEntry.challan_id == challan_id,
                    TDSEntry.is_active == True,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unlinked_entries(
        self,
        organization_id: UUID,
        tds_section_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[TDSEntry]:
        """Get TDS entries not yet linked to any challan."""
        query = (
            select(TDSEntry)
            .options(selectinload(TDSEntry.tds_section))
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.tds_section_id == tds_section_id,
                    TDSEntry.deduction_date >= from_date,
                    TDSEntry.deduction_date <= to_date,
                    TDSEntry.challan_id.is_(None),
                    TDSEntry.is_active == True,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def link_entries_to_challan(
        self,
        challan_id: UUID,
        entry_ids: List[UUID],
    ) -> int:
        """Link TDS entries to a challan."""
        stmt = (
            update(TDSEntry)
            .where(TDSEntry.id.in_(entry_ids))
            .values(challan_id=challan_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def unlink_entries_from_challan(
        self,
        entry_ids: List[UUID],
    ) -> int:
        """Unlink TDS entries from a challan."""
        stmt = (
            update(TDSEntry)
            .where(TDSEntry.id.in_(entry_ids))
            .values(challan_id=None)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
