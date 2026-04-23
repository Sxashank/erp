"""BRS matching golden tests (STAGE-4-PENDING-008 closure).

Covers: reference-first match, amount+date fallback, tolerance, stale-cheque
aging, unbooked credits/debits, unreconciled books.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.core.brs_matching import (
    DEFAULT_AMOUNT_TOLERANCE,
    STALE_CHEQUE_DAYS,
    BookEntry,
    BRSMatchStatus,
    StatementEntry,
    match_statement,
    summarise,
)


TODAY = date(2026, 4, 23)


# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------

def test_default_tolerance_is_one_rupee() -> None:
    assert DEFAULT_AMOUNT_TOLERANCE == Decimal("1.00")


def test_stale_cheque_window_is_90_days() -> None:
    assert STALE_CHEQUE_DAYS == 90


# ---------------------------------------------------------------------------
# Reference-first match.
# ---------------------------------------------------------------------------

def test_exact_reference_match_within_tolerance() -> None:
    books = [
        BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("10000"), reference="CHQ-1001"),
    ]
    stmt = [
        StatementEntry(id="s1", date=date(2026, 4, 22), amount=Decimal("10000.50"), reference="CHQ-1001"),
    ]
    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    assert len(out) == 1
    assert out[0].status == BRSMatchStatus.MATCHED
    assert out[0].book_entry_id == "b1"
    assert out[0].statement_entry_id == "s1"
    assert out[0].amount_delta == Decimal("0.50")


def test_reference_match_but_amount_outside_tolerance_is_mismatch() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("10000"), reference="CHQ-1001")]
    stmt = [
        StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("10200"), reference="CHQ-1001"),
    ]
    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    assert out[0].status == BRSMatchStatus.AMOUNT_MISMATCH
    assert out[0].amount_delta == Decimal("200")


def test_reference_match_is_case_insensitive_and_space_tolerant() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("5000"), reference="  utr-abc123  ")]
    stmt = [
        StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("5000"), reference="UTR-ABC123"),
    ]
    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    assert out[0].status == BRSMatchStatus.MATCHED


# ---------------------------------------------------------------------------
# Amount + date fallback.
# ---------------------------------------------------------------------------

def test_amount_date_fallback_without_reference() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("3500"))]
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 21), amount=Decimal("3500"))]
    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    assert out[0].status == BRSMatchStatus.MATCHED


def test_date_outside_window_does_not_match() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("3500"))]
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 24), amount=Decimal("3500"))]  # 4-day gap
    out = match_statement(books=books, statement=stmt, as_of=TODAY, date_window_days=3)
    # Book is unreconciled; statement is unbooked credit.
    statuses = {r.status for r in out}
    assert BRSMatchStatus.UNRECONCILED_BOOK in statuses
    assert BRSMatchStatus.UNBOOKED_CREDIT in statuses


def test_amount_outside_tolerance_does_not_match_in_fallback() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("3500"))]
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("3502"))]
    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    statuses = {r.status for r in out}
    assert BRSMatchStatus.UNRECONCILED_BOOK in statuses
    assert BRSMatchStatus.UNBOOKED_CREDIT in statuses


def test_custom_tolerance_accepts_wider_delta() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 20), amount=Decimal("3500"))]
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("3502"))]
    out = match_statement(
        books=books, statement=stmt, as_of=TODAY, amount_tolerance=Decimal("5")
    )
    assert out[0].status == BRSMatchStatus.MATCHED


# ---------------------------------------------------------------------------
# Stale cheques.
# ---------------------------------------------------------------------------

def test_unmatched_cheque_older_than_90_days_flagged_stale() -> None:
    books = [
        BookEntry(id="b1", date=date(2026, 1, 10), amount=Decimal("10000"), reference="CHQ-500"),
    ]
    out = match_statement(books=books, statement=[], as_of=date(2026, 4, 20))
    assert out[0].status == BRSMatchStatus.STALE_CHEQUE
    assert out[0].days_aged == 100


def test_unmatched_cheque_within_90_days_is_unreconciled() -> None:
    books = [
        BookEntry(id="b1", date=date(2026, 3, 1), amount=Decimal("10000"), reference="CHQ-500"),
    ]
    out = match_statement(books=books, statement=[], as_of=date(2026, 4, 20))
    assert out[0].status == BRSMatchStatus.UNRECONCILED_BOOK
    assert out[0].days_aged == 50


def test_custom_stale_window() -> None:
    books = [BookEntry(id="b1", date=date(2026, 4, 1), amount=Decimal("5000"))]
    out = match_statement(
        books=books, statement=[], as_of=date(2026, 4, 15), stale_cheque_days=10
    )
    assert out[0].status == BRSMatchStatus.STALE_CHEQUE


# ---------------------------------------------------------------------------
# Unbooked credits and debits.
# ---------------------------------------------------------------------------

def test_statement_credit_without_book_entry_is_unbooked_credit() -> None:
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("1000"))]
    out = match_statement(books=[], statement=stmt, as_of=TODAY)
    assert out[0].status == BRSMatchStatus.UNBOOKED_CREDIT


def test_statement_debit_without_book_entry_is_unbooked_debit() -> None:
    stmt = [StatementEntry(id="s1", date=date(2026, 4, 20), amount=Decimal("-500"))]
    out = match_statement(books=[], statement=stmt, as_of=TODAY)
    assert out[0].status == BRSMatchStatus.UNBOOKED_DEBIT


# ---------------------------------------------------------------------------
# Realistic multi-entry scenario.
# ---------------------------------------------------------------------------

def test_realistic_month_end_reconciliation() -> None:
    books = [
        # Clean match: cheque issued + cleared.
        BookEntry(id="b1", date=date(2026, 4, 15), amount=Decimal("-10000"), reference="CHQ-2001"),
        # Amount mismatch: bank charges added.
        BookEntry(id="b2", date=date(2026, 4, 18), amount=Decimal("-5000"), reference="NEFT-XYZ"),
        # Stale cheque: issued in January, never cleared.
        BookEntry(id="b3", date=date(2026, 1, 10), amount=Decimal("-7500"), reference="CHQ-1700"),
        # Recent unreconciled — cheque on the way.
        BookEntry(id="b4", date=date(2026, 4, 20), amount=Decimal("-3500"), reference="CHQ-2050"),
    ]
    stmt = [
        StatementEntry(id="s1", date=date(2026, 4, 16), amount=Decimal("-10000"), reference="CHQ-2001"),
        StatementEntry(id="s2", date=date(2026, 4, 18), amount=Decimal("-5250"), reference="NEFT-XYZ"),
        # Unbooked credit — loan payment received we haven't booked.
        StatementEntry(id="s3", date=date(2026, 4, 22), amount=Decimal("50000"), reference="UTR-IMPS"),
    ]

    out = match_statement(books=books, statement=stmt, as_of=TODAY)
    by_status = summarise(out)

    assert by_status[BRSMatchStatus.MATCHED] == 1          # b1-s1
    assert by_status[BRSMatchStatus.AMOUNT_MISMATCH] == 1  # b2-s2 (₹250 bank charge)
    assert by_status[BRSMatchStatus.STALE_CHEQUE] == 1     # b3
    assert by_status[BRSMatchStatus.UNRECONCILED_BOOK] == 1  # b4
    assert by_status[BRSMatchStatus.UNBOOKED_CREDIT] == 1  # s3


def test_empty_inputs_produce_empty_result() -> None:
    assert match_statement(books=[], statement=[], as_of=TODAY) == []


def test_summarise_reports_zero_counts_for_unseen_statuses() -> None:
    counts = summarise([])
    for status in BRSMatchStatus:
        assert counts.get(status, 0) == 0
