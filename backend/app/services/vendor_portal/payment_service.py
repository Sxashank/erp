"""Vendor Payment Service."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
)
from app.repositories.ap_ar.payment_repo import PaymentRepository
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.schemas.vendor_portal.payment import (
    VendorPaymentFilter,
    VendorAgingFilter,
    VendorStatementFilter,
    AgingBucket,
    VendorStatement,
    VendorStatementLine,
)


class VendorPaymentService:
    """Service for vendor payment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.vendor_repo = VendorRepository(session)

    async def get_payments(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[VendorPaymentFilter] = None,
    ) -> Tuple[List[Any], int]:
        """Get payments for a vendor."""
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}

        return await self.payment_repo.get_all_by_vendor(
            vendor_id=vendor_id,
            skip=skip,
            limit=limit,
            **filter_dict,
        )

    async def get_payment_details(
        self,
        vendor_id: UUID,
        payment_id: UUID,
    ) -> Any:
        """Get payment details."""
        payment = await self.payment_repo.get_with_details(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")

        if payment.vendor_id != vendor_id:
            raise NotFoundException("Payment not found")

        return payment

    async def get_remittance_advice(
        self,
        vendor_id: UUID,
        payment_id: UUID,
    ) -> Dict[str, Any]:
        """Get remittance advice for a payment."""
        payment = await self.payment_repo.get_with_details(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")

        if payment.vendor_id != vendor_id:
            raise NotFoundException("Payment not found")

        # Get vendor details
        vendor = await self.vendor_repo.get(vendor_id)

        # Build remittance advice
        remittance = {
            "payment_id": payment_id,
            "payment_date": payment.payment_date,
            "payment_reference": payment.payment_reference,
            "payment_mode": payment.payment_mode,
            "amount": payment.amount,
            "vendor": {
                "name": vendor.name,
                "code": vendor.code,
                "address": vendor.address_line1,
                "city": vendor.city,
                "state": vendor.state_code,
                "gstin": vendor.gstin,
            },
            "invoices": [],
            "deductions": [],
        }

        # Add invoice allocations
        if hasattr(payment, "allocations"):
            for allocation in payment.allocations:
                remittance["invoices"].append({
                    "invoice_number": allocation.invoice_number,
                    "invoice_date": allocation.invoice_date,
                    "invoice_amount": allocation.invoice_amount,
                    "allocated_amount": allocation.allocated_amount,
                })

        # Add deductions
        if hasattr(payment, "deductions"):
            for deduction in payment.deductions:
                remittance["deductions"].append({
                    "type": deduction.deduction_type,
                    "description": deduction.description,
                    "amount": deduction.amount,
                })

        return remittance

    async def download_remittance_pdf(
        self,
        vendor_id: UUID,
        payment_id: UUID,
    ) -> bytes:
        """Generate and return remittance advice PDF."""
        payment = await self.payment_repo.get_with_details(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")

        if payment.vendor_id != vendor_id:
            raise NotFoundException("Payment not found")

        # TODO: Implement PDF generation
        raise NotImplementedError("PDF generation not yet implemented")

    async def get_aging_report(
        self,
        vendor_id: UUID,
        filters: Optional[VendorAgingFilter] = None,
    ) -> Dict[str, Any]:
        """Get aging report for a vendor."""
        as_of_date = filters.as_of_date if filters else date.today()

        # Get all outstanding invoices
        outstanding = await self.payment_repo.get_outstanding_by_vendor(
            vendor_id=vendor_id,
            as_of_date=as_of_date,
        )

        # Initialize aging buckets
        buckets = {
            "current": AgingBucket(
                label="Current",
                min_days=0,
                max_days=0,
                amount=Decimal("0"),
                count=0,
            ),
            "1_30": AgingBucket(
                label="1-30 Days",
                min_days=1,
                max_days=30,
                amount=Decimal("0"),
                count=0,
            ),
            "31_60": AgingBucket(
                label="31-60 Days",
                min_days=31,
                max_days=60,
                amount=Decimal("0"),
                count=0,
            ),
            "61_90": AgingBucket(
                label="61-90 Days",
                min_days=61,
                max_days=90,
                amount=Decimal("0"),
                count=0,
            ),
            "over_90": AgingBucket(
                label="Over 90 Days",
                min_days=91,
                max_days=None,
                amount=Decimal("0"),
                count=0,
            ),
        }

        invoices = []
        total_amount = Decimal("0")

        for invoice in outstanding:
            days_overdue = (as_of_date - invoice.due_date).days if invoice.due_date else 0
            balance = invoice.balance_amount or Decimal("0")
            total_amount += balance

            invoice_data = {
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "invoice_amount": invoice.total_amount,
                "balance_amount": balance,
                "days_overdue": max(0, days_overdue),
            }
            invoices.append(invoice_data)

            # Categorize into buckets
            if days_overdue <= 0:
                buckets["current"].amount += balance
                buckets["current"].count += 1
            elif days_overdue <= 30:
                buckets["1_30"].amount += balance
                buckets["1_30"].count += 1
            elif days_overdue <= 60:
                buckets["31_60"].amount += balance
                buckets["31_60"].count += 1
            elif days_overdue <= 90:
                buckets["61_90"].amount += balance
                buckets["61_90"].count += 1
            else:
                buckets["over_90"].amount += balance
                buckets["over_90"].count += 1

        return {
            "as_of_date": as_of_date,
            "total_outstanding": total_amount,
            "invoice_count": len(invoices),
            "buckets": list(buckets.values()),
            "invoices": invoices,
        }

    async def get_account_statement(
        self,
        vendor_id: UUID,
        filters: VendorStatementFilter,
    ) -> VendorStatement:
        """Get account statement for a vendor."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Get opening balance
        opening_balance = await self.payment_repo.get_balance_as_of(
            vendor_id=vendor_id,
            as_of_date=filters.from_date,
        )

        # Get transactions in period
        transactions = await self.payment_repo.get_transactions_in_period(
            vendor_id=vendor_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )

        # Build statement lines
        lines = []
        running_balance = opening_balance

        for txn in transactions:
            if txn.type == "invoice":
                debit = txn.amount
                credit = Decimal("0")
                running_balance += debit
            else:  # payment
                debit = Decimal("0")
                credit = txn.amount
                running_balance -= credit

            lines.append(VendorStatementLine(
                date=txn.date,
                reference=txn.reference,
                description=txn.description,
                document_type=txn.type,
                debit=debit,
                credit=credit,
                balance=running_balance,
            ))

        closing_balance = running_balance

        return VendorStatement(
            vendor_id=vendor_id,
            vendor_name=vendor.name,
            vendor_code=vendor.code,
            from_date=filters.from_date,
            to_date=filters.to_date,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            total_invoices=sum(line.debit for line in lines),
            total_payments=sum(line.credit for line in lines),
            lines=lines,
            generated_at=datetime.utcnow(),
        )

    async def download_statement_pdf(
        self,
        vendor_id: UUID,
        filters: VendorStatementFilter,
    ) -> bytes:
        """Generate and return statement PDF."""
        # TODO: Implement PDF generation
        raise NotImplementedError("PDF generation not yet implemented")

    async def get_payment_summary(
        self,
        vendor_id: UUID,
    ) -> Dict[str, Any]:
        """Get payment summary for vendor dashboard."""
        # Get summary statistics
        summary = await self.payment_repo.get_summary_by_vendor(vendor_id)

        # Get recent payments
        recent_payments, _ = await self.payment_repo.get_all_by_vendor(
            vendor_id=vendor_id,
            skip=0,
            limit=5,
        )

        return {
            "total_received": summary.get("total_received", Decimal("0")),
            "total_outstanding": summary.get("total_outstanding", Decimal("0")),
            "pending_payments": summary.get("pending_payments", 0),
            "last_payment_date": summary.get("last_payment_date"),
            "last_payment_amount": summary.get("last_payment_amount"),
            "recent_payments": recent_payments,
        }

    async def get_upcoming_payments(
        self,
        vendor_id: UUID,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get upcoming payments (invoices due soon)."""
        return await self.payment_repo.get_upcoming_dues(
            vendor_id=vendor_id,
            days=days,
        )
