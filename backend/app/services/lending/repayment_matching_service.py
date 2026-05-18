"""Bank-statement to corporate loan repayment matching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
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
from app.schemas.lending.repayment_matching import (
    CreateMatchedReceiptResponse,
    RepaymentMatchCandidate,
    RepaymentMatchingResponse,
    RepaymentMatchingSummary,
)
from app.services.lending.receipt_service import ReceiptService


@dataclass
class _Candidate:
    loan_account_id: UUID | None
    loan_account_number: str | None
    entity_name: str | None
    receipt_id: UUID | None
    installment_id: UUID | None
    due_date: date | None
    due_amount: Decimal | None
    confidence: Decimal
    match_basis: list[str]
    suggested_action: str


class RepaymentMatchingService:
    """Read-only matching engine for imported bank credits."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_candidates(
        self,
        organization_id: UUID,
        *,
        bank_account_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        min_confidence: Decimal = Decimal("0"),
        limit: int = 50,
    ) -> RepaymentMatchingResponse:
        statements = await self._unmatched_credits(
            organization_id=organization_id,
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

        candidates: list[RepaymentMatchCandidate] = []
        for statement in statements:
            candidate = await self._best_candidate(organization_id, statement)
            if candidate.confidence < min_confidence:
                continue
            candidates.append(
                RepaymentMatchCandidate(
                    statement_id=statement.id,
                    transaction_date=statement.transaction_date,
                    value_date=statement.value_date,
                    reference_number=statement.reference_number,
                    utr_number=statement.utr_number,
                    description=statement.description,
                    credit_amount=statement.credit_amount,
                    suggested_loan_account_id=candidate.loan_account_id,
                    loan_account_number=candidate.loan_account_number,
                    entity_name=candidate.entity_name,
                    suggested_receipt_id=candidate.receipt_id,
                    suggested_installment_id=candidate.installment_id,
                    due_date=candidate.due_date,
                    due_amount=candidate.due_amount,
                    confidence=candidate.confidence,
                    match_basis=candidate.match_basis,
                    suggested_action=candidate.suggested_action,
                )
            )

        summary = self._summary_from_candidates(statements, candidates)
        return RepaymentMatchingResponse(summary=summary, candidates=candidates)

    async def get_summary(
        self,
        organization_id: UUID,
        *,
        bank_account_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> RepaymentMatchingSummary:
        unmatched_count, unmatched_amount = await self._unmatched_credit_totals(
            organization_id=organization_id,
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )
        response = await self.get_candidates(
            organization_id=organization_id,
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
            limit=100,
        )
        return RepaymentMatchingSummary(
            unmatched_credit_count=unmatched_count,
            unmatched_credit_amount=unmatched_amount,
            high_confidence_count=response.summary.high_confidence_count,
            review_required_count=max(
                unmatched_count - response.summary.high_confidence_count,
                0,
            ),
        )

    async def create_receipt_from_statement(
        self,
        organization_id: UUID,
        statement_id: UUID,
        *,
        loan_account_id: UUID | None = None,
        auto_allocate: bool = True,
        user_id: UUID | None = None,
    ) -> CreateMatchedReceiptResponse:
        statement = (
            await self.session.execute(
                select(BankStatement).where(
                    BankStatement.id == statement_id,
                    BankStatement.organization_id == organization_id,
                    BankStatement.transaction_type == StatementTransactionType.CREDIT,
                    BankStatement.credit_amount > 0,
                    BankStatement.deleted_at.is_(None),
                    BankStatement.reconciliation_status.in_(
                        [
                            ReconciliationStatus.UNRECONCILED,
                            ReconciliationStatus.PARTIALLY_MATCHED,
                        ]
                    ),
                )
            )
        ).scalar_one_or_none()
        if not statement:
            raise ValueError("Bank credit is not available for repayment matching")

        candidate = await self._best_candidate(organization_id, statement)
        selected_loan_account_id = loan_account_id
        if not selected_loan_account_id:
            selected_loan_account_id = candidate.loan_account_id
        if not selected_loan_account_id:
            raise ValueError("No loan account identified for this bank credit")

        candidate_applies = candidate.loan_account_id == selected_loan_account_id
        match_confidence = candidate.confidence if candidate_applies else Decimal("100")
        match_rules = candidate.match_basis if candidate_applies else ["user_selected_loan_account"]
        reference = statement.utr_number or statement.reference_number
        receipt = await ReceiptService(self.session).create_receipt(
            loan_account_id=selected_loan_account_id,
            receipt_amount=statement.unreconciled_amount,
            receipt_date=statement.transaction_date,
            value_date=statement.value_date,
            receipt_mode="NEFT",
            instrument_number=reference,
            remarks=(
                "Created from bank statement "
                f"{statement.id}; narration: {statement.description or '-'}"
            ),
            auto_allocate=auto_allocate,
            user_id=user_id,
            commit=False,
        )

        match = LoanReceiptBankStatementMatch(
            organization_id=organization_id,
            receipt_id=receipt.id,
            statement_id=statement.id,
            bank_account_id=statement.bank_account_id,
            matched_amount=receipt.receipt_amount,
            match_confidence=match_confidence,
            match_basis={
                "rules": match_rules,
                "source": "repayment_matching_workbench",
                "statement_reference": reference,
                "auto_allocate": auto_allocate,
            },
            match_type=(
                "AUTO" if not loan_account_id and match_confidence >= Decimal("80") else "MANUAL"
            ),
            matched_at=datetime.now(UTC),
            matched_by_id=user_id,
        )
        self.session.add(match)

        statement.reconciled_amount += receipt.receipt_amount
        statement.reconciliation_status = (
            ReconciliationStatus.RECONCILED
            if statement.unreconciled_amount <= 0
            else ReconciliationStatus.PARTIALLY_MATCHED
        )
        statement.reconciled_at = datetime.now(UTC)
        statement.reconciled_by_id = user_id
        await self.session.flush()
        await self.session.flush()

        return CreateMatchedReceiptResponse(
            statement_id=statement.id,
            match_id=match.id,
            receipt_id=receipt.id,
            receipt_number=receipt.receipt_number,
            loan_account_id=receipt.loan_account_id,
            receipt_amount=receipt.receipt_amount,
            allocated_amount=receipt.allocated_amount,
            unallocated_amount=receipt.unallocated_amount,
            statement_status=statement.reconciliation_status.value,
            match_confidence=match.match_confidence,
            match_type=match.match_type,
            match_basis=match.match_basis or {},
        )

    async def _unmatched_credits(
        self,
        organization_id: UUID,
        *,
        bank_account_id: UUID | None,
        from_date: date | None,
        to_date: date | None,
        limit: int,
    ) -> list[BankStatement]:
        conditions = [
            BankStatement.organization_id == organization_id,
            BankStatement.transaction_type == StatementTransactionType.CREDIT,
            BankStatement.credit_amount > 0,
            BankStatement.deleted_at.is_(None),
            BankStatement.reconciliation_status.in_(
                [
                    ReconciliationStatus.UNRECONCILED,
                    ReconciliationStatus.PARTIALLY_MATCHED,
                ]
            ),
        ]
        if bank_account_id:
            conditions.append(BankStatement.bank_account_id == bank_account_id)
        if from_date:
            conditions.append(BankStatement.transaction_date >= from_date)
        if to_date:
            conditions.append(BankStatement.transaction_date <= to_date)

        query = (
            select(BankStatement)
            .where(and_(*conditions))
            .order_by(BankStatement.transaction_date.desc(), BankStatement.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _unmatched_credit_totals(
        self,
        organization_id: UUID,
        *,
        bank_account_id: UUID | None,
        from_date: date | None,
        to_date: date | None,
    ) -> tuple[int, Decimal]:
        conditions = [
            BankStatement.organization_id == organization_id,
            BankStatement.transaction_type == StatementTransactionType.CREDIT,
            BankStatement.credit_amount > 0,
            BankStatement.deleted_at.is_(None),
            BankStatement.reconciliation_status.in_(
                [
                    ReconciliationStatus.UNRECONCILED,
                    ReconciliationStatus.PARTIALLY_MATCHED,
                ]
            ),
        ]
        if bank_account_id:
            conditions.append(BankStatement.bank_account_id == bank_account_id)
        if from_date:
            conditions.append(BankStatement.transaction_date >= from_date)
        if to_date:
            conditions.append(BankStatement.transaction_date <= to_date)

        query = select(
            func.count(BankStatement.id),
            func.coalesce(func.sum(BankStatement.credit_amount), 0),
        ).where(and_(*conditions))
        count, amount = (await self.session.execute(query)).one()
        return int(count or 0), _decimal(amount)

    async def _best_candidate(
        self,
        organization_id: UUID,
        statement: BankStatement,
    ) -> _Candidate:
        receipt_candidate = await self._receipt_candidate(organization_id, statement)
        installment_candidate = await self._installment_candidate(organization_id, statement)
        if receipt_candidate.confidence >= installment_candidate.confidence:
            return receipt_candidate
        return installment_candidate

    async def _receipt_candidate(
        self,
        organization_id: UUID,
        statement: BankStatement,
    ) -> _Candidate:
        references = _statement_references(statement)
        date_start = statement.transaction_date - timedelta(days=3)
        date_end = statement.transaction_date + timedelta(days=3)
        query = (
            select(LoanReceipt, LoanAccount, Entity)
            .join(LoanAccount, LoanAccount.id == LoanReceipt.loan_account_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanReceipt.organization_id == organization_id,
                LoanReceipt.receipt_amount == statement.credit_amount,
                LoanReceipt.status.in_([ReceiptStatus.PENDING, ReceiptStatus.ALLOCATED]),
                LoanReceipt.bounced.is_(False),
                LoanReceipt.receipt_date >= date_start,
                LoanReceipt.receipt_date <= date_end,
            )
            .order_by(LoanReceipt.receipt_date.desc())
            .limit(10)
        )
        rows = (await self.session.execute(query)).all()
        best = _empty_candidate()
        for receipt, loan, entity in rows:
            score = Decimal("45")
            basis = ["amount_match", "date_window"]
            if receipt.instrument_number and receipt.instrument_number.upper() in references:
                score += Decimal("40")
                basis.append("reference_match")
            if _text_contains(statement.description, loan.loan_account_number):
                score += Decimal("10")
                basis.append("account_number_in_narration")
            if _text_contains(statement.description, entity.legal_name):
                score += Decimal("5")
                basis.append("borrower_name_in_narration")
            candidate = _Candidate(
                loan_account_id=loan.id,
                loan_account_number=loan.loan_account_number,
                entity_name=entity.legal_name,
                receipt_id=receipt.id,
                installment_id=None,
                due_date=receipt.receipt_date,
                due_amount=receipt.receipt_amount,
                confidence=min(score, Decimal("100")),
                match_basis=basis,
                suggested_action="LINK_RECEIPT",
            )
            if candidate.confidence > best.confidence:
                best = candidate
        return best

    async def _installment_candidate(
        self,
        organization_id: UUID,
        statement: BankStatement,
    ) -> _Candidate:
        date_start = statement.transaction_date - timedelta(days=7)
        date_end = statement.transaction_date + timedelta(days=7)
        due_amount = (
            ScheduleInstallment.principal_amount
            + ScheduleInstallment.interest_amount
            + ScheduleInstallment.penal_interest_due
            - ScheduleInstallment.principal_paid
            - ScheduleInstallment.interest_paid
            - ScheduleInstallment.penal_interest_paid
        )
        query = (
            select(ScheduleInstallment, LoanAccount, Entity, due_amount.label("due_amount"))
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status == LoanAccountStatus.ACTIVE,
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.status != InstallmentStatus.PAID,
                ScheduleInstallment.due_date >= date_start,
                ScheduleInstallment.due_date <= date_end,
                due_amount > 0,
            )
            .order_by(ScheduleInstallment.due_date)
            .limit(25)
        )
        rows = (await self.session.execute(query)).all()
        best = _empty_candidate()
        for installment, loan, entity, outstanding in rows:
            outstanding_dec = _decimal(outstanding)
            score = Decimal("15")
            basis = ["due_date_window"]
            amount_gap = abs(outstanding_dec - statement.credit_amount)
            if amount_gap <= Decimal("1"):
                score += Decimal("45")
                basis.append("exact_due_amount")
            elif statement.credit_amount < outstanding_dec:
                score += Decimal("20")
                basis.append("partial_payment_possible")
            days_gap = abs((installment.due_date - statement.transaction_date).days)
            score += max(Decimal("0"), Decimal("20") - Decimal(days_gap * 2))
            if _text_contains(statement.description, loan.loan_account_number):
                score += Decimal("15")
                basis.append("account_number_in_narration")
            if _text_contains(statement.description, entity.legal_name):
                score += Decimal("5")
                basis.append("borrower_name_in_narration")
            candidate = _Candidate(
                loan_account_id=loan.id,
                loan_account_number=loan.loan_account_number,
                entity_name=entity.legal_name,
                receipt_id=None,
                installment_id=installment.id,
                due_date=installment.due_date,
                due_amount=outstanding_dec,
                confidence=min(score, Decimal("100")),
                match_basis=basis,
                suggested_action="CREATE_RECEIPT" if score >= Decimal("65") else "REVIEW",
            )
            if candidate.confidence > best.confidence:
                best = candidate
        return best

    def _summary_from_candidates(
        self,
        statements: list[BankStatement],
        candidates: list[RepaymentMatchCandidate],
    ) -> RepaymentMatchingSummary:
        high_confidence_count = sum(1 for c in candidates if c.confidence >= Decimal("80"))
        review_required_count = sum(1 for c in candidates if c.confidence < Decimal("80"))
        return RepaymentMatchingSummary(
            unmatched_credit_count=len(statements),
            unmatched_credit_amount=sum((s.credit_amount for s in statements), Decimal("0")),
            high_confidence_count=high_confidence_count,
            review_required_count=review_required_count,
        )


def _empty_candidate() -> _Candidate:
    return _Candidate(
        loan_account_id=None,
        loan_account_number=None,
        entity_name=None,
        receipt_id=None,
        installment_id=None,
        due_date=None,
        due_amount=None,
        confidence=Decimal("0"),
        match_basis=[],
        suggested_action="REVIEW",
    )


def _statement_references(statement: BankStatement) -> list[str]:
    values = [
        statement.reference_number,
        statement.utr_number,
        statement.cheque_number,
        statement.bank_transaction_id,
    ]
    return [value.strip().upper() for value in values if value and value.strip()]


def _text_contains(text: str | None, needle: str | None) -> bool:
    if not text or not needle:
        return False
    return needle.upper() in text.upper()


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))
