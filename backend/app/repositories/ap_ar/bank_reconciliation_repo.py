"""Bank Statement and Reconciliation Repository."""

from datetime import date
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ap_ar.bank_reconciliation import (
    BankStatement,
    BankStatementMatch,
    BankReconciliation,
    StatementTransactionType,
    ReconciliationStatus,
    BankReconciliationStatus,
)
from app.models.finance.voucher import Voucher, VoucherLine
from app.repositories.base import BaseRepository


class BankStatementRepository(BaseRepository[BankStatement]):
    """Repository for BankStatement operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BankStatement, session)

    async def get_by_reference(
        self,
        bank_account_id: UUID,
        reference_number: str,
        transaction_date: date,
    ) -> Optional[BankStatement]:
        """Check if statement entry already exists."""
        query = select(BankStatement).where(
            and_(
                BankStatement.bank_account_id == bank_account_id,
                BankStatement.reference_number == reference_number,
                BankStatement.transaction_date == transaction_date,
                BankStatement.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_statements(
        self,
        bank_account_id: UUID,
        organization_id: UUID,
        *,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        reconciliation_status: Optional[ReconciliationStatus] = None,
        transaction_type: Optional[StatementTransactionType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[BankStatement], int]:
        """List bank statements with filters."""
        conditions = [
            BankStatement.bank_account_id == bank_account_id,
            BankStatement.organization_id == organization_id,
            BankStatement.deleted_at.is_(None),
        ]

        if from_date:
            conditions.append(BankStatement.transaction_date >= from_date)
        if to_date:
            conditions.append(BankStatement.transaction_date <= to_date)
        if reconciliation_status:
            conditions.append(BankStatement.reconciliation_status == reconciliation_status)
        if transaction_type:
            conditions.append(BankStatement.transaction_type == transaction_type)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    BankStatement.reference_number.ilike(search_term),
                    BankStatement.description.ilike(search_term),
                    BankStatement.cheque_number.ilike(search_term),
                    BankStatement.utr_number.ilike(search_term),
                )
            )

        # Count query
        count_query = select(func.count(BankStatement.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(BankStatement)
            .options(selectinload(BankStatement.matches))
            .where(and_(*conditions))
            .order_by(desc(BankStatement.transaction_date), desc(BankStatement.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        statements = result.scalars().all()

        return statements, total

    async def get_unreconciled(
        self,
        bank_account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Sequence[BankStatement]:
        """Get unreconciled statements for a period."""
        query = (
            select(BankStatement)
            .options(selectinload(BankStatement.matches))
            .where(
                and_(
                    BankStatement.bank_account_id == bank_account_id,
                    BankStatement.transaction_date >= from_date,
                    BankStatement.transaction_date <= to_date,
                    BankStatement.reconciliation_status.in_([
                        ReconciliationStatus.UNRECONCILED,
                        ReconciliationStatus.PARTIALLY_MATCHED,
                    ]),
                    BankStatement.deleted_at.is_(None),
                )
            )
            .order_by(BankStatement.transaction_date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_import_batch(
        self,
        import_batch_id: UUID,
    ) -> Sequence[BankStatement]:
        """Get all statements from an import batch."""
        query = (
            select(BankStatement)
            .where(BankStatement.import_batch_id == import_batch_id)
            .order_by(BankStatement.import_row_number)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_statement_totals(
        self,
        bank_account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Get total credits and debits for a period."""
        query = select(
            func.coalesce(func.sum(BankStatement.credit_amount), Decimal("0.00")).label("total_credits"),
            func.coalesce(func.sum(BankStatement.debit_amount), Decimal("0.00")).label("total_debits"),
        ).where(
            and_(
                BankStatement.bank_account_id == bank_account_id,
                BankStatement.transaction_date >= from_date,
                BankStatement.transaction_date <= to_date,
                BankStatement.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_credits": row.total_credits,
            "total_debits": row.total_debits,
        }


class BankStatementMatchRepository(BaseRepository[BankStatementMatch]):
    """Repository for BankStatementMatch operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BankStatementMatch, session)

    async def get_matches_for_statement(
        self,
        statement_id: UUID,
    ) -> Sequence[BankStatementMatch]:
        """Get all matches for a statement."""
        query = (
            select(BankStatementMatch)
            .options(selectinload(BankStatementMatch.voucher))
            .where(BankStatementMatch.statement_id == statement_id)
            .order_by(BankStatementMatch.match_date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_matches_for_voucher(
        self,
        voucher_id: UUID,
    ) -> Sequence[BankStatementMatch]:
        """Get all matches for a voucher."""
        query = (
            select(BankStatementMatch)
            .options(selectinload(BankStatementMatch.statement))
            .where(BankStatementMatch.voucher_id == voucher_id)
            .order_by(BankStatementMatch.match_date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_matches_for_statement(
        self,
        statement_id: UUID,
    ) -> None:
        """Delete all matches for a statement."""
        query = select(BankStatementMatch).where(
            BankStatementMatch.statement_id == statement_id
        )
        result = await self.session.execute(query)
        matches = result.scalars().all()
        for match in matches:
            await self.session.delete(match)


class BankReconciliationRepository(BaseRepository[BankReconciliation]):
    """Repository for BankReconciliation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BankReconciliation, session)

    async def get_latest(
        self,
        bank_account_id: UUID,
    ) -> Optional[BankReconciliation]:
        """Get the latest reconciliation for a bank account."""
        query = (
            select(BankReconciliation)
            .where(BankReconciliation.bank_account_id == bank_account_id)
            .order_by(desc(BankReconciliation.reconciliation_date))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_date(
        self,
        bank_account_id: UUID,
        reconciliation_date: date,
    ) -> Optional[BankReconciliation]:
        """Get reconciliation for a specific date."""
        query = select(BankReconciliation).where(
            and_(
                BankReconciliation.bank_account_id == bank_account_id,
                BankReconciliation.reconciliation_date == reconciliation_date,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_reconciliations(
        self,
        bank_account_id: UUID,
        organization_id: UUID,
        *,
        status: Optional[BankReconciliationStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[BankReconciliation], int]:
        """List reconciliations with filters."""
        conditions = [
            BankReconciliation.bank_account_id == bank_account_id,
            BankReconciliation.organization_id == organization_id,
        ]

        if status:
            conditions.append(BankReconciliation.status == status)
        if from_date:
            conditions.append(BankReconciliation.reconciliation_date >= from_date)
        if to_date:
            conditions.append(BankReconciliation.reconciliation_date <= to_date)

        # Count query
        count_query = select(func.count(BankReconciliation.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(BankReconciliation)
            .where(and_(*conditions))
            .order_by(desc(BankReconciliation.reconciliation_date))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        reconciliations = result.scalars().all()

        return reconciliations, total


class UnreconciledBookEntriesRepository:
    """Repository for getting unreconciled book entries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_unreconciled_entries(
        self,
        bank_account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> list[dict]:
        """Get unreconciled voucher lines for the bank account."""
        # Get voucher lines that affect this bank account
        # and don't have corresponding bank statement matches
        query = (
            select(
                Voucher.id.label("voucher_id"),
                Voucher.voucher_number,
                Voucher.voucher_date,
                Voucher.narration,
                VoucherLine.debit_amount,
                VoucherLine.credit_amount,
            )
            .join(VoucherLine, VoucherLine.voucher_id == Voucher.id)
            .outerjoin(
                BankStatementMatch,
                BankStatementMatch.voucher_id == Voucher.id,
            )
            .where(
                and_(
                    VoucherLine.account_id == bank_account_id,
                    Voucher.voucher_date >= from_date,
                    Voucher.voucher_date <= to_date,
                    Voucher.status == "POSTED",
                    Voucher.deleted_at.is_(None),
                    BankStatementMatch.id.is_(None),  # Not matched
                )
            )
            .order_by(Voucher.voucher_date)
        )
        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "voucher_id": row.voucher_id,
                "voucher_number": row.voucher_number,
                "voucher_date": row.voucher_date,
                "narration": row.narration,
                "debit_amount": row.debit_amount,
                "credit_amount": row.credit_amount,
                "entry_type": "JOURNAL",  # Simplified
            }
            for row in rows
        ]
