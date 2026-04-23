"""Loan Receipt Processing Service."""

import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending import (
    LoanAccount,
    LoanSchedule,
    LoanReceipt,
    ReceiptAllocation,
)

logger = logging.getLogger(__name__)


class ReceiptService:
    """Service for processing loan receipts and allocations."""

    def __init__(self, db: AsyncSession):
        """Initialize receipt service."""
        self.db = db

    async def create_receipt(
        self,
        loan_account_id: UUID,
        amount: Decimal,
        receipt_date: date,
        payment_mode: str,
        reference_number: Optional[str] = None,
        bank_name: Optional[str] = None,
        instrument_number: Optional[str] = None,
        instrument_date: Optional[date] = None,
        remarks: Optional[str] = None,
        auto_allocate: bool = True,
        user_id: Optional[UUID] = None,
    ) -> LoanReceipt:
        """
        Create a new loan receipt.

        Args:
            loan_account_id: Loan account ID
            amount: Receipt amount
            receipt_date: Date of receipt
            payment_mode: cash, cheque, neft, rtgs, upi, nach, etc.
            reference_number: Payment reference
            bank_name: Bank name for cheque/transfer
            instrument_number: Cheque/instrument number
            instrument_date: Cheque/instrument date
            remarks: Additional remarks
            auto_allocate: Whether to auto-allocate to dues
            user_id: User creating the receipt

        Returns:
            Created receipt
        """
        # Get loan account
        result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == loan_account_id)
        )
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        # Generate receipt number
        receipt_number = await self._generate_receipt_number(loan.organization_id)

        # Create receipt
        receipt = LoanReceipt(
            organization_id=loan.organization_id,
            loan_account_id=loan_account_id,
            receipt_number=receipt_number,
            receipt_date=receipt_date,
            amount=amount,
            payment_mode=payment_mode,
            reference_number=reference_number,
            bank_name=bank_name,
            instrument_number=instrument_number,
            instrument_date=instrument_date,
            remarks=remarks,
            status="pending" if payment_mode == "cheque" else "received",
            unallocated_amount=amount,
            created_by=user_id,
        )
        self.db.add(receipt)
        await self.db.flush()

        # Auto-allocate if requested and payment is not cheque (which needs clearance)
        if auto_allocate and payment_mode != "cheque":
            await self.allocate_receipt(
                receipt_id=receipt.id,
                allocation_method="fifo",
                user_id=user_id,
            )

        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    async def _generate_receipt_number(self, organization_id: UUID) -> str:
        """Generate unique receipt number."""
        today = date.today().strftime("%Y%m%d")
        result = await self.db.execute(
            select(func.count())
            .select_from(LoanReceipt)
            .where(
                LoanReceipt.organization_id == organization_id,
                LoanReceipt.receipt_number.like(f"RCP-{today}%"),
            )
        )
        count = result.scalar() or 0
        return f"RCP-{today}-{(count + 1):04d}"

    async def allocate_receipt(
        self,
        receipt_id: UUID,
        allocation_method: str = "fifo",
        specific_allocations: Optional[List[Dict]] = None,
        user_id: Optional[UUID] = None,
    ) -> List[ReceiptAllocation]:
        """
        Allocate receipt amount to loan dues.

        Args:
            receipt_id: Receipt ID
            allocation_method: fifo (oldest first), lifo, proportional, specific
            specific_allocations: List of specific allocations for 'specific' method
            user_id: User performing allocation

        Returns:
            List of allocation records
        """
        # Get receipt
        result = await self.db.execute(
            select(LoanReceipt).where(LoanReceipt.id == receipt_id)
        )
        receipt = result.scalar_one_or_none()
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if receipt.unallocated_amount <= 0:
            logger.info(f"Receipt {receipt_id} has no unallocated amount")
            return []

        # Get loan account
        result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == receipt.loan_account_id)
        )
        loan = result.scalar_one_or_none()

        allocations = []
        available = receipt.unallocated_amount

        if allocation_method == "specific" and specific_allocations:
            allocations = await self._allocate_specific(
                receipt, specific_allocations, user_id
            )
        elif allocation_method == "fifo":
            allocations = await self._allocate_fifo(receipt, user_id)
        elif allocation_method == "proportional":
            allocations = await self._allocate_proportional(receipt, user_id)
        else:
            # Default to FIFO
            allocations = await self._allocate_fifo(receipt, user_id)

        # Update loan account balances
        await self._update_loan_balances(receipt.loan_account_id)

        await self.db.commit()

        return allocations

    async def _allocate_fifo(
        self,
        receipt: LoanReceipt,
        user_id: Optional[UUID] = None,
    ) -> List[ReceiptAllocation]:
        """Allocate using FIFO (oldest dues first)."""
        # Get unpaid/partial schedules ordered by due date
        result = await self.db.execute(
            select(LoanSchedule)
            .where(
                LoanSchedule.loan_account_id == receipt.loan_account_id,
                LoanSchedule.is_paid == False,
            )
            .order_by(LoanSchedule.due_date)
        )
        schedules = list(result.scalars().all())

        allocations = []
        available = receipt.unallocated_amount

        for schedule in schedules:
            if available <= 0:
                break

            # Calculate outstanding for this schedule
            interest_due = schedule.interest_amount - (schedule.interest_paid or Decimal("0"))
            principal_due = schedule.principal_amount - (schedule.principal_paid or Decimal("0"))
            total_due = interest_due + principal_due

            if total_due <= 0:
                continue

            # Allocate (interest first, then principal - standard allocation order)
            interest_allocation = min(interest_due, available)
            available -= interest_allocation

            principal_allocation = min(principal_due, available)
            available -= principal_allocation

            if interest_allocation > 0 or principal_allocation > 0:
                allocation = ReceiptAllocation(
                    receipt_id=receipt.id,
                    schedule_id=schedule.id,
                    loan_account_id=receipt.loan_account_id,
                    allocation_date=receipt.receipt_date,
                    principal_allocated=principal_allocation,
                    interest_allocated=interest_allocation,
                    total_allocated=principal_allocation + interest_allocation,
                    created_by=user_id,
                )
                self.db.add(allocation)
                allocations.append(allocation)

                # Update schedule
                schedule.principal_paid = (schedule.principal_paid or Decimal("0")) + principal_allocation
                schedule.interest_paid = (schedule.interest_paid or Decimal("0")) + interest_allocation
                schedule.is_paid = (
                    schedule.principal_paid >= schedule.principal_amount and
                    schedule.interest_paid >= schedule.interest_amount
                )
                schedule.is_partial = not schedule.is_paid and (
                    schedule.principal_paid > 0 or schedule.interest_paid > 0
                )
                if schedule.is_paid:
                    schedule.payment_date = receipt.receipt_date
                    schedule.receipt_id = receipt.id

        # Update receipt
        total_allocated = sum(a.total_allocated for a in allocations)
        receipt.allocated_amount = (receipt.allocated_amount or Decimal("0")) + total_allocated
        receipt.unallocated_amount = receipt.amount - receipt.allocated_amount

        return allocations

    async def _allocate_proportional(
        self,
        receipt: LoanReceipt,
        user_id: Optional[UUID] = None,
    ) -> List[ReceiptAllocation]:
        """Allocate proportionally across all outstanding EMIs."""
        # Get unpaid schedules
        result = await self.db.execute(
            select(LoanSchedule)
            .where(
                LoanSchedule.loan_account_id == receipt.loan_account_id,
                LoanSchedule.is_paid == False,
            )
            .order_by(LoanSchedule.due_date)
        )
        schedules = list(result.scalars().all())

        # Calculate total outstanding
        total_outstanding = Decimal("0")
        for schedule in schedules:
            interest_due = schedule.interest_amount - (schedule.interest_paid or Decimal("0"))
            principal_due = schedule.principal_amount - (schedule.principal_paid or Decimal("0"))
            total_outstanding += interest_due + principal_due

        if total_outstanding <= 0:
            return []

        allocations = []
        available = receipt.unallocated_amount
        remaining = available

        for i, schedule in enumerate(schedules):
            interest_due = schedule.interest_amount - (schedule.interest_paid or Decimal("0"))
            principal_due = schedule.principal_amount - (schedule.principal_paid or Decimal("0"))
            schedule_total = interest_due + principal_due

            if schedule_total <= 0:
                continue

            # Calculate proportional share
            if i == len(schedules) - 1:
                # Last schedule gets remaining to avoid rounding issues
                share = remaining
            else:
                share = (available * schedule_total / total_outstanding).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
                share = min(share, remaining)

            # Allocate proportionally to interest and principal
            if schedule_total > 0:
                interest_share = (share * interest_due / schedule_total).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
                principal_share = share - interest_share
            else:
                interest_share = Decimal("0")
                principal_share = share

            # Cap at actual dues
            interest_allocation = min(interest_share, interest_due)
            principal_allocation = min(principal_share, principal_due)

            remaining -= (interest_allocation + principal_allocation)

            if interest_allocation > 0 or principal_allocation > 0:
                allocation = ReceiptAllocation(
                    receipt_id=receipt.id,
                    schedule_id=schedule.id,
                    loan_account_id=receipt.loan_account_id,
                    allocation_date=receipt.receipt_date,
                    principal_allocated=principal_allocation,
                    interest_allocated=interest_allocation,
                    total_allocated=principal_allocation + interest_allocation,
                    created_by=user_id,
                )
                self.db.add(allocation)
                allocations.append(allocation)

                # Update schedule
                schedule.principal_paid = (schedule.principal_paid or Decimal("0")) + principal_allocation
                schedule.interest_paid = (schedule.interest_paid or Decimal("0")) + interest_allocation
                schedule.is_paid = (
                    schedule.principal_paid >= schedule.principal_amount and
                    schedule.interest_paid >= schedule.interest_amount
                )
                schedule.is_partial = not schedule.is_paid

        # Update receipt
        total_allocated = sum(a.total_allocated for a in allocations)
        receipt.allocated_amount = (receipt.allocated_amount or Decimal("0")) + total_allocated
        receipt.unallocated_amount = receipt.amount - receipt.allocated_amount

        return allocations

    async def _allocate_specific(
        self,
        receipt: LoanReceipt,
        specific_allocations: List[Dict],
        user_id: Optional[UUID] = None,
    ) -> List[ReceiptAllocation]:
        """Allocate to specific schedules as specified."""
        allocations = []
        available = receipt.unallocated_amount

        for alloc_spec in specific_allocations:
            schedule_id = alloc_spec.get("schedule_id")
            principal = Decimal(str(alloc_spec.get("principal", 0)))
            interest = Decimal(str(alloc_spec.get("interest", 0)))
            total = principal + interest

            if total <= 0 or total > available:
                continue

            # Get schedule
            result = await self.db.execute(
                select(LoanSchedule).where(LoanSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()
            if not schedule:
                continue

            # Validate amounts
            interest_due = schedule.interest_amount - (schedule.interest_paid or Decimal("0"))
            principal_due = schedule.principal_amount - (schedule.principal_paid or Decimal("0"))

            interest = min(interest, interest_due)
            principal = min(principal, principal_due)

            allocation = ReceiptAllocation(
                receipt_id=receipt.id,
                schedule_id=schedule.id,
                loan_account_id=receipt.loan_account_id,
                allocation_date=receipt.receipt_date,
                principal_allocated=principal,
                interest_allocated=interest,
                total_allocated=principal + interest,
                created_by=user_id,
            )
            self.db.add(allocation)
            allocations.append(allocation)

            # Update schedule
            schedule.principal_paid = (schedule.principal_paid or Decimal("0")) + principal
            schedule.interest_paid = (schedule.interest_paid or Decimal("0")) + interest
            schedule.is_paid = (
                schedule.principal_paid >= schedule.principal_amount and
                schedule.interest_paid >= schedule.interest_amount
            )
            schedule.is_partial = not schedule.is_paid

            available -= (principal + interest)

        # Update receipt
        total_allocated = sum(a.total_allocated for a in allocations)
        receipt.allocated_amount = (receipt.allocated_amount or Decimal("0")) + total_allocated
        receipt.unallocated_amount = receipt.amount - receipt.allocated_amount

        return allocations

    async def _update_loan_balances(self, loan_account_id: UUID) -> None:
        """Update loan account outstanding balances based on schedule."""
        # Sum paid amounts
        result = await self.db.execute(
            select(
                func.sum(LoanSchedule.principal_paid).label("principal_paid"),
                func.sum(LoanSchedule.interest_paid).label("interest_paid"),
            )
            .where(LoanSchedule.loan_account_id == loan_account_id)
        )
        row = result.one()
        total_principal_paid = row.principal_paid or Decimal("0")
        total_interest_paid = row.interest_paid or Decimal("0")

        # Get loan account
        result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == loan_account_id)
        )
        loan = result.scalar_one()

        # Update outstanding
        loan.principal_outstanding = loan.sanctioned_amount - total_principal_paid
        loan.interest_outstanding = loan.total_interest - total_interest_paid
        loan.total_amount_paid = total_principal_paid + total_interest_paid

        # Update status if fully paid
        if loan.principal_outstanding <= 0 and loan.interest_outstanding <= 0:
            loan.status = "closed"
            loan.closure_date = date.today()

    async def reverse_receipt(
        self,
        receipt_id: UUID,
        reason: str,
        user_id: Optional[UUID] = None,
    ) -> LoanReceipt:
        """
        Reverse a receipt (e.g., cheque bounce).

        Args:
            receipt_id: Receipt ID
            reason: Reason for reversal
            user_id: User performing reversal

        Returns:
            Updated receipt
        """
        # Get receipt with allocations
        result = await self.db.execute(
            select(LoanReceipt).where(LoanReceipt.id == receipt_id)
        )
        receipt = result.scalar_one_or_none()
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if receipt.status == "reversed":
            raise ValueError("Receipt is already reversed")

        # Get allocations
        result = await self.db.execute(
            select(ReceiptAllocation).where(
                ReceiptAllocation.receipt_id == receipt_id
            )
        )
        allocations = list(result.scalars().all())

        # Reverse allocations
        for allocation in allocations:
            # Get schedule
            result = await self.db.execute(
                select(LoanSchedule).where(LoanSchedule.id == allocation.schedule_id)
            )
            schedule = result.scalar_one_or_none()
            if schedule:
                schedule.principal_paid = (schedule.principal_paid or Decimal("0")) - allocation.principal_allocated
                schedule.interest_paid = (schedule.interest_paid or Decimal("0")) - allocation.interest_allocated
                schedule.is_paid = False
                schedule.is_partial = schedule.principal_paid > 0 or schedule.interest_paid > 0
                schedule.payment_date = None
                schedule.receipt_id = None

            # Mark allocation as reversed
            allocation.is_reversed = True
            allocation.reversal_date = date.today()
            allocation.reversal_reason = reason

        # Update receipt
        receipt.status = "reversed"
        receipt.reversal_date = date.today()
        receipt.reversal_reason = reason
        receipt.allocated_amount = Decimal("0")
        receipt.unallocated_amount = Decimal("0")
        receipt.updated_by = user_id

        # Update loan balances
        await self._update_loan_balances(receipt.loan_account_id)

        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    async def process_bulk_receipts(
        self,
        receipts_data: List[Dict],
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Process multiple receipts in bulk (e.g., from NACH response).

        Args:
            receipts_data: List of receipt data dictionaries
            user_id: User processing the receipts

        Returns:
            Summary of processing results
        """
        summary = {
            "total": len(receipts_data),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for data in receipts_data:
            try:
                await self.create_receipt(
                    loan_account_id=UUID(data["loan_account_id"]),
                    amount=Decimal(str(data["amount"])),
                    receipt_date=data.get("receipt_date", date.today()),
                    payment_mode=data.get("payment_mode", "nach"),
                    reference_number=data.get("reference_number"),
                    remarks=data.get("remarks"),
                    auto_allocate=data.get("auto_allocate", True),
                    user_id=user_id,
                )
                summary["successful"] += 1
            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append({
                    "loan_account_id": data.get("loan_account_id"),
                    "error": str(e),
                })

        return summary

    async def get_receipt_history(
        self,
        loan_account_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[LoanReceipt]:
        """Get receipt history for a loan account."""
        conditions = [LoanReceipt.loan_account_id == loan_account_id]

        if from_date:
            conditions.append(LoanReceipt.receipt_date >= from_date)
        if to_date:
            conditions.append(LoanReceipt.receipt_date <= to_date)

        result = await self.db.execute(
            select(LoanReceipt)
            .where(and_(*conditions))
            .order_by(LoanReceipt.receipt_date.desc())
        )
        return list(result.scalars().all())

    async def get_allocation_details(
        self,
        receipt_id: UUID,
    ) -> List[ReceiptAllocation]:
        """Get allocation details for a receipt."""
        result = await self.db.execute(
            select(ReceiptAllocation)
            .where(ReceiptAllocation.receipt_id == receipt_id)
            .order_by(ReceiptAllocation.allocation_date)
        )
        return list(result.scalars().all())
