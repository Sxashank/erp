"""Audit cold-partition archival tests (STAGE-5-PENDING-003 closure).

Retention rules under test:
  * Login events (LOGIN / LOGOUT / LOGIN_FAILED) — 2-year retention.
  * Everything else (financial, lending, HR, GL, ...) — 7-year retention.

The archival logic is pure-ish: it issues SQL but doesn't own a session. We
test the pure helpers directly and the orchestrator with an ``AsyncMock`` that
recognises the three kinds of SQL it issues (year-discovery SELECT, CREATE
TABLE, and the DELETE+INSERT CTE).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.audit.audit_archival import (
    LOGIN_ACTIONS,
    ArchivalResult,
    archive_old_audit_rows,
    archive_table_for_year,
    is_archive_table,
)

# ---------------------------------------------------------------------------
# Pure helpers.
# ---------------------------------------------------------------------------


def test_login_actions_set_matches_spec() -> None:
    """CLAUDE.md §8.5 defines the login actions; pin the set so renames surface."""
    assert LOGIN_ACTIONS == {"LOGIN", "LOGOUT", "LOGIN_FAILED"}


def test_archive_table_name_is_deterministic() -> None:
    assert archive_table_for_year(2018) == "txn_audit_log_archive_2018"
    assert archive_table_for_year(2026) == "txn_audit_log_archive_2026"


@pytest.mark.parametrize("year", [1899, 0, -1, 10000])
def test_archive_table_rejects_out_of_range_years(year: int) -> None:
    with pytest.raises(ValueError, match="4-digit"):
        archive_table_for_year(year)


def test_is_archive_table_recognises_valid_names() -> None:
    assert is_archive_table("txn_audit_log_archive_2018")
    assert is_archive_table("txn_audit_log_archive_9999")


def test_is_archive_table_rejects_unrelated_names() -> None:
    assert not is_archive_table("txn_audit_log")  # live table
    assert not is_archive_table("txn_audit_log_archive_XX")  # non-digit suffix
    assert not is_archive_table("txn_audit_log_archive_20")  # too short
    assert not is_archive_table("txn_audit_log_archive_202600")  # too long
    assert not is_archive_table("")


# ---------------------------------------------------------------------------
# Orchestrator — with a session double.
# ---------------------------------------------------------------------------


class _YearResult:
    """Sync iterable of fake `Row` objects for the year-discovery query."""

    def __init__(self, years: list[int]) -> None:
        self._rows = [SimpleNamespace(yr=y) for y in years]

    def __iter__(self):
        return iter(self._rows)


class _CountResult:
    def __init__(self, total: int) -> None:
        self._total = total

    def scalar(self) -> int:
        return self._total


class _MoveResult:
    """DELETE...RETURNING result — iterable of fake rows."""

    def __init__(self, n: int) -> None:
        self._rows = [object()] * n

    def __iter__(self):
        return iter(self._rows)


def _make_session(year_rows: list[int], move_counts: dict[int, int] | None = None):
    """Build an async-mock session responding to the archival's SQL patterns."""
    moves = move_counts or {}
    call_log: list[str] = []
    pending_years: list[int] = list(year_rows)

    async def execute(stmt, *args, **kwargs):
        compiled = str(stmt).strip().upper()
        call_log.append(compiled)
        if compiled.startswith("SELECT"):
            if "COUNT(" in compiled:
                return _CountResult(sum(moves.values()))
            return _YearResult(year_rows)
        if compiled.startswith("CREATE TABLE"):
            return SimpleNamespace()
        if "DELETE FROM TXN_AUDIT_LOG" in compiled or compiled.startswith("WITH"):
            target_year = pending_years.pop(0) if pending_years else None
            count = moves.get(target_year, 0) if target_year is not None else 0
            return _MoveResult(count)
        return SimpleNamespace()

    return SimpleNamespace(execute=execute, call_log=call_log)


@pytest.mark.asyncio
async def test_archive_old_audit_rows_no_eligible_returns_empty_result() -> None:
    session = _make_session(year_rows=[])
    now = datetime(2026, 1, 15, tzinfo=UTC)

    result = await archive_old_audit_rows(session, as_of=now)

    assert result.rows_archived == 0
    assert result.archive_tables_used == []
    assert result.as_of == now
    # Retention cutoffs computed correctly — 7 years / 2 years back.
    assert result.financial_cutoff == now - timedelta(days=7 * 365)
    assert result.login_cutoff == now - timedelta(days=2 * 365)


@pytest.mark.asyncio
async def test_archive_old_audit_rows_creates_one_table_per_year() -> None:
    """Two eligible years → two CREATE TABLE statements + two DELETE/INSERTs."""
    session = _make_session(
        year_rows=[2016, 2017],
        move_counts={2016: 12, 2017: 8},
    )
    result = await archive_old_audit_rows(session)

    assert result.rows_archived == 20
    assert result.archive_tables_used == [
        "txn_audit_log_archive_2016",
        "txn_audit_log_archive_2017",
    ]

    # Sequence: 1 SELECT, then per-year pairs of CREATE + WITH ... DELETE.
    ct_count = sum(1 for stmt in session.call_log if stmt.startswith("CREATE TABLE"))
    del_count = sum(1 for stmt in session.call_log if "DELETE FROM TXN_AUDIT_LOG" in stmt)
    assert ct_count == 2
    assert del_count == 2


@pytest.mark.asyncio
async def test_archive_old_audit_rows_dry_run_counts_without_moving() -> None:
    """Dry-run reports the total count but never issues CREATE / DELETE."""
    session = _make_session(
        year_rows=[2016, 2017],
        move_counts={2016: 12, 2017: 8},
    )
    result = await archive_old_audit_rows(session, dry_run=True)

    assert result.rows_archived == 20  # taken from the COUNT(*) path
    # Archive tables listed (for the operator to know what *would* be created)
    # but never actually created.
    assert result.archive_tables_used == [
        "txn_audit_log_archive_2016",
        "txn_audit_log_archive_2017",
    ]

    ct_count = sum(1 for stmt in session.call_log if stmt.startswith("CREATE TABLE"))
    del_count = sum(1 for stmt in session.call_log if "DELETE FROM TXN_AUDIT_LOG" in stmt)
    assert ct_count == 0
    assert del_count == 0


@pytest.mark.asyncio
async def test_archival_result_is_frozen() -> None:
    """Freezing the result dataclass protects against mutation after reporting."""
    now = datetime(2026, 1, 15, tzinfo=UTC)
    result = ArchivalResult(
        as_of=now,
        financial_cutoff=now,
        login_cutoff=now,
        rows_archived=5,
        archive_tables_used=["txn_audit_log_archive_2018"],
    )
    with pytest.raises(Exception):
        # dataclass(frozen=True) raises FrozenInstanceError on set.
        result.rows_archived = 99  # type: ignore[misc]
