"""Dashboard service for KPI calculations."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.vendor import Vendor
from app.models.ap_ar.customer import Customer
from app.models.ap_ar.purchase_bill import PurchaseBill, BillStatus, PaymentStatus as BillPaymentStatus
from app.models.ap_ar.sales_invoice import SalesInvoice, InvoiceStatus, ReceiptStatus
from app.models.ap_ar.payment import Payment, PaymentStatus, PaymentType, PaymentMode, ChequeStatus
from app.models.finance.voucher import Voucher, VoucherStatus
from app.models.finance.account import Account
from app.models.finance.financial_year import FinancialYear
from app.schemas.dashboard.dashboard import (
    DashboardSummary,
    APSummary,
    ARSummary,
    CashFlowSummary,
    TrendData,
    TrendDataPoint,
    RecentActivity,
    TopParty,
    AgingBucket,
    PendingApprovalItem,
)


class DashboardService:
    """Service for dashboard KPI calculations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_summary(
        self, organization_id: UUID
    ) -> DashboardSummary:
        """Get overall dashboard summary."""
        today = date.today()

        # Get counts
        vendor_count = await self._get_active_count(Vendor, organization_id)
        customer_count = await self._get_active_count(Customer, organization_id)
        pending_approvals = await self._get_pending_approvals_count(organization_id)

        # Get current financial year
        fy_result = await self.session.execute(
            select(FinancialYear)
            .where(
                and_(
                    FinancialYear.organization_id == organization_id,
                    FinancialYear.is_active == True,
                    FinancialYear.start_date <= today,
                    FinancialYear.end_date >= today,
                )
            )
        )
        current_fy = fy_result.scalar_one_or_none()

        # Get MTD revenue and expenses
        month_start = today.replace(day=1)
        revenue_mtd, expenses_mtd = await self._get_mtd_financials(
            organization_id, month_start, today
        )

        # Get last month for comparison
        last_month_end = month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        revenue_lm, expenses_lm = await self._get_mtd_financials(
            organization_id, last_month_start, last_month_end
        )

        # Calculate changes
        revenue_change = self._calculate_change(revenue_mtd, revenue_lm)
        expenses_change = self._calculate_change(expenses_mtd, expenses_lm)

        return DashboardSummary(
            total_vendors=vendor_count,
            total_customers=customer_count,
            total_pending_approvals=pending_approvals,
            total_revenue_mtd=revenue_mtd,
            total_expenses_mtd=expenses_mtd,
            net_profit_mtd=revenue_mtd - expenses_mtd,
            revenue_change=revenue_change,
            expenses_change=expenses_change,
            current_financial_year=current_fy.name if current_fy else None,
            as_on_date=today,
        )

    async def get_ap_summary(self, organization_id: UUID) -> APSummary:
        """Get Accounts Payable summary."""
        today = date.today()
        week_end = today + timedelta(days=7)

        # Get all posted/approved bills with outstanding amounts
        result = await self.session.execute(
            select(
                PurchaseBill.id,
                PurchaseBill.vendor_id,
                PurchaseBill.bill_number,
                PurchaseBill.bill_date,
                PurchaseBill.due_date,
                PurchaseBill.total_amount,
                (PurchaseBill.total_amount - PurchaseBill.balance_amount).label("paid_amount"),
                PurchaseBill.balance_amount.label("outstanding"),
                Vendor.name.label("vendor_name"),
                Vendor.code.label("vendor_code"),
            )
            .join(Vendor, PurchaseBill.vendor_id == Vendor.id)
            .where(
                and_(
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.is_active == True,
                    PurchaseBill.status.in_([BillStatus.APPROVED, BillStatus.PARTIALLY_PAID, BillStatus.PAID]),
                    PurchaseBill.payment_status != BillPaymentStatus.PAID,
                )
            )
        )
        bills = result.all()

        # Calculate totals
        total_outstanding = Decimal("0")
        total_overdue = Decimal("0")
        overdue_count = 0
        due_this_week = Decimal("0")
        due_this_week_count = 0

        # Aging buckets
        aging_0_30 = Decimal("0")
        aging_31_60 = Decimal("0")
        aging_61_90 = Decimal("0")
        aging_90_plus = Decimal("0")

        # Vendor outstanding map
        vendor_outstanding = {}

        for bill in bills:
            outstanding = bill.outstanding or Decimal("0")
            if outstanding <= 0:
                continue

            total_outstanding += outstanding

            # Check if overdue
            if bill.due_date and bill.due_date < today:
                total_overdue += outstanding
                overdue_count += 1
                days_overdue = (today - bill.due_date).days

                if days_overdue <= 30:
                    aging_0_30 += outstanding
                elif days_overdue <= 60:
                    aging_31_60 += outstanding
                elif days_overdue <= 90:
                    aging_61_90 += outstanding
                else:
                    aging_90_plus += outstanding

            # Check due this week
            if bill.due_date and today <= bill.due_date <= week_end:
                due_this_week += outstanding
                due_this_week_count += 1

            # Track vendor outstanding
            if bill.vendor_id not in vendor_outstanding:
                vendor_outstanding[bill.vendor_id] = {
                    "name": bill.vendor_name,
                    "code": bill.vendor_code,
                    "outstanding": Decimal("0"),
                    "overdue": Decimal("0"),
                }
            vendor_outstanding[bill.vendor_id]["outstanding"] += outstanding
            if bill.due_date and bill.due_date < today:
                vendor_outstanding[bill.vendor_id]["overdue"] += outstanding

        # Create aging buckets
        aging_buckets = [
            AgingBucket(
                label="0-30 days",
                amount=aging_0_30,
                percentage=float(aging_0_30 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="31-60 days",
                amount=aging_31_60,
                percentage=float(aging_31_60 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="61-90 days",
                amount=aging_61_90,
                percentage=float(aging_61_90 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="90+ days",
                amount=aging_90_plus,
                percentage=float(aging_90_plus / total_overdue * 100) if total_overdue else 0,
            ),
        ]

        # Top 5 vendors by outstanding
        top_vendors = sorted(
            [
                TopParty(
                    id=vid,
                    name=v["name"],
                    code=v["code"],
                    outstanding=v["outstanding"],
                    overdue=v["overdue"],
                )
                for vid, v in vendor_outstanding.items()
            ],
            key=lambda x: x.outstanding,
            reverse=True,
        )[:5]

        return APSummary(
            total_outstanding=total_outstanding,
            total_overdue=total_overdue,
            overdue_count=overdue_count,
            due_this_week=due_this_week,
            due_this_week_count=due_this_week_count,
            aging_buckets=aging_buckets,
            top_vendors=top_vendors,
        )

    async def get_ar_summary(self, organization_id: UUID) -> ARSummary:
        """Get Accounts Receivable summary."""
        today = date.today()
        week_end = today + timedelta(days=7)

        # Get all posted/approved invoices with outstanding amounts
        result = await self.session.execute(
            select(
                SalesInvoice.id,
                SalesInvoice.customer_id,
                SalesInvoice.invoice_number,
                SalesInvoice.invoice_date,
                SalesInvoice.due_date,
                SalesInvoice.total_amount,
                (SalesInvoice.total_amount - SalesInvoice.balance_amount).label("received_amount"),
                SalesInvoice.balance_amount.label("outstanding"),
                Customer.name.label("customer_name"),
                Customer.code.label("customer_code"),
            )
            .join(Customer, SalesInvoice.customer_id == Customer.id)
            .where(
                and_(
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.is_active == True,
                    SalesInvoice.status.in_([InvoiceStatus.APPROVED, InvoiceStatus.PARTIALLY_RECEIVED, InvoiceStatus.RECEIVED]),
                    SalesInvoice.receipt_status != ReceiptStatus.RECEIVED,
                )
            )
        )
        invoices = result.all()

        # Calculate totals
        total_outstanding = Decimal("0")
        total_overdue = Decimal("0")
        overdue_count = 0
        due_this_week = Decimal("0")
        due_this_week_count = 0

        # Aging buckets
        aging_0_30 = Decimal("0")
        aging_31_60 = Decimal("0")
        aging_61_90 = Decimal("0")
        aging_90_plus = Decimal("0")

        # Customer outstanding map
        customer_outstanding = {}

        for inv in invoices:
            outstanding = inv.outstanding or Decimal("0")
            if outstanding <= 0:
                continue

            total_outstanding += outstanding

            # Check if overdue
            if inv.due_date and inv.due_date < today:
                total_overdue += outstanding
                overdue_count += 1
                days_overdue = (today - inv.due_date).days

                if days_overdue <= 30:
                    aging_0_30 += outstanding
                elif days_overdue <= 60:
                    aging_31_60 += outstanding
                elif days_overdue <= 90:
                    aging_61_90 += outstanding
                else:
                    aging_90_plus += outstanding

            # Check due this week
            if inv.due_date and today <= inv.due_date <= week_end:
                due_this_week += outstanding
                due_this_week_count += 1

            # Track customer outstanding
            if inv.customer_id not in customer_outstanding:
                customer_outstanding[inv.customer_id] = {
                    "name": inv.customer_name,
                    "code": inv.customer_code,
                    "outstanding": Decimal("0"),
                    "overdue": Decimal("0"),
                }
            customer_outstanding[inv.customer_id]["outstanding"] += outstanding
            if inv.due_date and inv.due_date < today:
                customer_outstanding[inv.customer_id]["overdue"] += outstanding

        # Create aging buckets
        aging_buckets = [
            AgingBucket(
                label="0-30 days",
                amount=aging_0_30,
                percentage=float(aging_0_30 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="31-60 days",
                amount=aging_31_60,
                percentage=float(aging_31_60 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="61-90 days",
                amount=aging_61_90,
                percentage=float(aging_61_90 / total_overdue * 100) if total_overdue else 0,
            ),
            AgingBucket(
                label="90+ days",
                amount=aging_90_plus,
                percentage=float(aging_90_plus / total_overdue * 100) if total_overdue else 0,
            ),
        ]

        # Top 5 customers by outstanding
        top_customers = sorted(
            [
                TopParty(
                    id=cid,
                    name=c["name"],
                    code=c["code"],
                    outstanding=c["outstanding"],
                    overdue=c["overdue"],
                )
                for cid, c in customer_outstanding.items()
            ],
            key=lambda x: x.outstanding,
            reverse=True,
        )[:5]

        return ARSummary(
            total_outstanding=total_outstanding,
            total_overdue=total_overdue,
            overdue_count=overdue_count,
            due_this_week=due_this_week,
            due_this_week_count=due_this_week_count,
            aging_buckets=aging_buckets,
            top_customers=top_customers,
        )

    async def get_cashflow_summary(self, organization_id: UUID) -> CashFlowSummary:
        """Get cash flow summary."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        # Get posted payments for different periods
        async def get_payment_totals(from_date: date, to_date: date):
            result = await self.session.execute(
                select(
                    Payment.payment_type,
                    func.sum(Payment.net_amount).label("total"),
                )
                .where(
                    and_(
                        Payment.organization_id == organization_id,
                        Payment.is_active == True,
                        Payment.status == PaymentStatus.POSTED,
                        Payment.payment_date >= from_date,
                        Payment.payment_date <= to_date,
                    )
                )
                .group_by(Payment.payment_type)
            )
            totals = result.all()

            receipts = Decimal("0")
            payments = Decimal("0")

            for row in totals:
                if row.payment_type in [
                    PaymentType.CUSTOMER_RECEIPT,
                    PaymentType.ADVANCE_RECEIPT,
                ]:
                    receipts += row.total or Decimal("0")
                elif row.payment_type in [
                    PaymentType.VENDOR_PAYMENT,
                    PaymentType.ADVANCE_PAYMENT,
                ]:
                    payments += row.total or Decimal("0")

            return receipts, payments

        # Get totals for different periods
        receipts_today, payments_today = await get_payment_totals(today, today)
        receipts_week, payments_week = await get_payment_totals(week_start, today)
        receipts_month, payments_month = await get_payment_totals(month_start, today)

        # Get pending cheques
        pending_result = await self.session.execute(
            select(
                Payment.payment_type,
                func.sum(Payment.net_amount).label("total"),
            )
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.is_active == True,
                    Payment.status == PaymentStatus.POSTED,
                    Payment.payment_mode == PaymentMode.CHEQUE,
                    Payment.cheque_status.in_([ChequeStatus.ISSUED, ChequeStatus.DEPOSITED]),
                )
            )
            .group_by(Payment.payment_type)
        )
        pending_totals = pending_result.all()

        pending_receipts = Decimal("0")
        pending_payments = Decimal("0")

        for row in pending_totals:
            if row.payment_type in [
                PaymentType.CUSTOMER_RECEIPT,
                PaymentType.ADVANCE_RECEIPT,
            ]:
                pending_receipts += row.total or Decimal("0")
            elif row.payment_type in [
                PaymentType.VENDOR_PAYMENT,
                PaymentType.ADVANCE_PAYMENT,
            ]:
                pending_payments += row.total or Decimal("0")

        # Get total bank balance from bank accounts
        bank_result = await self.session.execute(
            select(func.sum(Account.current_balance))
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.is_active == True,
                    Account.is_bank_account == True,
                )
            )
        )
        total_bank_balance = bank_result.scalar() or Decimal("0")

        return CashFlowSummary(
            total_bank_balance=total_bank_balance,
            receipts_today=receipts_today,
            payments_today=payments_today,
            net_today=receipts_today - payments_today,
            receipts_week=receipts_week,
            payments_week=payments_week,
            net_week=receipts_week - payments_week,
            receipts_month=receipts_month,
            payments_month=payments_month,
            net_month=receipts_month - payments_month,
            pending_cheque_receipts=pending_receipts,
            pending_cheque_payments=pending_payments,
        )

    async def get_trends(
        self, organization_id: UUID, months: int = 6
    ) -> TrendData:
        """Get trend data for the last N months."""
        today = date.today()
        trends = TrendData()

        for i in range(months - 1, -1, -1):
            # Calculate month start and end
            month_date = today - timedelta(days=i * 30)
            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

            period_label = month_start.strftime("%b %Y")

            # Get collections (customer receipts)
            collections_result = await self.session.execute(
                select(func.sum(Payment.net_amount))
                .where(
                    and_(
                        Payment.organization_id == organization_id,
                        Payment.is_active == True,
                        Payment.status == PaymentStatus.POSTED,
                        Payment.payment_type.in_([
                            PaymentType.CUSTOMER_RECEIPT,
                            PaymentType.ADVANCE_RECEIPT,
                        ]),
                        Payment.payment_date >= month_start,
                        Payment.payment_date <= month_end,
                    )
                )
            )
            collections = collections_result.scalar() or Decimal("0")
            trends.collections.append(TrendDataPoint(period=period_label, value=collections))

            # Get payments (vendor payments)
            payments_result = await self.session.execute(
                select(func.sum(Payment.net_amount))
                .where(
                    and_(
                        Payment.organization_id == organization_id,
                        Payment.is_active == True,
                        Payment.status == PaymentStatus.POSTED,
                        Payment.payment_type.in_([
                            PaymentType.VENDOR_PAYMENT,
                            PaymentType.ADVANCE_PAYMENT,
                        ]),
                        Payment.payment_date >= month_start,
                        Payment.payment_date <= month_end,
                    )
                )
            )
            payments = payments_result.scalar() or Decimal("0")
            trends.payments.append(TrendDataPoint(period=period_label, value=payments))

            # Get revenue (from sales invoices)
            revenue_result = await self.session.execute(
                select(func.sum(SalesInvoice.total_amount))
                .where(
                    and_(
                        SalesInvoice.organization_id == organization_id,
                        SalesInvoice.is_active == True,
                        SalesInvoice.status.in_([InvoiceStatus.APPROVED, InvoiceStatus.PARTIALLY_RECEIVED, InvoiceStatus.RECEIVED]),
                        SalesInvoice.invoice_date >= month_start,
                        SalesInvoice.invoice_date <= month_end,
                    )
                )
            )
            revenue = revenue_result.scalar() or Decimal("0")
            trends.revenue.append(TrendDataPoint(period=period_label, value=revenue))

            # Get expenses (from purchase bills)
            expenses_result = await self.session.execute(
                select(func.sum(PurchaseBill.total_amount))
                .where(
                    and_(
                        PurchaseBill.organization_id == organization_id,
                        PurchaseBill.is_active == True,
                        PurchaseBill.status.in_([BillStatus.APPROVED, BillStatus.PARTIALLY_PAID, BillStatus.PAID]),
                        PurchaseBill.bill_date >= month_start,
                        PurchaseBill.bill_date <= month_end,
                    )
                )
            )
            expenses = expenses_result.scalar() or Decimal("0")
            trends.expenses.append(TrendDataPoint(period=period_label, value=expenses))

            # Net profit
            trends.net_profit.append(
                TrendDataPoint(period=period_label, value=revenue - expenses)
            )

        return trends

    async def get_recent_activity(
        self, organization_id: UUID, limit: int = 10
    ) -> List[RecentActivity]:
        """Get recent transaction activity."""
        activities = []

        # Get recent payments
        payments_result = await self.session.execute(
            select(Payment)
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.is_active == True,
                )
            )
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        for payment in payments_result.scalars():
            type_label = "RECEIPT" if payment.payment_type in [
                PaymentType.CUSTOMER_RECEIPT,
                PaymentType.ADVANCE_RECEIPT,
            ] else "PAYMENT"
            activities.append(
                RecentActivity(
                    id=payment.id,
                    type=type_label,
                    number=payment.payment_number,
                    description=f"{payment.payment_type.value} - {payment.payment_mode}",
                    amount=payment.net_amount,
                    party_name=None,  # Would need join for party name
                    status=payment.status.value,
                    created_at=payment.created_at,
                )
            )

        # Get recent invoices
        invoices_result = await self.session.execute(
            select(SalesInvoice, Customer.name)
            .join(Customer, SalesInvoice.customer_id == Customer.id)
            .where(
                and_(
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.is_active == True,
                )
            )
            .order_by(SalesInvoice.created_at.desc())
            .limit(limit)
        )
        for inv, customer_name in invoices_result:
            activities.append(
                RecentActivity(
                    id=inv.id,
                    type="INVOICE",
                    number=inv.invoice_number,
                    description=f"Sales Invoice",
                    amount=inv.total_amount,
                    party_name=customer_name,
                    status=inv.status.value,
                    created_at=inv.created_at,
                )
            )

        # Get recent bills
        bills_result = await self.session.execute(
            select(PurchaseBill, Vendor.name)
            .join(Vendor, PurchaseBill.vendor_id == Vendor.id)
            .where(
                and_(
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.is_active == True,
                )
            )
            .order_by(PurchaseBill.created_at.desc())
            .limit(limit)
        )
        for bill, vendor_name in bills_result:
            activities.append(
                RecentActivity(
                    id=bill.id,
                    type="BILL",
                    number=bill.bill_number,
                    description=f"Purchase Bill",
                    amount=bill.total_amount,
                    party_name=vendor_name,
                    status=bill.status.value,
                    created_at=bill.created_at,
                )
            )

        # Sort by created_at and return top N
        # Handle mixed timezone-aware and naive datetimes by normalizing
        def get_sort_key(activity):
            dt = activity.created_at
            if dt is None:
                return datetime.min
            # Remove timezone info for consistent comparison
            if hasattr(dt, 'replace') and dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        activities.sort(key=get_sort_key, reverse=True)
        return activities[:limit]

    async def get_pending_approvals(
        self, organization_id: UUID, user_id: UUID
    ) -> List[PendingApprovalItem]:
        """Get pending approval items for a user."""
        items = []
        today = date.today()

        # Get pending bills
        bills_result = await self.session.execute(
            select(PurchaseBill, Vendor.name)
            .join(Vendor, PurchaseBill.vendor_id == Vendor.id)
            .where(
                and_(
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.is_active == True,
                    PurchaseBill.status == BillStatus.SUBMITTED,
                )
            )
        )
        for bill, vendor_name in bills_result:
            days_pending = (today - bill.created_at.date()).days if bill.created_at else 0
            items.append(
                PendingApprovalItem(
                    id=bill.id,
                    type="PURCHASE_BILL",
                    number=bill.bill_number,
                    amount=bill.total_amount,
                    party_name=vendor_name,
                    submitted_by="",  # Would need join for user name
                    submitted_at=bill.created_at,
                    days_pending=days_pending,
                )
            )

        # Get pending invoices
        invoices_result = await self.session.execute(
            select(SalesInvoice, Customer.name)
            .join(Customer, SalesInvoice.customer_id == Customer.id)
            .where(
                and_(
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.is_active == True,
                    SalesInvoice.status == InvoiceStatus.SUBMITTED,
                )
            )
        )
        for inv, customer_name in invoices_result:
            days_pending = (today - inv.created_at.date()).days if inv.created_at else 0
            items.append(
                PendingApprovalItem(
                    id=inv.id,
                    type="SALES_INVOICE",
                    number=inv.invoice_number,
                    amount=inv.total_amount,
                    party_name=customer_name,
                    submitted_by="",
                    submitted_at=inv.created_at,
                    days_pending=days_pending,
                )
            )

        # Get pending payments
        payments_result = await self.session.execute(
            select(Payment)
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.is_active == True,
                    Payment.status == PaymentStatus.SUBMITTED,
                )
            )
        )
        for payment in payments_result.scalars():
            days_pending = (today - payment.created_at.date()).days if payment.created_at else 0
            items.append(
                PendingApprovalItem(
                    id=payment.id,
                    type="PAYMENT",
                    number=payment.payment_number,
                    amount=payment.net_amount,
                    party_name=None,
                    submitted_by="",
                    submitted_at=payment.created_at,
                    days_pending=days_pending,
                )
            )

        return items

    # Helper methods

    async def _get_active_count(self, model, organization_id: UUID) -> int:
        """Get count of active records for a model."""
        result = await self.session.execute(
            select(func.count(model.id))
            .where(
                and_(
                    model.organization_id == organization_id,
                    model.is_active == True,
                )
            )
        )
        return result.scalar() or 0

    async def _get_pending_approvals_count(self, organization_id: UUID) -> int:
        """Get total count of pending approvals."""
        count = 0

        # Count pending bills
        bills_result = await self.session.execute(
            select(func.count(PurchaseBill.id))
            .where(
                and_(
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.is_active == True,
                    PurchaseBill.status == BillStatus.SUBMITTED,
                )
            )
        )
        count += bills_result.scalar() or 0

        # Count pending invoices
        invoices_result = await self.session.execute(
            select(func.count(SalesInvoice.id))
            .where(
                and_(
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.is_active == True,
                    SalesInvoice.status == InvoiceStatus.SUBMITTED,
                )
            )
        )
        count += invoices_result.scalar() or 0

        # Count pending payments
        payments_result = await self.session.execute(
            select(func.count(Payment.id))
            .where(
                and_(
                    Payment.organization_id == organization_id,
                    Payment.is_active == True,
                    Payment.status == PaymentStatus.SUBMITTED,
                )
            )
        )
        count += payments_result.scalar() or 0

        return count

    async def _get_mtd_financials(
        self, organization_id: UUID, from_date: date, to_date: date
    ) -> tuple[Decimal, Decimal]:
        """Get month-to-date revenue and expenses."""
        # Revenue from sales invoices
        revenue_result = await self.session.execute(
            select(func.sum(SalesInvoice.total_amount))
            .where(
                and_(
                    SalesInvoice.organization_id == organization_id,
                    SalesInvoice.is_active == True,
                    SalesInvoice.status.in_([InvoiceStatus.APPROVED, InvoiceStatus.PARTIALLY_RECEIVED, InvoiceStatus.RECEIVED]),
                    SalesInvoice.invoice_date >= from_date,
                    SalesInvoice.invoice_date <= to_date,
                )
            )
        )
        revenue = revenue_result.scalar() or Decimal("0")

        # Expenses from purchase bills
        expenses_result = await self.session.execute(
            select(func.sum(PurchaseBill.total_amount))
            .where(
                and_(
                    PurchaseBill.organization_id == organization_id,
                    PurchaseBill.is_active == True,
                    PurchaseBill.status.in_([BillStatus.APPROVED, BillStatus.PARTIALLY_PAID, BillStatus.PAID]),
                    PurchaseBill.bill_date >= from_date,
                    PurchaseBill.bill_date <= to_date,
                )
            )
        )
        expenses = expenses_result.scalar() or Decimal("0")

        return revenue, expenses

    def _calculate_change(self, current: Decimal, previous: Decimal) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return float((current - previous) / previous * 100)
