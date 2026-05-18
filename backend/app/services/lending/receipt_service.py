"""Loan receipt processing service."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import GLEntrySourceType
from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.models.lending.enums import (
    AllocationComponent,
    InstallmentStatus,
    LoanAccountStatus,
    ReceiptMode,
    ReceiptStatus,
    ReceiptType,
)
from app.models.lending.loan_account import (
    LoanAccount,
    LoanReceipt,
    ReceiptAllocation,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.repositories.finance.financial_year_repo import (
    FinancialPeriodRepository,
    FinancialYearRepository,
)
from app.services.audit import record_financial_action
from app.services.finance.gl_posting_service import GLPostingService


class ReceiptService:
    """Service for creating loan receipts and allocating them to dues."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.gl_posting_service = GLPostingService(db)
        self.fy_repo = FinancialYearRepository(db)
        self.period_repo = FinancialPeriodRepository(db)

    async def list_receipts_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status: ReceiptStatus | None = None,
    ) -> tuple[list[LoanReceipt], int]:
        base_query = (
            select(LoanReceipt)
            .where(LoanReceipt.organization_id == organization_id)
            .options(
                selectinload(LoanReceipt.loan_account).selectinload(LoanAccount.entity),
            )
        )

        if search:
            term = f"%{search}%"
            base_query = base_query.where(
                LoanReceipt.receipt_number.ilike(term) | LoanReceipt.instrument_number.ilike(term)
            )
        if status is not None:
            base_query = base_query.where(LoanReceipt.status == status)

        total = (
            await self.db.execute(select(func.count()).select_from(base_query.subquery()))
        ).scalar() or 0
        result = await self.db.execute(
            base_query.order_by(LoanReceipt.receipt_date.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create_receipt(
        self,
        loan_account_id: UUID,
        receipt_amount: Decimal | None = None,
        receipt_date: date | None = None,
        value_date: date | None = None,
        receipt_type: str | ReceiptType = ReceiptType.REGULAR,
        receipt_mode: str | ReceiptMode | None = None,
        instrument_number: str | None = None,
        instrument_date: date | None = None,
        instrument_bank: str | None = None,
        mandate_id: UUID | None = None,
        remarks: str | None = None,
        auto_allocate: bool = False,
        user_id: UUID | None = None,
        amount: Decimal | None = None,
        payment_mode: str | None = None,
        reference_number: str | None = None,
        bank_name: str | None = None,
        receipt_account_id: UUID | None = None,
        receipt_suspense_account_id: UUID | None = None,
        commit: bool = True,
    ) -> LoanReceipt:
        amount_dec = _decimal(receipt_amount if receipt_amount is not None else amount)
        if amount_dec <= 0:
            raise ValueError("Receipt amount must be positive")
        if receipt_date is None:
            raise ValueError("Receipt date is required")

        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        receipt_number = await self._generate_receipt_number(loan.organization_id)
        mode = _receipt_mode(receipt_mode or payment_mode or ReceiptMode.NEFT)
        instrument = instrument_number or reference_number
        bank = instrument_bank or bank_name
        resolved_receipt_account_id = (
            receipt_account_id
            or await self._resolve_bank_ledger_account(
                organization_id=loan.organization_id,
                allow_flag="allow_receipts",
                account_label="receipt",
            )
        )
        resolved_suspense_account_id = (
            receipt_suspense_account_id or loan.receipt_suspense_account_id
        )
        if not resolved_suspense_account_id:
            raise ValueError("Borrower receipt suspense GL account is not configured")

        receipt = LoanReceipt(
            organization_id=loan.organization_id,
            loan_account_id=loan_account_id,
            receipt_number=receipt_number,
            receipt_date=receipt_date,
            value_date=value_date or receipt_date,
            receipt_amount=amount_dec,
            receipt_type=_receipt_type(receipt_type),
            receipt_mode=mode,
            instrument_number=instrument,
            instrument_date=instrument_date,
            instrument_bank=bank,
            mandate_id=mandate_id,
            receipt_account_id=resolved_receipt_account_id,
            receipt_suspense_account_id=resolved_suspense_account_id,
            allocated_amount=Decimal("0"),
            unallocated_amount=amount_dec,
            status=ReceiptStatus.PENDING,
            processed_by_id=user_id,
            processed_at=datetime.now(UTC),
            remarks=remarks,
            created_by=user_id,
        )
        self.db.add(receipt)
        await self.db.flush()
        cash_entries = await self._post_receipt_cash_to_gl(
            receipt=receipt,
            loan=loan,
            posted_by=user_id,
        )
        if cash_entries:
            receipt.voucher_id = cash_entries[0].voucher_id

        if auto_allocate:
            await self._allocate_fifo(receipt, user_id=user_id)
            await self._post_receipt_allocation_to_gl(
                receipt=receipt,
                loan=loan,
                posted_by=user_id,
            )
            await self._update_loan_status(receipt.loan_account_id)

        if commit:
            await self.db.flush()
            await self.db.refresh(receipt)
        return receipt

    async def _generate_receipt_number(self, organization_id: UUID) -> str:
        today = date.today().strftime("%Y%m%d")
        count = (
            await self.db.execute(
                select(func.count())
                .select_from(LoanReceipt)
                .where(
                    LoanReceipt.organization_id == organization_id,
                    LoanReceipt.receipt_number.like(f"RCP-{today}%"),
                )
            )
        ).scalar() or 0
        return f"RCP-{today}-{(count + 1):04d}"

    async def allocate_receipt(
        self,
        receipt_id: UUID,
        allocation_method: str = "fifo",
        specific_allocations: list[dict[str, Any]] | None = None,
        user_id: UUID | None = None,
    ) -> list[ReceiptAllocation]:
        receipt = await self.get_receipt(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")
        if receipt.status == ReceiptStatus.REVERSED:
            raise ValueError("Cannot allocate a reversed receipt")
        if receipt.unallocated_amount <= 0:
            return []

        # Snapshot the receipt's allocation breakdown BEFORE this run so the
        # domain audit row (§8.5) can record exactly what this allocation pass
        # added to each component.
        before_snapshot = {
            "receipt_amount": receipt.receipt_amount,
            "unallocated_amount": receipt.unallocated_amount,
            "principal_allocated": receipt.principal_allocated,
            "interest_allocated": receipt.interest_allocated,
            "penal_interest_allocated": receipt.penal_interest_allocated,
            "charges_allocated": receipt.charges_allocated,
            "status": receipt.status.value if hasattr(receipt.status, "value") else str(receipt.status),
        }

        if allocation_method == "specific" and specific_allocations:
            allocations = await self._allocate_specific(receipt, specific_allocations)
        else:
            allocations = await self._allocate_fifo(receipt, user_id=user_id)

        loan = (
            await self.db.execute(select(LoanAccount).where(LoanAccount.id == receipt.loan_account_id))
        ).scalar_one()
        if not receipt.voucher_id:
            cash_entries = await self._post_receipt_cash_to_gl(
                receipt=receipt,
                loan=loan,
                posted_by=user_id,
            )
            if cash_entries:
                receipt.voucher_id = cash_entries[0].voucher_id
        await self._post_receipt_allocation_to_gl(
            receipt=receipt,
            loan=loan,
            posted_by=user_id,
        )
        await self._update_loan_status(receipt.loan_account_id)
        await self.db.flush()

        # Domain audit: receipt allocation — §8.5 / §4.8.
        # The per-installment breakdown lives in metadata so reviewers can
        # reconstruct the priority-ordered application (penal → charges →
        # interest → principal across installments).
        if user_id is not None:
            after_snapshot = {
                "receipt_amount": receipt.receipt_amount,
                "unallocated_amount": receipt.unallocated_amount,
                "principal_allocated": receipt.principal_allocated,
                "interest_allocated": receipt.interest_allocated,
                "penal_interest_allocated": receipt.penal_interest_allocated,
                "charges_allocated": receipt.charges_allocated,
                "status": receipt.status.value if hasattr(receipt.status, "value") else str(receipt.status),
            }
            await record_financial_action(
                self.db,
                organization_id=receipt.organization_id,
                entity_type="LOAN_RECEIPT",
                entity_id=receipt.id,
                entity_reference=receipt.receipt_number,
                action="RECEIPT_ALLOCATE",
                user_id=user_id,
                before=before_snapshot,
                after=after_snapshot,
                metadata={
                    "transaction_type": "RECEIPT_ALLOCATE",
                    "allocation_method": allocation_method,
                    "loan_account_id": str(receipt.loan_account_id),
                    "loan_account_number": loan.loan_account_number,
                    "allocation_breakdown": [
                        {
                            "installment_id": str(a.installment_id)
                            if getattr(a, "installment_id", None) is not None
                            else None,
                            "component": a.allocation_component.value
                            if hasattr(getattr(a, "allocation_component", None), "value")
                            else str(getattr(a, "allocation_component", "")),
                            "allocated_amount": str(getattr(a, "allocated_amount", "")),
                            "sequence": getattr(a, "allocation_sequence", None),
                        }
                        for a in allocations
                    ],
                    "allocation_count": len(allocations),
                },
                change_reason="Receipt allocated to dues",
            )

        return allocations

    async def _resolve_bank_ledger_account(
        self,
        *,
        organization_id: UUID,
        allow_flag: str,
        account_label: str,
    ) -> UUID:
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
            f"Select a {account_label} GL account; organization bank ledger mapping is not uniquely configured"
        )

    async def _get_financial_context(self, organization_id: UUID, voucher_date: date):
        fy = await self.fy_repo.get_by_date(organization_id, voucher_date)
        if not fy:
            raise ValueError(f"No financial year configured for {voucher_date}")
        period = await self.period_repo.get_by_date(fy.id, voucher_date)
        if not period:
            raise ValueError(f"No financial period configured for {voucher_date}")
        return fy, period

    async def _post_receipt_cash_to_gl(
        self,
        *,
        receipt: LoanReceipt,
        loan: LoanAccount,
        posted_by: UUID | None,
    ):
        if posted_by is None:
            raise ValueError("User is required for GL posting")
        if receipt.voucher_id:
            return []
        if not receipt.receipt_account_id:
            raise ValueError("Receipt bank/cash GL account is not configured")
        if not receipt.receipt_suspense_account_id:
            raise ValueError("Borrower receipt suspense GL account is not configured")
        fy, period = await self._get_financial_context(loan.organization_id, receipt.value_date)
        return await self.gl_posting_service.post_entries(
            organization_id=loan.organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=receipt.value_date,
            source_type=GLEntrySourceType.LOAN_RECEIPT,
            source_id=receipt.id,
            source_reference=f"{receipt.receipt_number}/CASH",
            lines=[
                {
                    "account_id": receipt.receipt_account_id,
                    "debit_amount": receipt.receipt_amount,
                    "credit_amount": Decimal("0"),
                    "narration": f"Loan receipt {receipt.receipt_number}",
                },
                {
                    "account_id": receipt.receipt_suspense_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": receipt.receipt_amount,
                    "narration": f"Borrower receipt suspense {loan.loan_account_number}",
                },
            ],
            narration=f"Loan receipt received: {loan.loan_account_number}",
            posted_by=posted_by,
        )

    async def _post_receipt_allocation_to_gl(
        self,
        *,
        receipt: LoanReceipt,
        loan: LoanAccount,
        posted_by: UUID | None,
    ):
        if posted_by is None:
            raise ValueError("User is required for GL posting")
        principal_amount = receipt.principal_allocated - receipt.gl_principal_allocated
        interest_amount = receipt.interest_allocated - receipt.gl_interest_allocated
        penal_amount = receipt.penal_interest_allocated - receipt.gl_penal_interest_allocated
        charges_amount = receipt.charges_allocated - receipt.gl_charges_allocated
        posting_amount = principal_amount + interest_amount + penal_amount + charges_amount
        if posting_amount <= 0:
            return []
        if not receipt.receipt_suspense_account_id:
            raise ValueError("Borrower receipt suspense GL account is not configured")
        lines = [
            {
                "account_id": receipt.receipt_suspense_account_id,
                "debit_amount": posting_amount,
                "credit_amount": Decimal("0"),
                "narration": f"Receipt allocation {receipt.receipt_number}",
            }
        ]
        if principal_amount > 0:
            if not loan.loan_asset_account_id:
                raise ValueError("Loan asset GL account is not configured on the loan account")
            lines.append(
                {
                    "account_id": loan.loan_asset_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": principal_amount,
                    "narration": f"Principal received {loan.loan_account_number}",
                }
            )
        if interest_amount > 0:
            if not loan.interest_receivable_account_id:
                raise ValueError(
                    "Interest receivable GL account is required for receipt allocation"
                )
            lines.append(
                {
                    "account_id": loan.interest_receivable_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": interest_amount,
                    "narration": f"Interest received {loan.loan_account_number}",
                }
            )
        if penal_amount > 0:
            if not loan.penal_interest_income_account_id:
                raise ValueError(
                    "Penal interest income GL account is required for receipt allocation"
                )
            lines.append(
                {
                    "account_id": loan.penal_interest_income_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": penal_amount,
                    "narration": f"Penal interest received {loan.loan_account_number}",
                }
            )
        if charges_amount > 0:
            if not loan.charges_income_account_id:
                raise ValueError("Charges income GL account is required for receipt allocation")
            lines.append(
                {
                    "account_id": loan.charges_income_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": charges_amount,
                    "narration": f"Charges received {loan.loan_account_number}",
                }
            )

        fy, period = await self._get_financial_context(loan.organization_id, receipt.value_date)
        entries = await self.gl_posting_service.post_entries(
            organization_id=loan.organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=receipt.value_date,
            source_type=GLEntrySourceType.LOAN_RECEIPT,
            source_id=receipt.id,
            source_reference=f"{receipt.receipt_number}/ALLOC",
            lines=lines,
            narration=f"Loan receipt allocated: {loan.loan_account_number}",
            posted_by=posted_by,
        )
        if entries:
            receipt.allocation_voucher_id = entries[0].voucher_id
            receipt.gl_allocated_amount += posting_amount
            receipt.gl_principal_allocated += principal_amount
            receipt.gl_interest_allocated += interest_amount
            receipt.gl_penal_interest_allocated += penal_amount
            receipt.gl_charges_allocated += charges_amount
        return entries

    async def _allocate_fifo(
        self,
        receipt: LoanReceipt,
        user_id: UUID | None = None,
    ) -> list[ReceiptAllocation]:
        query = (
            select(ScheduleInstallment)
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .where(
                RepaymentSchedule.loan_account_id == receipt.loan_account_id,
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.status != InstallmentStatus.PAID,
            )
            .order_by(ScheduleInstallment.due_date, ScheduleInstallment.installment_number)
        )
        installments = list((await self.db.execute(query)).scalars().all())
        allocations: list[ReceiptAllocation] = []
        sequence = await self._next_allocation_sequence(receipt.id)

        for installment in installments:
            if receipt.unallocated_amount <= 0:
                break
            for component, due in self._component_dues(installment):
                if receipt.unallocated_amount <= 0:
                    break
                amount = min(due, receipt.unallocated_amount)
                if amount <= 0:
                    continue
                allocation = self._apply_installment_allocation(
                    receipt=receipt,
                    installment=installment,
                    component=component,
                    amount=amount,
                    sequence=sequence,
                )
                allocation.created_by = user_id
                self.db.add(allocation)
                allocations.append(allocation)
                sequence += 1

        return allocations

    async def _allocate_specific(
        self,
        receipt: LoanReceipt,
        specific_allocations: list[dict[str, Any]],
    ) -> list[ReceiptAllocation]:
        allocations: list[ReceiptAllocation] = []
        sequence = await self._next_allocation_sequence(receipt.id)
        for item in specific_allocations:
            if receipt.unallocated_amount <= 0:
                break
            installment_id = item.get("installment_id") or item.get("schedule_id")
            component = _allocation_component(item.get("component"))
            amount = _decimal(item.get("amount"))
            if not installment_id or amount <= 0:
                continue
            installment = (
                await self.db.execute(
                    select(ScheduleInstallment).where(
                        ScheduleInstallment.id == UUID(str(installment_id))
                    )
                )
            ).scalar_one_or_none()
            if not installment:
                continue
            amount = min(amount, receipt.unallocated_amount)
            allocation = self._apply_installment_allocation(
                receipt=receipt,
                installment=installment,
                component=component,
                amount=amount,
                sequence=sequence,
            )
            self.db.add(allocation)
            allocations.append(allocation)
            sequence += 1
        return allocations

    def _apply_installment_allocation(
        self,
        *,
        receipt: LoanReceipt,
        installment: ScheduleInstallment,
        component: AllocationComponent,
        amount: Decimal,
        sequence: int,
    ) -> ReceiptAllocation:
        if component == AllocationComponent.PENAL_INTEREST:
            installment.penal_interest_paid += amount
            receipt.penal_interest_allocated += amount
        elif component == AllocationComponent.INTEREST:
            installment.interest_paid += amount
            receipt.interest_allocated += amount
        elif component == AllocationComponent.PRINCIPAL:
            installment.principal_paid += amount
            receipt.principal_allocated += amount
        elif component == AllocationComponent.CHARGES:
            receipt.charges_allocated += amount

        receipt.allocated_amount += amount
        receipt.unallocated_amount = max(
            receipt.receipt_amount - receipt.allocated_amount,
            Decimal("0"),
        )
        receipt.status = (
            ReceiptStatus.ALLOCATED if receipt.unallocated_amount <= 0 else ReceiptStatus.PENDING
        )
        self._refresh_installment_status(installment)

        return ReceiptAllocation(
            receipt_id=receipt.id,
            installment_id=installment.id,
            allocation_component=component,
            allocated_amount=amount,
            allocation_sequence=sequence,
        )

    def _component_dues(
        self,
        installment: ScheduleInstallment,
    ) -> list[tuple[AllocationComponent, Decimal]]:
        penal_due = installment.penal_interest_due - installment.penal_interest_paid
        interest_due = installment.interest_amount - installment.interest_paid
        principal_due = installment.principal_amount - installment.principal_paid
        return [
            (AllocationComponent.PENAL_INTEREST, max(penal_due, Decimal("0"))),
            (AllocationComponent.INTEREST, max(interest_due, Decimal("0"))),
            (AllocationComponent.PRINCIPAL, max(principal_due, Decimal("0"))),
        ]

    async def _next_allocation_sequence(self, receipt_id: UUID) -> int:
        max_sequence = (
            await self.db.execute(
                select(func.max(ReceiptAllocation.allocation_sequence)).where(
                    ReceiptAllocation.receipt_id == receipt_id
                )
            )
        ).scalar()
        return int(max_sequence or 0) + 1

    def _refresh_installment_status(self, installment: ScheduleInstallment) -> None:
        total_due = (
            installment.principal_amount
            + installment.interest_amount
            + installment.penal_interest_due
        )
        total_paid = (
            installment.principal_paid + installment.interest_paid + installment.penal_interest_paid
        )
        if total_paid >= total_due:
            installment.status = InstallmentStatus.PAID
            installment.paid_date = date.today()
        elif total_paid > 0:
            installment.status = InstallmentStatus.PARTIALLY_PAID
        elif installment.due_date < date.today():
            installment.status = InstallmentStatus.OVERDUE
        else:
            installment.status = InstallmentStatus.NOT_DUE

    async def _update_loan_status(self, loan_account_id: UUID) -> None:
        loan = (
            await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        ).scalar_one()
        loan.total_principal_received = (
            await self.db.execute(
                select(func.coalesce(func.sum(LoanReceipt.principal_allocated), 0)).where(
                    LoanReceipt.loan_account_id == loan_account_id,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
            )
        ).scalar() or Decimal("0")
        loan.total_interest_received = (
            await self.db.execute(
                select(func.coalesce(func.sum(LoanReceipt.interest_allocated), 0)).where(
                    LoanReceipt.loan_account_id == loan_account_id,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
            )
        ).scalar() or Decimal("0")
        loan.total_penal_interest_received = (
            await self.db.execute(
                select(func.coalesce(func.sum(LoanReceipt.penal_interest_allocated), 0)).where(
                    LoanReceipt.loan_account_id == loan_account_id,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
            )
        ).scalar() or Decimal("0")
        loan.total_charges_received = (
            await self.db.execute(
                select(func.coalesce(func.sum(LoanReceipt.charges_allocated), 0)).where(
                    LoanReceipt.loan_account_id == loan_account_id,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
            )
        ).scalar() or Decimal("0")

        installment_rows = (
            await self.db.execute(
                select(ScheduleInstallment)
                .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
                .where(
                    RepaymentSchedule.loan_account_id == loan_account_id,
                    RepaymentSchedule.is_current.is_(True),
                )
            )
        ).scalars()
        principal_overdue = Decimal("0")
        interest_overdue = Decimal("0")
        current_interest = Decimal("0")
        penal_outstanding = Decimal("0")
        oldest_due_date: date | None = None
        today = date.today()

        for installment in installment_rows:
            principal_due = max(
                installment.principal_amount - installment.principal_paid,
                Decimal("0"),
            )
            interest_due = max(
                installment.interest_amount - installment.interest_paid,
                Decimal("0"),
            )
            penal_due = max(
                installment.penal_interest_due - installment.penal_interest_paid,
                Decimal("0"),
            )
            if principal_due + interest_due + penal_due <= 0:
                continue
            if installment.due_date < today:
                principal_overdue += principal_due
                interest_overdue += interest_due
                if oldest_due_date is None or installment.due_date < oldest_due_date:
                    oldest_due_date = installment.due_date
            else:
                current_interest += interest_due
            penal_outstanding += penal_due

        principal_base = loan.total_disbursed_amount or loan.sanctioned_amount
        loan.principal_outstanding = max(
            principal_base - loan.total_principal_received,
            Decimal("0"),
        )
        loan.principal_overdue = principal_overdue
        loan.interest_overdue = interest_overdue
        loan.interest_outstanding = current_interest
        loan.penal_interest_outstanding = penal_outstanding
        loan.oldest_due_date = oldest_due_date
        loan.days_past_due = (today - oldest_due_date).days if oldest_due_date else 0
        loan.total_outstanding = (
            loan.principal_outstanding
            + loan.interest_outstanding
            + loan.interest_overdue
            + loan.penal_interest_outstanding
            + loan.charges_outstanding
        )

        if loan.principal_outstanding <= 0 and loan.total_outstanding <= 0:
            loan.status = LoanAccountStatus.CLOSED
            loan.closure_date = date.today()

    async def reverse_receipt(
        self,
        receipt_id: UUID,
        reason: str | None = None,
        reversal_reason: str | None = None,
        reversal_date: date | None = None,
        user_id: UUID | None = None,
    ) -> LoanReceipt:
        receipt = await self.get_receipt(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")
        if receipt.status == ReceiptStatus.REVERSED:
            raise ValueError("Receipt is already reversed")

        allocations = await self.get_allocations(receipt_id)
        for allocation in allocations:
            if allocation.installment:
                self._reverse_installment_allocation(allocation)
            await self.db.delete(allocation)

        receipt.status = ReceiptStatus.REVERSED
        receipt.allocated_amount = Decimal("0")
        receipt.unallocated_amount = Decimal("0")
        receipt.principal_allocated = Decimal("0")
        receipt.interest_allocated = Decimal("0")
        receipt.penal_interest_allocated = Decimal("0")
        receipt.charges_allocated = Decimal("0")
        receipt.remarks = " | ".join(
            value
            for value in [
                receipt.remarks,
                f"Reversed on {reversal_date or date.today()}: {reversal_reason or reason}",
            ]
            if value
        )
        receipt.updated_by = user_id

        await self._update_loan_status(receipt.loan_account_id)
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    def _reverse_installment_allocation(self, allocation: ReceiptAllocation) -> None:
        installment = allocation.installment
        amount = allocation.allocated_amount
        if allocation.allocation_component == AllocationComponent.PENAL_INTEREST:
            installment.penal_interest_paid = max(
                installment.penal_interest_paid - amount,
                Decimal("0"),
            )
        elif allocation.allocation_component == AllocationComponent.INTEREST:
            installment.interest_paid = max(installment.interest_paid - amount, Decimal("0"))
        elif allocation.allocation_component == AllocationComponent.PRINCIPAL:
            installment.principal_paid = max(
                installment.principal_paid - amount,
                Decimal("0"),
            )
        self._refresh_installment_status(installment)

    async def process_bulk_receipts(
        self,
        receipts_data: list[dict[str, Any]],
        organization_id: UUID | None = None,
        auto_allocate: bool = True,
        user_id: UUID | None = None,
    ) -> dict[str, Any]:
        failures: list[dict[str, Any]] = []
        total_amount = Decimal("0")
        success_count = 0

        for idx, data in enumerate(receipts_data, start=1):
            try:
                loan_account_id = await self._resolve_loan_account_id(data, organization_id)
                amount = _decimal(data.get("receipt_amount") or data.get("amount"))
                await self.create_receipt(
                    loan_account_id=loan_account_id,
                    receipt_amount=amount,
                    receipt_date=data.get("receipt_date") or date.today(),
                    receipt_mode=data.get("receipt_mode") or data.get("payment_mode") or "NEFT",
                    instrument_number=data.get("instrument_number"),
                    remarks=data.get("remarks"),
                    auto_allocate=auto_allocate,
                    user_id=user_id,
                )
                total_amount += amount
                success_count += 1
            except Exception as exc:
                failures.append(
                    {
                        "row": idx,
                        "loan_account_number": data.get("loan_account_number"),
                        "error": str(exc),
                    }
                )

        return {
            "total_count": len(receipts_data),
            "success_count": success_count,
            "failed_count": len(failures),
            "total_amount": total_amount,
            "failures": failures,
        }

    async def _resolve_loan_account_id(
        self,
        data: dict[str, Any],
        organization_id: UUID | None,
    ) -> UUID:
        if data.get("loan_account_id"):
            return UUID(str(data["loan_account_id"]))
        loan_number = data.get("loan_account_number")
        if not loan_number:
            raise ValueError("loan_account_id or loan_account_number is required")
        conditions = [LoanAccount.loan_account_number == loan_number]
        if organization_id:
            conditions.append(LoanAccount.organization_id == organization_id)
        loan = (
            await self.db.execute(select(LoanAccount).where(and_(*conditions)))
        ).scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_number} not found")
        return loan.id

    async def get_receipts(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        status: str | None = None,
    ) -> list[LoanReceipt]:
        conditions = [LoanReceipt.loan_account_id == loan_account_id]
        if from_date:
            conditions.append(LoanReceipt.receipt_date >= from_date)
        if to_date:
            conditions.append(LoanReceipt.receipt_date <= to_date)
        if status:
            conditions.append(LoanReceipt.status == _receipt_status(status))
        result = await self.db.execute(
            select(LoanReceipt).where(and_(*conditions)).order_by(LoanReceipt.receipt_date.desc())
        )
        return list(result.scalars().all())

    async def get_receipt(self, receipt_id: UUID) -> LoanReceipt | None:
        return (
            await self.db.execute(
                select(LoanReceipt)
                .where(LoanReceipt.id == receipt_id)
                .options(
                    selectinload(LoanReceipt.allocations),
                    selectinload(LoanReceipt.bank_statement_matches),
                )
            )
        ).scalar_one_or_none()

    async def get_allocations(self, receipt_id: UUID) -> list[ReceiptAllocation]:
        result = await self.db.execute(
            select(ReceiptAllocation)
            .where(ReceiptAllocation.receipt_id == receipt_id)
            .options(selectinload(ReceiptAllocation.installment))
            .order_by(ReceiptAllocation.allocation_sequence)
        )
        return list(result.scalars().all())

    async def get_receipt_summary(
        self,
        organization_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        conditions = [LoanReceipt.organization_id == organization_id]
        if from_date:
            conditions.append(LoanReceipt.receipt_date >= from_date)
        if to_date:
            conditions.append(LoanReceipt.receipt_date <= to_date)
        row = (
            await self.db.execute(
                select(
                    func.count(LoanReceipt.id),
                    func.coalesce(func.sum(LoanReceipt.receipt_amount), 0),
                    func.coalesce(func.sum(LoanReceipt.allocated_amount), 0),
                    func.coalesce(func.sum(LoanReceipt.unallocated_amount), 0),
                ).where(and_(*conditions))
            )
        ).one()
        return {
            "receipt_count": int(row[0] or 0),
            "receipt_amount": row[1] or Decimal("0"),
            "allocated_amount": row[2] or Decimal("0"),
            "unallocated_amount": row[3] or Decimal("0"),
        }

    async def mark_bounced(
        self,
        receipt_id: UUID,
        bounce_reason: str,
        bounce_date: date | None = None,
        bounce_charges: Decimal = Decimal("0"),
        user_id: UUID | None = None,
    ) -> LoanReceipt:
        receipt = await self.get_receipt(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")
        receipt.bounced = True
        receipt.bounce_reason = bounce_reason
        receipt.bounce_date = bounce_date or date.today()
        receipt.bounce_charges = bounce_charges
        receipt.status = ReceiptStatus.BOUNCED
        receipt.updated_by = user_id
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def _receipt_type(value: str | ReceiptType) -> ReceiptType:
    if isinstance(value, ReceiptType):
        return value
    normalized = str(value or "REGULAR").upper()
    if normalized in {"EMI", "PART_PAYMENT", "PENAL", "CHARGES", "PROCESSING_FEE"}:
        normalized = "REGULAR"
    return ReceiptType.__members__.get(normalized, ReceiptType.REGULAR)


def _receipt_mode(value: str | ReceiptMode) -> ReceiptMode:
    if isinstance(value, ReceiptMode):
        return value
    normalized = str(value or "NEFT").upper()
    return ReceiptMode.__members__.get(normalized, ReceiptMode.NEFT)


def _receipt_status(value: str | ReceiptStatus) -> ReceiptStatus:
    if isinstance(value, ReceiptStatus):
        return value
    normalized = str(value or "PENDING").upper()
    return ReceiptStatus.__members__.get(normalized, ReceiptStatus.PENDING)


def _allocation_component(value: Any) -> AllocationComponent:
    normalized = str(value or "INTEREST").upper()
    if normalized in {"OVERDUE_INTEREST", "CURRENT_INTEREST"}:
        normalized = "INTEREST"
    if normalized in {"OVERDUE_PRINCIPAL", "CURRENT_PRINCIPAL", "PREPAYMENT"}:
        normalized = "PRINCIPAL"
    if normalized == "ON_ACCOUNT":
        normalized = "INTEREST"
    return AllocationComponent.__members__.get(normalized, AllocationComponent.INTEREST)
