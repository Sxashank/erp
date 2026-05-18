"""Loan Schedule Generation Service."""

import logging
import math
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending import (
    LoanAccount,
    LoanSchedule,
)

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service for generating and managing loan repayment schedules."""

    def __init__(self, db: AsyncSession):
        """Initialize schedule service."""
        self.db = db

    async def generate_schedule(
        self,
        loan_account_id: UUID,
        principal: Decimal,
        interest_rate: Decimal,
        tenure_months: int,
        disbursement_date: date,
        emi_day: int = 1,
        calculation_method: str = "reducing_balance",
        moratorium_months: int = 0,
        user_id: UUID | None = None,
    ) -> list[LoanSchedule]:
        """
        Generate loan repayment schedule.

        Args:
            loan_account_id: Loan account ID
            principal: Loan principal amount
            interest_rate: Annual interest rate (percentage)
            tenure_months: Loan tenure in months
            disbursement_date: Disbursement/first date
            emi_day: Day of month for EMI payment (1-28)
            calculation_method: flat, reducing_balance, emi, rule_of_78
            moratorium_months: Number of moratorium months (interest only)
            user_id: User creating the schedule

        Returns:
            List of generated schedule entries
        """
        # Delete existing schedule
        await self.db.execute(
            delete(LoanSchedule).where(LoanSchedule.loan_account_id == loan_account_id)
        )

        # Validate EMI day
        emi_day = min(max(emi_day, 1), 28)

        # Calculate schedule based on method
        if calculation_method == "flat":
            entries = self._generate_flat_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )
        elif calculation_method == "reducing_balance":
            entries = self._generate_reducing_balance_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )
        elif calculation_method == "emi" or calculation_method == "equated":
            entries = self._generate_emi_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )
        elif calculation_method == "rule_of_78":
            entries = self._generate_rule_of_78_schedule(
                principal, interest_rate, tenure_months, disbursement_date, emi_day
            )
        else:
            # Default to reducing balance
            entries = self._generate_reducing_balance_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )

        # Create database records
        schedules = []
        for idx, entry in enumerate(entries, 1):
            schedule = LoanSchedule(
                loan_account_id=loan_account_id,
                installment_number=idx,
                due_date=entry["due_date"],
                principal_amount=entry["principal"],
                interest_amount=entry["interest"],
                total_amount=entry["total"],
                opening_balance=entry["opening_balance"],
                closing_balance=entry["closing_balance"],
                is_moratorium=entry.get("is_moratorium", False),
                created_by=user_id,
            )
            self.db.add(schedule)
            schedules.append(schedule)

        await self.db.flush()

        return schedules

    def _get_next_emi_date(self, current_date: date, emi_day: int, months_ahead: int = 1) -> date:
        """Calculate next EMI date."""
        year = current_date.year
        month = current_date.month + months_ahead

        while month > 12:
            month -= 12
            year += 1

        # Handle months with fewer days
        max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
        actual_day = min(emi_day, max_day)

        return date(year, month, actual_day)

    def _generate_flat_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        tenure: int,
        start_date: date,
        emi_day: int,
        moratorium: int = 0,
    ) -> list[dict]:
        """Generate flat interest schedule (total interest divided equally)."""
        total_interest = (principal * annual_rate * Decimal(tenure)) / (
            Decimal("100") * Decimal("12")
        )
        monthly_interest = (total_interest / Decimal(tenure)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        monthly_principal = (
            (principal / Decimal(tenure - moratorium)).quantize(Decimal("0.01"), ROUND_HALF_UP)
            if moratorium < tenure
            else Decimal("0")
        )

        entries = []
        balance = principal
        current_date = start_date

        for i in range(tenure):
            due_date = self._get_next_emi_date(current_date, emi_day, i + 1)
            is_moratorium = i < moratorium

            if is_moratorium:
                prin = Decimal("0")
            elif i == tenure - 1:
                # Last installment - pay remaining balance
                prin = balance
            else:
                prin = monthly_principal

            opening = balance
            closing = (balance - prin).quantize(Decimal("0.01"), ROUND_HALF_UP)

            entries.append(
                {
                    "due_date": due_date,
                    "principal": prin,
                    "interest": monthly_interest,
                    "total": prin + monthly_interest,
                    "opening_balance": opening,
                    "closing_balance": max(closing, Decimal("0")),
                    "is_moratorium": is_moratorium,
                }
            )

            balance = closing

        return entries

    def _generate_reducing_balance_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        tenure: int,
        start_date: date,
        emi_day: int,
        moratorium: int = 0,
    ) -> list[dict]:
        """Generate reducing balance schedule (interest on outstanding principal)."""
        monthly_rate = annual_rate / Decimal("1200")  # Annual rate to monthly
        principal_installments = tenure - moratorium

        if principal_installments > 0:
            monthly_principal = (principal / Decimal(principal_installments)).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
        else:
            monthly_principal = Decimal("0")

        entries = []
        balance = principal
        current_date = start_date

        for i in range(tenure):
            due_date = self._get_next_emi_date(current_date, emi_day, i + 1)
            is_moratorium = i < moratorium

            # Interest on current balance
            interest = (balance * monthly_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)

            if is_moratorium:
                prin = Decimal("0")
            elif i == tenure - 1:
                # Last installment - pay remaining balance
                prin = balance
            else:
                prin = monthly_principal

            opening = balance
            closing = (balance - prin).quantize(Decimal("0.01"), ROUND_HALF_UP)

            entries.append(
                {
                    "due_date": due_date,
                    "principal": prin,
                    "interest": interest,
                    "total": prin + interest,
                    "opening_balance": opening,
                    "closing_balance": max(closing, Decimal("0")),
                    "is_moratorium": is_moratorium,
                }
            )

            balance = closing

        return entries

    def _generate_emi_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        tenure: int,
        start_date: date,
        emi_day: int,
        moratorium: int = 0,
    ) -> list[dict]:
        """Generate EMI (Equated Monthly Installment) schedule."""
        monthly_rate = annual_rate / Decimal("1200")
        principal_tenure = tenure - moratorium

        # Calculate EMI using formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        if monthly_rate > 0 and principal_tenure > 0:
            r = float(monthly_rate)
            n = principal_tenure
            p = float(principal)
            emi = p * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
            emi = Decimal(str(emi)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        else:
            emi = (principal / Decimal(max(principal_tenure, 1))).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        entries = []
        balance = principal
        current_date = start_date

        for i in range(tenure):
            due_date = self._get_next_emi_date(current_date, emi_day, i + 1)
            is_moratorium = i < moratorium

            # Interest on current balance
            interest = (balance * monthly_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)

            if is_moratorium:
                prin = Decimal("0")
                total = interest
            elif i == tenure - 1:
                # Last installment
                prin = balance
                total = prin + interest
            else:
                prin = (emi - interest).quantize(Decimal("0.01"), ROUND_HALF_UP)
                prin = max(prin, Decimal("0"))  # Ensure non-negative
                total = emi

            opening = balance
            closing = (balance - prin).quantize(Decimal("0.01"), ROUND_HALF_UP)

            entries.append(
                {
                    "due_date": due_date,
                    "principal": prin,
                    "interest": interest,
                    "total": total,
                    "opening_balance": opening,
                    "closing_balance": max(closing, Decimal("0")),
                    "is_moratorium": is_moratorium,
                }
            )

            balance = closing

        return entries

    def _generate_rule_of_78_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        tenure: int,
        start_date: date,
        emi_day: int,
    ) -> list[dict]:
        """Generate Rule of 78 schedule (sum of digits method)."""
        # Total interest for the loan
        total_interest = (principal * annual_rate * Decimal(tenure)) / (
            Decimal("100") * Decimal("12")
        )

        # Sum of digits (1 + 2 + ... + n = n*(n+1)/2)
        sum_of_digits = tenure * (tenure + 1) // 2

        # Monthly principal (equal)
        monthly_principal = (principal / Decimal(tenure)).quantize(Decimal("0.01"), ROUND_HALF_UP)

        entries = []
        balance = principal
        current_date = start_date

        for i in range(tenure):
            due_date = self._get_next_emi_date(current_date, emi_day, i + 1)

            # Interest for this period (higher weight for earlier periods)
            weight = tenure - i
            interest = (total_interest * Decimal(weight) / Decimal(sum_of_digits)).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

            if i == tenure - 1:
                prin = balance
            else:
                prin = monthly_principal

            opening = balance
            closing = (balance - prin).quantize(Decimal("0.01"), ROUND_HALF_UP)

            entries.append(
                {
                    "due_date": due_date,
                    "principal": prin,
                    "interest": interest,
                    "total": prin + interest,
                    "opening_balance": opening,
                    "closing_balance": max(closing, Decimal("0")),
                    "is_moratorium": False,
                }
            )

            balance = closing

        return entries

    def preview_schedule(
        self,
        principal: Decimal,
        interest_rate: Decimal,
        tenure_months: int,
        disbursement_date: date,
        emi_day: int = 1,
        calculation_method: str = "reducing_balance",
        moratorium_months: int = 0,
    ) -> dict[str, Any]:
        """
        Compute a repayment schedule without persisting.

        Pure math — no DB writes — so callers (LOS / sanction calculators,
        borrower-facing what-if previews) can run this without an existing
        loan account. Mirrors `generate_schedule` but returns rows + summary
        as plain Decimals; persistence is the caller's responsibility.

        Args:
            principal: Loan principal amount
            interest_rate: Annual interest rate (percentage)
            tenure_months: Loan tenure in months
            disbursement_date: First-date anchor for the schedule
            emi_day: Day of month for EMI payment (1-28)
            calculation_method: flat / reducing_balance / emi / rule_of_78
            moratorium_months: Interest-only months at start

        Returns:
            Dict with `entries` (per-installment) and `summary` totals.
        """
        emi_day = min(max(emi_day, 1), 28)
        method = (calculation_method or "reducing_balance").lower()

        if method == "flat":
            entries = self._generate_flat_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )
        elif method in ("emi", "equated"):
            entries = self._generate_emi_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )
        elif method == "rule_of_78":
            entries = self._generate_rule_of_78_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
            )
        else:  # reducing_balance (default) — matches generate_schedule
            entries = self._generate_reducing_balance_schedule(
                principal,
                interest_rate,
                tenure_months,
                disbursement_date,
                emi_day,
                moratorium_months,
            )

        rows: list[dict[str, Any]] = []
        total_principal = Decimal("0")
        total_interest = Decimal("0")
        for idx, entry in enumerate(entries, 1):
            rows.append(
                {
                    "installment_number": idx,
                    "due_date": entry["due_date"],
                    "principal_amount": entry["principal"],
                    "interest_amount": entry["interest"],
                    "total_amount": entry["total"],
                    "opening_balance": entry["opening_balance"],
                    "closing_balance": entry["closing_balance"],
                    "is_moratorium": entry.get("is_moratorium", False),
                }
            )
            total_principal += entry["principal"]
            total_interest += entry["interest"]

        # Pull a representative EMI: first non-moratorium row's total.
        emi_amount = next(
            (r["total_amount"] for r in rows if not r["is_moratorium"]),
            Decimal("0"),
        )
        last_due_date = rows[-1]["due_date"] if rows else disbursement_date

        return {
            "entries": rows,
            "summary": {
                "total_installments": len(rows),
                "total_principal": total_principal.quantize(Decimal("0.01"), ROUND_HALF_UP),
                "total_interest": total_interest.quantize(Decimal("0.01"), ROUND_HALF_UP),
                "total_amount": (total_principal + total_interest).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                ),
                "emi_amount": emi_amount,
                "last_due_date": last_due_date,
            },
        }

    async def calculate_emi(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        tenure_months: int,
    ) -> dict[str, Decimal]:
        """
        Calculate EMI amount and other details.

        Returns:
            Dictionary with emi, total_interest, total_payment
        """
        monthly_rate = annual_rate / Decimal("1200")

        if monthly_rate > 0:
            r = float(monthly_rate)
            n = tenure_months
            p = float(principal)
            emi = p * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
            emi = Decimal(str(emi)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        else:
            emi = (principal / Decimal(tenure_months)).quantize(Decimal("0.01"), ROUND_HALF_UP)

        total_payment = emi * Decimal(tenure_months)
        total_interest = total_payment - principal

        return {
            "emi": emi,
            "total_interest": total_interest.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "total_payment": total_payment.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
        }

    async def reschedule_loan(
        self,
        loan_account_id: UUID,
        new_tenure: int | None = None,
        new_rate: Decimal | None = None,
        new_emi: Decimal | None = None,
        effective_date: date | None = None,
        reason: str = "",
        user_id: UUID | None = None,
    ) -> list[LoanSchedule]:
        """
        Reschedule a loan with new terms.

        Args:
            loan_account_id: Loan account ID
            new_tenure: New tenure in months (remaining)
            new_rate: New interest rate
            new_emi: New EMI amount (if specifying EMI instead of tenure)
            effective_date: Date from which new schedule applies
            reason: Reason for rescheduling
            user_id: User performing the action

        Returns:
            New schedule entries
        """
        # Get loan account
        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        if effective_date is None:
            effective_date = date.today()

        # Get current outstanding
        outstanding = loan.principal_outstanding

        # Determine new terms
        rate = new_rate if new_rate is not None else loan.interest_rate
        tenure = new_tenure if new_tenure is not None else loan.remaining_tenure

        # If EMI specified, calculate required tenure
        if new_emi and new_emi > 0:
            # Calculate tenure needed for given EMI
            monthly_rate = rate / Decimal("1200")
            if monthly_rate > 0:
                r = float(monthly_rate)
                p = float(outstanding)
                emi = float(new_emi)
                # n = -log(1 - P*r/EMI) / log(1+r)
                if emi > p * r:
                    n = -math.log(1 - p * r / emi) / math.log(1 + r)
                    tenure = int(math.ceil(n))

        # Generate new schedule
        return await self.generate_schedule(
            loan_account_id=loan_account_id,
            principal=outstanding,
            interest_rate=rate,
            tenure_months=tenure,
            disbursement_date=effective_date,
            emi_day=loan.emi_day or 1,
            calculation_method=loan.calculation_method or "reducing_balance",
            user_id=user_id,
        )

    async def get_schedule(
        self,
        loan_account_id: UUID,
        include_paid: bool = True,
    ) -> list[LoanSchedule]:
        """Get loan schedule entries."""
        conditions = [LoanSchedule.loan_account_id == loan_account_id]

        if not include_paid:
            conditions.append(LoanSchedule.is_paid == False)

        result = await self.db.execute(
            select(LoanSchedule).where(and_(*conditions)).order_by(LoanSchedule.installment_number)
        )
        return list(result.scalars().all())

    async def get_overdue_installments(
        self,
        loan_account_id: UUID,
        as_of_date: date | None = None,
    ) -> list[LoanSchedule]:
        """Get overdue installments for a loan."""
        if as_of_date is None:
            as_of_date = date.today()

        result = await self.db.execute(
            select(LoanSchedule)
            .where(
                LoanSchedule.loan_account_id == loan_account_id,
                LoanSchedule.due_date < as_of_date,
                LoanSchedule.is_paid == False,
            )
            .order_by(LoanSchedule.due_date)
        )
        return list(result.scalars().all())

    async def mark_installment_paid(
        self,
        schedule_id: UUID,
        payment_date: date,
        principal_paid: Decimal,
        interest_paid: Decimal,
        receipt_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> LoanSchedule:
        """Mark an installment as paid (fully or partially)."""
        result = await self.db.execute(select(LoanSchedule).where(LoanSchedule.id == schedule_id))
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError(f"Schedule entry {schedule_id} not found")

        schedule.principal_paid = principal_paid
        schedule.interest_paid = interest_paid
        schedule.payment_date = payment_date
        schedule.receipt_id = receipt_id
        schedule.is_paid = (
            principal_paid >= schedule.principal_amount
            and interest_paid >= schedule.interest_amount
        )
        schedule.is_partial = (principal_paid > 0 or interest_paid > 0) and not schedule.is_paid
        schedule.updated_by = user_id

        await self.db.flush()
        await self.db.refresh(schedule)

        return schedule
