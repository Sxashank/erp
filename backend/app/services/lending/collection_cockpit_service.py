"""Collection and reconciliation cockpit service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.bank_reconciliation import (
    BankStatement,
    ReconciliationStatus,
    StatementTransactionType,
)
from app.models.lending.entity import Entity
from app.models.lending.enums import InstallmentStatus, LoanAccountStatus, ReceiptStatus
from app.models.lending.loan_account import (
    LoanAccount,
    LoanReceipt,
    LoanReceiptBankStatementMatch,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.schemas.lending.collection_cockpit import (
    CollectionBucketMetric,
    CollectionCockpitResponse,
    CollectionCockpitSummary,
    UnmatchedBankCreditItem,
    UpcomingCollectionItem,
)

MONEY = Decimal("0.01")
PERCENT = Decimal("0.01")
OPEN_LOAN_STATUSES = (
    LoanAccountStatus.CREATED,
    LoanAccountStatus.ACTIVE,
    LoanAccountStatus.DORMANT,
    LoanAccountStatus.FROZEN,
    LoanAccountStatus.RECALLED,
)
COLLECTABLE_INSTALLMENT_STATUSES = (
    InstallmentStatus.NOT_DUE,
    InstallmentStatus.DUE,
    InstallmentStatus.PARTIALLY_PAID,
    InstallmentStatus.OVERDUE,
)
ACTIVE_RECEIPT_STATUSES = (
    ReceiptStatus.PENDING,
    ReceiptStatus.ALLOCATED,
)
UNMATCHED_STATUSES = (
    ReconciliationStatus.UNRECONCILED,
    ReconciliationStatus.PARTIALLY_MATCHED,
)
AGEING_BUCKETS = (
    ("overdue_90_plus", "90+ days overdue", None, -91),
    ("overdue_31_90", "31-90 days overdue", -90, -31),
    ("overdue_1_30", "1-30 days overdue", -30, -1),
    ("due_today", "Due today", 0, 0),
    ("next_7", "Next 7 days", 1, 7),
    ("next_30", "Next 8-30 days", 8, 30),
    ("beyond_30", "Beyond 30 days", 31, None),
)


@dataclass
class AgeingAccumulator:
    """Mutable due ageing accumulator."""

    installment_count: int = 0
    amount_due: Decimal = Decimal("0")


@dataclass
class CollectionAccumulator:
    """Mutable collection cockpit accumulator."""

    overdue_accounts: set[UUID] = field(default_factory=set)
    overdue_amount: Decimal = Decimal("0")
    ageing_buckets: dict[str, AgeingAccumulator] = field(
        default_factory=lambda: {bucket: AgeingAccumulator() for bucket, _, _, _ in AGEING_BUCKETS}
    )


class CollectionCockpitService:
    """Builds collection and bank-credit reconciliation metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cockpit(
        self,
        organization_id: UUID,
        *,
        period_from: date,
        period_to: date,
        limit: int = 10,
    ) -> CollectionCockpitResponse:
        today = date.today()
        demand_amount = await self._period_demand(organization_id, period_from, period_to)
        receipt_amount, allocated_amount, unallocated_receipts = await self._period_receipts(
            organization_id,
            period_from,
            period_to,
        )
        unmatched_count, unmatched_amount = await self._unmatched_bank_credit_totals(
            organization_id
        )
        matched_count, matched_amount = await self._matched_bank_credit_totals(
            organization_id,
            period_from,
            period_to,
        )
        due_rows = await self._due_rows(organization_id, max(period_to, today + timedelta(days=30)))
        accumulator = self._age_due_rows(due_rows, today)

        return CollectionCockpitResponse(
            summary=CollectionCockpitSummary(
                period_from=period_from.isoformat(),
                period_to=period_to.isoformat(),
                demand_amount=demand_amount,
                receipt_amount=receipt_amount,
                allocated_amount=allocated_amount,
                unallocated_receipts=unallocated_receipts,
                collection_efficiency_percent=self._percent(
                    allocated_amount,
                    demand_amount,
                ),
                overdue_amount=self._money(accumulator.overdue_amount),
                overdue_accounts=len(accumulator.overdue_accounts),
                unmatched_bank_credit_count=unmatched_count,
                unmatched_bank_credit_amount=unmatched_amount,
                matched_bank_credit_count=matched_count,
                matched_bank_credit_amount=matched_amount,
            ),
            ageing_buckets=self._bucket_rows(accumulator),
            upcoming_collections=self._upcoming_collection_rows(due_rows, today, limit),
            unmatched_bank_credits=await self._unmatched_bank_credits(
                organization_id,
                limit,
            ),
        )

    async def _period_demand(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
    ) -> Decimal:
        scheduled_amount = (
            ScheduleInstallment.principal_amount
            + ScheduleInstallment.interest_amount
            + ScheduleInstallment.penal_interest_due
        )
        result = await self.db.execute(
            select(func.coalesce(func.sum(scheduled_amount), 0))
            .select_from(ScheduleInstallment)
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(OPEN_LOAN_STATUSES),
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.due_date >= period_from,
                ScheduleInstallment.due_date <= period_to,
                ScheduleInstallment.status.in_(COLLECTABLE_INSTALLMENT_STATUSES),
            )
        )
        return self._money(result.scalar_one_or_none())

    async def _period_receipts(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
    ) -> tuple[Decimal, Decimal, Decimal]:
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(LoanReceipt.receipt_amount), 0),
                func.coalesce(func.sum(LoanReceipt.allocated_amount), 0),
                func.coalesce(func.sum(LoanReceipt.unallocated_amount), 0),
            ).where(
                LoanReceipt.organization_id == organization_id,
                LoanReceipt.receipt_date >= period_from,
                LoanReceipt.receipt_date <= period_to,
                LoanReceipt.status.in_(ACTIVE_RECEIPT_STATUSES),
                LoanReceipt.bounced.is_(False),
            )
        )
        receipt_amount, allocated_amount, unallocated_amount = result.one()
        return (
            self._money(receipt_amount),
            self._money(allocated_amount),
            self._money(unallocated_amount),
        )

    async def _unmatched_bank_credit_totals(
        self,
        organization_id: UUID,
    ) -> tuple[int, Decimal]:
        result = await self.db.execute(
            select(
                func.count(BankStatement.id),
                func.coalesce(
                    func.sum(BankStatement.credit_amount - BankStatement.reconciled_amount),
                    0,
                ),
            ).where(
                BankStatement.organization_id == organization_id,
                BankStatement.transaction_type == StatementTransactionType.CREDIT,
                BankStatement.credit_amount > 0,
                BankStatement.deleted_at.is_(None),
                BankStatement.reconciliation_status.in_(UNMATCHED_STATUSES),
            )
        )
        count, amount = result.one()
        return int(count or 0), self._money(amount)

    async def _matched_bank_credit_totals(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
    ) -> tuple[int, Decimal]:
        start = datetime.combine(period_from, time.min)
        end = datetime.combine(period_to, time.max)
        result = await self.db.execute(
            select(
                func.count(LoanReceiptBankStatementMatch.id),
                func.coalesce(func.sum(LoanReceiptBankStatementMatch.matched_amount), 0),
            ).where(
                LoanReceiptBankStatementMatch.organization_id == organization_id,
                LoanReceiptBankStatementMatch.matched_at >= start,
                LoanReceiptBankStatementMatch.matched_at <= end,
            )
        )
        count, amount = result.one()
        return int(count or 0), self._money(amount)

    async def _due_rows(
        self,
        organization_id: UUID,
        period_to: date,
    ) -> list[tuple[ScheduleInstallment, LoanAccount, str, Decimal]]:
        due_amount = (
            ScheduleInstallment.principal_amount
            + ScheduleInstallment.interest_amount
            + ScheduleInstallment.penal_interest_due
            - ScheduleInstallment.principal_paid
            - ScheduleInstallment.interest_paid
            - ScheduleInstallment.penal_interest_paid
        )
        result = await self.db.execute(
            select(
                ScheduleInstallment,
                LoanAccount,
                Entity.legal_name,
                due_amount.label("due_amount"),
            )
            .select_from(ScheduleInstallment)
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(OPEN_LOAN_STATUSES),
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.status.in_(COLLECTABLE_INSTALLMENT_STATUSES),
                ScheduleInstallment.due_date <= period_to,
                due_amount > 0,
            )
            .order_by(ScheduleInstallment.due_date.asc())
        )
        return [
            (installment, loan, borrower_name, self._money(due_amount_value))
            for installment, loan, borrower_name, due_amount_value in result.all()
        ]

    def _age_due_rows(
        self,
        due_rows: list[tuple[ScheduleInstallment, LoanAccount, str, Decimal]],
        today: date,
    ) -> CollectionAccumulator:
        accumulator = CollectionAccumulator()
        for installment, loan, _, due_amount in due_rows:
            bucket = self._bucket_for_due_date(installment.due_date, today)
            accumulator.ageing_buckets[bucket].installment_count += 1
            accumulator.ageing_buckets[bucket].amount_due += due_amount
            if installment.due_date < today:
                accumulator.overdue_accounts.add(loan.id)
                accumulator.overdue_amount += due_amount
        return accumulator

    def _bucket_rows(
        self,
        accumulator: CollectionAccumulator,
    ) -> list[CollectionBucketMetric]:
        total_due = sum(
            (bucket.amount_due for bucket in accumulator.ageing_buckets.values()),
            Decimal("0"),
        )
        return [
            CollectionBucketMetric(
                bucket=bucket_key,
                label=label,
                installment_count=accumulator.ageing_buckets[bucket_key].installment_count,
                amount_due=self._money(accumulator.ageing_buckets[bucket_key].amount_due),
                portfolio_percent=self._percent(
                    accumulator.ageing_buckets[bucket_key].amount_due,
                    total_due,
                ),
            )
            for bucket_key, label, _, _ in AGEING_BUCKETS
        ]

    def _upcoming_collection_rows(
        self,
        due_rows: list[tuple[ScheduleInstallment, LoanAccount, str, Decimal]],
        today: date,
        limit: int,
    ) -> list[UpcomingCollectionItem]:
        return [
            UpcomingCollectionItem(
                loan_account_id=loan.id,
                loan_account_number=loan.loan_account_number,
                borrower_name=borrower_name,
                due_date=installment.due_date.isoformat(),
                installment_number=installment.installment_number,
                status=installment.status.value,
                days_past_due=max((today - installment.due_date).days, 0),
                principal_due=self._money(
                    installment.principal_amount - installment.principal_paid
                ),
                interest_due=self._money(installment.interest_amount - installment.interest_paid),
                penal_due=self._money(
                    installment.penal_interest_due - installment.penal_interest_paid
                ),
                amount_due=due_amount,
            )
            for installment, loan, borrower_name, due_amount in due_rows[:limit]
        ]

    async def _unmatched_bank_credits(
        self,
        organization_id: UUID,
        limit: int,
    ) -> list[UnmatchedBankCreditItem]:
        result = await self.db.execute(
            select(BankStatement)
            .where(
                BankStatement.organization_id == organization_id,
                BankStatement.transaction_type == StatementTransactionType.CREDIT,
                BankStatement.credit_amount > 0,
                BankStatement.deleted_at.is_(None),
                BankStatement.reconciliation_status.in_(UNMATCHED_STATUSES),
            )
            .order_by(BankStatement.transaction_date.desc(), BankStatement.created_at.desc())
            .limit(limit)
        )
        return [
            UnmatchedBankCreditItem(
                statement_id=statement.id,
                transaction_date=statement.transaction_date.isoformat(),
                value_date=statement.value_date.isoformat(),
                reference_number=statement.reference_number,
                utr_number=statement.utr_number,
                description=statement.description,
                credit_amount=self._money(statement.credit_amount),
                reconciled_amount=self._money(statement.reconciled_amount),
                unreconciled_amount=self._money(
                    statement.credit_amount - statement.reconciled_amount
                ),
            )
            for statement in result.scalars().all()
        ]

    @staticmethod
    def _bucket_for_due_date(due_date: date, today: date) -> str:
        day_gap = (due_date - today).days
        for bucket, _, start, end in AGEING_BUCKETS:
            if start is None and end is not None and day_gap <= end:
                return bucket
            if end is None and start is not None and day_gap >= start:
                return bucket
            if start is not None and end is not None and start <= day_gap <= end:
                return bucket
        return "beyond_30"

    @staticmethod
    def _money(value: Decimal | int | float | None) -> Decimal:
        return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
        if not denominator:
            return Decimal("0.00")
        return ((numerator / denominator) * Decimal("100")).quantize(
            PERCENT,
            rounding=ROUND_HALF_UP,
        )
