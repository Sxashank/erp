"""Sales Invoice repository."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ap_ar.sales_invoice import (
    SalesInvoice,
    SalesInvoiceLine,
    InvoiceStatus,
    ReceiptStatus,
)
from app.repositories.base import BaseRepository


class SalesInvoiceRepository(BaseRepository[SalesInvoice]):
    """Repository for SalesInvoice model."""

    def __init__(self, db: AsyncSession):
        super().__init__(SalesInvoice, db)

    async def get_with_lines(self, invoice_id: UUID) -> Optional[SalesInvoice]:
        """Get invoice with all lines."""
        query = (
            select(SalesInvoice)
            .options(selectinload(SalesInvoice.lines))
            .where(
                SalesInvoice.id == invoice_id,
                SalesInvoice.deleted_at.is_(None),
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
        receipt_status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[SalesInvoice], int]:
        """Get all sales invoices with filters."""
        query = (
            select(SalesInvoice)
            .options(selectinload(SalesInvoice.customer))
            .where(
                SalesInvoice.organization_id == organization_id,
                SalesInvoice.deleted_at.is_(None),
            )
        )

        if not include_inactive:
            query = query.where(SalesInvoice.is_active == True)

        if status:
            query = query.where(SalesInvoice.status == status)

        if receipt_status:
            query = query.where(SalesInvoice.receipt_status == receipt_status)

        if customer_id:
            query = query.where(SalesInvoice.customer_id == customer_id)

        if from_date:
            query = query.where(SalesInvoice.invoice_date >= from_date)

        if to_date:
            query = query.where(SalesInvoice.invoice_date <= to_date)

        if search:
            search_filter = or_(
                SalesInvoice.invoice_number.ilike(f"%{search}%"),
                SalesInvoice.reference_number.ilike(f"%{search}%"),
                SalesInvoice.po_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(
            SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_number.desc()
        )
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        invoices = list(result.scalars().all())

        return invoices, total

    async def get_unreceived_for_customer(
        self, organization_id: UUID, customer_id: UUID
    ) -> List[SalesInvoice]:
        """Get unreceived/partially received invoices for a customer."""
        query = (
            select(SalesInvoice)
            .where(
                SalesInvoice.organization_id == organization_id,
                SalesInvoice.customer_id == customer_id,
                SalesInvoice.receipt_status.in_([
                    ReceiptStatus.UNRECEIVED, ReceiptStatus.PARTIALLY_RECEIVED
                ]),
                SalesInvoice.status.in_([
                    InvoiceStatus.APPROVED, InvoiceStatus.PARTIALLY_RECEIVED
                ]),
                SalesInvoice.deleted_at.is_(None),
                SalesInvoice.is_active == True,
            )
            .order_by(SalesInvoice.due_date, SalesInvoice.invoice_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_number(
        self, organization_id: UUID, prefix: str = "INV"
    ) -> str:
        """Generate next invoice number."""
        query = (
            select(SalesInvoice.invoice_number)
            .where(
                SalesInvoice.organization_id == organization_id,
                SalesInvoice.invoice_number.like(f"{prefix}%"),
            )
            .order_by(SalesInvoice.invoice_number.desc())
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

    async def create_line(self, line_data: dict) -> SalesInvoiceLine:
        """Create an invoice line."""
        line = SalesInvoiceLine(**line_data)
        self.session.add(line)
        return line

    async def delete_lines(self, invoice_id: UUID) -> None:
        """Delete all lines for an invoice."""
        query = select(SalesInvoiceLine).where(
            SalesInvoiceLine.invoice_id == invoice_id
        )
        result = await self.session.execute(query)
        lines = result.scalars().all()
        for line in lines:
            await self.session.delete(line)
