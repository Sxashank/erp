"""Loan Disbursement Service."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import GLEntrySourceType
from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.models.lending.enums import DisbursementMode, DisbursementStatus
from app.models.lending.loan_account import (
    Disbursement,
    LoanAccount,
    LoanAccountStatus,
)
from app.repositories.finance.financial_year_repo import (
    FinancialPeriodRepository,
    FinancialYearRepository,
)
from app.services.audit import record_financial_action
from app.services.finance.gl_posting_service import GLPostingService

logger = logging.getLogger(__name__)


class DisbursementService:
    """Service for managing loan disbursements."""

    def __init__(self, db: AsyncSession):
        """Initialize disbursement service."""
        self.db = db
        self.gl_posting_service = GLPostingService(db)
        self.fy_repo = FinancialYearRepository(db)
        self.period_repo = FinancialPeriodRepository(db)

    async def create_disbursement_request(
        self,
        loan_account_id: UUID,
        requested_amount: Decimal,
        beneficiary_name: str,
        beneficiary_account: str,
        beneficiary_ifsc: str,
        disbursement_mode: str = "RTGS",
        scheduled_date: date | None = None,
        purpose: str | None = None,
        beneficiary_bank: str | None = None,
        bank_account_id: UUID | None = None,
        milestone_id: UUID | None = None,
        user_id: UUID | None = None,
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
        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
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
            select(func.coalesce(func.max(Disbursement.disbursement_number), 0)).where(
                Disbursement.loan_account_id == loan_account_id
            )
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
        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def verify_conditions(
        self,
        disbursement_id: UUID,
        verification_notes: str | None = None,
        user_id: UUID | None = None,
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
            raise ValueError(
                f"Cannot verify conditions for disbursement in {disbursement.status} status"
            )

        disbursement.conditions_verified = True
        disbursement.conditions_verified_by = user_id
        disbursement.conditions_verified_at = datetime.utcnow()
        disbursement.remarks = verification_notes

        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def approve_disbursement(
        self,
        disbursement_id: UUID,
        approved_amount: Decimal | None = None,
        remarks: str | None = None,
        user_id: UUID | None = None,
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
        from app.core.maker_checker import ensure_maker_is_not_checker

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

        # §8.4 maker-checker: the operations user who raised the disbursement
        # request cannot also approve it — this is a cash-movement action.
        ensure_maker_is_not_checker(
            maker_user_id=disbursement.created_by,
            checker_user_id=user_id,
        )

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

        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def reject_disbursement(
        self,
        disbursement_id: UUID,
        rejection_reason: str,
        user_id: UUID | None = None,
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

        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def process_disbursement(
        self,
        disbursement_id: UUID,
        disbursed_amount: Decimal,
        disbursement_date: date | None = None,
        value_date: date | None = None,
        utr_number: str | None = None,
        cheque_number: str | None = None,
        disbursement_charges: Decimal = Decimal("0"),
        source_account_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> tuple[Disbursement, LoanAccount]:
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
            source_account_id: SMFC bank/cash GL account used to release funds
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
        resolved_source_account_id = source_account_id or await self._resolve_payment_account(
            organization_id=loan.organization_id,
            allow_flag="allow_payments",
        )

        # Snapshot the disbursement at APPROVED before mutating — feeds the
        # domain audit row (§8.5) so reviewers can see the APPROVED → PROCESSED
        # transition with UTR + processed_date.
        before_snapshot = {
            "status": disbursement.status.value
            if hasattr(disbursement.status, "value")
            else str(disbursement.status),
            "approved_amount": disbursement.approved_amount,
            "disbursed_amount": disbursement.disbursed_amount,
            "disbursement_charges": disbursement.disbursement_charges,
            "net_disbursement": disbursement.net_disbursement,
            "disbursement_date": disbursement.disbursement_date,
            "value_date": disbursement.value_date,
            "utr_number": disbursement.utr_number,
            "cheque_number": disbursement.cheque_number,
        }

        # Update disbursement
        disbursement.disbursed_amount = disbursed_amount
        disbursement.disbursement_charges = disbursement_charges
        disbursement.net_disbursement = disbursed_amount - disbursement_charges
        disbursement.source_account_id = resolved_source_account_id
        disbursement.disbursement_date = actual_date
        disbursement.value_date = actual_value_date
        disbursement.utr_number = utr_number
        disbursement.cheque_number = cheque_number
        disbursement.status = DisbursementStatus.PROCESSED
        disbursement.processed_by_id = user_id
        disbursement.processed_at = datetime.utcnow()

        # Update loan account
        loan.total_disbursed_amount += disbursed_amount
        loan.undisbursed_amount = loan.sanctioned_amount - loan.total_disbursed_amount
        loan.principal_outstanding += disbursed_amount
        loan.total_outstanding = (
            loan.principal_outstanding
            + loan.interest_outstanding
            + loan.interest_overdue
            + loan.principal_overdue
            + loan.penal_interest_outstanding
            + loan.charges_outstanding
        )

        # Update dates if first disbursement
        if loan.first_disbursement_date is None:
            loan.first_disbursement_date = actual_date
            loan.status = LoanAccountStatus.ACTIVE

        loan.last_disbursement_date = actual_date

        # Check if fully disbursed
        if loan.undisbursed_amount <= Decimal("0"):
            loan.status = LoanAccountStatus.ACTIVE

        gl_entries = await self._post_disbursement_to_gl(
            disbursement=disbursement,
            loan=loan,
            source_account_id=resolved_source_account_id,
            posted_by=user_id,
        )
        if gl_entries:
            disbursement.voucher_id = gl_entries[0].voucher_id

        await self.db.flush()
        await self.db.refresh(disbursement)
        await self.db.refresh(loan)

        # Domain audit: disbursement processed — §8.5 / §4.8.
        # Captures the APPROVED → PROCESSED transition with UTR + processed_date.
        if user_id is not None:
            await record_financial_action(
                self.db,
                organization_id=loan.organization_id,
                entity_type="DISBURSEMENT",
                entity_id=disbursement.id,
                entity_reference=disbursement.disbursement_reference,
                action="DISBURSEMENT_PROCESS",
                user_id=user_id,
                before=before_snapshot,
                after={
                    "status": disbursement.status.value
                    if hasattr(disbursement.status, "value")
                    else str(disbursement.status),
                    "approved_amount": disbursement.approved_amount,
                    "disbursed_amount": disbursement.disbursed_amount,
                    "disbursement_charges": disbursement.disbursement_charges,
                    "net_disbursement": disbursement.net_disbursement,
                    "disbursement_date": disbursement.disbursement_date,
                    "value_date": disbursement.value_date,
                    "utr_number": disbursement.utr_number,
                    "cheque_number": disbursement.cheque_number,
                    "processed_at": disbursement.processed_at,
                },
                metadata={
                    "transaction_type": "DISBURSEMENT_PROCESS",
                    "loan_account_id": str(loan.id),
                    "loan_account_number": loan.loan_account_number,
                    "source_account_id": str(resolved_source_account_id),
                    "voucher_id": str(disbursement.voucher_id)
                    if disbursement.voucher_id
                    else None,
                    "gl_entry_count": len(gl_entries) if gl_entries else 0,
                },
                change_reason="Disbursement processed and funds released",
            )

        return disbursement, loan

    async def cancel_disbursement(
        self,
        disbursement_id: UUID,
        cancellation_reason: str,
        user_id: UUID | None = None,
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

        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def reverse_disbursement(
        self,
        disbursement_id: UUID,
        reversal_reason: str,
        reversal_date: date | None = None,
        user_id: UUID | None = None,
    ) -> tuple[Disbursement, LoanAccount]:
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

        if disbursement.status != DisbursementStatus.PROCESSED:
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
            loan.principal_outstanding
            + loan.interest_outstanding
            + loan.interest_overdue
            + loan.principal_overdue
            + loan.penal_interest_outstanding
            + loan.charges_outstanding
        )

        # Update status if needed
        if loan.total_disbursed_amount <= Decimal("0"):
            loan.status = LoanAccountStatus.CREATED
            loan.first_disbursement_date = None
            loan.last_disbursement_date = None

        await self.db.flush()
        await self.db.refresh(disbursement)
        await self.db.refresh(loan)

        return disbursement, loan

    async def _resolve_payment_account(
        self,
        *,
        organization_id: UUID,
        allow_flag: str,
    ) -> UUID:
        """Resolve a configured organization bank ledger account when one is unambiguous."""
        result = await self.db.execute(
            select(OrganizationBankAccount)
            .where(
                OrganizationBankAccount.organization_id == organization_id,
                OrganizationBankAccount.ledger_account_id.is_not(None),
                OrganizationBankAccount.is_active.is_(True),
                getattr(OrganizationBankAccount, allow_flag).is_(True),
            )
            .order_by(OrganizationBankAccount.is_primary.desc(), OrganizationBankAccount.created_at)
        )
        bank_accounts = list(result.scalars().all())
        if len(bank_accounts) == 1:
            return bank_accounts[0].ledger_account_id
        primary_accounts = [account for account in bank_accounts if account.is_primary]
        if len(primary_accounts) == 1:
            return primary_accounts[0].ledger_account_id
        raise ValueError(
            "Select a source GL account; organization bank ledger mapping is not uniquely configured"
        )

    async def _get_financial_context(self, organization_id: UUID, voucher_date: date):
        fy = await self.fy_repo.get_by_date(organization_id, voucher_date)
        if not fy:
            raise ValueError(f"No financial year configured for {voucher_date}")
        period = await self.period_repo.get_by_date(fy.id, voucher_date)
        if not period:
            raise ValueError(f"No financial period configured for {voucher_date}")
        return fy, period

    async def _post_disbursement_to_gl(
        self,
        *,
        disbursement: Disbursement,
        loan: LoanAccount,
        source_account_id: UUID,
        posted_by: UUID | None,
    ):
        if posted_by is None:
            raise ValueError("User is required for GL posting")
        if disbursement.voucher_id:
            return []
        if not loan.loan_asset_account_id:
            raise ValueError("Loan asset GL account is not configured on the loan account")

        disbursement_charges = disbursement.disbursement_charges or Decimal("0")
        if disbursement_charges > 0 and not loan.charges_income_account_id:
            raise ValueError(
                "Charges income GL account is required when disbursement charges are recorded"
            )

        disbursed_amount = disbursement.disbursed_amount or Decimal("0")
        net_disbursement = disbursement.net_disbursement or disbursed_amount
        if disbursed_amount <= 0 or net_disbursement <= 0:
            raise ValueError("Disbursement amount must be positive for GL posting")

        fy, period = await self._get_financial_context(
            loan.organization_id,
            disbursement.disbursement_date or date.today(),
        )
        lines = [
            {
                "account_id": loan.loan_asset_account_id,
                "debit_amount": disbursed_amount,
                "credit_amount": Decimal("0"),
                "narration": f"Loan disbursement {disbursement.disbursement_reference}",
            },
            {
                "account_id": source_account_id,
                "debit_amount": Decimal("0"),
                "credit_amount": net_disbursement,
                "narration": f"Funds released for {loan.loan_account_number}",
            },
        ]
        if disbursement_charges > 0:
            lines.append(
                {
                    "account_id": loan.charges_income_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": disbursement_charges,
                    "narration": f"Disbursement charges {disbursement.disbursement_reference}",
                }
            )

        return await self.gl_posting_service.post_entries(
            organization_id=loan.organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=disbursement.disbursement_date or date.today(),
            source_type=GLEntrySourceType.LOAN_DISBURSEMENT,
            source_id=disbursement.id,
            source_reference=disbursement.disbursement_reference,
            lines=lines,
            narration=f"Loan disbursement: {loan.loan_account_number}",
            posted_by=posted_by,
        )

    async def list_disbursements_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status: DisbursementStatus | None = None,
    ) -> tuple[list[Disbursement], int]:
        """Paginated list of disbursements scoped to the caller's org.

        Eagerly loads the parent loan_account (and its entity) so the
        list response can flatten entity_name + loan_account_number
        without N+1 queries.
        """
        base_query = (
            select(Disbursement)
            .join(LoanAccount, Disbursement.loan_account_id == LoanAccount.id)
            .where(LoanAccount.organization_id == organization_id)
            .options(
                selectinload(Disbursement.loan_account).selectinload(LoanAccount.entity),
            )
        )

        if search:
            term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Disbursement.disbursement_reference.ilike(term),
                    LoanAccount.loan_account_number.ilike(term),
                )
            )
        if status is not None:
            base_query = base_query.where(Disbursement.status == status)

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        result = await self.db.execute(
            base_query.order_by(Disbursement.request_date.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_disbursements(
        self,
        loan_account_id: UUID,
        status: str | None = None,
    ) -> list[Disbursement]:
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
            select(Disbursement).where(and_(*conditions)).order_by(Disbursement.disbursement_number)
        )
        return list(result.scalars().all())

    async def get_pending_disbursements(
        self,
        organization_id: UUID,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
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
            disbursements.append(
                {
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
                }
            )

        return disbursements

    async def get_disbursement_summary(
        self,
        organization_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
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
                Disbursement.status == DisbursementStatus.PROCESSED,
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
        tranche_data: list[dict[str, Any]],
        user_id: UUID | None = None,
    ) -> list[Disbursement]:
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
