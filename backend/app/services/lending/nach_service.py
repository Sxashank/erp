"""NACH service for batch generation and EMI collection."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.nach_batch import NachBatch, NachTransaction, NachMandateLog
from app.models.lending.loan_account import (
    LoanAccount, LoanMandate, ScheduleInstallment, RepaymentSchedule, LoanReceipt
)
from app.models.lending.enums import (
    NachBatchStatus, NachTransactionStatus, NachReturnCode, NachFileFormat,
    MandateStatus, InstallmentStatus, ReceiptMode, ReceiptStatus, ReceiptType,
    LoanAccountStatus
)
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.schemas.lending.nach import (
    NachBatchCreate, NachBatchGenerateRequest, NachBatchResponse,
    NachTransactionResponse, NachBatchStatistics, NachRetryDue, NachRetryDueList,
    NachBatchDetailResponse, NachTransactionSummary, NachBounceAnalysis,
)
from app.integrations.nach import NachClient, NachFileGenerator
from app.integrations.nach.client import NachClientFactory
from app.integrations.nach.schemas import NachReturnCodeMapping

logger = logging.getLogger(__name__)


class NachService:
    """Service for NACH batch management and EMI collection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Batch Generation
    # =========================================================================

    async def generate_batch_from_due_emis(
        self,
        request: NachBatchGenerateRequest,
        created_by_id: Optional[UUID] = None,
    ) -> NachBatch:
        """Generate a NACH batch from due EMIs.

        Args:
            request: Batch generation request
            created_by_id: User creating the batch

        Returns:
            Created NachBatch with transactions
        """
        # Get integration config if specified
        integration_config = None
        if request.integration_config_id:
            integration_config = await self.db.get(IntegrationConfig, request.integration_config_id)

        # Find due installments with active mandates
        query = (
            select(ScheduleInstallment)
            .join(RepaymentSchedule)
            .join(LoanAccount)
            .join(LoanMandate, LoanAccount.id == LoanMandate.loan_account_id)
            .where(
                and_(
                    LoanAccount.organization_id == request.organization_id,
                    LoanAccount.status == LoanAccountStatus.ACTIVE,
                    RepaymentSchedule.is_current == True,
                    ScheduleInstallment.status.in_([
                        InstallmentStatus.DUE,
                        InstallmentStatus.OVERDUE,
                        InstallmentStatus.PARTIALLY_PAID,
                    ]),
                    ScheduleInstallment.due_date <= request.debit_date,
                    LoanMandate.status == MandateStatus.ACTIVE,
                    LoanMandate.umrn.isnot(None),
                    LoanMandate.start_date <= request.debit_date,
                    LoanMandate.end_date >= request.debit_date,
                )
            )
            .options(
                selectinload(ScheduleInstallment.schedule).selectinload(RepaymentSchedule.loan_account)
            )
        )

        # Apply filters
        if request.loan_account_ids:
            query = query.where(LoanAccount.id.in_(request.loan_account_ids))

        if request.product_ids:
            query = query.where(LoanAccount.product_id.in_(request.product_ids))

        if not request.include_overdue:
            query = query.where(ScheduleInstallment.status == InstallmentStatus.DUE)

        if request.max_dpd:
            min_due_date = request.debit_date - timedelta(days=request.max_dpd)
            query = query.where(ScheduleInstallment.due_date >= min_due_date)

        result = await self.db.execute(query)
        installments = result.scalars().all()

        if not installments:
            raise ValueError("No due EMIs found for the given criteria")

        # Generate batch reference
        batch_ref = await self._generate_batch_reference(request.organization_id)

        # Create batch
        batch = NachBatch(
            organization_id=request.organization_id,
            batch_reference=batch_ref,
            batch_date=date.today(),
            debit_date=request.debit_date,
            integration_config_id=request.integration_config_id,
            file_format=NachFileFormat.ACH_DEBIT,
            status=NachBatchStatus.CREATED,
            created_by_id=created_by_id,
        )
        self.db.add(batch)
        await self.db.flush()

        # Create transactions
        total_amount = Decimal("0")
        for installment in installments:
            schedule = installment.schedule
            loan_account = schedule.loan_account

            # Get active mandate
            mandate = await self._get_active_mandate(loan_account.id, request.debit_date)
            if not mandate:
                continue

            # Calculate amount due
            amount_due = (
                installment.principal_amount - installment.principal_paid +
                installment.interest_amount - installment.interest_paid +
                installment.penal_interest_due - installment.penal_interest_paid
            )

            if amount_due <= 0:
                continue

            # Create transaction
            txn_ref = f"{batch_ref}-{installment.installment_number:04d}"

            transaction = NachTransaction(
                batch_id=batch.id,
                loan_account_id=loan_account.id,
                loan_mandate_id=mandate.id,
                installment_id=installment.id,
                transaction_reference=txn_ref,
                umrn=mandate.umrn,
                account_number=mandate.account_number,
                ifsc_code=mandate.ifsc_code,
                account_holder_name=mandate.account_holder_name,
                bank_name=mandate.bank_name,
                debit_amount=amount_due,
                debit_date=request.debit_date,
                narration=f"EMI {installment.installment_number} - {loan_account.loan_account_number}",
                status=NachTransactionStatus.PENDING,
            )
            self.db.add(transaction)
            total_amount += amount_due

        # Update batch totals
        batch.total_transactions = len([t for t in batch.transactions])
        batch.total_amount = total_amount
        batch.pending_count = batch.total_transactions

        await self.db.commit()
        await self.db.refresh(batch)

        return batch

    async def _generate_batch_reference(self, organization_id: UUID) -> str:
        """Generate unique batch reference."""
        today = date.today()
        prefix = f"NACH/{today.year}/{today.month:02d}"

        # Get count of batches this month
        query = select(func.count(NachBatch.id)).where(
            and_(
                NachBatch.organization_id == organization_id,
                NachBatch.batch_reference.like(f"{prefix}%"),
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0

        return f"{prefix}/{count + 1:05d}"

    async def _get_active_mandate(
        self,
        loan_account_id: UUID,
        as_of_date: date,
    ) -> Optional[LoanMandate]:
        """Get active mandate for a loan account."""
        query = (
            select(LoanMandate)
            .where(
                and_(
                    LoanMandate.loan_account_id == loan_account_id,
                    LoanMandate.status == MandateStatus.ACTIVE,
                    LoanMandate.umrn.isnot(None),
                    LoanMandate.start_date <= as_of_date,
                    LoanMandate.end_date >= as_of_date,
                )
            )
            .order_by(LoanMandate.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # =========================================================================
    # File Generation & Submission
    # =========================================================================

    async def generate_batch_file(
        self,
        batch_id: UUID,
    ) -> Tuple[str, str, str]:
        """Generate NACH ACH file for a batch.

        Args:
            batch_id: Batch ID

        Returns:
            Tuple of (file_name, file_path, checksum)
        """
        batch = await self.db.get(
            NachBatch,
            batch_id,
            options=[selectinload(NachBatch.transactions)],
        )
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        if batch.status not in (NachBatchStatus.CREATED, NachBatchStatus.VALIDATED):
            raise ValueError(f"Batch in invalid status for file generation: {batch.status}")

        # Get integration config for sponsor bank details
        config = None
        if batch.integration_config_id:
            config = await self.db.get(IntegrationConfig, batch.integration_config_id)

        sponsor_ifsc = config.config_data.get("sponsor_bank_ifsc", "") if config else ""
        utility_code = config.config_data.get("utility_code", "") if config else ""

        # Initialize file generator
        generator = NachFileGenerator(
            sponsor_bank_ifsc=sponsor_ifsc,
            utility_code=utility_code,
        )

        # Prepare transaction data
        transactions = [
            {
                "transaction_reference": t.transaction_reference,
                "umrn": t.umrn,
                "account_number": t.account_number,
                "ifsc_code": t.ifsc_code,
                "account_holder_name": t.account_holder_name,
                "bank_name": t.bank_name,
                "amount": t.debit_amount,
                "narration": t.narration,
            }
            for t in batch.transactions
            if t.status == NachTransactionStatus.PENDING
        ]

        # Generate file
        file_name, file_path, checksum, count, amount = generator.generate_debit_file(
            batch_reference=batch.batch_reference,
            debit_date=batch.debit_date,
            transactions=transactions,
        )

        # Update batch
        batch.file_name = file_name
        batch.file_path = file_path
        batch.file_checksum = checksum
        batch.file_generated_at = datetime.utcnow()
        batch.status = NachBatchStatus.FILE_GENERATED

        # Update transactions to INCLUDED status
        for t in batch.transactions:
            if t.status == NachTransactionStatus.PENDING:
                t.status = NachTransactionStatus.INCLUDED

        await self.db.commit()

        return file_name, file_path, checksum

    async def submit_batch(
        self,
        batch_id: UUID,
        submitted_by_id: Optional[UUID] = None,
    ) -> NachBatch:
        """Submit batch to NACH provider.

        Args:
            batch_id: Batch ID
            submitted_by_id: User submitting

        Returns:
            Updated batch
        """
        batch = await self.db.get(NachBatch, batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        if batch.status != NachBatchStatus.FILE_GENERATED:
            raise ValueError(f"Batch must be in FILE_GENERATED status: {batch.status}")

        # Get integration config
        config = await self.db.get(IntegrationConfig, batch.integration_config_id)
        if not config:
            raise ValueError("Integration config not found")

        # Create NACH client
        client = NachClientFactory.create(
            provider=config.provider.value,
            config=config.config_data,
            sandbox_mode=config.sandbox_mode,
        )

        # Submit batch
        response = await client.submit_debit_batch(
            batch_reference=batch.batch_reference,
            file_path=batch.file_path,
        )

        if response.success:
            batch.status = NachBatchStatus.SUBMITTED
            batch.submitted_at = datetime.utcnow()
            batch.submitted_by_id = submitted_by_id
            batch.submission_reference = response.request_id

            # Update transactions
            for t in batch.transactions:
                if t.status == NachTransactionStatus.INCLUDED:
                    t.status = NachTransactionStatus.SUBMITTED
        else:
            batch.status = NachBatchStatus.FAILED
            batch.error_message = response.message

        await self.db.commit()
        await self.db.refresh(batch)

        return batch

    # =========================================================================
    # Response Processing
    # =========================================================================

    async def process_response_file(
        self,
        batch_id: UUID,
        response_file_path: str,
    ) -> Tuple[int, int, List[str]]:
        """Process NACH response file.

        Args:
            batch_id: Batch ID
            response_file_path: Path to response file

        Returns:
            Tuple of (success_count, failure_count, errors)
        """
        batch = await self.db.get(
            NachBatch,
            batch_id,
            options=[selectinload(NachBatch.transactions)],
        )
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        # Get integration config
        config = await self.db.get(IntegrationConfig, batch.integration_config_id)
        sponsor_ifsc = config.config_data.get("sponsor_bank_ifsc", "") if config else ""
        utility_code = config.config_data.get("utility_code", "") if config else ""

        # Parse response file
        generator = NachFileGenerator(
            sponsor_bank_ifsc=sponsor_ifsc,
            utility_code=utility_code,
        )
        records, parse_errors = generator.parse_response_file(response_file_path)

        # Build transaction lookup
        txn_lookup = {t.transaction_reference: t for t in batch.transactions}

        success_count = 0
        failure_count = 0
        success_amount = Decimal("0")
        failure_amount = Decimal("0")

        for record in records:
            txn = txn_lookup.get(record.transaction_reference)
            if not txn:
                parse_errors.append(f"Transaction not found: {record.transaction_reference}")
                continue

            if record.status == "SUCCESS":
                txn.status = NachTransactionStatus.SUCCESS
                txn.bank_reference = record.bank_reference
                txn.return_code = NachReturnCode.SUCCESS
                txn.processed_at = datetime.utcnow()
                success_count += 1
                success_amount += txn.debit_amount

                # Create loan receipt
                await self._create_receipt_from_nach(txn)
            else:
                txn.status = NachTransactionStatus.BOUNCED
                txn.return_code = NachReturnCode(record.return_code) if record.return_code in [e.value for e in NachReturnCode] else NachReturnCode.OTHER
                txn.failure_reason = record.return_reason
                txn.processed_at = datetime.utcnow()
                failure_count += 1
                failure_amount += txn.debit_amount

                # Check if retryable
                if NachReturnCodeMapping.is_retryable(record.return_code):
                    if txn.retry_count < txn.max_retries:
                        txn.status = NachTransactionStatus.RETRY_SCHEDULED
                        txn.next_retry_date = date.today() + timedelta(days=7)

        # Update batch
        batch.success_count = success_count
        batch.success_amount = success_amount
        batch.failure_count = failure_count
        batch.failure_amount = failure_amount
        batch.pending_count = batch.total_transactions - success_count - failure_count
        batch.response_received_at = datetime.utcnow()
        batch.response_file_name = response_file_path.split("/")[-1]
        batch.response_file_path = response_file_path
        batch.status = NachBatchStatus.RESPONSE_RECEIVED

        if batch.pending_count == 0:
            batch.status = NachBatchStatus.COMPLETED

        await self.db.commit()

        return success_count, failure_count, parse_errors

    async def _create_receipt_from_nach(self, transaction: NachTransaction) -> LoanReceipt:
        """Create loan receipt from successful NACH transaction."""
        # Get loan account
        loan_account = await self.db.get(LoanAccount, transaction.loan_account_id)

        receipt = LoanReceipt(
            organization_id=loan_account.organization_id,
            loan_account_id=transaction.loan_account_id,
            receipt_number=f"NACH/{transaction.transaction_reference}",
            receipt_date=date.today(),
            value_date=date.today(),
            receipt_amount=transaction.debit_amount,
            receipt_type=ReceiptType.REGULAR,
            receipt_mode=ReceiptMode.NACH,
            instrument_number=transaction.bank_reference,
            instrument_date=date.today(),
            mandate_id=transaction.loan_mandate_id,
            status=ReceiptStatus.PENDING,
        )
        self.db.add(receipt)
        await self.db.flush()

        # Link receipt to transaction
        transaction.receipt_id = receipt.id

        return receipt

    # =========================================================================
    # Retry Management
    # =========================================================================

    async def get_transactions_for_retry(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> NachRetryDueList:
        """Get transactions due for retry.

        Args:
            organization_id: Organization ID
            as_of_date: Date to check (default: today)

        Returns:
            List of transactions due for retry
        """
        if not as_of_date:
            as_of_date = date.today()

        query = (
            select(NachTransaction)
            .join(NachBatch)
            .join(LoanAccount)
            .where(
                and_(
                    NachBatch.organization_id == organization_id,
                    NachTransaction.status == NachTransactionStatus.RETRY_SCHEDULED,
                    NachTransaction.next_retry_date <= as_of_date,
                )
            )
            .options(
                selectinload(NachTransaction.loan_account),
                selectinload(NachTransaction.batch),
            )
        )

        result = await self.db.execute(query)
        transactions = result.scalars().all()

        total_amount = Decimal("0")
        items = []

        for txn in transactions:
            total_amount += txn.debit_amount
            items.append(NachRetryDue(
                id=txn.id,
                transaction_reference=txn.transaction_reference,
                loan_account_number=txn.loan_account.loan_account_number,
                borrower_name=txn.account_holder_name,
                original_debit_date=txn.debit_date,
                retry_count=txn.retry_count,
                next_retry_date=txn.next_retry_date,
                debit_amount=txn.debit_amount,
                last_failure_reason=txn.failure_reason,
            ))

        return NachRetryDueList(
            items=items,
            total=len(items),
            total_amount=total_amount,
        )

    async def create_retry_batch(
        self,
        organization_id: UUID,
        transaction_ids: List[UUID],
        new_debit_date: date,
        created_by_id: Optional[UUID] = None,
    ) -> NachBatch:
        """Create a retry batch from failed transactions.

        Args:
            organization_id: Organization ID
            transaction_ids: List of transaction IDs to retry
            new_debit_date: New debit date
            created_by_id: User creating the batch

        Returns:
            New retry batch
        """
        # Get original transactions
        query = select(NachTransaction).where(
            and_(
                NachTransaction.id.in_(transaction_ids),
                NachTransaction.status == NachTransactionStatus.RETRY_SCHEDULED,
            )
        )
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        if not transactions:
            raise ValueError("No valid transactions found for retry")

        # Create new batch
        batch_ref = await self._generate_batch_reference(organization_id)

        batch = NachBatch(
            organization_id=organization_id,
            batch_reference=batch_ref,
            batch_date=date.today(),
            debit_date=new_debit_date,
            file_format=NachFileFormat.ACH_DEBIT,
            status=NachBatchStatus.CREATED,
            created_by_id=created_by_id,
            remarks="Retry batch",
        )
        self.db.add(batch)
        await self.db.flush()

        total_amount = Decimal("0")

        for orig_txn in transactions:
            # Create new transaction
            txn_ref = f"{batch_ref}-{orig_txn.transaction_reference[-4:]}"

            new_txn = NachTransaction(
                batch_id=batch.id,
                loan_account_id=orig_txn.loan_account_id,
                loan_mandate_id=orig_txn.loan_mandate_id,
                installment_id=orig_txn.installment_id,
                transaction_reference=txn_ref,
                umrn=orig_txn.umrn,
                account_number=orig_txn.account_number,
                ifsc_code=orig_txn.ifsc_code,
                account_holder_name=orig_txn.account_holder_name,
                bank_name=orig_txn.bank_name,
                debit_amount=orig_txn.debit_amount,
                debit_date=new_debit_date,
                narration=orig_txn.narration,
                status=NachTransactionStatus.PENDING,
                retry_count=orig_txn.retry_count + 1,
                original_transaction_id=orig_txn.id,
            )
            self.db.add(new_txn)
            total_amount += orig_txn.debit_amount

            # Update original transaction
            orig_txn.status = NachTransactionStatus.CANCELLED
            orig_txn.remarks = f"Retried in batch {batch_ref}"

        batch.total_transactions = len(transactions)
        batch.total_amount = total_amount
        batch.pending_count = len(transactions)

        await self.db.commit()
        await self.db.refresh(batch)

        return batch

    # =========================================================================
    # Statistics & Reporting
    # =========================================================================

    async def get_batch_statistics(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> NachBatchStatistics:
        """Get NACH batch statistics.

        Args:
            organization_id: Organization ID
            start_date: Start date (default: beginning of month)
            end_date: End date (default: today)

        Returns:
            Batch statistics
        """
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if not end_date:
            end_date = date.today()

        # Get batch counts by status
        query = (
            select(
                NachBatch.status,
                func.count(NachBatch.id).label("count"),
            )
            .where(
                and_(
                    NachBatch.organization_id == organization_id,
                    NachBatch.batch_date >= start_date,
                    NachBatch.batch_date <= end_date,
                )
            )
            .group_by(NachBatch.status)
        )
        result = await self.db.execute(query)
        status_counts = {row.status.value: row.count for row in result}

        # Get totals
        totals_query = (
            select(
                func.count(NachBatch.id).label("total_batches"),
                func.sum(NachBatch.total_transactions).label("total_txns"),
                func.sum(NachBatch.total_amount).label("total_amount"),
                func.sum(NachBatch.success_count).label("success_count"),
                func.sum(NachBatch.success_amount).label("success_amount"),
            )
            .where(
                and_(
                    NachBatch.organization_id == organization_id,
                    NachBatch.batch_date >= start_date,
                    NachBatch.batch_date <= end_date,
                )
            )
        )
        result = await self.db.execute(totals_query)
        totals = result.one()

        total_batches = totals.total_batches or 0
        total_txns = totals.total_txns or 0
        success_count = totals.success_count or 0

        success_rate = (success_count / total_txns * 100) if total_txns > 0 else 0
        avg_batch_size = (total_txns / total_batches) if total_batches > 0 else 0

        return NachBatchStatistics(
            total_batches=total_batches,
            total_transactions=total_txns,
            total_amount=totals.total_amount or Decimal("0"),
            success_rate=round(success_rate, 2),
            avg_batch_size=round(avg_batch_size, 2),
            status_breakdown=status_counts,
        )

    async def get_bounce_analysis(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
    ) -> NachBounceAnalysis:
        """Analyze NACH bounces.

        Args:
            organization_id: Organization ID
            start_date: Start date
            end_date: End date

        Returns:
            Bounce analysis
        """
        # Get bounced transactions by return code
        query = (
            select(
                NachTransaction.return_code,
                func.count(NachTransaction.id).label("count"),
                func.sum(NachTransaction.debit_amount).label("amount"),
            )
            .join(NachBatch)
            .where(
                and_(
                    NachBatch.organization_id == organization_id,
                    NachTransaction.status == NachTransactionStatus.BOUNCED,
                    NachTransaction.debit_date >= start_date,
                    NachTransaction.debit_date <= end_date,
                )
            )
            .group_by(NachTransaction.return_code)
        )
        result = await self.db.execute(query)
        code_breakdown = []
        total_bounced = 0
        total_bounce_amount = Decimal("0")

        for row in result:
            code = row.return_code.value if row.return_code else "UNKNOWN"
            name, description = NachReturnCodeMapping.get_description(code)
            code_breakdown.append({
                "return_code": code,
                "reason": description,
                "count": row.count,
                "amount": row.amount,
            })
            total_bounced += row.count
            total_bounce_amount += row.amount or Decimal("0")

        # Calculate percentages
        for item in code_breakdown:
            item["percentage"] = round(item["count"] / total_bounced * 100, 2) if total_bounced > 0 else 0

        # Calculate retry success rate
        retry_query = (
            select(
                func.count(NachTransaction.id).filter(NachTransaction.status == NachTransactionStatus.SUCCESS).label("success"),
                func.count(NachTransaction.id).label("total"),
            )
            .join(NachBatch)
            .where(
                and_(
                    NachBatch.organization_id == organization_id,
                    NachTransaction.retry_count > 0,
                    NachTransaction.debit_date >= start_date,
                    NachTransaction.debit_date <= end_date,
                )
            )
        )
        retry_result = await self.db.execute(retry_query)
        retry_data = retry_result.one()

        retry_success_rate = (
            retry_data.success / retry_data.total * 100
            if retry_data.total > 0 else 0
        )

        return NachBounceAnalysis(
            period_start=start_date,
            period_end=end_date,
            total_bounced=total_bounced,
            total_bounce_amount=total_bounce_amount,
            reason_breakdown=code_breakdown,
            retry_success_rate=round(retry_success_rate, 2),
            avg_retries_to_success=0,  # Could be calculated with more complex query
        )

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_batch(self, batch_id: UUID) -> Optional[NachBatch]:
        """Get batch by ID."""
        return await self.db.get(
            NachBatch,
            batch_id,
            options=[selectinload(NachBatch.transactions)],
        )

    async def get_batches(
        self,
        organization_id: UUID,
        status: Optional[NachBatchStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[NachBatch], int]:
        """Get paginated list of batches."""
        query = select(NachBatch).where(NachBatch.organization_id == organization_id)

        if status:
            query = query.where(NachBatch.status == status)
        if start_date:
            query = query.where(NachBatch.batch_date >= start_date)
        if end_date:
            query = query.where(NachBatch.batch_date <= end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get page
        query = query.order_by(NachBatch.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        batches = result.scalars().all()

        return batches, total

    async def cancel_batch(self, batch_id: UUID) -> NachBatch:
        """Cancel a batch."""
        batch = await self.db.get(NachBatch, batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        if batch.status not in (NachBatchStatus.CREATED, NachBatchStatus.VALIDATED, NachBatchStatus.FILE_GENERATED):
            raise ValueError(f"Cannot cancel batch in status: {batch.status}")

        batch.status = NachBatchStatus.CANCELLED

        # Cancel all pending transactions
        for txn in batch.transactions:
            if txn.status in (NachTransactionStatus.PENDING, NachTransactionStatus.INCLUDED):
                txn.status = NachTransactionStatus.CANCELLED

        await self.db.commit()
        await self.db.refresh(batch)

        return batch
