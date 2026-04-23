"""Bank Statement and Reconciliation Service."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.bank_reconciliation import (
    BankStatement,
    BankStatementMatch,
    BankReconciliation,
    StatementTransactionType,
    ReconciliationStatus,
    BankReconciliationStatus,
)
from app.repositories.ap_ar.bank_reconciliation_repo import (
    BankStatementRepository,
    BankStatementMatchRepository,
    BankReconciliationRepository,
    UnreconciledBookEntriesRepository,
)
from app.schemas.ap_ar.bank_reconciliation import (
    BankStatementCreate,
    BankStatementImport,
    BankStatementImportRow,
    BankStatementMatchCreate,
    BankReconciliationCreate,
    BankReconciliationUpdate,
    BRSReportItem,
    BRSReportResponse,
    ReconciliationWorkspaceResponse,
    UnreconciledBookEntry,
    UnreconciledStatementEntry,
)
from app.core.exceptions import ValidationException, NotFoundException, BadRequestException


class BankStatementService:
    """Service for bank statement operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.statement_repo = BankStatementRepository(session)
        self.match_repo = BankStatementMatchRepository(session)

    async def import_statements(
        self,
        data: BankStatementImport,
        user_id: UUID,
    ) -> tuple[int, int, list[str]]:
        """
        Import bank statements from parsed data.
        Returns (success_count, error_count, error_messages).
        """
        import_batch_id = uuid4()
        success_count = 0
        error_count = 0
        errors = []

        for idx, row in enumerate(data.rows, start=1):
            try:
                # Check for duplicate
                existing = await self.statement_repo.get_by_reference(
                    bank_account_id=data.bank_account_id,
                    reference_number=row.reference_number or f"ROW-{idx}",
                    transaction_date=row.transaction_date,
                )
                if existing:
                    errors.append(f"Row {idx}: Duplicate entry for {row.reference_number} on {row.transaction_date}")
                    error_count += 1
                    continue

                # Determine transaction type
                if row.credit_amount > 0:
                    transaction_type = StatementTransactionType.CREDIT
                else:
                    transaction_type = StatementTransactionType.DEBIT

                # Create statement entry
                statement = BankStatement(
                    bank_account_id=data.bank_account_id,
                    organization_id=data.organization_id,
                    transaction_date=row.transaction_date,
                    value_date=row.value_date or row.transaction_date,
                    reference_number=row.reference_number,
                    description=row.description,
                    transaction_type=transaction_type,
                    debit_amount=row.debit_amount,
                    credit_amount=row.credit_amount,
                    running_balance=row.running_balance,
                    cheque_number=row.cheque_number,
                    utr_number=row.utr_number,
                    reconciliation_status=ReconciliationStatus.UNRECONCILED,
                    reconciled_amount=Decimal("0.00"),
                    import_batch_id=import_batch_id,
                    import_row_number=idx,
                    created_by_id=user_id,
                )
                self.session.add(statement)
                success_count += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                error_count += 1

        if success_count > 0:
            await self.session.commit()

        return success_count, error_count, errors

    async def parse_csv_statement(
        self,
        csv_content: str,
        column_mapping: dict,
    ) -> list[BankStatementImportRow]:
        """
        Parse CSV content into statement rows.
        column_mapping: {"transaction_date": "Date", "debit_amount": "Withdrawal", ...}
        """
        rows = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                # Parse date
                date_str = row.get(column_mapping.get("transaction_date", "Date"), "")
                transaction_date = datetime.strptime(date_str, "%d/%m/%Y").date()

                # Parse amounts
                debit_str = row.get(column_mapping.get("debit_amount", "Withdrawal"), "0")
                credit_str = row.get(column_mapping.get("credit_amount", "Deposit"), "0")

                debit_amount = Decimal(debit_str.replace(",", "")) if debit_str else Decimal("0.00")
                credit_amount = Decimal(credit_str.replace(",", "")) if credit_str else Decimal("0.00")

                # Parse optional fields
                value_date_str = row.get(column_mapping.get("value_date", "Value Date"), "")
                value_date = datetime.strptime(value_date_str, "%d/%m/%Y").date() if value_date_str else None

                balance_str = row.get(column_mapping.get("running_balance", "Balance"), "")
                running_balance = Decimal(balance_str.replace(",", "")) if balance_str else None

                rows.append(BankStatementImportRow(
                    transaction_date=transaction_date,
                    value_date=value_date,
                    reference_number=row.get(column_mapping.get("reference_number", "Reference"), ""),
                    description=row.get(column_mapping.get("description", "Description"), ""),
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    running_balance=running_balance,
                    cheque_number=row.get(column_mapping.get("cheque_number", "Cheque No"), ""),
                    utr_number=row.get(column_mapping.get("utr_number", "UTR"), ""),
                ))
            except Exception:
                continue  # Skip invalid rows

        return rows

    async def get_statement(self, statement_id: UUID) -> Optional[BankStatement]:
        """Get a bank statement by ID."""
        return await self.statement_repo.get(statement_id)

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
        return await self.statement_repo.list_statements(
            bank_account_id=bank_account_id,
            organization_id=organization_id,
            from_date=from_date,
            to_date=to_date,
            reconciliation_status=reconciliation_status,
            transaction_type=transaction_type,
            search=search,
            skip=skip,
            limit=limit,
        )

    async def delete_statement(self, statement_id: UUID, user_id: UUID) -> None:
        """Delete a bank statement (soft delete)."""
        statement = await self.statement_repo.get(statement_id)
        if not statement:
            raise NotFoundException("Bank statement not found")

        if statement.reconciliation_status == ReconciliationStatus.RECONCILED:
            raise ValidationException("Cannot delete a reconciled statement")

        # Delete any matches
        await self.match_repo.delete_matches_for_statement(statement_id)

        # Soft delete
        statement.deleted_at = datetime.utcnow()
        statement.deleted_by_id = user_id
        await self.session.commit()


class BankReconciliationService:
    """Service for bank reconciliation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.statement_repo = BankStatementRepository(session)
        self.match_repo = BankStatementMatchRepository(session)
        self.recon_repo = BankReconciliationRepository(session)
        self.book_entries_repo = UnreconciledBookEntriesRepository(session)

    async def get_reconciliation_workspace(
        self,
        bank_account_id: UUID,
        from_date: date,
        to_date: date,
        bank_account_name: str,
    ) -> ReconciliationWorkspaceResponse:
        """Get all data needed for reconciliation workspace."""
        # Get unreconciled statements
        statements = await self.statement_repo.get_unreconciled(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Get unreconciled book entries
        book_entries = await self.book_entries_repo.get_unreconciled_entries(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Convert to response schemas
        unreconciled_statements = [
            UnreconciledStatementEntry(
                statement_id=s.id,
                transaction_date=s.transaction_date,
                reference_number=s.reference_number,
                description=s.description,
                debit_amount=s.debit_amount,
                credit_amount=s.credit_amount,
                unreconciled_amount=s.unreconciled_amount,
            )
            for s in statements
        ]

        unreconciled_book = [
            UnreconciledBookEntry(
                voucher_id=e["voucher_id"],
                voucher_number=e["voucher_number"],
                voucher_date=e["voucher_date"],
                narration=e["narration"],
                debit_amount=e["debit_amount"],
                credit_amount=e["credit_amount"],
                entry_type=e["entry_type"],
            )
            for e in book_entries
        ]

        # Calculate totals
        total_bank_credits = sum(s.credit_amount for s in statements)
        total_bank_debits = sum(s.debit_amount for s in statements)
        total_book_credits = sum(Decimal(e["credit_amount"]) for e in book_entries)
        total_book_debits = sum(Decimal(e["debit_amount"]) for e in book_entries)

        return ReconciliationWorkspaceResponse(
            bank_account_id=bank_account_id,
            bank_account_name=bank_account_name,
            from_date=from_date,
            to_date=to_date,
            unreconciled_statements=unreconciled_statements,
            unreconciled_book_entries=unreconciled_book,
            total_unreconciled_bank_credits=total_bank_credits,
            total_unreconciled_bank_debits=total_bank_debits,
            total_unreconciled_book_credits=total_book_credits,
            total_unreconciled_book_debits=total_book_debits,
        )

    async def match_statement_with_voucher(
        self,
        data: BankStatementMatchCreate,
        user_id: UUID,
    ) -> BankStatementMatch:
        """Match a bank statement entry with a voucher."""
        # Get statement
        statement = await self.statement_repo.get(data.statement_id)
        if not statement:
            raise NotFoundException("Bank statement not found")

        if statement.reconciliation_status == ReconciliationStatus.RECONCILED:
            raise ValidationException("Statement is already fully reconciled")

        # Validate amount
        unreconciled = statement.unreconciled_amount
        if data.matched_amount > unreconciled:
            raise ValidationException(
                f"Match amount {data.matched_amount} exceeds unreconciled amount {unreconciled}"
            )

        # Create match
        match = BankStatementMatch(
            statement_id=data.statement_id,
            voucher_id=data.voucher_id,
            matched_amount=data.matched_amount,
            match_date=date.today(),
            match_type=data.match_type,
        )
        self.session.add(match)

        # Update statement reconciliation status
        new_reconciled = statement.reconciled_amount + data.matched_amount
        statement.reconciled_amount = new_reconciled

        total_amount = (
            statement.credit_amount
            if statement.credit_amount > 0
            else statement.debit_amount
        )

        if new_reconciled >= total_amount:
            statement.reconciliation_status = ReconciliationStatus.RECONCILED
            statement.reconciled_at = datetime.utcnow()
            statement.reconciled_by_id = user_id
        else:
            statement.reconciliation_status = ReconciliationStatus.PARTIALLY_MATCHED

        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def unmatch_statement(
        self,
        match_id: UUID,
    ) -> None:
        """Remove a match between statement and voucher."""
        match = await self.match_repo.get(match_id)
        if not match:
            raise NotFoundException("Match not found")

        statement = await self.statement_repo.get(match.statement_id)
        if not statement:
            raise NotFoundException("Statement not found")

        # Update statement
        statement.reconciled_amount -= match.matched_amount
        if statement.reconciled_amount <= 0:
            statement.reconciliation_status = ReconciliationStatus.UNRECONCILED
            statement.reconciled_at = None
            statement.reconciled_by_id = None
        else:
            statement.reconciliation_status = ReconciliationStatus.PARTIALLY_MATCHED

        # Delete match
        await self.session.delete(match)
        await self.session.commit()

    async def auto_match_statements(
        self,
        bank_account_id: UUID,
        from_date: date,
        to_date: date,
        user_id: UUID,
        *,
        date_tolerance: int = 7,
        amount_tolerance: Decimal = Decimal("0.01"),
        match_by_reference: bool = True,
        match_by_cheque: bool = True,
        match_by_utr: bool = True,
        match_by_amount_only: bool = True,
    ) -> tuple[int, list[str]]:
        """
        Automatically match statements with vouchers using multiple strategies:
        1. Exact reference/cheque/UTR match (highest priority)
        2. Amount + date proximity match (fallback)

        Matching rules:
        - date_tolerance: Maximum days difference for date matching (default: 7)
        - amount_tolerance: Allowed difference in amounts (default: 0.01)
        - match_by_reference: Try to match using reference numbers
        - match_by_cheque: Try to match using cheque numbers
        - match_by_utr: Try to match using UTR numbers
        - match_by_amount_only: Fall back to amount-only matching

        Returns (match_count, messages).
        """
        matched = 0
        messages = []

        # Get unreconciled statements
        statements = await self.statement_repo.get_unreconciled(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Get unreconciled book entries
        book_entries = await self.book_entries_repo.get_unreconciled_entries(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Convert to mutable list
        available_entries = list(book_entries)

        # Try to match each statement
        for statement in statements:
            if statement.reconciliation_status == ReconciliationStatus.RECONCILED:
                continue

            statement_amount = (
                statement.credit_amount
                if statement.credit_amount > 0
                else statement.debit_amount
            )

            best_match = None
            best_score = 0
            match_reason = ""

            # Find matching book entry using priority-based scoring
            for entry in available_entries:
                # For bank credit (deposit), match with book debit (receipt entry)
                # For bank debit (withdrawal), match with book credit (payment entry)
                if statement.credit_amount > 0:
                    entry_amount = Decimal(str(entry["debit_amount"]))
                else:
                    entry_amount = Decimal(str(entry["credit_amount"]))

                # Skip if amounts don't match within tolerance
                if abs(entry_amount - statement_amount) > amount_tolerance:
                    continue

                score = 0
                reasons = []

                # Check date proximity
                date_diff = abs((statement.transaction_date - entry["voucher_date"]).days)
                if date_diff > date_tolerance:
                    continue  # Too far apart

                # Score based on date proximity (closer = higher score)
                date_score = max(0, (date_tolerance - date_diff) * 10)
                score += date_score

                # Priority 1: Exact reference number match (highest score)
                if match_by_reference and statement.reference_number and entry.get("reference_number"):
                    stmt_ref = str(statement.reference_number).strip().upper()
                    entry_ref = str(entry.get("reference_number", "")).strip().upper()
                    if stmt_ref and entry_ref and stmt_ref == entry_ref:
                        score += 1000
                        reasons.append("reference")

                # Priority 2: Cheque number match
                if match_by_cheque and statement.cheque_number and entry.get("cheque_number"):
                    stmt_chq = str(statement.cheque_number).strip().upper()
                    entry_chq = str(entry.get("cheque_number", "")).strip().upper()
                    if stmt_chq and entry_chq and stmt_chq == entry_chq:
                        score += 500
                        reasons.append("cheque")

                # Priority 3: UTR number match
                if match_by_utr and statement.utr_number and entry.get("utr_number"):
                    stmt_utr = str(statement.utr_number).strip().upper()
                    entry_utr = str(entry.get("utr_number", "")).strip().upper()
                    if stmt_utr and entry_utr and stmt_utr == entry_utr:
                        score += 500
                        reasons.append("UTR")

                # Priority 4: Amount-only match (lowest priority)
                if match_by_amount_only and score < 100:
                    # Only use amount matching if no reference matches found
                    # and within tight date window (3 days)
                    if date_diff <= 3:
                        score += 50
                        reasons.append("amount+date")

                # Check if this is the best match so far
                if score > best_score and score >= 50:  # Minimum threshold
                    best_score = score
                    best_match = entry
                    match_reason = ", ".join(reasons) if reasons else "amount"

            # Create match if found
            if best_match:
                try:
                    await self.match_statement_with_voucher(
                        BankStatementMatchCreate(
                            statement_id=statement.id,
                            voucher_id=best_match["voucher_id"],
                            matched_amount=statement_amount,
                            match_type="AUTO",
                        ),
                        user_id=user_id,
                    )
                    matched += 1
                    messages.append(
                        f"Matched '{statement.reference_number or statement.description[:30]}' "
                        f"with voucher {best_match['voucher_number']} "
                        f"(by {match_reason}, score: {best_score})"
                    )
                    # Remove from list to avoid double matching
                    available_entries.remove(best_match)
                except Exception as e:
                    messages.append(f"Failed to match: {str(e)}")

        return matched, messages

    async def create_reconciliation(
        self,
        data: BankReconciliationCreate,
        user_id: UUID,
    ) -> BankReconciliation:
        """Create a new bank reconciliation session."""
        # Check for existing reconciliation
        existing = await self.recon_repo.get_by_date(
            bank_account_id=data.bank_account_id,
            reconciliation_date=data.reconciliation_date,
        )
        if existing:
            raise ValidationException(
                f"Reconciliation already exists for {data.reconciliation_date}"
            )

        # Create reconciliation
        recon = BankReconciliation(
            bank_account_id=data.bank_account_id,
            organization_id=data.organization_id,
            reconciliation_date=data.reconciliation_date,
            from_date=data.from_date,
            to_date=data.to_date,
            statement_opening_balance=data.statement_opening_balance,
            statement_closing_balance=data.statement_closing_balance,
            book_balance=data.book_balance,
            deposits_in_transit=data.deposits_in_transit,
            outstanding_cheques=data.outstanding_cheques,
            bank_charges=data.bank_charges,
            bank_interest=data.bank_interest,
            other_adjustments=data.other_adjustments,
            notes=data.notes,
            status=BankReconciliationStatus.DRAFT,
            created_by_id=user_id,
        )

        # Calculate reconciled balance and difference
        recon.reconciled_balance = recon.calculate_reconciled_balance()
        recon.difference = recon.calculate_difference()

        self.session.add(recon)
        await self.session.commit()
        await self.session.refresh(recon)
        return recon

    async def update_reconciliation(
        self,
        reconciliation_id: UUID,
        data: BankReconciliationUpdate,
        user_id: UUID,
    ) -> BankReconciliation:
        """Update a bank reconciliation."""
        recon = await self.recon_repo.get(reconciliation_id)
        if not recon:
            raise NotFoundException("Reconciliation not found")

        if recon.status == BankReconciliationStatus.COMPLETED:
            raise ValidationException("Cannot update a completed reconciliation")

        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(recon, field, value)

        # Recalculate
        recon.reconciled_balance = recon.calculate_reconciled_balance()
        recon.difference = recon.calculate_difference()
        recon.updated_by_id = user_id

        await self.session.commit()
        await self.session.refresh(recon)
        return recon

    async def complete_reconciliation(
        self,
        reconciliation_id: UUID,
        user_id: UUID,
    ) -> BankReconciliation:
        """Complete a bank reconciliation."""
        recon = await self.recon_repo.get(reconciliation_id)
        if not recon:
            raise NotFoundException("Reconciliation not found")

        if recon.status == BankReconciliationStatus.COMPLETED:
            raise ValidationException("Reconciliation is already completed")

        # Check if difference is acceptable (within tolerance)
        if abs(recon.difference) > Decimal("1.00"):
            raise ValidationException(
                f"Cannot complete reconciliation with difference of {recon.difference}. "
                "Difference must be within 1.00"
            )

        recon.status = BankReconciliationStatus.COMPLETED
        recon.completed_at = datetime.utcnow()
        recon.completed_by_id = user_id

        await self.session.commit()
        await self.session.refresh(recon)
        return recon

    async def get_reconciliation(
        self,
        reconciliation_id: UUID,
    ) -> Optional[BankReconciliation]:
        """Get a reconciliation by ID."""
        return await self.recon_repo.get(reconciliation_id)

    async def get_latest_reconciliation(
        self,
        bank_account_id: UUID,
    ) -> Optional[BankReconciliation]:
        """Get the latest reconciliation for a bank account."""
        return await self.recon_repo.get_latest(bank_account_id)

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
        return await self.recon_repo.list_reconciliations(
            bank_account_id=bank_account_id,
            organization_id=organization_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

    async def generate_brs_report(
        self,
        bank_account_id: UUID,
        bank_account_name: str,
        reconciliation_date: date,
        from_date: date,
        to_date: date,
        statement_opening_balance: Decimal,
        statement_closing_balance: Decimal,
        book_opening_balance: Decimal,
        book_closing_balance: Decimal,
    ) -> BRSReportResponse:
        """Generate Bank Reconciliation Statement report."""
        # Get unreconciled statements
        statements = await self.statement_repo.get_unreconciled(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Get unreconciled book entries
        book_entries = await self.book_entries_repo.get_unreconciled_entries(
            bank_account_id=bank_account_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Categorize items
        deposits_in_transit = []  # Credits in books, not in bank
        outstanding_cheques = []  # Debits in books, not in bank
        credits_in_bank_not_books = []  # Credits in bank, not in books
        debits_in_bank_not_books = []  # Debits in bank, not in books

        # Process unreconciled book entries
        for entry in book_entries:
            item = BRSReportItem(
                id=entry["voucher_id"],
                date=entry["voucher_date"],
                reference=entry["voucher_number"],
                description=entry["narration"],
                amount=Decimal(entry["debit_amount"]) if entry["debit_amount"] > 0 else Decimal(entry["credit_amount"]),
                item_type="DEPOSIT_IN_TRANSIT" if entry["debit_amount"] > 0 else "OUTSTANDING_CHEQUE",
            )
            if entry["debit_amount"] > 0:
                deposits_in_transit.append(item)
            else:
                outstanding_cheques.append(item)

        # Process unreconciled bank statements
        for stmt in statements:
            item = BRSReportItem(
                id=stmt.id,
                date=stmt.transaction_date,
                reference=stmt.reference_number or "",
                description=stmt.description,
                amount=stmt.credit_amount if stmt.credit_amount > 0 else stmt.debit_amount,
                item_type="CREDIT_IN_BANK" if stmt.credit_amount > 0 else "DEBIT_IN_BANK",
            )
            if stmt.credit_amount > 0:
                credits_in_bank_not_books.append(item)
            else:
                debits_in_bank_not_books.append(item)

        # Calculate totals
        total_deposits_in_transit = sum(item.amount for item in deposits_in_transit)
        total_outstanding_cheques = sum(item.amount for item in outstanding_cheques)
        total_credits_not_in_books = sum(item.amount for item in credits_in_bank_not_books)
        total_debits_not_in_books = sum(item.amount for item in debits_in_bank_not_books)

        # Calculate reconciled balance
        # Book balance + Deposits in transit - Outstanding cheques + Credits not in books - Debits not in books
        reconciled_balance = (
            book_closing_balance
            + total_deposits_in_transit
            - total_outstanding_cheques
            + total_credits_not_in_books
            - total_debits_not_in_books
        )

        difference = statement_closing_balance - reconciled_balance

        return BRSReportResponse(
            bank_account_id=bank_account_id,
            bank_account_name=bank_account_name,
            reconciliation_date=reconciliation_date,
            from_date=from_date,
            to_date=to_date,
            statement_opening_balance=statement_opening_balance,
            statement_closing_balance=statement_closing_balance,
            book_opening_balance=book_opening_balance,
            book_closing_balance=book_closing_balance,
            deposits_in_transit=deposits_in_transit,
            outstanding_cheques=outstanding_cheques,
            credits_in_bank_not_books=credits_in_bank_not_books,
            debits_in_bank_not_books=debits_in_bank_not_books,
            total_deposits_in_transit=total_deposits_in_transit,
            total_outstanding_cheques=total_outstanding_cheques,
            total_credits_not_in_books=total_credits_not_in_books,
            total_debits_not_in_books=total_debits_not_in_books,
            reconciled_balance=reconciled_balance,
            difference=difference,
        )
