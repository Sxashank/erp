"""GL Posting Service - Creates GL entries from vouchers and source documents."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ClosedPeriodError, NotFoundException
from app.core.constants import (
    BalanceType,
    PartyType,
    VoucherClass,
    VoucherStatus,
    GLEntryType,
    GLEntrySourceType,
)
from app.models.finance.financial_year import FinancialPeriod, FinancialYear
from app.models.finance.gl_entry import GLEntry
from app.models.finance.voucher_type import VoucherType
from app.models.finance.voucher import Voucher, VoucherLine
from app.repositories.finance.gl_entry_repo import GLEntryRepository
from app.repositories.finance.voucher_repo import VoucherRepository
from app.repositories.finance.account_repo import AccountRepository
from app.services.audit import record_financial_action
from app.schemas.finance.gl_entry import (
    GLEntryCreate,
    GLEntryResponse,
    GLEntrySummary,
    GLAccountStatement,
    GLPartyStatement,
    GLTrialBalanceItem,
    GLTrialBalanceResponse,
    GLDayBookResponse,
    GLDayBookEntry,
    GLCostCenterSummary,
    GLSourceSummary,
    GLPeriodSummary,
)


class GLPostingService:
    """
    Service for GL posting and querying.

    This service is the central point for:
    1. Creating GL entries when vouchers are posted
    2. Creating GL entries from AP/AR transactions (auto-posting)
    3. Handling reversals
    4. Querying GL for reports and statements
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_repo = GLEntryRepository(session)
        self.voucher_repo = VoucherRepository(session)
        self.account_repo = AccountRepository(session)

    # =========================================================================
    # GL Posting Methods
    # =========================================================================

    async def post_voucher(
        self,
        voucher: Voucher,
        posted_by: UUID,
        source_type: GLEntrySourceType = GLEntrySourceType.MANUAL,
        source_reference: Optional[str] = None,
        source_id: Optional[UUID] = None,
    ) -> List[GLEntry]:
        """
        Create GL entries from a voucher.

        This is called when a voucher is posted to the ledger.
        Creates one GLEntry per VoucherLine.
        """
        if posted_by is None:
            raise BadRequestException("posted_by is required for GL posting")

        await self._validate_period_open(voucher.period_id)

        existing_entries = await self.gl_repo.get_by_voucher(
            voucher_id=voucher.id,
            include_reversed=True,
        )
        if existing_entries:
            raise BadRequestException("Voucher is already posted to GL")

        normalized_lines = self._normalize_posting_lines(
            [
                {
                    "account_id": line.account_id,
                    "debit_amount": line.debit_amount,
                    "credit_amount": line.credit_amount,
                    "party_type": line.party_type,
                    "party_id": line.party_id,
                    "cost_center_id": line.cost_center_id,
                    "narration": line.narration or voucher.narration,
                    "reference_number": line.reference_number,
                    "voucher_line_id": line.id,
                }
                for line in voucher.lines
            ]
        )

        gl_entries = []
        posting_time = datetime.now(timezone.utc)

        for line in normalized_lines:
            # Get account details
            account = await self.account_repo.get(line["account_id"])
            if not account:
                raise NotFoundException(f"Account not found: {line['account_id']}")

            # Determine balance type
            balance_type = (
                BalanceType.DEBIT
                if line["debit_amount"] > 0
                else BalanceType.CREDIT
            )

            # Get next sequence number
            sequence_number = await self.gl_repo.get_next_sequence_number(
                account_id=line["account_id"],
                period_id=voucher.period_id,
            )

            # Get party name if party is set
            party_name = None
            if line.get("party_id"):
                party_name = await self._get_party_name(
                    line.get("party_type"),
                    line.get("party_id"),
                )

            # Create GL entry data
            entry_data = {
                "voucher_id": voucher.id,
                "voucher_line_id": line.get("voucher_line_id"),
                "voucher_number": voucher.voucher_number,
                "voucher_date": voucher.voucher_date,
                "entry_type": GLEntryType.NORMAL,
                "source_type": source_type,
                "source_reference": source_reference or voucher.reference_number,
                "source_id": source_id,
                "account_id": line["account_id"],
                "account_code": account.code,
                "account_name": account.name,
                "debit_amount": line["debit_amount"],
                "credit_amount": line["credit_amount"],
                "balance_type": balance_type,
                "currency_code": account.currency_code,
                "exchange_rate": Decimal("1.000000"),
                "base_debit_amount": line["debit_amount"],
                "base_credit_amount": line["credit_amount"],
                "party_type": line.get("party_type"),
                "party_id": line.get("party_id"),
                "party_name": party_name,
                "cost_center_id": line.get("cost_center_id"),
                "cost_center_code": None,  # TODO: Get from cost center master
                "financial_year_id": voucher.financial_year_id,
                "period_id": voucher.period_id,
                "narration": line.get("narration") or voucher.narration,
                "reference_number": line.get("reference_number") or voucher.reference_number,
                "reference_date": voucher.reference_date,
                "posting_date": posting_time,
                "posted_by": posted_by,
                "sequence_number": sequence_number,
                "organization_id": voucher.organization_id,
                "unit_id": voucher.unit_id,
                "created_by": posted_by,
            }

            gl_entry = await self.gl_repo.create(entry_data)
            gl_entries.append(gl_entry)

            # Update account running balance
            await self._update_account_balance(
                account_id=line["account_id"],
                debit_amount=line["debit_amount"],
                credit_amount=line["credit_amount"],
            )

        await self.session.flush()

        # Domain audit: voucher post — CLAUDE.md §8.5 / §4.3.
        # Captures the DRAFT → POSTED transition with the totals and a
        # compact snapshot of the GL footprint (one entry per line).
        total_debit = sum((line.debit_amount for line in voucher.lines), Decimal("0"))
        total_credit = sum((line.credit_amount for line in voucher.lines), Decimal("0"))
        await record_financial_action(
            self.session,
            organization_id=voucher.organization_id,
            entity_type="VOUCHER",
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action="VOUCHER_POST",
            user_id=posted_by,
            before={
                "status": VoucherStatus.DRAFT.value
                if hasattr(VoucherStatus.DRAFT, "value")
                else str(VoucherStatus.DRAFT),
                "voucher_number": voucher.voucher_number,
                "voucher_date": voucher.voucher_date,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "period_id": voucher.period_id,
            },
            after={
                "status": "POSTED",
                "voucher_number": voucher.voucher_number,
                "voucher_date": voucher.voucher_date,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "period_id": voucher.period_id,
                "posted_at": posting_time,
            },
            metadata={
                "transaction_type": "VOUCHER_POST",
                "source_type": source_type.value if hasattr(source_type, "value") else str(source_type),
                "source_reference": source_reference or voucher.reference_number,
                "source_id": str(source_id) if source_id else None,
                "gl_entry_count": len(gl_entries),
                "gl_entry_ids": [str(entry.id) for entry in gl_entries],
            },
            change_reason="Voucher posted to GL",
        )

        return gl_entries

    async def post_entries(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        period_id: UUID,
        voucher_date: date,
        source_type: GLEntrySourceType,
        source_id: UUID,
        source_reference: str,
        lines: List[Dict[str, Any]],
        narration: str,
        posted_by: UUID,
        unit_id: Optional[UUID] = None,
        is_reversal: bool = False,
        original_entry_id: Optional[UUID] = None,
    ) -> List[GLEntry]:
        """
        Canonical GL posting entry point for source documents.

        Non-manual source documents are first represented as real accounting
        vouchers, then posted to GL. This preserves the FK from GL entries to
        `txn_voucher` and keeps AP/AR, lending, fixed assets, payroll, and
        other source ledgers auditable through the same voucher backbone.
        """
        return await self.post_from_source(
            source_type=source_type,
            source_id=source_id,
            source_reference=source_reference,
            organization_id=organization_id,
            financial_year_id=financial_year_id,
            period_id=period_id,
            voucher_date=voucher_date,
            narration=narration,
            lines=lines,
            posted_by=posted_by,
            unit_id=unit_id,
            is_reversal=is_reversal,
            original_entry_id=original_entry_id,
        )

    async def post_from_source(
        self,
        source_type: GLEntrySourceType,
        source_id: UUID,
        source_reference: str,
        organization_id: UUID,
        financial_year_id: UUID,
        period_id: UUID,
        voucher_date: date,
        narration: str,
        lines: List[Dict[str, Any]],
        posted_by: UUID,
        unit_id: Optional[UUID] = None,
        is_reversal: bool = False,
        original_entry_id: Optional[UUID] = None,
    ) -> List[GLEntry]:
        """
        Create GL entries directly from a source document (AP/AR).

        This is used for auto-posting from purchase bills, sales invoices,
        payments, receipts, loan disbursements, etc.

        Each line should contain:
        - account_id: UUID
        - debit_amount: Decimal
        - credit_amount: Decimal
        - party_type: Optional[PartyType]
        - party_id: Optional[UUID]
        - cost_center_id: Optional[UUID]
        - narration: Optional[str]
        """
        if posted_by is None:
            raise BadRequestException("posted_by is required for GL posting")

        await self._validate_period_open(period_id)
        normalized_lines = self._normalize_posting_lines(lines)

        resolved_accounts = {}
        for line in normalized_lines:
            account_id = line["account_id"]
            account = await self.account_repo.get(account_id)
            if not account:
                raise NotFoundException(f"Account not found: {account_id}")
            resolved_accounts[account_id] = account

        voucher = await self._create_source_voucher(
            source_type=source_type,
            source_id=source_id,
            source_reference=source_reference,
            organization_id=organization_id,
            financial_year_id=financial_year_id,
            period_id=period_id,
            voucher_date=voucher_date,
            narration=narration,
            lines=normalized_lines,
            posted_by=posted_by,
            unit_id=unit_id,
        )

        gl_entries = []
        posting_time = datetime.now(timezone.utc)

        for line in normalized_lines:
            account_id = line["account_id"]
            debit_amount = line["debit_amount"]
            credit_amount = line["credit_amount"]
            account = resolved_accounts[account_id]

            # Determine balance type
            balance_type = BalanceType.DEBIT if debit_amount > 0 else BalanceType.CREDIT

            # Get next sequence number
            sequence_number = await self.gl_repo.get_next_sequence_number(
                account_id=account_id,
                period_id=period_id,
            )

            # Get party name if party is set
            party_type = line.get("party_type")
            party_id = line.get("party_id")
            party_name = None
            if party_id:
                party_name = await self._get_party_name(party_type, party_id)

            # Create GL entry data
            entry_data = {
                "voucher_id": voucher.id,
                "voucher_line_id": line.get("voucher_line_id"),
                "voucher_number": voucher.voucher_number,
                "voucher_date": voucher_date,
                "entry_type": GLEntryType.REVERSAL if is_reversal else GLEntryType.NORMAL,
                "source_type": source_type,
                "source_reference": source_reference,
                "source_id": source_id,
                "account_id": account_id,
                "account_code": account.code,
                "account_name": account.name,
                "debit_amount": debit_amount,
                "credit_amount": credit_amount,
                "balance_type": balance_type,
                "currency_code": account.currency_code,
                "exchange_rate": Decimal("1.000000"),
                "base_debit_amount": debit_amount,
                "base_credit_amount": credit_amount,
                "party_type": party_type,
                "party_id": party_id,
                "party_name": party_name,
                "cost_center_id": line.get("cost_center_id"),
                "cost_center_code": None,
                "financial_year_id": financial_year_id,
                "period_id": period_id,
                "narration": line.get("narration") or narration,
                "reference_number": source_reference,
                "reference_date": voucher_date,
                "original_entry_id": original_entry_id,
                "posting_date": posting_time,
                "posted_by": posted_by,
                "sequence_number": sequence_number,
                "organization_id": organization_id,
                "unit_id": unit_id,
                "created_by": posted_by,
            }

            gl_entry = await self.gl_repo.create(entry_data)
            gl_entries.append(gl_entry)

            # Update account running balance
            await self._update_account_balance(
                account_id=account_id,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
            )

        await self.session.flush()
        voucher.status = VoucherStatus.POSTED
        voucher.posted_at = posting_time
        voucher.posted_by = posted_by
        await self.session.flush()
        return gl_entries

    async def reverse_entries(
        self,
        original_voucher_id: UUID,
        reversal_voucher_id: UUID,
        reversal_date: date,
        reversed_by: UUID,
        reversal_reason: Optional[str] = None,
    ) -> List[GLEntry]:
        """
        Reverse GL entries for a voucher.

        Creates opposite entries and marks original entries as reversed.
        """
        # Get original entries
        original_entries = await self.gl_repo.get_by_voucher(
            voucher_id=original_voucher_id,
            include_reversed=False,
        )

        if not original_entries:
            raise BadRequestException("No GL entries found to reverse")

        reversal_entries = []
        posting_time = datetime.now(timezone.utc)

        for original in original_entries:
            # Get next sequence number
            sequence_number = await self.gl_repo.get_next_sequence_number(
                account_id=original.account_id,
                period_id=original.period_id,
            )

            # Create reversal entry (swap debit/credit)
            reversal_data = {
                "voucher_id": reversal_voucher_id,
                "voucher_line_id": None,
                "voucher_number": f"REV-{original.voucher_number}",
                "voucher_date": reversal_date,
                "entry_type": GLEntryType.REVERSAL,
                "source_type": original.source_type,
                "source_reference": original.source_reference,
                "source_id": original.source_id,
                "account_id": original.account_id,
                "account_code": original.account_code,
                "account_name": original.account_name,
                # Swap debit and credit
                "debit_amount": original.credit_amount,
                "credit_amount": original.debit_amount,
                "balance_type": BalanceType.CREDIT if original.balance_type == BalanceType.DEBIT else BalanceType.DEBIT,
                "currency_code": original.currency_code,
                "exchange_rate": original.exchange_rate,
                "base_debit_amount": original.base_credit_amount,
                "base_credit_amount": original.base_debit_amount,
                "party_type": original.party_type,
                "party_id": original.party_id,
                "party_name": original.party_name,
                "cost_center_id": original.cost_center_id,
                "cost_center_code": original.cost_center_code,
                "financial_year_id": original.financial_year_id,
                "period_id": original.period_id,
                "narration": f"Reversal: {reversal_reason or original.narration}",
                "reference_number": original.reference_number,
                "reference_date": reversal_date,
                "original_entry_id": original.id,
                "posting_date": posting_time,
                "posted_by": reversed_by,
                "sequence_number": sequence_number,
                "organization_id": original.organization_id,
                "unit_id": original.unit_id,
                "created_by": reversed_by,
            }

            reversal_entry = await self.gl_repo.create(reversal_data)
            reversal_entries.append(reversal_entry)

            # Mark original as reversed
            await self.gl_repo.mark_reversed(
                entry_id=original.id,
                reversal_entry_id=reversal_entry.id,
                reversal_date=reversal_date,
            )

            # Update account balance (reverse the effect)
            await self._update_account_balance(
                account_id=original.account_id,
                debit_amount=original.credit_amount,
                credit_amount=original.debit_amount,
            )

        await self.session.flush()
        return reversal_entries

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def get_entry(self, entry_id: UUID) -> Optional[GLEntry]:
        """Get a single GL entry by ID."""
        return await self.gl_repo.get(entry_id)

    async def get_entries_by_voucher(
        self,
        voucher_id: UUID,
        include_reversed: bool = False,
    ) -> List[GLEntry]:
        """Get all GL entries for a voucher."""
        return await self.gl_repo.get_by_voucher(voucher_id, include_reversed)

    async def get_entries_by_source(
        self,
        source_type: GLEntrySourceType,
        source_id: UUID,
    ) -> List[GLEntry]:
        """Get GL entries by source document."""
        return await self.gl_repo.get_by_source(source_type, source_id)

    async def search_entries(
        self,
        organization_id: UUID,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GLEntry], int]:
        """Search GL entries with filters."""
        return await self.gl_repo.search(organization_id, filters, skip, limit)

    # =========================================================================
    # Report Methods
    # =========================================================================

    async def get_account_statement(
        self,
        account_id: UUID,
        date_from: date,
        date_to: date,
        include_reversed: bool = False,
        include_opening_balance: bool = True,
    ) -> GLAccountStatement:
        """Generate account statement with running balance."""
        # Get account details
        account = await self.account_repo.get(account_id)
        if not account:
            raise NotFoundException("Account not found")

        # Get opening balance
        opening_debit = Decimal("0.00")
        opening_credit = Decimal("0.00")
        if include_opening_balance:
            opening_debit, opening_credit = await self.gl_repo.get_account_balance_before_date(
                account_id=account_id,
                before_date=date_from,
                include_reversed=include_reversed,
            )

        # Add account's own opening balance
        if account.opening_balance:
            if account.opening_balance_type == BalanceType.DEBIT:
                opening_debit += account.opening_balance
            else:
                opening_credit += account.opening_balance

        opening_balance = opening_debit - opening_credit
        opening_balance_type = BalanceType.DEBIT if opening_balance >= 0 else BalanceType.CREDIT
        opening_balance = abs(opening_balance)

        # Get entries for period
        entries, _ = await self.gl_repo.get_by_account(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            include_reversed=include_reversed,
            skip=0,
            limit=10000,  # Large limit for full statement
        )

        # Calculate totals
        total_debit = sum(e.debit_amount for e in entries)
        total_credit = sum(e.credit_amount for e in entries)

        # Calculate closing balance
        closing_balance = (
            (opening_debit + total_debit) - (opening_credit + total_credit)
        )
        closing_balance_type = BalanceType.DEBIT if closing_balance >= 0 else BalanceType.CREDIT
        closing_balance = abs(closing_balance)

        # Convert entries to response
        entry_responses = [
            GLEntryResponse(
                id=e.id,
                voucher_id=e.voucher_id,
                voucher_number=e.voucher_number,
                voucher_date=e.voucher_date,
                entry_type=e.entry_type,
                source_type=e.source_type,
                source_reference=e.source_reference,
                account_id=e.account_id,
                account_code=e.account_code,
                account_name=e.account_name,
                debit_amount=e.debit_amount,
                credit_amount=e.credit_amount,
                balance_type=e.balance_type,
                currency_code=e.currency_code,
                party_type=e.party_type,
                party_id=e.party_id,
                party_name=e.party_name,
                cost_center_id=e.cost_center_id,
                cost_center_code=e.cost_center_code,
                narration=e.narration,
                reference_number=e.reference_number,
                posting_date=e.posting_date,
                is_reversed=e.is_reversed,
                organization_id=e.organization_id,
            )
            for e in entries
        ]

        return GLAccountStatement(
            account_id=account_id,
            account_code=account.code,
            account_name=account.name,
            period_from=date_from,
            period_to=date_to,
            opening_balance=opening_balance,
            opening_balance_type=opening_balance_type,
            entries=entry_responses,
            total_debit=total_debit,
            total_credit=total_credit,
            closing_balance=closing_balance,
            closing_balance_type=closing_balance_type,
        )

    async def get_party_statement(
        self,
        party_type: PartyType,
        party_id: UUID,
        date_from: date,
        date_to: date,
        include_reversed: bool = False,
        include_opening_balance: bool = True,
    ) -> GLPartyStatement:
        """Generate party (sub-ledger) statement."""
        # Get party name
        party_name = await self._get_party_name(party_type, party_id) or "Unknown"

        # Get opening balance
        opening_debit = Decimal("0.00")
        opening_credit = Decimal("0.00")
        if include_opening_balance:
            # Get balance before date_from
            entries_before, _ = await self.gl_repo.get_by_party(
                party_type=party_type,
                party_id=party_id,
                date_to=date_from,
                include_reversed=include_reversed,
                skip=0,
                limit=10000,
            )
            for e in entries_before:
                if e.voucher_date < date_from:
                    opening_debit += e.debit_amount
                    opening_credit += e.credit_amount

        opening_balance = opening_debit - opening_credit
        opening_balance_type = BalanceType.DEBIT if opening_balance >= 0 else BalanceType.CREDIT
        opening_balance = abs(opening_balance)

        # Get entries for period
        entries, _ = await self.gl_repo.get_by_party(
            party_type=party_type,
            party_id=party_id,
            date_from=date_from,
            date_to=date_to,
            include_reversed=include_reversed,
            skip=0,
            limit=10000,
        )

        # Calculate totals
        total_debit = sum(e.debit_amount for e in entries)
        total_credit = sum(e.credit_amount for e in entries)

        # Calculate closing balance
        closing_balance = (
            (opening_debit + total_debit) - (opening_credit + total_credit)
        )
        closing_balance_type = BalanceType.DEBIT if closing_balance >= 0 else BalanceType.CREDIT
        closing_balance = abs(closing_balance)

        # Convert entries to response
        entry_responses = [
            GLEntryResponse(
                id=e.id,
                voucher_id=e.voucher_id,
                voucher_number=e.voucher_number,
                voucher_date=e.voucher_date,
                entry_type=e.entry_type,
                source_type=e.source_type,
                source_reference=e.source_reference,
                account_id=e.account_id,
                account_code=e.account_code,
                account_name=e.account_name,
                debit_amount=e.debit_amount,
                credit_amount=e.credit_amount,
                balance_type=e.balance_type,
                currency_code=e.currency_code,
                party_type=e.party_type,
                party_id=e.party_id,
                party_name=e.party_name,
                cost_center_id=e.cost_center_id,
                cost_center_code=e.cost_center_code,
                narration=e.narration,
                reference_number=e.reference_number,
                posting_date=e.posting_date,
                is_reversed=e.is_reversed,
                organization_id=e.organization_id,
            )
            for e in entries
        ]

        return GLPartyStatement(
            party_type=party_type,
            party_id=party_id,
            party_name=party_name,
            period_from=date_from,
            period_to=date_to,
            opening_balance=opening_balance,
            opening_balance_type=opening_balance_type,
            entries=entry_responses,
            total_debit=total_debit,
            total_credit=total_credit,
            closing_balance=closing_balance,
            closing_balance_type=closing_balance_type,
        )

    async def get_trial_balance(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        period_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None,
        include_zero_balance: bool = False,
    ) -> GLTrialBalanceResponse:
        """Generate trial balance report."""
        # Get trial balance data
        data = await self.gl_repo.get_trial_balance_data(
            organization_id=organization_id,
            financial_year_id=financial_year_id,
            period_id=period_id,
            as_of_date=as_of_date,
            include_reversed=False,
        )

        items = []
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        total_opening_debit = Decimal("0.00")
        total_opening_credit = Decimal("0.00")

        # Determine the opening-balance cutoff date. Opening balance is the
        # sum of all entries strictly BEFORE this date. Priority:
        #   1. If the caller passed period_id, load the period and use its
        #      start_date.
        #   2. Else if financial_year_id, load the FY and use its start_date.
        #   3. Else default to the start of the current fiscal year (April 1
        #      of `as_of_date` if that date is >= April, else previous year).
        # See CLAUDE.md §7.1 (fiscal year April-March IST).
        opening_cutoff: Optional[date] = None
        if period_id is not None:
            period_row = await self.session.get(FinancialPeriod, period_id)
            if period_row is not None:
                opening_cutoff = period_row.start_date
        if opening_cutoff is None and financial_year_id is not None:
            from app.models.finance.financial_year import FinancialYear

            fy_row = await self.session.get(FinancialYear, financial_year_id)
            if fy_row is not None:
                opening_cutoff = fy_row.start_date
        if opening_cutoff is None:
            ref = as_of_date or date.today()
            fy_start_year = ref.year if ref.month >= 4 else ref.year - 1
            opening_cutoff = date(fy_start_year, 4, 1)

        for row in data:
            debit = row["total_debit"]
            credit = row["total_credit"]
            balance = debit - credit

            # Skip zero balances if not requested
            if not include_zero_balance and balance == 0:
                continue

            # Opening balance as of `opening_cutoff`.
            open_debit, open_credit = await self.gl_repo.get_account_balance_before_date(
                row["account_id"], opening_cutoff
            )
            opening_balance = open_debit - open_credit
            opening_debit_side = opening_balance if opening_balance > 0 else Decimal("0.00")
            opening_credit_side = abs(opening_balance) if opening_balance < 0 else Decimal("0.00")

            # Closing = opening + period.
            closing_balance = opening_balance + (debit - credit)
            closing_debit = closing_balance if closing_balance > 0 else Decimal("0.00")
            closing_credit = abs(closing_balance) if closing_balance < 0 else Decimal("0.00")

            items.append(
                GLTrialBalanceItem(
                    account_id=row["account_id"],
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    opening_debit=opening_debit_side,
                    opening_credit=opening_credit_side,
                    period_debit=debit,
                    period_credit=credit,
                    closing_debit=closing_debit,
                    closing_credit=closing_credit,
                )
            )

            total_opening_debit += opening_debit_side
            total_opening_credit += opening_credit_side
            total_debit += closing_debit
            total_credit += closing_credit

        is_balanced = total_debit == total_credit

        return GLTrialBalanceResponse(
            organization_id=organization_id,
            financial_year_id=financial_year_id,
            period_id=period_id,
            as_of_date=as_of_date or date.today(),
            items=items,
            total_opening_debit=total_opening_debit,
            total_opening_credit=total_opening_credit,
            total_period_debit=sum(i.period_debit for i in items),
            total_period_credit=sum(i.period_credit for i in items),
            total_closing_debit=total_debit,
            total_closing_credit=total_credit,
            is_balanced=is_balanced,
        )

    async def get_day_book(
        self,
        organization_id: UUID,
        for_date: date,
        include_reversed: bool = False,
    ) -> GLDayBookResponse:
        """Generate day book for a specific date."""
        data = await self.gl_repo.get_day_book(
            organization_id=organization_id,
            for_date=for_date,
            include_reversed=include_reversed,
        )

        entries = [
            GLDayBookEntry(
                voucher_id=row["voucher_id"],
                voucher_number=row["voucher_number"],
                voucher_date=for_date,
                narration=row["narration"],
                total_debit=row["total_debit"],
                total_credit=row["total_credit"],
                entry_count=row["entry_count"],
            )
            for row in data
        ]

        return GLDayBookResponse(
            organization_id=organization_id,
            date=for_date,
            entries=entries,
            total_debit=sum(e.total_debit for e in entries),
            total_credit=sum(e.total_credit for e in entries),
            voucher_count=len(entries),
        )

    async def get_cost_center_summary(
        self,
        organization_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
    ) -> List[GLCostCenterSummary]:
        """Get summary by cost center."""
        data = await self.gl_repo.get_cost_center_summary(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
            include_reversed=include_reversed,
        )

        return [
            GLCostCenterSummary(
                cost_center_id=row["cost_center_id"],
                cost_center_code=row["cost_center_code"],
                total_debit=row["total_debit"],
                total_credit=row["total_credit"],
                net_amount=row["total_debit"] - row["total_credit"],
                entry_count=row["entry_count"],
            )
            for row in data
        ]

    async def get_source_summary(
        self,
        organization_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_reversed: bool = False,
    ) -> List[GLSourceSummary]:
        """Get summary by source type."""
        data = await self.gl_repo.get_source_summary(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
            include_reversed=include_reversed,
        )

        return [
            GLSourceSummary(
                source_type=row["source_type"],
                total_debit=row["total_debit"],
                total_credit=row["total_credit"],
                entry_count=row["entry_count"],
                voucher_count=row["voucher_count"],
            )
            for row in data
        ]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _validate_period_open(self, period_id: UUID) -> None:
        """Reject postings into closed or locked accounting periods."""
        period_row = await self.session.get(FinancialPeriod, period_id)
        if period_row is None:
            raise NotFoundException(f"Financial period not found: {period_id}")
        if period_row.is_closed:
            raise ClosedPeriodError(period=period_row.name)
        if period_row.is_locked:
            raise ClosedPeriodError(
                period=period_row.name,
                detail=f"Financial period '{period_row.name}' is locked for new entries",
            )

    def _normalize_posting_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize and validate source/voucher lines before any DB writes."""
        if not lines:
            raise BadRequestException("No lines provided for GL posting")

        normalized_lines: list[dict[str, Any]] = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for index, line in enumerate(lines, start=1):
            account_id = line.get("account_id")
            if not account_id:
                raise BadRequestException(f"Line {index} is missing account_id")

            debit_amount = Decimal(str(line.get("debit_amount", 0) or 0))
            credit_amount = Decimal(str(line.get("credit_amount", 0) or 0))

            if debit_amount < 0 or credit_amount < 0:
                raise BadRequestException("GL line amounts cannot be negative")
            if debit_amount > 0 and credit_amount > 0:
                raise BadRequestException(
                    "A GL line cannot have both debit and credit amounts"
                )
            if debit_amount == 0 and credit_amount == 0:
                raise BadRequestException("Zero-value GL lines are not allowed")

            total_debit += debit_amount
            total_credit += credit_amount
            normalized_lines.append(
                {
                    **line,
                    "account_id": account_id,
                    "debit_amount": debit_amount,
                    "credit_amount": credit_amount,
                }
            )

        if len(normalized_lines) < 2:
            raise BadRequestException("At least two non-zero GL lines are required")

        if total_debit <= 0 or total_credit <= 0:
            raise BadRequestException("GL posting must contain debit and credit lines")

        if total_debit != total_credit:
            raise BadRequestException(
                f"GL entries are not balanced. Debit: {total_debit}, Credit: {total_credit}"
            )

        return normalized_lines

    async def _create_source_voucher(
        self,
        source_type: GLEntrySourceType,
        source_id: UUID,
        source_reference: str,
        organization_id: UUID,
        financial_year_id: UUID,
        period_id: UUID,
        voucher_date: date,
        narration: str,
        lines: list[dict[str, Any]],
        posted_by: UUID,
        unit_id: Optional[UUID] = None,
    ) -> Voucher:
        """Create a posted system voucher that backs source-document GL entries."""
        voucher_type = await self._get_voucher_type_for_source(
            organization_id=organization_id,
            source_type=source_type,
        )

        financial_year = await self.session.get(FinancialYear, financial_year_id)
        financial_year_code = financial_year.code if financial_year else "FY"
        voucher_number = (
            voucher_type.get_next_number(financial_year_code)
            if voucher_type.auto_numbering
            else source_reference
        )

        voucher = Voucher(
            voucher_type_id=voucher_type.id,
            voucher_number=voucher_number,
            voucher_date=voucher_date,
            financial_year_id=financial_year_id,
            period_id=period_id,
            reference_number=source_reference,
            reference_date=voucher_date,
            narration=narration,
            total_debit=sum(line["debit_amount"] for line in lines),
            total_credit=sum(line["credit_amount"] for line in lines),
            status=VoucherStatus.APPROVED,
            approved_at=datetime.now(timezone.utc),
            approved_by=posted_by,
            organization_id=organization_id,
            unit_id=unit_id,
            created_by=posted_by,
        )
        self.session.add(voucher)
        await self.session.flush()

        for line_number, line in enumerate(lines, start=1):
            voucher_line = VoucherLine(
                voucher_id=voucher.id,
                line_number=line_number,
                account_id=line["account_id"],
                debit_amount=line["debit_amount"],
                credit_amount=line["credit_amount"],
                narration=line.get("narration") or narration,
                cost_center_id=line.get("cost_center_id"),
                party_type=line.get("party_type"),
                party_id=line.get("party_id"),
                reference_type=source_type.value,
                reference_id=source_id,
                reference_number=source_reference,
                created_by=posted_by,
            )
            self.session.add(voucher_line)
            await self.session.flush()
            line["voucher_line_id"] = voucher_line.id

        await self.session.refresh(voucher, attribute_names=["lines"])
        return voucher

    async def _get_voucher_type_for_source(
        self,
        organization_id: UUID,
        source_type: GLEntrySourceType,
    ) -> VoucherType:
        """Resolve the voucher type that should back a source-document posting."""
        voucher_class = self._source_voucher_class(source_type)
        query = (
            select(VoucherType)
            .where(
                and_(
                    VoucherType.organization_id == organization_id,
                    VoucherType.voucher_class == voucher_class,
                    VoucherType.is_active == True,
                )
            )
            .order_by(VoucherType.is_system.desc(), VoucherType.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        voucher_type = result.scalar_one_or_none()
        if voucher_type:
            return voucher_type

        fallback_query = (
            select(VoucherType)
            .where(
                and_(
                    VoucherType.organization_id == organization_id,
                    VoucherType.code == "JV",
                    VoucherType.is_active == True,
                )
            )
            .limit(1)
        )
        fallback_result = await self.session.execute(fallback_query)
        voucher_type = fallback_result.scalar_one_or_none()
        if voucher_type:
            return voucher_type

        raise BadRequestException(
            "No active voucher type is configured for source posting. "
            f"Configure a {voucher_class.value} or JV voucher type for this organization."
        )

    def _source_voucher_class(self, source_type: GLEntrySourceType) -> VoucherClass:
        """Map source ledgers into the accounting voucher class backbone."""
        mapping = {
            GLEntrySourceType.PURCHASE_BILL: VoucherClass.PURCHASE,
            GLEntrySourceType.SALES_INVOICE: VoucherClass.SALES,
            GLEntrySourceType.PAYMENT: VoucherClass.PAYMENT,
            GLEntrySourceType.RECEIPT: VoucherClass.RECEIPT,
            GLEntrySourceType.LOAN_RECEIPT: VoucherClass.RECEIPT,
        }
        return mapping.get(source_type, VoucherClass.JOURNAL)

    async def _update_account_balance(
        self,
        account_id: UUID,
        debit_amount: Decimal,
        credit_amount: Decimal,
    ) -> None:
        """Update account's current balance."""
        account = await self.account_repo.get(account_id)
        if account:
            current_balance = account.current_balance or Decimal("0")
            if account.current_balance_type == BalanceType.CREDIT:
                current_balance = -current_balance

            current_balance = current_balance + debit_amount - credit_amount

            if current_balance >= 0:
                account.current_balance_type = BalanceType.DEBIT
                account.current_balance = current_balance
            else:
                account.current_balance_type = BalanceType.CREDIT
                account.current_balance = abs(current_balance)

    async def _get_party_name(
        self,
        party_type: Optional[PartyType],
        party_id: Optional[UUID],
    ) -> Optional[str]:
        """Get party name from vendor/customer/employee."""
        if not party_type or not party_id:
            return None

        # Import here to avoid circular imports
        if party_type == PartyType.VENDOR:
            from app.repositories.ap_ar.vendor_repo import VendorRepository
            repo = VendorRepository(self.session)
            vendor = await repo.get(party_id)
            return vendor.name if vendor else None
        elif party_type == PartyType.CUSTOMER:
            from app.repositories.ap_ar.customer_repo import CustomerRepository
            repo = CustomerRepository(self.session)
            customer = await repo.get(party_id)
            return customer.name if customer else None
        elif party_type == PartyType.EMPLOYEE:
            # TODO: Implement employee lookup when HR module is ready
            return None

        return None
