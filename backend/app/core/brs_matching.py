"""Bank reconciliation matching helpers (STAGE-4-PENDING-008 closure).

CLAUDE.md §4.4 / §7.1:
  - Auto-match on (reference, amount, date±n_days) within ±₹1 tolerance.
  - Stale-cheque aging > 90 days → flagged.
  - Unbooked credits / debits (on statement but not in books) flagged.
  - Unreconciled books entries (in books but not on statement) flagged.

Pure helpers imported by `BRSService` — no DB, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Iterable

DEFAULT_AMOUNT_TOLERANCE = Decimal("1.00")   # ±₹1
DEFAULT_DATE_WINDOW_DAYS = 3
STALE_CHEQUE_DAYS = 90


class BRSMatchStatus(str, Enum):
    MATCHED = "matched"
    AMOUNT_MISMATCH = "amount_mismatch"
    UNBOOKED_CREDIT = "unbooked_credit"       # on statement, not in books, inflow
    UNBOOKED_DEBIT = "unbooked_debit"         # on statement, not in books, outflow
    UNRECONCILED_BOOK = "unreconciled_book"   # in books, not on statement
    STALE_CHEQUE = "stale_cheque"             # book entry > 90 days old, no match


@dataclass(frozen=True)
class BookEntry:
    """Single entry in the company's own cash/bank book."""
    id: str
    date: date
    amount: Decimal          # signed: + = inflow, - = outflow
    reference: str | None = None  # cheque no, UTR, etc.


@dataclass(frozen=True)
class StatementEntry:
    """Single line from the bank's statement."""
    id: str
    date: date
    amount: Decimal          # signed: + = credit in account, - = debit
    reference: str | None = None


@dataclass(frozen=True)
class BRSMatchResult:
    status: BRSMatchStatus
    book_entry_id: str | None
    statement_entry_id: str | None
    book_amount: Decimal | None = None
    statement_amount: Decimal | None = None
    amount_delta: Decimal | None = None
    days_aged: int | None = None


def _within_tolerance(a: Decimal, b: Decimal, tolerance: Decimal) -> bool:
    return abs(a - b) <= tolerance


def _dates_close(a: date, b: date, window_days: int) -> bool:
    return abs((a - b).days) <= window_days


def match_statement(
    *,
    books: Iterable[BookEntry],
    statement: Iterable[StatementEntry],
    as_of: date,
    amount_tolerance: Decimal = DEFAULT_AMOUNT_TOLERANCE,
    date_window_days: int = DEFAULT_DATE_WINDOW_DAYS,
    stale_cheque_days: int = STALE_CHEQUE_DAYS,
) -> list[BRSMatchResult]:
    """Reconcile a book + statement pair.

    Matching rules in priority order:
      1. Exact reference match (amount within tolerance, date within window).
      2. Fall-back amount + date match (no reference required).
      3. Remainder → unmatched in either direction.

    A book entry older than `stale_cheque_days` with no match is flagged
    STALE_CHEQUE (accountant must write it off or re-issue).
    """
    book_list = list(books)
    stmt_list = list(statement)

    # Index helpers.
    matched_book_ids: set[str] = set()
    matched_stmt_ids: set[str] = set()
    results: list[BRSMatchResult] = []

    # ------- Pass 1: exact reference match -------
    stmt_by_ref: dict[str, list[StatementEntry]] = {}
    for s in stmt_list:
        if s.reference:
            stmt_by_ref.setdefault(s.reference.strip().upper(), []).append(s)

    for b in book_list:
        if not b.reference:
            continue
        candidates = stmt_by_ref.get(b.reference.strip().upper(), [])
        for s in candidates:
            if s.id in matched_stmt_ids:
                continue
            if not _dates_close(b.date, s.date, date_window_days):
                continue
            delta = abs(b.amount - s.amount)
            if delta <= amount_tolerance:
                matched_book_ids.add(b.id)
                matched_stmt_ids.add(s.id)
                results.append(
                    BRSMatchResult(
                        status=BRSMatchStatus.MATCHED,
                        book_entry_id=b.id,
                        statement_entry_id=s.id,
                        book_amount=b.amount,
                        statement_amount=s.amount,
                        amount_delta=delta,
                    )
                )
                break
            # Reference + date match but amount outside tolerance:
            # report the mismatch and stop considering this book entry.
            matched_book_ids.add(b.id)
            matched_stmt_ids.add(s.id)
            results.append(
                BRSMatchResult(
                    status=BRSMatchStatus.AMOUNT_MISMATCH,
                    book_entry_id=b.id,
                    statement_entry_id=s.id,
                    book_amount=b.amount,
                    statement_amount=s.amount,
                    amount_delta=delta,
                )
            )
            break

    # ------- Pass 2: amount + date fallback -------
    for b in book_list:
        if b.id in matched_book_ids:
            continue
        for s in stmt_list:
            if s.id in matched_stmt_ids:
                continue
            if not _dates_close(b.date, s.date, date_window_days):
                continue
            if _within_tolerance(b.amount, s.amount, amount_tolerance):
                matched_book_ids.add(b.id)
                matched_stmt_ids.add(s.id)
                results.append(
                    BRSMatchResult(
                        status=BRSMatchStatus.MATCHED,
                        book_entry_id=b.id,
                        statement_entry_id=s.id,
                        book_amount=b.amount,
                        statement_amount=s.amount,
                        amount_delta=abs(b.amount - s.amount),
                    )
                )
                break

    # ------- Unmatched books -------
    for b in book_list:
        if b.id in matched_book_ids:
            continue
        aged = (as_of - b.date).days
        if aged > stale_cheque_days:
            results.append(
                BRSMatchResult(
                    status=BRSMatchStatus.STALE_CHEQUE,
                    book_entry_id=b.id,
                    statement_entry_id=None,
                    book_amount=b.amount,
                    days_aged=aged,
                )
            )
        else:
            results.append(
                BRSMatchResult(
                    status=BRSMatchStatus.UNRECONCILED_BOOK,
                    book_entry_id=b.id,
                    statement_entry_id=None,
                    book_amount=b.amount,
                    days_aged=aged,
                )
            )

    # ------- Unmatched statement lines -------
    for s in stmt_list:
        if s.id in matched_stmt_ids:
            continue
        if s.amount >= 0:
            status = BRSMatchStatus.UNBOOKED_CREDIT
        else:
            status = BRSMatchStatus.UNBOOKED_DEBIT
        results.append(
            BRSMatchResult(
                status=status,
                book_entry_id=None,
                statement_entry_id=s.id,
                statement_amount=s.amount,
            )
        )

    return results


def summarise(results: Iterable[BRSMatchResult]) -> dict[BRSMatchStatus, int]:
    """Bucket counts by status. Useful for dashboards + BRS reports."""
    counts: dict[BRSMatchStatus, int] = {s: 0 for s in BRSMatchStatus}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return counts
