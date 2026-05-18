"""Audit cold-partition archival (STAGE-5-PENDING-003 closure).

CLAUDE.md §7.1 / §8.5 mandates audit retention of 7 years (financial) and 2 years
(login) — that's 7+ years of live `txn_audit_log` rows if nothing moves. This
module moves old rows into year-partitioned cold tables so the hot table stays
query-fast while retention obligations are preserved.

Strategy — purposely simple:

  * Retention cutoffs computed at call time (``as_of - 7 years`` for financial,
    ``as_of - 2 years`` for ``LOGIN``/``LOGOUT``/``LOGIN_FAILED``).
  * Rows older than the applicable cutoff are copied into ``txn_audit_log_archive_YYYY``
    (one table per calendar year, created on demand) then deleted from the live
    table — inside a single transaction so partial moves aren't observable.
  * Archive tables are schema-identical to the live table; the shape is frozen
    at migration time, so we materialise them via ``CREATE TABLE ... (LIKE
    txn_audit_log INCLUDING DEFAULTS INCLUDING INDEXES INCLUDING CONSTRAINTS)``.
  * The archive table also gets a row-level hash-chain anchor so tampered
    archive rows surface in the same verify endpoint used for the live table
    (STAGE-5-011). That runs in `build_chain` separately; nothing to do here.

We deliberately do NOT use native Postgres declarative partitioning — it would
require rewriting the live table as partitioned, which is a bigger change than
this project wants at this stage. Instead we mimic it with parallel tables.

All logic is DB-free here; the service takes a session and uses bind-param SQL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Action codes that follow the shorter (2-year) retention. Everything else is
# treated as "financial" and retained for 7 years.
LOGIN_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "LOGIN",
        "LOGOUT",
        "LOGIN_FAILED",
    }
)

# Retention windows in days (approximated — 365/year is close enough for the
# monthly cron; we're not shaving hours off retention boundaries).
_FINANCIAL_RETENTION_DAYS: Final[int] = 7 * 365
_LOGIN_RETENTION_DAYS: Final[int] = 2 * 365

# Archive-table name pattern: ``txn_audit_log_archive_<year>`` where <year> is
# the 4-digit calendar year of ``changed_at``. A single regex pins the naming
# contract so we don't accidentally drift in two places.
_ARCHIVE_TABLE_RE: Final[re.Pattern[str]] = re.compile(r"^txn_audit_log_archive_\d{4}$")


@dataclass(frozen=True)
class ArchivalResult:
    """What the job did this run. Emitted so alerts + audit rows can consume it."""

    as_of: datetime
    financial_cutoff: datetime  # rows with changed_at < this were eligible for archival
    login_cutoff: datetime
    rows_archived: int
    archive_tables_used: list[str]  # alphabetical


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _financial_cutoff(as_of: datetime) -> datetime:
    return as_of - timedelta(days=_FINANCIAL_RETENTION_DAYS)


def _login_cutoff(as_of: datetime) -> datetime:
    return as_of - timedelta(days=_LOGIN_RETENTION_DAYS)


def archive_table_for_year(year: int) -> str:
    """Stable, predictable archive-table name for a given calendar year."""
    if not 1900 <= year <= 9999:
        raise ValueError(f"Year {year} outside 4-digit range")
    return f"txn_audit_log_archive_{year}"


def is_archive_table(name: str) -> bool:
    """Narrow predicate so external callers can enumerate/introspect safely."""
    return bool(_ARCHIVE_TABLE_RE.match(name))


# ---------------------------------------------------------------------------
# DDL: archive table creation on demand.
# ---------------------------------------------------------------------------


async def ensure_archive_table(session: AsyncSession, year: int) -> str:
    """Create the archive table for ``year`` if it doesn't already exist.

    Uses ``LIKE`` so the archive row shape can never drift from the live one —
    any future migration that adds a column to ``txn_audit_log`` will transparently
    propagate to every subsequent archive-table creation. Existing archives stay
    frozen at the shape they had at creation; that's fine because we never
    add-columns-to-ancient-archives as a compliance practice.
    """
    table = archive_table_for_year(year)
    # `CREATE TABLE IF NOT EXISTS` with `LIKE` is idempotent in Postgres and
    # safe to call on every run.
    await session.execute(
        text(
            f"CREATE TABLE IF NOT EXISTS {table} "
            f"(LIKE txn_audit_log INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)"
        )
    )
    return table


# ---------------------------------------------------------------------------
# The one-shot job.
# ---------------------------------------------------------------------------


async def archive_old_audit_rows(
    session: AsyncSession,
    *,
    as_of: datetime | None = None,
    dry_run: bool = False,
) -> ArchivalResult:
    """Move audit rows past their retention horizon into ``_archive_<year>`` tables.

    Args:
        session: Active DB session; the whole operation runs in one transaction.
        as_of: Reference timestamp (usually ``now``). Tests pass a fixed value.
        dry_run: If True, report what *would* move but don't move it. Useful
            for the first prod run so operators can sanity-check volumes.

    Retention rules (CLAUDE.md §8.5):
      * Login events (``LOGIN``/``LOGOUT``/``LOGIN_FAILED``) — keep 2 years.
      * Everything else — keep 7 years.

    Both filters apply: a row is eligible only if
    ``changed_at < financial_cutoff``, OR it's a login action with
    ``changed_at < login_cutoff``.

    Returns an :class:`ArchivalResult` so callers can log + alert on row
    counts. Does NOT emit an audit row for the archival itself — the job is
    administrative and the idempotency / re-run safety is what matters.
    """
    now = as_of or datetime.now(UTC)
    fin_cut = _financial_cutoff(now)
    login_cut = _login_cutoff(now)

    # 1. Find the distinct years that have at least one eligible row. We
    #    materialise the archive table once per year, not per row.
    year_rows = await session.execute(
        text("""
            SELECT DISTINCT EXTRACT(YEAR FROM changed_at)::int AS yr
            FROM txn_audit_log
            WHERE (
                (action NOT IN :login_actions AND changed_at < :fin_cut)
                OR (action IN :login_actions AND changed_at < :login_cut)
            )
            ORDER BY yr
            """).bindparams(
            login_actions=tuple(LOGIN_ACTIONS),
            fin_cut=fin_cut,
            login_cut=login_cut,
        )
    )
    years: list[int] = [row.yr for row in year_rows]

    if not years:
        return ArchivalResult(
            as_of=now,
            financial_cutoff=fin_cut,
            login_cutoff=login_cut,
            rows_archived=0,
            archive_tables_used=[],
        )

    if dry_run:
        count_row = await session.execute(
            text("""
                SELECT COUNT(*) AS c
                FROM txn_audit_log
                WHERE (
                    (action NOT IN :login_actions AND changed_at < :fin_cut)
                    OR (action IN :login_actions AND changed_at < :login_cut)
                )
                """).bindparams(
                login_actions=tuple(LOGIN_ACTIONS),
                fin_cut=fin_cut,
                login_cut=login_cut,
            )
        )
        total = int(count_row.scalar() or 0)
        return ArchivalResult(
            as_of=now,
            financial_cutoff=fin_cut,
            login_cutoff=login_cut,
            rows_archived=total,
            archive_tables_used=[archive_table_for_year(y) for y in years],
        )

    # 2. For each year, create the archive table if it doesn't exist, INSERT
    #    the eligible rows, then DELETE them from the live table. The whole
    #    loop runs inside the caller's transaction so a mid-loop failure
    #    rolls back cleanly.
    tables_used: list[str] = []
    total_moved = 0
    for year in years:
        table = await ensure_archive_table(session, year)
        tables_used.append(table)

        # Postgres RETURNING lets us count without a follow-up SELECT.
        moved = await session.execute(
            text(f"""
                WITH moved AS (
                    DELETE FROM txn_audit_log
                    WHERE EXTRACT(YEAR FROM changed_at)::int = :year
                      AND (
                        (action NOT IN :login_actions AND changed_at < :fin_cut)
                        OR (action IN :login_actions AND changed_at < :login_cut)
                      )
                    RETURNING *
                )
                INSERT INTO {table}
                SELECT * FROM moved
                RETURNING id
                """).bindparams(
                year=year,
                login_actions=tuple(LOGIN_ACTIONS),
                fin_cut=fin_cut,
                login_cut=login_cut,
            )
        )
        total_moved += len(list(moved))

    return ArchivalResult(
        as_of=now,
        financial_cutoff=fin_cut,
        login_cutoff=login_cut,
        rows_archived=total_moved,
        archive_tables_used=sorted(tables_used),
    )
