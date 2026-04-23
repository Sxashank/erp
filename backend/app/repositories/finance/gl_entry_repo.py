"""GL Entry repository for audit trail queries."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.finance.gl_entry import GLEntry
from app.core.constants import (
    BalanceType,
    PartyType,
    GLEntryType,
    GLEntrySourceType,
)


class GLEntryRepository(BaseRepository[GLEntry]):
    """Repository for GL Entry operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(GLEntry, session)

    async def get_by_voucher(
        self,
        voucher_id: UUID,
        include_reversed: bool = False,
    ) -> List[GLEntry]:
        """Get GL entries for a voucher."""
        query = select(GLEntry).where(GLEntry.voucher_id == voucher_id)
        if not include_reversed:
            query = query.where(GLEntry.is_reversed == False)
        query = query.order_by(GLEntry.sequence_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_account(
        self,
        account_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GLEntry], int]:
        """Get GL entries for an account with date range."""
        conditions = [GLEntry.account_id == account_id, GLEntry.is_active == True]

        if date_from:
            conditions.append(GLEntry.voucher_date >= date_from)
        if date_to:
            conditions.append(GLEntry.voucher_date <= date_to)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        # Count query
        count_query = select(func.count(GLEntry.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(GLEntry)
            .where(and_(*conditions))
            .order_by(GLEntry.voucher_date, GLEntry.posting_date, GLEntry.sequence_number)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_party(
        self,
        party_type: PartyType,
        party_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GLEntry], int]:
        """Get GL entries for a party (sub-ledger)."""
        conditions = [
            GLEntry.party_type == party_type,
            GLEntry.party_id == party_id,
            GLEntry.is_active == True,
        ]

        if date_from:
            conditions.append(GLEntry.voucher_date >= date_from)
        if date_to:
            conditions.append(GLEntry.voucher_date <= date_to)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        # Count query
        count_query = select(func.count(GLEntry.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(GLEntry)
            .where(and_(*conditions))
            .order_by(GLEntry.voucher_date, GLEntry.posting_date, GLEntry.sequence_number)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_cost_center(
        self,
        cost_center_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GLEntry], int]:
        """Get GL entries for a cost center."""
        conditions = [
            GLEntry.cost_center_id == cost_center_id,
            GLEntry.is_active == True,
        ]

        if date_from:
            conditions.append(GLEntry.voucher_date >= date_from)
        if date_to:
            conditions.append(GLEntry.voucher_date <= date_to)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        # Count query
        count_query = select(func.count(GLEntry.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(GLEntry)
            .where(and_(*conditions))
            .order_by(GLEntry.voucher_date, GLEntry.posting_date)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_account_balance_before_date(
        self,
        account_id: UUID,
        before_date: date,
        include_reversed: bool = False,
    ) -> Tuple[Decimal, Decimal]:
        """Get total debit and credit for an account before a date."""
        conditions = [
            GLEntry.account_id == account_id,
            GLEntry.voucher_date < before_date,
            GLEntry.is_active == True,
        ]
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = select(
            func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
        ).where(and_(*conditions))

        result = await self.session.execute(query)
        row = result.first()
        return (
            Decimal(str(row.total_debit)) if row else Decimal("0.00"),
            Decimal(str(row.total_credit)) if row else Decimal("0.00"),
        )

    async def get_account_balance_for_period(
        self,
        account_id: UUID,
        date_from: date,
        date_to: date,
        include_reversed: bool = False,
    ) -> Tuple[Decimal, Decimal]:
        """Get total debit and credit for an account within a period."""
        conditions = [
            GLEntry.account_id == account_id,
            GLEntry.voucher_date >= date_from,
            GLEntry.voucher_date <= date_to,
            GLEntry.is_active == True,
        ]
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = select(
            func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
        ).where(and_(*conditions))

        result = await self.session.execute(query)
        row = result.first()
        return (
            Decimal(str(row.total_debit)) if row else Decimal("0.00"),
            Decimal(str(row.total_credit)) if row else Decimal("0.00"),
        )

    async def get_party_balance(
        self,
        party_type: PartyType,
        party_id: UUID,
        as_of_date: Optional[date] = None,
        include_reversed: bool = False,
    ) -> Tuple[Decimal, Decimal]:
        """Get total debit and credit for a party."""
        conditions = [
            GLEntry.party_type == party_type,
            GLEntry.party_id == party_id,
            GLEntry.is_active == True,
        ]
        if as_of_date:
            conditions.append(GLEntry.voucher_date <= as_of_date)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = select(
            func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
        ).where(and_(*conditions))

        result = await self.session.execute(query)
        row = result.first()
        return (
            Decimal(str(row.total_debit)) if row else Decimal("0.00"),
            Decimal(str(row.total_credit)) if row else Decimal("0.00"),
        )

    async def get_trial_balance_data(
        self,
        organization_id: UUID,
        financial_year_id: Optional[UUID] = None,
        period_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None,
        include_reversed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get trial balance data grouped by account."""
        conditions = [
            GLEntry.organization_id == organization_id,
            GLEntry.is_active == True,
        ]
        if financial_year_id:
            conditions.append(GLEntry.financial_year_id == financial_year_id)
        if period_id:
            conditions.append(GLEntry.period_id == period_id)
        if as_of_date:
            conditions.append(GLEntry.voucher_date <= as_of_date)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = (
            select(
                GLEntry.account_id,
                GLEntry.account_code,
                GLEntry.account_name,
                func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
                func.count(GLEntry.id).label("entry_count"),
            )
            .where(and_(*conditions))
            .group_by(GLEntry.account_id, GLEntry.account_code, GLEntry.account_name)
            .order_by(GLEntry.account_code)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "account_id": row.account_id,
                "account_code": row.account_code,
                "account_name": row.account_name,
                "total_debit": Decimal(str(row.total_debit)),
                "total_credit": Decimal(str(row.total_credit)),
                "entry_count": row.entry_count,
            }
            for row in rows
        ]

    async def get_cost_center_summary(
        self,
        organization_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get summary by cost center."""
        conditions = [
            GLEntry.organization_id == organization_id,
            GLEntry.cost_center_id.isnot(None),
            GLEntry.is_active == True,
        ]
        if date_from:
            conditions.append(GLEntry.voucher_date >= date_from)
        if date_to:
            conditions.append(GLEntry.voucher_date <= date_to)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = (
            select(
                GLEntry.cost_center_id,
                GLEntry.cost_center_code,
                func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
                func.count(GLEntry.id).label("entry_count"),
            )
            .where(and_(*conditions))
            .group_by(GLEntry.cost_center_id, GLEntry.cost_center_code)
            .order_by(GLEntry.cost_center_code)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "cost_center_id": row.cost_center_id,
                "cost_center_code": row.cost_center_code,
                "total_debit": Decimal(str(row.total_debit)),
                "total_credit": Decimal(str(row.total_credit)),
                "entry_count": row.entry_count,
            }
            for row in rows
        ]

    async def get_source_summary(
        self,
        organization_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get summary by source type."""
        conditions = [
            GLEntry.organization_id == organization_id,
            GLEntry.is_active == True,
        ]
        if date_from:
            conditions.append(GLEntry.voucher_date >= date_from)
        if date_to:
            conditions.append(GLEntry.voucher_date <= date_to)
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = (
            select(
                GLEntry.source_type,
                func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
                func.count(GLEntry.id).label("entry_count"),
                func.count(func.distinct(GLEntry.voucher_id)).label("voucher_count"),
            )
            .where(and_(*conditions))
            .group_by(GLEntry.source_type)
            .order_by(GLEntry.source_type)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "source_type": row.source_type,
                "total_debit": Decimal(str(row.total_debit)),
                "total_credit": Decimal(str(row.total_credit)),
                "entry_count": row.entry_count,
                "voucher_count": row.voucher_count,
            }
            for row in rows
        ]

    async def get_day_book(
        self,
        organization_id: UUID,
        for_date: date,
        include_reversed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get day book (daily transaction summary)."""
        conditions = [
            GLEntry.organization_id == organization_id,
            GLEntry.voucher_date == for_date,
            GLEntry.is_active == True,
        ]
        if not include_reversed:
            conditions.append(GLEntry.is_reversed == False)

        query = (
            select(
                GLEntry.voucher_id,
                GLEntry.voucher_number,
                GLEntry.narration,
                func.coalesce(func.sum(GLEntry.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(GLEntry.credit_amount), 0).label("total_credit"),
                func.count(GLEntry.id).label("entry_count"),
            )
            .where(and_(*conditions))
            .group_by(GLEntry.voucher_id, GLEntry.voucher_number, GLEntry.narration)
            .order_by(GLEntry.voucher_number)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "voucher_id": row.voucher_id,
                "voucher_number": row.voucher_number,
                "narration": row.narration,
                "total_debit": Decimal(str(row.total_debit)),
                "total_credit": Decimal(str(row.total_credit)),
                "entry_count": row.entry_count,
            }
            for row in rows
        ]

    async def get_next_sequence_number(
        self,
        account_id: UUID,
        period_id: UUID,
    ) -> int:
        """Get next sequence number for an account in a period."""
        query = select(func.coalesce(func.max(GLEntry.sequence_number), 0)).where(
            and_(
                GLEntry.account_id == account_id,
                GLEntry.period_id == period_id,
            )
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) + 1

    async def mark_reversed(
        self,
        entry_id: UUID,
        reversal_entry_id: UUID,
        reversal_date: date,
    ) -> bool:
        """Mark an entry as reversed."""
        entry = await self.get(entry_id)
        if entry:
            entry.is_reversed = True
            entry.reversal_entry_id = reversal_entry_id
            entry.reversal_date = reversal_date
            await self.session.flush()
            return True
        return False

    async def get_by_source(
        self,
        source_type: GLEntrySourceType,
        source_id: UUID,
    ) -> List[GLEntry]:
        """Get GL entries by source document."""
        query = select(GLEntry).where(
            and_(
                GLEntry.source_type == source_type,
                GLEntry.source_id == source_id,
                GLEntry.is_active == True,
            )
        ).order_by(GLEntry.sequence_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        organization_id: UUID,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GLEntry], int]:
        """Search GL entries with filters."""
        conditions = [
            GLEntry.organization_id == organization_id,
            GLEntry.is_active == True,
        ]

        if filters.get("account_id"):
            conditions.append(GLEntry.account_id == filters["account_id"])
        if filters.get("account_ids"):
            conditions.append(GLEntry.account_id.in_(filters["account_ids"]))
        if filters.get("voucher_id"):
            conditions.append(GLEntry.voucher_id == filters["voucher_id"])
        if filters.get("voucher_number"):
            conditions.append(GLEntry.voucher_number.ilike(f"%{filters['voucher_number']}%"))
        if filters.get("date_from"):
            conditions.append(GLEntry.voucher_date >= filters["date_from"])
        if filters.get("date_to"):
            conditions.append(GLEntry.voucher_date <= filters["date_to"])
        if filters.get("entry_type"):
            conditions.append(GLEntry.entry_type == filters["entry_type"])
        if filters.get("source_type"):
            conditions.append(GLEntry.source_type == filters["source_type"])
        if filters.get("party_type"):
            conditions.append(GLEntry.party_type == filters["party_type"])
        if filters.get("party_id"):
            conditions.append(GLEntry.party_id == filters["party_id"])
        if filters.get("cost_center_id"):
            conditions.append(GLEntry.cost_center_id == filters["cost_center_id"])
        if filters.get("financial_year_id"):
            conditions.append(GLEntry.financial_year_id == filters["financial_year_id"])
        if filters.get("period_id"):
            conditions.append(GLEntry.period_id == filters["period_id"])
        if filters.get("min_amount"):
            conditions.append(
                or_(
                    GLEntry.debit_amount >= filters["min_amount"],
                    GLEntry.credit_amount >= filters["min_amount"],
                )
            )
        if filters.get("max_amount"):
            conditions.append(
                or_(
                    and_(GLEntry.debit_amount > 0, GLEntry.debit_amount <= filters["max_amount"]),
                    and_(GLEntry.credit_amount > 0, GLEntry.credit_amount <= filters["max_amount"]),
                )
            )
        if not filters.get("include_reversed", False):
            conditions.append(GLEntry.is_reversed == False)
        if filters.get("unit_id"):
            conditions.append(GLEntry.unit_id == filters["unit_id"])

        # Count query
        count_query = select(func.count(GLEntry.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(GLEntry)
            .where(and_(*conditions))
            .order_by(GLEntry.voucher_date.desc(), GLEntry.posting_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def bulk_create(self, entries: List[Dict[str, Any]]) -> List[GLEntry]:
        """Bulk create GL entries."""
        gl_entries = []
        for entry_data in entries:
            gl_entry = GLEntry(**entry_data)
            self.session.add(gl_entry)
            gl_entries.append(gl_entry)
        await self.session.flush()
        for entry in gl_entries:
            await self.session.refresh(entry)
        return gl_entries
