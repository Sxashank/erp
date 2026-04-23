"""Purchase Bill repository."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ap_ar.purchase_bill import PurchaseBill, PurchaseBillLine, BillStatus, PaymentStatus
from app.repositories.base import BaseRepository


class PurchaseBillRepository(BaseRepository[PurchaseBill]):
    """Repository for PurchaseBill model."""

    def __init__(self, db: AsyncSession):
        super().__init__(PurchaseBill, db)

    async def get_with_lines(self, bill_id: UUID) -> Optional[PurchaseBill]:
        """Get bill with all lines."""
        query = (
            select(PurchaseBill)
            .options(selectinload(PurchaseBill.lines))
            .where(
                PurchaseBill.id == bill_id,
                PurchaseBill.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        vendor_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[PurchaseBill], int]:
        """Get all purchase bills with filters."""
        query = (
            select(PurchaseBill)
            .options(selectinload(PurchaseBill.vendor))
            .where(
                PurchaseBill.organization_id == organization_id,
                PurchaseBill.deleted_at.is_(None),
            )
        )

        if not include_inactive:
            query = query.where(PurchaseBill.is_active == True)

        if status:
            query = query.where(PurchaseBill.status == status)

        if payment_status:
            query = query.where(PurchaseBill.payment_status == payment_status)

        if vendor_id:
            query = query.where(PurchaseBill.vendor_id == vendor_id)

        if from_date:
            query = query.where(PurchaseBill.bill_date >= from_date)

        if to_date:
            query = query.where(PurchaseBill.bill_date <= to_date)

        if search:
            search_filter = or_(
                PurchaseBill.bill_number.ilike(f"%{search}%"),
                PurchaseBill.vendor_invoice_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(PurchaseBill.bill_date.desc(), PurchaseBill.bill_number.desc())
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        bills = list(result.scalars().all())

        return bills, total

    async def get_unpaid_for_vendor(
        self, organization_id: UUID, vendor_id: UUID
    ) -> List[PurchaseBill]:
        """Get unpaid/partially paid bills for a vendor."""
        query = (
            select(PurchaseBill)
            .where(
                PurchaseBill.organization_id == organization_id,
                PurchaseBill.vendor_id == vendor_id,
                PurchaseBill.payment_status.in_([
                    PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
                ]),
                PurchaseBill.status.in_([
                    BillStatus.APPROVED, BillStatus.PARTIALLY_PAID
                ]),
                PurchaseBill.deleted_at.is_(None),
                PurchaseBill.is_active == True,
            )
            .order_by(PurchaseBill.due_date, PurchaseBill.bill_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_number(self, organization_id: UUID, prefix: str = "PB") -> str:
        """Generate next bill number."""
        query = (
            select(PurchaseBill.bill_number)
            .where(
                PurchaseBill.organization_id == organization_id,
                PurchaseBill.bill_number.like(f"{prefix}%"),
            )
            .order_by(PurchaseBill.bill_number.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        last_number = result.scalar_one_or_none()

        if last_number:
            try:
                num = int(last_number[len(prefix):]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:06d}"

    async def create_line(self, line_data: dict) -> PurchaseBillLine:
        """Create a bill line."""
        line = PurchaseBillLine(**line_data)
        self.session.add(line)
        return line

    async def delete_lines(self, bill_id: UUID) -> None:
        """Delete all lines for a bill."""
        query = select(PurchaseBillLine).where(PurchaseBillLine.bill_id == bill_id)
        result = await self.session.execute(query)
        lines = result.scalars().all()
        for line in lines:
            await self.session.delete(line)
