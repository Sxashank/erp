"""Loan Disbursement Service."""

import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.loan_account import (
    LoanAccount,
    Disbursement,
    LoanAccountStatus,
)
from app.models.lending.enums import DisbursementStatus, DisbursementMode

logger = logging.getLogger(__name__)


class DisbursementService:
    """Service for managing loan disbursements."""

    def __init__(self, db: AsyncSession):
        """Initialize disbursement service."""
        self.db = db

    async def create_disbursement_request(
        self,
        loan_account_id: UUID,
        requested_amount: Decimal,
        beneficiary_name: str,
        beneficiary_account: str,
        beneficiary_ifsc: str,
        disbursement_mode: str = "RTGS",
        scheduled_date: Optional[date] = None,
        purpose: Optional[str] = None,
        beneficiary_bank: Optional[str] = None,
        bank_account_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Disbursement:
        """
        Create a new disbursement request.

        Args:
            loan_account_id: Loan account ID
            requested_amount: Amount to disburse
            beneficiary_name: Beneficiary name
            beneficiary_account: Beneficiary account number
            beneficiary_ifsc: Beneficiary IFSC code
            disbursement_mode: Mode of disbursement
            scheduled_date: Scheduled disbursement date
            purpose: Purpose of disbursement
            beneficiary_bank: Beneficiary bank name
            bank_account_id: Entity bank account reference
            milestone_id: Project milestone reference
            user_id: User creating request

        Returns:
            Created Disbursement object
        """
        # Get loan account
        result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == loan_account_id)
        )
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        # Validate amount
        if requested_amount > loan.undisbursed_amount:
            raise ValueError(
                f"Requested amount {requested_amount} exceeds undisbursed amount {loan.undisbursed_amount}"
            )

        # Get next disbursement number
        num_result = await self.db.execute(
            select(func.coalesce(func.max(Disbursement.disbursement_number), 0))
            .where(Disbursement.loan_account_id == loan_account_id)
        )
        next_number = num_result.scalar() + 1

        # Generate disbursement reference
        disbursement_ref = f"{loan.loan_account_number}/D{next_number:03d}"

        disbursement = Disbursement(
            loan_account_id=loan_account_id,
            disbursement_number=next_number,
            disbursement_reference=disbursement_ref,
            requested_amount=requested_amount,
            request_date=date.today(),
            scheduled_date=scheduled_date,
            disbursement_mode=DisbursementMode[disbursement_mode],
            beneficiary_name=beneficiary_name,
            beneficiary_account_number=beneficiary_account,
            beneficiary_ifsc=beneficiary_ifsc,
            beneficiary_bank=beneficiary_bank,
            bank_account_id=bank_account_id,
            purpose=purpose,
            milestone_id=milestone_id,
            status=DisbursementStatus.PENDING,
            created_by=user_id,
        )

        self.db.add(disbursement)
        await self.db.commit()
        await self.db.refresh(disbursement)

        return disbursement

    async def verify_conditions(
        self,
        disbursement_id: UUID,
        verification_notes: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> Disbursement:
        """
        Verify pre-disbursement conditions.

        Args:
            disbursement_id: Disbursement ID
            verification_notes: Notes on verification
            user_id: User verifying conditions

        Returns:
            Updated Disbursement
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status != DisbursementStatus.PENDING:
            raise ValueError(f"Cannot verify conditions for disbursement in {disbursement.status} status")

        disbursement.conditions_verified = True
        disbursement.conditions_verified_by = user_id
        disbursement.conditions_verified_at = datetime.utcnow()
        disbursement.remarks = verification_notes

        await self.db.commit()
        await self.db.refresh(disbursement)

        return disbursement

    async def approve_disbursement(
        self,
        disbursement_id: UUID,
        approved_amount: Optional[Decimal] = None,
        remarks: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> Disbursement:
        """
        Approve a disbursement request.

        Args:
            disbursement_id: Disbursement ID
            approved_amount: Approved amount (defaults to requested)
            remarks: Approval remarks
            user_id: User approving

        Returns:
            Updated Disbursement
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status != DisbursementStatus.PENDING:
            raise ValueError(f"Cannot approve disbursement in {disbursement.status} status")

        if not disbursement.conditions_verified:
            raise ValueError("Pre-disbursement conditions must be verified before approval")

        # Set approved amount
        approved = approved_amount if approved_amount else disbursement.requested_amount

        # Validate approved amount
        loan_result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == disbursement.loan_account_id)
        )
        loan = loan_result.scalar_one_or_none()

        if approved > loan.undisbursed_amount:
            raise ValueError(
                f"Approved amount {approved} exceeds undisbursed amount {loan.undisbursed_amount}"
            )

        disbursement.approved_amount = approved
        disbursement.approval_date = date.today()
        disbursement.approved_by_id = user_id
        disbursement.approved_at = datetime.utcnow()
        disbursement.status = DisbursementStatus.APPROVED
        if remarks:
            disbursement.remarks = remarks

        await self.db.commit()
        await self.db.refresh(disbursement)

        return disbursement

    async def reject_disbursement(
        self,
        disbursement_id: UUID,
        rejection_reason: str,
        user_id: Optional[UUID] = None,
    ) -> Disbursement:
        """
        Reject a disbursement request.

        Args:
            disbursement_id: Disbursement ID
            rejection_reason: Reason for rejection
            user_id: User rejecting

        Returns:
            Updated Disbursement
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status not in [DisbursementStatus.PENDING, DisbursementStatus.APPROVED]:
            raise ValueError(f"Cannot reject disbursement in {disbursement.status} status")

        disbursement.status = DisbursementStatus.REJECTED
        disbursement.rejection_reason = rejection_reason
        disbursement.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(disbursement)

        return disbursement

    async def process_disbursement(
        self,
        disbursement_id: UUID,
        disbursed_amount: Decimal,
        disbursement_date: Optional[date] = None,
        value_date: Optional[date] = None,
        utr_number: Optional[str] = None,
        cheque_number: Optional[str] = None,
        disbursement_charges: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Tuple[Disbursement, LoanAccount]:
        """
        Process an approved disbursement.

        Args:
            disbursement_id: Disbursement ID
            disbursed_amount: Actual amount disbursed
            disbursement_date: Date of disbursement
            value_date: Value date for interest
            utr_number: UTR/Transaction reference
            cheque_number: Cheque number if applicable
            disbursement_charges: Charges deducted
            user_id: User processing

        Returns:
            Tuple of updated Disbursement and LoanAccount
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status != DisbursementStatus.APPROVED:
            raise ValueError(f"Cannot process disbursement in {disbursement.status} status")

        # Get loan account
        loan_result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == disbursement.loan_account_id)
        )
        loan = loan_result.scalar_one_or_none()

        # Validate disbursement
        if disbursed_amount > disbursement.approved_amount:
            raise ValueError(
                f"Disbursed amount {disbursed_amount} exceeds approved amount {disbursement.approved_amount}"
            )

        actual_date = disbursement_date or date.today()
        actual_value_date = value_date or actual_date

        # Update disbursement
        disbursement.disbursed_amount = disbursed_amount
        disbursement.disbursement_charges = disbursement_charges
        disbursement.net_disbursement = disbursed_amount - disbursement_charges
        disbursement.disbursement_date = actual_date
        disbursement.value_date = actual_value_date
        disbursement.utr_number = utr_number
        disbursement.cheque_number = cheque_number
        disbursement.status = DisbursementStatus.DISBURSED
        disbursement.processed_by_id = user_id
        disbursement.processed_at = datetime.utcnow()

        # Update loan account
        loan.total_disbursed_amount += disbursed_amount
        loan.undisbursed_amount = loan.sanctioned_amount - loan.total_disbursed_amount
        loan.principal_outstanding += disbursed_amount
        loan.total_outstanding = (
            loan.principal_outstanding + loan.interest_outstanding +
            loan.interest_overdue + loan.principal_overdue +
            loan.penal_interest_outstanding + loan.charges_outstanding
        )

        # Update dates if first disbursement
        if loan.first_disbursement_date is None:
            loan.first_disbursement_date = actual_date
            loan.status = LoanAccountStatus.ACTIVE

        loan.last_disbursement_date = actual_date

        # Check if fully disbursed
        if loan.undisbursed_amount <= Decimal("0"):
            loan.status = LoanAccountStatus.FULLY_DISBURSED

        await self.db.commit()
        await self.db.refresh(disbursement)
        await self.db.refresh(loan)

        return disbursement, loan

    async def cancel_disbursement(
        self,
        disbursement_id: UUID,
        cancellation_reason: str,
        user_id: Optional[UUID] = None,
    ) -> Disbursement:
        """
        Cancel a pending or approved disbursement.

        Args:
            disbursement_id: Disbursement ID
            cancellation_reason: Reason for cancellation
            user_id: User cancelling

        Returns:
            Updated Disbursement
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status not in [DisbursementStatus.PENDING, DisbursementStatus.APPROVED]:
            raise ValueError(f"Cannot cancel disbursement in {disbursement.status} status")

        disbursement.status = DisbursementStatus.CANCELLED
        disbursement.rejection_reason = cancellation_reason
        disbursement.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(disbursement)

        return disbursement

    async def reverse_disbursement(
        self,
        disbursement_id: UUID,
        reversal_reason: str,
        reversal_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
    ) -> Tuple[Disbursement, LoanAccount]:
        """
        Reverse a completed disbursement.

        Args:
            disbursement_id: Disbursement ID
            reversal_reason: Reason for reversal
            reversal_date: Date of reversal
            user_id: User reversing

        Returns:
            Tuple of updated Disbursement and LoanAccount
        """
        result = await self.db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )
        disbursement = result.scalar_one_or_none()
        if not disbursement:
            raise ValueError(f"Disbursement {disbursement_id} not found")

        if disbursement.status != DisbursementStatus.DISBURSED:
            raise ValueError(f"Cannot reverse disbursement in {disbursement.status} status")

        # Get loan account
        loan_result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == disbursement.loan_account_id)
        )
        loan = loan_result.scalar_one_or_none()

        # Validate reversal
        if loan.principal_outstanding < disbursement.disbursed_amount:
            raise ValueError(
                f"Cannot reverse - principal outstanding {loan.principal_outstanding} is less than "
                f"disbursed amount {disbursement.disbursed_amount}"
            )

        # Update disbursement
        disbursement.status = DisbursementStatus.REVERSED
        disbursement.rejection_reason = reversal_reason
        disbursement.updated_by = user_id

        # Update loan account
        loan.total_disbursed_amount -= disbursement.disbursed_amount
        loan.undisbursed_amount = loan.sanctioned_amount - loan.total_disbursed_amount
        loan.principal_outstanding -= disbursement.disbursed_amount
        loan.total_outstanding = (
            loan.principal_outstanding + loan.interest_outstanding +
            loan.interest_overdue + loan.principal_overdue +
            loan.penal_interest_outstanding + loan.charges_outstanding
        )

        # Update status if needed
        if loan.total_disbursed_amount <= Decimal("0"):
            loan.status = LoanAccountStatus.CREATED
            loan.first_disbursement_date = None
            loan.last_disbursement_date = None

        await self.db.commit()
        await self.db.refresh(disbursement)
        await self.db.refresh(loan)

        return disbursement, loan

    async def get_disbursements(
        self,
        loan_account_id: UUID,
        status: Optional[str] = None,
    ) -> List[Disbursement]:
        """
        Get disbursements for a loan account.

        Args:
            loan_account_id: Loan account ID
            status: Filter by status

        Returns:
            List of disbursements
        """
        conditions = [Disbursement.loan_account_id == loan_account_id]
        if status:
            conditions.append(Disbursement.status == DisbursementStatus[status])

        result = await self.db.execute(
            select(Disbursement)
            .where(and_(*conditions))
            .order_by(Disbursement.disbursement_number)
        )
        return list(result.scalars().all())

    async def get_pending_disbursements(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pending disbursements for organization.

        Args:
            organization_id: Organization ID
            status: Filter by specific status

        Returns:
            List of pending disbursements with loan details
        """
        statuses = [DisbursementStatus.PENDING, DisbursementStatus.APPROVED]
        if status:
            statuses = [DisbursementStatus[status]]

        result = await self.db.execute(
            select(Disbursement, LoanAccount)
            .join(LoanAccount, Disbursement.loan_account_id == LoanAccount.id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.status.in_(statuses),
            )
            .order_by(Disbursement.request_date)
        )

        disbursements = []
        for disb, loan in result.all():
            disbursements.append({
                "disbursement_id": str(disb.id),
                "disbursement_reference": disb.disbursement_reference,
                "loan_account_number": loan.loan_account_number,
                "loan_account_id": str(loan.id),
                "entity_id": str(loan.entity_id),
                "requested_amount": disb.requested_amount,
                "approved_amount": disb.approved_amount,
                "request_date": disb.request_date,
                "scheduled_date": disb.scheduled_date,
                "status": disb.status.name,
                "conditions_verified": disb.conditions_verified,
                "beneficiary_name": disb.beneficiary_name,
                "disbursement_mode": disb.disbursement_mode.name,
            })

        return disbursements

    async def get_disbursement_summary(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get disbursement summary for organization.

        Args:
            organization_id: Organization ID
            from_date: Start date
            to_date: End date

        Returns:
            Disbursement summary statistics
        """
        if to_date is None:
            to_date = date.today()
        if from_date is None:
            from_date = date(to_date.year, to_date.month, 1)

        # Get all disbursements for period
        result = await self.db.execute(
            select(Disbursement, LoanAccount)
            .join(LoanAccount, Disbursement.loan_account_id == LoanAccount.id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.disbursement_date >= from_date,
                Disbursement.disbursement_date <= to_date,
                Disbursement.status == DisbursementStatus.DISBURSED,
            )
        )

        total_count = 0
        total_amount = Decimal("0")
        by_mode = {}

        for disb, loan in result.all():
            total_count += 1
            total_amount += disb.disbursed_amount

            mode = disb.disbursement_mode.name
            if mode not in by_mode:
                by_mode[mode] = {"count": 0, "amount": Decimal("0")}
            by_mode[mode]["count"] += 1
            by_mode[mode]["amount"] += disb.disbursed_amount

        # Get pending counts
        pending_result = await self.db.execute(
            select(func.count(Disbursement.id))
            .join(LoanAccount, Disbursement.loan_account_id == LoanAccount.id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.status == DisbursementStatus.PENDING,
            )
        )
        pending_count = pending_result.scalar() or 0

        approved_result = await self.db.execute(
            select(func.count(Disbursement.id), func.sum(Disbursement.approved_amount))
            .join(LoanAccount, Disbursement.loan_account_id == LoanAccount.id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.status == DisbursementStatus.APPROVED,
            )
        )
        approved_data = approved_result.one()
        approved_count = approved_data[0] or 0
        approved_amount = approved_data[1] or Decimal("0")

        return {
            "from_date": from_date,
            "to_date": to_date,
            "disbursed": {
                "count": total_count,
                "amount": total_amount,
            },
            "by_mode": by_mode,
            "pending_count": pending_count,
            "approved": {
                "count": approved_count,
                "amount": approved_amount,
            },
        }

    async def create_tranche_disbursement(
        self,
        loan_account_id: UUID,
        tranche_data: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
    ) -> List[Disbursement]:
        """
        Create multiple tranche disbursements.

        Args:
            loan_account_id: Loan account ID
            tranche_data: List of tranche details
            user_id: User creating tranches

        Returns:
            List of created disbursements
        """
        disbursements = []

        for tranche in tranche_data:
            disb = await self.create_disbursement_request(
                loan_account_id=loan_account_id,
                requested_amount=tranche["amount"],
                beneficiary_name=tranche["beneficiary_name"],
                beneficiary_account=tranche["beneficiary_account"],
                beneficiary_ifsc=tranche["beneficiary_ifsc"],
                disbursement_mode=tranche.get("mode", "RTGS"),
                scheduled_date=tranche.get("scheduled_date"),
                purpose=tranche.get("purpose"),
                beneficiary_bank=tranche.get("beneficiary_bank"),
                milestone_id=tranche.get("milestone_id"),
                user_id=user_id,
            )
            disbursements.append(disb)

        return disbursements
