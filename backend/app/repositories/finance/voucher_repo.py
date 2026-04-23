"""Voucher repository."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.finance.voucher import Voucher, VoucherLine
from app.core.constants import VoucherStatus, VoucherClass


class VoucherRepository(BaseRepository[Voucher]):
    """Repository for Voucher operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Voucher, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers for an organization with pagination."""
        base_query = select(Voucher).where(
            Voucher.organization_id == organization_id
        )
        if not include_inactive:
            base_query = base_query.where(Voucher.is_active == True)

        # Count query
        count_query = select(func.count(Voucher.id)).where(
            Voucher.organization_id == organization_id
        )
        if not include_inactive:
            count_query = count_query.where(Voucher.is_active == True)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            base_query
            .options(selectinload(Voucher.voucher_type))
            .order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_status(
        self,
        organization_id: UUID,
        status: VoucherStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers by status."""
        base_query = select(Voucher).where(
            and_(
                Voucher.organization_id == organization_id,
                Voucher.status == status,
                Voucher.is_active == True,
            )
        )

        count_query = select(func.count(Voucher.id)).where(
            and_(
                Voucher.organization_id == organization_id,
                Voucher.status == status,
                Voucher.is_active == True,
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            base_query
            .options(selectinload(Voucher.voucher_type))
            .order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_financial_year(
        self,
        financial_year_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers for a financial year."""
        base_query = select(Voucher).where(
            and_(
                Voucher.financial_year_id == financial_year_id,
                Voucher.is_active == True,
            )
        )

        count_query = select(func.count(Voucher.id)).where(
            and_(
                Voucher.financial_year_id == financial_year_id,
                Voucher.is_active == True,
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            base_query
            .options(selectinload(Voucher.voucher_type))
            .order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_period(
        self,
        period_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Voucher]:
        """Get vouchers for a financial period."""
        query = (
            select(Voucher)
            .options(selectinload(Voucher.voucher_type))
            .where(
                and_(
                    Voucher.period_id == period_id,
                    Voucher.is_active == True,
                )
            )
            .order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
        voucher_class: Optional[VoucherClass] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers within a date range."""
        base_conditions = [
            Voucher.organization_id == organization_id,
            Voucher.voucher_date >= from_date,
            Voucher.voucher_date <= to_date,
            Voucher.is_active == True,
        ]

        if voucher_class:
            from app.models.finance.voucher_type import VoucherType
            base_query = (
                select(Voucher)
                .join(VoucherType)
                .where(and_(*base_conditions, VoucherType.voucher_class == voucher_class))
            )
            count_query = (
                select(func.count(Voucher.id))
                .join(VoucherType)
                .where(and_(*base_conditions, VoucherType.voucher_class == voucher_class))
            )
        else:
            base_query = select(Voucher).where(and_(*base_conditions))
            count_query = select(func.count(Voucher.id)).where(and_(*base_conditions))

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            base_query
            .options(selectinload(Voucher.voucher_type))
            .order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_with_lines(self, id: UUID) -> Optional[Voucher]:
        """Get voucher with lines loaded."""
        query = (
            select(Voucher)
            .options(
                selectinload(Voucher.voucher_type),
                selectinload(Voucher.financial_year),
                selectinload(Voucher.period),
                selectinload(Voucher.unit),
                selectinload(Voucher.lines).selectinload(VoucherLine.account),
            )
            .where(
                and_(
                    Voucher.id == id,
                    Voucher.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_approval(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Voucher]:
        """Get vouchers pending approval."""
        query = (
            select(Voucher)
            .options(selectinload(Voucher.voucher_type))
            .where(
                and_(
                    Voucher.organization_id == organization_id,
                    Voucher.status == VoucherStatus.PENDING_APPROVAL,
                    Voucher.is_active == True,
                )
            )
            .order_by(Voucher.submitted_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def voucher_number_exists(
        self,
        voucher_number: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a voucher number exists."""
        query = select(Voucher.id).where(
            and_(
                Voucher.voucher_number == voucher_number,
                Voucher.organization_id == organization_id,
                Voucher.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(Voucher.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


class VoucherLineRepository(BaseRepository[VoucherLine]):
    """Repository for Voucher Line operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VoucherLine, session)

    async def get_by_voucher(self, voucher_id: UUID) -> List[VoucherLine]:
        """Get all lines for a voucher."""
        query = (
            select(VoucherLine)
            .options(selectinload(VoucherLine.account))
            .where(
                and_(
                    VoucherLine.voucher_id == voucher_id,
                    VoucherLine.is_active == True,
                )
            )
            .order_by(VoucherLine.line_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_account(
        self,
        account_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[VoucherLine]:
        """Get voucher lines for an account within date range."""
        conditions = [
            VoucherLine.account_id == account_id,
            VoucherLine.is_active == True,
            Voucher.status == VoucherStatus.POSTED,
        ]

        if from_date:
            conditions.append(Voucher.voucher_date >= from_date)
        if to_date:
            conditions.append(Voucher.voucher_date <= to_date)

        query = (
            select(VoucherLine)
            .join(Voucher)
            .options(selectinload(VoucherLine.account))
            .where(and_(*conditions))
            .order_by(Voucher.voucher_date, Voucher.created_at, VoucherLine.line_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_voucher(self, voucher_id: UUID) -> None:
        """Delete all lines for a voucher."""
        lines = await self.get_by_voucher(voucher_id)
        for line in lines:
            await self.session.delete(line)
        await self.session.flush()
