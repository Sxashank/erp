"""Portal Dashboard Service.

Provides loan summary, upcoming dues, payment history for the customer portal.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.loan_account import (
    LoanAccount,
    LoanReceipt,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.models.portal.portal_user import PortalUser


class PortalDashboardService:
    """Portal dashboard service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Dashboard Summary
    # =========================================================================

    async def get_dashboard(
        self,
        user_id: UUID,
        customer_id: UUID,
        entity_ids: set[UUID] | None = None,
    ) -> Dict[str, Any]:
        """Get dashboard summary for the customer."""
        # Get loan summary
        loans = await self.get_loan_summary(customer_id, entity_ids=entity_ids)

        # Calculate totals
        total_outstanding = sum(loan.get("total_outstanding", 0) for loan in loans)
        total_overdue = sum(loan.get("overdue_amount", 0) for loan in loans)
        active_loans = len([l for l in loans if l.get("status") == "ACTIVE"])

        # Get upcoming EMIs
        upcoming_dues = await self.get_upcoming_dues(customer_id, days=30)
        next_due_date = upcoming_dues[0]["due_date"] if upcoming_dues else None
        next_due_amount = upcoming_dues[0]["amount"] if upcoming_dues else 0

        # Get recent payments
        recent_payments = await self.get_payment_history(
            customer_id, page=1, page_size=5, entity_ids=entity_ids
        )

        # Get unread notifications count
        unread_notifications = await self._get_unread_notification_count(user_id)

        # Get pending service requests
        pending_requests = await self._get_pending_request_count(user_id)

        return {
            "summary": {
                "total_outstanding": float(total_outstanding),
                "total_overdue": float(total_overdue),
                "active_loans": active_loans,
                "next_due_date": next_due_date.isoformat() if next_due_date else None,
                "next_due_amount": float(next_due_amount),
            },
            "loans": loans[:5],  # Top 5 loans
            "upcoming_dues": upcoming_dues[:3],  # Next 3 dues
            "recent_payments": recent_payments[0][:3],  # Last 3 payments
            "notifications": {
                "unread_count": unread_notifications,
            },
            "service_requests": {
                "pending_count": pending_requests,
            },
        }

    # =========================================================================
    # Loan Summary
    # =========================================================================

    async def get_loan_summary(
        self,
        customer_id: UUID | None = None,
        entity_ids: set[UUID] | None = None,
    ) -> List[Dict[str, Any]]:
        """Get all loans for a customer."""
        if not entity_ids:
            return []

        stmt = (
            select(LoanAccount)
            .options(
                selectinload(LoanAccount.product),
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.schedules).selectinload(RepaymentSchedule.installments),
            )
            .where(
                LoanAccount.entity_id.in_(entity_ids),
                LoanAccount.deleted_at.is_(None),
            )
            .order_by(LoanAccount.account_open_date.desc())
        )
        loans = list((await self.db.execute(stmt)).scalars().unique().all())
        return [self._loan_summary(loan) for loan in loans]

    async def get_loan_details(
        self,
        loan_account_id: UUID,
        customer_id: UUID | None = None,
        entity_ids: set[UUID] | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific loan."""
        if not entity_ids:
            return None

        stmt = (
            select(LoanAccount)
            .options(
                selectinload(LoanAccount.product),
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.schedules).selectinload(RepaymentSchedule.installments),
            )
            .where(
                LoanAccount.id == loan_account_id,
                LoanAccount.entity_id.in_(entity_ids),
                LoanAccount.deleted_at.is_(None),
            )
        )
        loan = (await self.db.execute(stmt)).scalars().unique().one_or_none()
        if loan is None:
            return None

        summary = self._loan_summary(loan)
        total_paid = (
            loan.total_principal_received
            + loan.total_interest_received
            + loan.total_penal_interest_received
            + loan.total_charges_received
        )
        summary.update(
            {
                "borrower_name": loan.entity.legal_name if loan.entity else "",
                "co_borrowers": [],
                "product_type": self._enum_value(getattr(loan.product, "category", "")),
                "rate_type": self._enum_value(loan.interest_type),
                "outstanding_interest": float(loan.interest_outstanding + loan.interest_overdue),
                "charges_due": float(loan.charges_outstanding),
                "emi_start_date": (
                    loan.repayment_start_date.isoformat() if loan.repayment_start_date else None
                ),
                "emi_end_date": loan.maturity_date.isoformat() if loan.maturity_date else None,
                "total_paid": float(total_paid),
                "total_principal_paid": float(loan.total_principal_received),
                "total_interest_paid": float(loan.total_interest_received),
                "prepaid_amount": 0,
                "nach_mandate_status": None,
            }
        )
        return summary

    # =========================================================================
    # Repayment Schedule
    # =========================================================================

    async def get_repayment_schedule(
        self,
        loan_account_id: UUID,
        customer_id: UUID | None = None,
        entity_ids: set[UUID] | None = None,
    ) -> List[Dict[str, Any]]:
        """Get EMI repayment schedule for a loan."""
        if not entity_ids:
            return []

        loan = await self._get_accessible_loan(loan_account_id, entity_ids)
        if loan is None:
            return []

        current_schedule = self._current_schedule(loan)
        if current_schedule is None:
            return []

        return [
            {
                "installment_number": row.installment_number,
                "due_date": row.due_date.isoformat(),
                "emi_amount": float(row.emi_amount),
                "principal_component": float(row.principal_amount),
                "interest_component": float(row.interest_amount),
                "principal": float(row.principal_amount),
                "interest": float(row.interest_amount),
                "opening_balance": float(row.opening_balance),
                "closing_balance": float(row.closing_balance),
                "status": self._schedule_status(row),
                "paid_amount": float((row.principal_paid or 0) + (row.interest_paid or 0)),
                "paid_date": row.paid_date.isoformat() if row.paid_date else None,
            }
            for row in current_schedule.installments
        ]

    # =========================================================================
    # Upcoming Dues
    # =========================================================================

    async def get_upcoming_dues(
        self,
        customer_id: UUID,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get upcoming EMI dues across all loans."""
        # Would aggregate upcoming dues from all active loans
        # Placeholder implementation

        dues = []
        # Example structure:
        # dues = [
        #     {
        #         "loan_account_id": str(loan_id),
        #         "loan_account_number": "LN0001",
        #         "due_date": date(2024, 1, 5),
        #         "amount": 10000,
        #         "principal": 8000,
        #         "interest": 2000,
        #         "is_overdue": False,
        #         "days_until_due": 5,
        #     }
        # ]

        return dues

    async def get_overdue_summary(
        self,
        customer_id: UUID,
    ) -> Dict[str, Any]:
        """Get summary of overdue amounts."""
        # Would calculate total overdue across all loans
        return {
            "total_overdue": 0,
            "overdue_principal": 0,
            "overdue_interest": 0,
            "overdue_charges": 0,
            "oldest_overdue_date": None,
            "max_dpd": 0,
            "loans_in_overdue": 0,
        }

    # =========================================================================
    # Payment History
    # =========================================================================

    async def get_payment_history(
        self,
        customer_id: UUID,
        loan_account_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        entity_ids: set[UUID] | None = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get payment history."""
        if not entity_ids:
            return [], 0
        stmt = (
            select(LoanReceipt)
            .join(LoanAccount, LoanAccount.id == LoanReceipt.loan_account_id)
            .options(selectinload(LoanReceipt.loan_account))
            .where(LoanAccount.entity_id.in_(entity_ids))
        )
        if loan_account_id:
            stmt = stmt.where(LoanReceipt.loan_account_id == loan_account_id)
        if from_date:
            stmt = stmt.where(LoanReceipt.receipt_date >= from_date)
        if to_date:
            stmt = stmt.where(LoanReceipt.receipt_date <= to_date)

        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        stmt = (
            stmt.order_by(LoanReceipt.receipt_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        receipts = list((await self.db.execute(stmt)).scalars().all())
        return [
            {
                "id": str(row.id),
                "receipt_id": str(row.id),
                "receipt_number": row.receipt_number,
                "payment_date": row.receipt_date.isoformat(),
                "amount": float(row.receipt_amount),
                "principal_applied": float(row.principal_allocated),
                "interest_applied": float(row.interest_allocated),
                "charges_applied": float(row.charges_allocated),
                "payment_mode": self._enum_value(row.receipt_mode),
                "reference_number": row.instrument_number,
                "loan_account_id": str(row.loan_account_id),
                "loan_account_number": (
                    row.loan_account.loan_account_number if row.loan_account else ""
                ),
                "status": self._enum_value(row.status),
            }
            for row in receipts
        ], int(total or 0)

    async def _get_accessible_loan(
        self, loan_account_id: UUID, entity_ids: set[UUID]
    ) -> LoanAccount | None:
        stmt = (
            select(LoanAccount)
            .options(
                selectinload(LoanAccount.product),
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.schedules).selectinload(RepaymentSchedule.installments),
            )
            .where(
                LoanAccount.id == loan_account_id,
                LoanAccount.entity_id.in_(entity_ids),
                LoanAccount.deleted_at.is_(None),
            )
        )
        return (await self.db.execute(stmt)).scalars().unique().one_or_none()

    def _loan_summary(self, loan: LoanAccount) -> Dict[str, Any]:
        next_due = self._next_due(loan)
        current_schedule = self._current_schedule(loan)
        remaining = (
            len([i for i in current_schedule.installments if self._schedule_status(i) != "PAID"])
            if current_schedule
            else loan.tenure_months
        )
        overdue_amount = loan.principal_overdue + loan.interest_overdue
        next_emi_iso = next_due["due_date"] if next_due else None
        # Derive day-of-month from next due date; default to 5 (most common).
        try:
            emi_day = int(next_emi_iso.split("-")[2]) if next_emi_iso else 5
        except (ValueError, IndexError):
            emi_day = 5
        return {
            "id": str(loan.id),
            "loan_account_id": str(loan.id),
            "loan_account_number": loan.loan_account_number,
            "product_name": loan.product.name if loan.product else "",
            "sanctioned_amount": float(loan.sanctioned_amount),
            "disbursed_amount": float(loan.total_disbursed_amount),
            "outstanding_principal": float(loan.principal_outstanding),
            "principal_outstanding": float(loan.principal_outstanding),
            "outstanding_interest": float(loan.interest_outstanding + loan.interest_overdue),
            "interest_outstanding": float(loan.interest_outstanding + loan.interest_overdue),
            "charges_outstanding": float(loan.charges_outstanding or 0),
            "charges_due": float(loan.charges_outstanding or 0),
            "total_outstanding": float(loan.total_outstanding),
            "overdue_amount": float(overdue_amount),
            "emi_amount": float(loan.current_emi_amount or 0),
            "emi_date": emi_day,
            "interest_rate": float(loan.current_interest_rate),
            "tenure_months": loan.tenure_months,
            "remaining_tenure": remaining,
            "remaining_emis": remaining,
            "disbursement_date": (
                loan.first_disbursement_date.isoformat() if loan.first_disbursement_date else None
            ),
            "maturity_date": loan.maturity_date.isoformat() if loan.maturity_date else None,
            "next_emi_date": next_emi_iso,
            "next_emi_amount": next_due["emi_amount"] if next_due else None,
            "overdue_days": loan.days_past_due,
            "dpd": loan.days_past_due,
            "status": self._enum_value(loan.status),
        }

    def _current_schedule(self, loan: LoanAccount) -> RepaymentSchedule | None:
        return next((schedule for schedule in loan.schedules if schedule.is_current), None)

    def _next_due(self, loan: LoanAccount) -> Dict[str, Any] | None:
        schedule = self._current_schedule(loan)
        if schedule is None:
            return None
        for row in sorted(schedule.installments, key=lambda item: item.due_date):
            if self._schedule_status(row) != "PAID":
                return {
                    "due_date": row.due_date.isoformat(),
                    "emi_amount": float(row.emi_amount),
                }
        return None

    def _schedule_status(self, row: ScheduleInstallment) -> str:
        status = self._enum_value(row.status)
        if status in {"NOT_DUE", "UPCOMING"}:
            return "FUTURE"
        if status == "PARTIALLY_PAID":
            return "PARTIAL"
        return status

    def _enum_value(self, value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)

    # =========================================================================
    # Loan Statements
    # =========================================================================

    async def get_account_statement(
        self,
        loan_account_id: UUID,
        customer_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Dict[str, Any]:
        """Generate account statement for a loan."""
        # Would generate detailed statement with all transactions
        return {
            "loan_account_number": "",
            "customer_name": "",
            "statement_period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            },
            "opening_balance": 0,
            "closing_balance": 0,
            "transactions": [],
            "summary": {
                "total_debits": 0,
                "total_credits": 0,
                "principal_paid": 0,
                "interest_paid": 0,
                "charges_paid": 0,
            },
        }

    # =========================================================================
    # Quotes
    # =========================================================================

    async def get_prepayment_quote(
        self,
        loan_account_id: UUID,
        customer_id: UUID,
        prepayment_amount: Decimal,
        prepayment_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Calculate prepayment quote."""
        # Would calculate prepayment with charges from lending module
        if not prepayment_date:
            prepayment_date = date.today()

        return {
            "loan_account_id": str(loan_account_id),
            "quote_date": date.today().isoformat(),
            "prepayment_date": prepayment_date.isoformat(),
            "prepayment_amount": float(prepayment_amount),
            "prepayment_charges": 0,
            "interest_till_date": 0,
            "total_payable": float(prepayment_amount),
            "valid_until": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "impact": {
                "tenure_reduction_months": 0,
                "emi_reduction": 0,
                "interest_savings": 0,
            },
        }

    async def get_foreclosure_quote(
        self,
        loan_account_id: UUID,
        customer_id: UUID,
        foreclosure_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Calculate foreclosure quote."""
        # Would calculate full settlement amount from lending module
        if not foreclosure_date:
            foreclosure_date = date.today()

        return {
            "loan_account_id": str(loan_account_id),
            "quote_date": date.today().isoformat(),
            "foreclosure_date": foreclosure_date.isoformat(),
            "principal_outstanding": 0,
            "interest_till_date": 0,
            "foreclosure_charges": 0,
            "other_charges": 0,
            "total_payable": 0,
            "valid_until": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "breakdown": {
                "principal": 0,
                "accrued_interest": 0,
                "penal_interest": 0,
                "late_payment_charges": 0,
                "foreclosure_charges": 0,
                "gst_on_charges": 0,
            },
        }

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_unread_notification_count(
        self,
        user_id: UUID,
    ) -> int:
        """Get count of unread notifications."""
        # Would query portal_notification table
        return 0

    async def _get_pending_request_count(
        self,
        user_id: UUID,
    ) -> int:
        """Get count of pending service requests."""
        # Would query portal_service_request table
        return 0
