"""AP/AR Aging Report Service."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.vendor import Vendor
from app.models.ap_ar.customer import Customer
from app.models.ap_ar.purchase_bill import PurchaseBill, BillStatus, PaymentStatus
from app.models.ap_ar.sales_invoice import SalesInvoice, InvoiceStatus, ReceiptStatus


class AgingReportService:
    """Service for generating AP/AR aging reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ap_aging_summary(
        self,
        organization_id: UUID,
        as_of_date: date,
        vendor_id: Optional[UUID] = None,
    ) -> dict:
        """
        Get AP aging summary with buckets: Current, 1-30, 31-60, 61-90, 90+
        """
        # Calculate bucket boundaries
        current_end = as_of_date
        bucket_30 = as_of_date - timedelta(days=30)
        bucket_60 = as_of_date - timedelta(days=60)
        bucket_90 = as_of_date - timedelta(days=90)

        conditions = [
            PurchaseBill.organization_id == organization_id,
            PurchaseBill.status == BillStatus.APPROVED,
            PurchaseBill.payment_status.in_([PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID]),
            PurchaseBill.deleted_at.is_(None),
        ]

        if vendor_id:
            conditions.append(PurchaseBill.vendor_id == vendor_id)

        # Query with aging buckets
        query = (
            select(
                PurchaseBill.vendor_id,
                Vendor.code.label("vendor_code"),
                Vendor.name.label("vendor_name"),
                func.sum(
                    case(
                        (PurchaseBill.due_date >= current_end, PurchaseBill.balance_amount),
                        else_=Decimal("0.00"),
                    )
                ).label("current"),
                func.sum(
                    case(
                        (
                            and_(
                                PurchaseBill.due_date < current_end,
                                PurchaseBill.due_date >= bucket_30,
                            ),
                            PurchaseBill.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_1_30"),
                func.sum(
                    case(
                        (
                            and_(
                                PurchaseBill.due_date < bucket_30,
                                PurchaseBill.due_date >= bucket_60,
                            ),
                            PurchaseBill.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_31_60"),
                func.sum(
                    case(
                        (
                            and_(
                                PurchaseBill.due_date < bucket_60,
                                PurchaseBill.due_date >= bucket_90,
                            ),
                            PurchaseBill.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_61_90"),
                func.sum(
                    case(
                        (PurchaseBill.due_date < bucket_90, PurchaseBill.balance_amount),
                        else_=Decimal("0.00"),
                    )
                ).label("days_90_plus"),
                func.sum(PurchaseBill.balance_amount).label("total"),
            )
            .join(Vendor, Vendor.id == PurchaseBill.vendor_id)
            .where(and_(*conditions))
            .group_by(PurchaseBill.vendor_id, Vendor.code, Vendor.name)
            .order_by(Vendor.name)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Calculate totals
        totals = {
            "current": Decimal("0.00"),
            "days_1_30": Decimal("0.00"),
            "days_31_60": Decimal("0.00"),
            "days_61_90": Decimal("0.00"),
            "days_90_plus": Decimal("0.00"),
            "total": Decimal("0.00"),
        }

        vendors = []
        for row in rows:
            vendor_data = {
                "vendor_id": str(row.vendor_id),
                "vendor_code": row.vendor_code,
                "vendor_name": row.vendor_name,
                "current": float(row.current or 0),
                "days_1_30": float(row.days_1_30 or 0),
                "days_31_60": float(row.days_31_60 or 0),
                "days_61_90": float(row.days_61_90 or 0),
                "days_90_plus": float(row.days_90_plus or 0),
                "total": float(row.total or 0),
            }
            vendors.append(vendor_data)

            totals["current"] += row.current or Decimal("0.00")
            totals["days_1_30"] += row.days_1_30 or Decimal("0.00")
            totals["days_31_60"] += row.days_31_60 or Decimal("0.00")
            totals["days_61_90"] += row.days_61_90 or Decimal("0.00")
            totals["days_90_plus"] += row.days_90_plus or Decimal("0.00")
            totals["total"] += row.total or Decimal("0.00")

        return {
            "as_of_date": as_of_date.isoformat(),
            "vendors": vendors,
            "totals": {k: float(v) for k, v in totals.items()},
        }

    async def get_ar_aging_summary(
        self,
        organization_id: UUID,
        as_of_date: date,
        customer_id: Optional[UUID] = None,
    ) -> dict:
        """
        Get AR aging summary with buckets: Current, 1-30, 31-60, 61-90, 90+
        """
        # Calculate bucket boundaries
        current_end = as_of_date
        bucket_30 = as_of_date - timedelta(days=30)
        bucket_60 = as_of_date - timedelta(days=60)
        bucket_90 = as_of_date - timedelta(days=90)

        conditions = [
            SalesInvoice.organization_id == organization_id,
            SalesInvoice.status == InvoiceStatus.APPROVED,
            SalesInvoice.receipt_status.in_([ReceiptStatus.UNRECEIVED, ReceiptStatus.PARTIALLY_RECEIVED]),
            SalesInvoice.deleted_at.is_(None),
        ]

        if customer_id:
            conditions.append(SalesInvoice.customer_id == customer_id)

        # Query with aging buckets
        query = (
            select(
                SalesInvoice.customer_id,
                Customer.code.label("customer_code"),
                Customer.name.label("customer_name"),
                func.sum(
                    case(
                        (SalesInvoice.due_date >= current_end, SalesInvoice.balance_amount),
                        else_=Decimal("0.00"),
                    )
                ).label("current"),
                func.sum(
                    case(
                        (
                            and_(
                                SalesInvoice.due_date < current_end,
                                SalesInvoice.due_date >= bucket_30,
                            ),
                            SalesInvoice.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_1_30"),
                func.sum(
                    case(
                        (
                            and_(
                                SalesInvoice.due_date < bucket_30,
                                SalesInvoice.due_date >= bucket_60,
                            ),
                            SalesInvoice.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_31_60"),
                func.sum(
                    case(
                        (
                            and_(
                                SalesInvoice.due_date < bucket_60,
                                SalesInvoice.due_date >= bucket_90,
                            ),
                            SalesInvoice.balance_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ).label("days_61_90"),
                func.sum(
                    case(
                        (SalesInvoice.due_date < bucket_90, SalesInvoice.balance_amount),
                        else_=Decimal("0.00"),
                    )
                ).label("days_90_plus"),
                func.sum(SalesInvoice.balance_amount).label("total"),
            )
            .join(Customer, Customer.id == SalesInvoice.customer_id)
            .where(and_(*conditions))
            .group_by(SalesInvoice.customer_id, Customer.code, Customer.name)
            .order_by(Customer.name)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Calculate totals
        totals = {
            "current": Decimal("0.00"),
            "days_1_30": Decimal("0.00"),
            "days_31_60": Decimal("0.00"),
            "days_61_90": Decimal("0.00"),
            "days_90_plus": Decimal("0.00"),
            "total": Decimal("0.00"),
        }

        customers = []
        for row in rows:
            customer_data = {
                "customer_id": str(row.customer_id),
                "customer_code": row.customer_code,
                "customer_name": row.customer_name,
                "current": float(row.current or 0),
                "days_1_30": float(row.days_1_30 or 0),
                "days_31_60": float(row.days_31_60 or 0),
                "days_61_90": float(row.days_61_90 or 0),
                "days_90_plus": float(row.days_90_plus or 0),
                "total": float(row.total or 0),
            }
            customers.append(customer_data)

            totals["current"] += row.current or Decimal("0.00")
            totals["days_1_30"] += row.days_1_30 or Decimal("0.00")
            totals["days_31_60"] += row.days_31_60 or Decimal("0.00")
            totals["days_61_90"] += row.days_61_90 or Decimal("0.00")
            totals["days_90_plus"] += row.days_90_plus or Decimal("0.00")
            totals["total"] += row.total or Decimal("0.00")

        return {
            "as_of_date": as_of_date.isoformat(),
            "customers": customers,
            "totals": {k: float(v) for k, v in totals.items()},
        }

    async def get_ap_aging_detail(
        self,
        organization_id: UUID,
        vendor_id: UUID,
        as_of_date: date,
    ) -> dict:
        """Get detailed AP aging for a specific vendor."""
        # Calculate bucket boundaries
        current_end = as_of_date
        bucket_30 = as_of_date - timedelta(days=30)
        bucket_60 = as_of_date - timedelta(days=60)
        bucket_90 = as_of_date - timedelta(days=90)

        # Get vendor
        vendor_query = select(Vendor).where(Vendor.id == vendor_id)
        vendor_result = await self.session.execute(vendor_query)
        vendor = vendor_result.scalar_one_or_none()

        if not vendor:
            return {"error": "Vendor not found"}

        # Get bills
        conditions = [
            PurchaseBill.organization_id == organization_id,
            PurchaseBill.vendor_id == vendor_id,
            PurchaseBill.status == BillStatus.APPROVED,
            PurchaseBill.payment_status.in_([PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID]),
            PurchaseBill.deleted_at.is_(None),
        ]

        query = (
            select(PurchaseBill)
            .where(and_(*conditions))
            .order_by(PurchaseBill.due_date)
        )

        result = await self.session.execute(query)
        bills = result.scalars().all()

        def get_bucket(due_date: date) -> str:
            if due_date >= current_end:
                return "current"
            elif due_date >= bucket_30:
                return "days_1_30"
            elif due_date >= bucket_60:
                return "days_31_60"
            elif due_date >= bucket_90:
                return "days_61_90"
            else:
                return "days_90_plus"

        bill_details = []
        for bill in bills:
            days_overdue = (as_of_date - bill.due_date).days if bill.due_date < as_of_date else 0
            bill_details.append({
                "bill_id": str(bill.id),
                "bill_number": bill.bill_number,
                "bill_date": bill.bill_date.isoformat(),
                "due_date": bill.due_date.isoformat(),
                "total_amount": float(bill.total_amount),
                "balance_amount": float(bill.balance_amount),
                "days_overdue": days_overdue,
                "bucket": get_bucket(bill.due_date),
            })

        return {
            "as_of_date": as_of_date.isoformat(),
            "vendor_id": str(vendor.id),
            "vendor_code": vendor.code,
            "vendor_name": vendor.name,
            "bills": bill_details,
        }

    async def get_ar_aging_detail(
        self,
        organization_id: UUID,
        customer_id: UUID,
        as_of_date: date,
    ) -> dict:
        """Get detailed AR aging for a specific customer."""
        # Calculate bucket boundaries
        current_end = as_of_date
        bucket_30 = as_of_date - timedelta(days=30)
        bucket_60 = as_of_date - timedelta(days=60)
        bucket_90 = as_of_date - timedelta(days=90)

        # Get customer
        customer_query = select(Customer).where(Customer.id == customer_id)
        customer_result = await self.session.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            return {"error": "Customer not found"}

        # Get invoices
        conditions = [
            SalesInvoice.organization_id == organization_id,
            SalesInvoice.customer_id == customer_id,
            SalesInvoice.status == InvoiceStatus.APPROVED,
            SalesInvoice.receipt_status.in_([ReceiptStatus.UNRECEIVED, ReceiptStatus.PARTIALLY_RECEIVED]),
            SalesInvoice.deleted_at.is_(None),
        ]

        query = (
            select(SalesInvoice)
            .where(and_(*conditions))
            .order_by(SalesInvoice.due_date)
        )

        result = await self.session.execute(query)
        invoices = result.scalars().all()

        def get_bucket(due_date: date) -> str:
            if due_date >= current_end:
                return "current"
            elif due_date >= bucket_30:
                return "days_1_30"
            elif due_date >= bucket_60:
                return "days_31_60"
            elif due_date >= bucket_90:
                return "days_61_90"
            else:
                return "days_90_plus"

        invoice_details = []
        for invoice in invoices:
            days_overdue = (as_of_date - invoice.due_date).days if invoice.due_date < as_of_date else 0
            invoice_details.append({
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "total_amount": float(invoice.total_amount),
                "balance_amount": float(invoice.balance_amount),
                "days_overdue": days_overdue,
                "bucket": get_bucket(invoice.due_date),
            })

        return {
            "as_of_date": as_of_date.isoformat(),
            "customer_id": str(customer.id),
            "customer_code": customer.code,
            "customer_name": customer.name,
            "invoices": invoice_details,
        }
