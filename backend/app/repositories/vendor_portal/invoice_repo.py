"""Vendor Invoice Repositories."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.vendor_portal.invoice import (
    VendorInvoice,
    VendorInvoiceLine,
    VendorInvoiceDocument,
)
from app.models.vendor_portal.enums import (
    VendorInvoiceStatus,
    InvoiceMatchingStatus,
    InvoiceDocumentType,
)


class VendorInvoiceRepository(BaseRepository[VendorInvoice]):
    """Repository for vendor invoice operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorInvoice, session)

    async def get_with_details(self, id: UUID) -> Optional[VendorInvoice]:
        """Get invoice with lines and documents."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.lines),
                selectinload(self.model.documents),
            )
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invoice_number(
        self, vendor_id: UUID, invoice_number: str
    ) -> Optional[VendorInvoice]:
        """Get invoice by number for a vendor."""
        query = select(self.model).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.invoice_number == invoice_number,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_vendor(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VendorInvoiceStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        po_number: Optional[str] = None,
    ) -> Tuple[List[VendorInvoice], int]:
        """Get all invoices for a vendor with filters."""
        conditions = [
            self.model.vendor_id == vendor_id,
            self.model.is_active == True,
        ]

        if status:
            conditions.append(self.model.status == status)
        if from_date:
            conditions.append(self.model.invoice_date >= from_date)
        if to_date:
            conditions.append(self.model.invoice_date <= to_date)
        if po_number:
            conditions.append(self.model.purchase_order_number.ilike(f"%{po_number}%"))

        # Count query
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VendorInvoiceStatus] = None,
        vendor_id: Optional[UUID] = None,
        matching_status: Optional[InvoiceMatchingStatus] = None,
    ) -> Tuple[List[VendorInvoice], int]:
        """Get all invoices for an organization with filters."""
        conditions = [
            self.model.organization_id == organization_id,
            self.model.is_active == True,
        ]

        if status:
            conditions.append(self.model.status == status)
        if vendor_id:
            conditions.append(self.model.vendor_id == vendor_id)
        if matching_status:
            conditions.append(self.model.matching_status == matching_status)

        # Count query
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.submitted_at.desc().nullsfirst())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pending_approval(
        self, organization_id: UUID
    ) -> List[VendorInvoice]:
        """Get invoices pending approval."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.status.in_([
                        VendorInvoiceStatus.SUBMITTED,
                        VendorInvoiceStatus.MATCHED,
                    ]),
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.submitted_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_totals_by_vendor(
        self, vendor_id: UUID
    ) -> dict:
        """Get invoice totals for a vendor."""
        query = select(
            func.count(self.model.id).label("count"),
            func.sum(self.model.total_amount).label("total"),
            func.sum(self.model.paid_amount).label("paid"),
            func.sum(self.model.balance_amount).label("balance"),
        ).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.status.notin_([
                    VendorInvoiceStatus.DRAFT,
                    VendorInvoiceStatus.REJECTED,
                ]),
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        row = result.one()

        return {
            "count": row.count or 0,
            "total": row.total or Decimal("0"),
            "paid": row.paid or Decimal("0"),
            "balance": row.balance or Decimal("0"),
        }


class VendorInvoiceLineRepository(BaseRepository[VendorInvoiceLine]):
    """Repository for vendor invoice line operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorInvoiceLine, session)

    async def get_by_invoice(self, invoice_id: UUID) -> List[VendorInvoiceLine]:
        """Get all lines for an invoice."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.invoice_id == invoice_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.line_number.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_line_number(self, invoice_id: UUID) -> int:
        """Get next line number for an invoice."""
        query = select(func.max(self.model.line_number)).where(
            self.model.invoice_id == invoice_id
        )
        result = await self.session.execute(query)
        max_line = result.scalar() or 0
        return max_line + 1

    async def delete_by_invoice(self, invoice_id: UUID) -> int:
        """Delete all lines for an invoice."""
        lines = await self.get_by_invoice(invoice_id)
        for line in lines:
            await self.session.delete(line)
        await self.session.flush()
        return len(lines)


class VendorInvoiceDocumentRepository(BaseRepository[VendorInvoiceDocument]):
    """Repository for vendor invoice document operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorInvoiceDocument, session)

    async def get_by_invoice(self, invoice_id: UUID) -> List[VendorInvoiceDocument]:
        """Get all documents for an invoice."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.invoice_id == invoice_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self, invoice_id: UUID, document_type: InvoiceDocumentType
    ) -> Optional[VendorInvoiceDocument]:
        """Get document by type."""
        query = select(self.model).where(
            and_(
                self.model.invoice_id == invoice_id,
                self.model.document_type == document_type,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
