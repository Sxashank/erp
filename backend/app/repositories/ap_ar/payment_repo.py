"""Payment Repository for database operations."""

from datetime import date
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ap_ar.payment import (
    Payment,
    PaymentAllocation,
    PaymentType,
    PartyType,
    PaymentMode,
    PaymentStatus,
    ChequeStatus,
    DocumentType,
)
from app.models.ap_ar.purchase_bill import PurchaseBill
from app.models.ap_ar.sales_invoice import SalesInvoice
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_number(
        self,
        payment_number: str,
        organization_id: UUID,
    ) -> Optional[Payment]:
        """Get payment by number within organization."""
        query = select(Payment).where(
            and_(
                Payment.payment_number == payment_number,
                Payment.organization_id == organization_id,
                Payment.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_allocations(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment with all allocations."""
        query = (
            select(Payment)
            .options(selectinload(Payment.allocations))
            .where(
                and_(
                    Payment.id == payment_id,
                    Payment.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_payments(
        self,
        organization_id: UUID,
        *,
        search: Optional[str] = None,
        payment_type: Optional[PaymentType] = None,
        party_type: Optional[PartyType] = None,
        vendor_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        payment_mode: Optional[PaymentMode] = None,
        status: Optional[PaymentStatus] = None,
        cheque_status: Optional[ChequeStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        is_posted: Optional[bool] = None,
        unit_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Payment], int]:
        """List payments with filters and pagination."""
        conditions = [
            Payment.organization_id == organization_id,
            Payment.deleted_at.is_(None),
        ]

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Payment.payment_number.ilike(search_term),
                    Payment.reference_number.ilike(search_term),
                    Payment.cheque_number.ilike(search_term),
                    Payment.narration.ilike(search_term),
                )
            )

        if payment_type:
            conditions.append(Payment.payment_type == payment_type)
        if party_type:
            conditions.append(Payment.party_type == party_type)
        if vendor_id:
            conditions.append(Payment.vendor_id == vendor_id)
        if customer_id:
            conditions.append(Payment.customer_id == customer_id)
        if payment_mode:
            conditions.append(Payment.payment_mode == payment_mode)
        if status:
            conditions.append(Payment.status == status)
        if cheque_status:
            conditions.append(Payment.cheque_status == cheque_status)
        if from_date:
            conditions.append(Payment.payment_date >= from_date)
        if to_date:
            conditions.append(Payment.payment_date <= to_date)
        if is_posted is not None:
            conditions.append(Payment.is_posted == is_posted)
        if unit_id:
            conditions.append(Payment.unit_id == unit_id)

        # Count query
        count_query = select(func.count(Payment.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(Payment)
            .where(and_(*conditions))
            .order_by(desc(Payment.payment_date), desc(Payment.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        payments = result.scalars().all()

        return payments, total

    async def get_pending_cheques(
        self,
        organization_id: UUID,
        *,
        party_type: Optional[PartyType] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Payment], int]:
        """Get pending (uncleared) cheques."""
        conditions = [
            Payment.organization_id == organization_id,
            Payment.payment_mode == PaymentMode.CHEQUE,
            Payment.cheque_status.in_([ChequeStatus.ISSUED, ChequeStatus.DEPOSITED]),
            Payment.status == PaymentStatus.POSTED,
            Payment.deleted_at.is_(None),
        ]

        if party_type:
            conditions.append(Payment.party_type == party_type)
        if from_date:
            conditions.append(Payment.cheque_date >= from_date)
        if to_date:
            conditions.append(Payment.cheque_date <= to_date)

        # Count query
        count_query = select(func.count(Payment.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(Payment)
            .where(and_(*conditions))
            .order_by(Payment.cheque_date)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        payments = result.scalars().all()

        return payments, total

    async def get_next_number(
        self,
        organization_id: UUID,
        payment_type: PaymentType,
        prefix: str,
    ) -> str:
        """Generate next payment number."""
        # Get the latest payment number with this prefix
        query = (
            select(Payment.payment_number)
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.payment_type == payment_type,
                    Payment.payment_number.like(f"{prefix}%"),
                )
            )
            .order_by(desc(Payment.payment_number))
            .limit(1)
        )
        result = await self.session.execute(query)
        last_number = result.scalar_one_or_none()

        if last_number:
            try:
                # Extract number part and increment
                num_part = last_number.replace(prefix, "")
                next_num = int(num_part) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:06d}"

    async def get_party_payments(
        self,
        party_type: PartyType,
        party_id: UUID,
        organization_id: UUID,
        *,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[PaymentStatus] = None,
    ) -> Sequence[Payment]:
        """Get all payments for a specific party."""
        conditions = [
            Payment.organization_id == organization_id,
            Payment.party_type == party_type,
            Payment.deleted_at.is_(None),
        ]

        if party_type == PartyType.VENDOR:
            conditions.append(Payment.vendor_id == party_id)
        else:
            conditions.append(Payment.customer_id == party_id)

        if from_date:
            conditions.append(Payment.payment_date >= from_date)
        if to_date:
            conditions.append(Payment.payment_date <= to_date)
        if status:
            conditions.append(Payment.status == status)

        query = (
            select(Payment)
            .options(selectinload(Payment.allocations))
            .where(and_(*conditions))
            .order_by(Payment.payment_date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class PaymentAllocationRepository(BaseRepository[PaymentAllocation]):
    """Repository for PaymentAllocation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PaymentAllocation, session)

    async def get_allocations_for_document(
        self,
        document_type: DocumentType,
        document_id: UUID,
    ) -> Sequence[PaymentAllocation]:
        """Get all allocations for a specific document."""
        query = (
            select(PaymentAllocation)
            .options(selectinload(PaymentAllocation.payment))
            .where(
                and_(
                    PaymentAllocation.document_type == document_type,
                    PaymentAllocation.document_id == document_id,
                )
            )
            .order_by(PaymentAllocation.allocation_date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_total_allocated_for_document(
        self,
        document_type: DocumentType,
        document_id: UUID,
    ) -> Decimal:
        """Get total amount allocated to a document."""
        query = select(
            func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00"))
        ).where(
            and_(
                PaymentAllocation.document_type == document_type,
                PaymentAllocation.document_id == document_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0.00")

    async def delete_allocations_for_payment(self, payment_id: UUID) -> None:
        """Delete all allocations for a payment."""
        query = select(PaymentAllocation).where(
            PaymentAllocation.payment_id == payment_id
        )
        result = await self.session.execute(query)
        allocations = result.scalars().all()
        for allocation in allocations:
            await self.session.delete(allocation)


class OutstandingDocumentsRepository:
    """Repository for getting outstanding documents for allocation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_outstanding_bills(
        self,
        vendor_id: UUID,
        organization_id: UUID,
    ) -> list[dict]:
        """Get outstanding purchase bills for a vendor."""
        # Get bills that are approved/posted and have balance
        query = (
            select(
                PurchaseBill.id,
                PurchaseBill.bill_number,
                PurchaseBill.bill_date,
                PurchaseBill.due_date,
                PurchaseBill.total_amount,
                PurchaseBill.balance_amount,
            )
            .where(
                and_(
                    PurchaseBill.vendor_id == vendor_id,
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.status.in_(["APPROVED", "PARTIALLY_PAID"]),
                    PurchaseBill.balance_amount > 0,
                    PurchaseBill.deleted_at.is_(None),
                )
            )
            .order_by(PurchaseBill.due_date, PurchaseBill.bill_date)
        )
        result = await self.session.execute(query)
        rows = result.all()

        today = date.today()
        return [
            {
                "document_type": DocumentType.PURCHASE_BILL,
                "document_id": row.id,
                "document_number": row.bill_number,
                "document_date": row.bill_date,
                "due_date": row.due_date,
                "total_amount": row.total_amount,
                "paid_amount": row.total_amount - row.balance_amount,
                "outstanding_amount": row.balance_amount,
                "days_overdue": max(0, (today - row.due_date).days) if row.due_date else 0,
            }
            for row in rows
        ]

    async def get_outstanding_invoices(
        self,
        customer_id: UUID,
        organization_id: UUID,
    ) -> list[dict]:
        """Get outstanding sales invoices for a customer."""
        query = (
            select(
                SalesInvoice.id,
                SalesInvoice.invoice_number,
                SalesInvoice.invoice_date,
                SalesInvoice.due_date,
                SalesInvoice.total_amount,
                SalesInvoice.balance_amount,
            )
            .where(
                and_(
                    SalesInvoice.customer_id == customer_id,
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.status.in_(["APPROVED", "PARTIALLY_RECEIVED"]),
                    SalesInvoice.balance_amount > 0,
                    SalesInvoice.deleted_at.is_(None),
                )
            )
            .order_by(SalesInvoice.due_date, SalesInvoice.invoice_date)
        )
        result = await self.session.execute(query)
        rows = result.all()

        today = date.today()
        return [
            {
                "document_type": DocumentType.SALES_INVOICE,
                "document_id": row.id,
                "document_number": row.invoice_number,
                "document_date": row.invoice_date,
                "due_date": row.due_date,
                "total_amount": row.total_amount,
                "paid_amount": row.total_amount - row.balance_amount,
                "outstanding_amount": row.balance_amount,
                "days_overdue": max(0, (today - row.due_date).days) if row.due_date else 0,
            }
            for row in rows
        ]
