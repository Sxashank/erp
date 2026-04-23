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
    ) -> Dict[str, Any]:
        """Get dashboard summary for the customer."""
        # Get loan summary
        loans = await self.get_loan_summary(customer_id)

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
            customer_id, page=1, page_size=5
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
        customer_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all loans for a customer."""
        # This would join with the lending module's loan account table
        # Simplified implementation - actual implementation would query loan tables

        # Placeholder: In production, this would query txn_loan_account
        # and related tables
        loans = []

        # Example structure of what would be returned:
        # loans = [
        #     {
        #         "loan_account_id": str(loan.id),
        #         "loan_account_number": loan.account_number,
        #         "product_name": loan.product.name,
        #         "sanctioned_amount": float(loan.sanctioned_amount),
        #         "disbursed_amount": float(loan.disbursed_amount),
        #         "principal_outstanding": float(loan.principal_outstanding),
        #         "interest_outstanding": float(loan.interest_outstanding),
        #         "total_outstanding": float(loan.total_outstanding),
        #         "overdue_amount": float(loan.overdue_amount),
        #         "emi_amount": float(loan.emi_amount),
        #         "emi_date": loan.emi_date,
        #         "tenure_months": loan.tenure_months,
        #         "remaining_tenure": loan.remaining_tenure,
        #         "interest_rate": float(loan.interest_rate),
        #         "status": loan.status.value,
        #         "disbursement_date": loan.disbursement_date.isoformat(),
        #         "maturity_date": loan.maturity_date.isoformat(),
        #         "dpd": loan.days_past_due,
        #     }
        # ]

        return loans

    async def get_loan_details(
        self,
        loan_account_id: UUID,
        customer_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific loan."""
        # Verify loan belongs to customer
        # Query loan details from lending module

        # Placeholder implementation
        return {
            "loan_account_id": str(loan_account_id),
            "loan_account_number": "",
            "product_name": "",
            "product_type": "",
            # Basic Details
            "sanctioned_amount": 0,
            "disbursed_amount": 0,
            "disbursement_date": None,
            "maturity_date": None,
            "tenure_months": 0,
            "interest_rate": 0,
            "rate_type": "FLOATING",
            # Outstanding
            "principal_outstanding": 0,
            "interest_outstanding": 0,
            "charges_outstanding": 0,
            "total_outstanding": 0,
            "overdue_amount": 0,
            # EMI Details
            "emi_amount": 0,
            "emi_date": 1,
            "next_emi_date": None,
            "remaining_emis": 0,
            # Status
            "status": "ACTIVE",
            "dpd": 0,
            "npa_status": None,
            # Payments
            "total_paid": 0,
            "last_payment_date": None,
            "last_payment_amount": 0,
            # Security (if applicable)
            "security_type": None,
            "security_value": 0,
            # Insurance
            "insurance_premium": 0,
            "insurance_expiry": None,
        }

    # =========================================================================
    # Repayment Schedule
    # =========================================================================

    async def get_repayment_schedule(
        self,
        loan_account_id: UUID,
        customer_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get EMI repayment schedule for a loan."""
        # Would query the repayment schedule from lending module
        # Placeholder implementation

        schedule = []
        # Example structure:
        # schedule = [
        #     {
        #         "installment_number": 1,
        #         "due_date": "2024-01-05",
        #         "emi_amount": 10000,
        #         "principal_component": 8000,
        #         "interest_component": 2000,
        #         "opening_balance": 100000,
        #         "closing_balance": 92000,
        #         "status": "PAID",  # PAID, PARTIALLY_PAID, DUE, OVERDUE, UPCOMING
        #         "paid_amount": 10000,
        #         "paid_date": "2024-01-05",
        #     }
        # ]

        return schedule

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
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get payment history."""
        # Would query payment receipts from lending module
        # Placeholder implementation

        payments = []
        total = 0
        # Example structure:
        # payments = [
        #     {
        #         "receipt_id": str(receipt.id),
        #         "receipt_number": "RCP0001",
        #         "payment_date": "2024-01-05",
        #         "amount": 10000,
        #         "principal_adjusted": 8000,
        #         "interest_adjusted": 2000,
        #         "charges_adjusted": 0,
        #         "payment_mode": "UPI",
        #         "reference_number": "UPI123456",
        #         "loan_account_id": str(loan_id),
        #         "loan_account_number": "LN0001",
        #         "status": "SUCCESS",
        #     }
        # ]

        return payments, total

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
