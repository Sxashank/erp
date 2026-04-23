"""Audit integrity hash chain.

CLAUDE.md §8.5: `daily integrity hash chain makes tampering detectable`.

The chain works like this: every calendar day we compute a hash over the
audit-log rows for that day + the previous day's anchor hash. The result
is stored in `audit_day_anchor` along with the row count. If anyone later
edits a historical audit row, re-computing the chain produces a different
anchor at that day and every subsequent day — tampering surfaces visibly.

This module exposes only the pure computation functions. The persistence
(daily cron, new table, verification-on-demand) is Stage 6+ scope and is
tracked in `.stubs-approved.md::STAGE-5-PENDING-audit-chain-persistence`.

Canonicalisation rules:
  - Every audit row renders as a single UTF-8 line.
  - Fields are ordered alphabetically by key.
  - Datetimes serialize as ISO-8601 with explicit timezone.
  - `None` renders as the literal string `null` (matches JSON).
  - Separators are fixed: `|` between fields, `=` between key and value,
    `\n` between rows. No dependency on spaces.

The canonical form is stable across Python versions, dict iteration
orders, and JSON encoder variants.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping

GENESIS_ANCHOR = "0" * 64  # all-zero sentinel for day 1


def _canonicalise_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, datetime):
        # Always serialize with timezone; default UTC if missing.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, (bool, int, float)):
        return str(value)
    return str(value)


def canonicalise_row(row: Mapping[str, object]) -> str:
    """Return the canonical one-line rendering of an audit row.

    Order is enforced by `sorted(keys)`. No user-controlled field can
    change the serialization shape."""
    parts = []
    for key in sorted(row.keys()):
        parts.append(f"{key}={_canonicalise_value(row[key])}")
    return "|".join(parts)


def compute_day_anchor(
    *,
    rows: Iterable[Mapping[str, object]],
    previous_anchor: str = GENESIS_ANCHOR,
) -> str:
    """Return the SHA-256 hex anchor for a day.

    Inputs:
      rows:              the audit rows for the day, in deterministic order
                         (the caller must sort by (created_at, id)).
      previous_anchor:   the prior day's anchor, or GENESIS_ANCHOR for day 1.
    """
    h = hashlib.sha256()
    h.update(previous_anchor.encode("utf-8"))
    h.update(b"\n")
    for row in rows:
        h.update(canonicalise_row(row).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


@dataclass(frozen=True)
class DayChainResult:
    day: str  # ISO date string (yyyy-mm-dd)
    row_count: int
    anchor: str
    previous_anchor: str


def build_chain(
    *,
    rows_by_day: Mapping[str, Iterable[Mapping[str, object]]],
    seed: str = GENESIS_ANCHOR,
) -> list[DayChainResult]:
    """Build anchors for a sequence of days.

    Args:
      rows_by_day:  ordered mapping of ISO date → iterable of rows.
      seed:         the anchor to roll from (GENESIS_ANCHOR at day 1, or
                    the last-known anchor from the previous verified
                    run).
    """
    results: list[DayChainResult] = []
    previous = seed
    for day, rows in rows_by_day.items():
        rows_list = list(rows)
        anchor = compute_day_anchor(rows=rows_list, previous_anchor=previous)
        results.append(
            DayChainResult(
                day=day,
                row_count=len(rows_list),
                anchor=anchor,
                previous_anchor=previous,
            )
        )
        previous = anchor
    return results


def verify_chain(
    *,
    rows_by_day: Mapping[str, Iterable[Mapping[str, object]]],
    expected_anchors: Mapping[str, str],
    seed: str = GENESIS_ANCHOR,
) -> list[str]:
    """Return the ISO-date keys whose anchor does NOT match expected.

    An empty list means the chain is intact."""
    mismatches: list[str] = []
    previous = seed
    for day, rows in rows_by_day.items():
        anchor = compute_day_anchor(rows=rows, previous_anchor=previous)
        if expected_anchors.get(day) != anchor:
            mismatches.append(day)
        previous = anchor
    return mismatches
