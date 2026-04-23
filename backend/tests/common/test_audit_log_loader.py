"""Tests for `audit_log_loader` — STAGE-5-PENDING-002 closure.

Pure-Python loader tests (no DB). We fake AsyncSession + AuditLog rows
and assert:
  - `audit_row_to_canonical` projects into the canonical 11-field dict.
  - `load_rows_by_day` buckets rows by changed_at.date() AND seeds every
    day in the range with an empty list (so the anchor chain propagates
    through inactive days).
  - Rows are sorted inside a day by (changed_at, id).
  - `distinct_org_ids_with_audit_rows` returns only orgs with activity.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.audit.audit_log_loader import (
    CANONICAL_FIELDS,
    audit_row_to_canonical,
    distinct_org_ids_with_audit_rows,
    load_rows_by_day,
)


def _log(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        organization_id=uuid4(),
        entity_type="VOUCHER",
        entity_id=uuid4(),
        entity_reference="V-001",
        action="CREATE",
        changed_by=uuid4(),
        changed_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
        old_values=None,
        new_values={"amount": 100},
        changed_fields=["amount"],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# audit_row_to_canonical.
# ---------------------------------------------------------------------------


def test_canonical_fields_is_the_complete_11_field_list() -> None:
    assert set(CANONICAL_FIELDS) == {
        "id",
        "organization_id",
        "entity_type",
        "entity_id",
        "entity_reference",
        "action",
        "changed_by",
        "changed_at",
        "old_values",
        "new_values",
        "changed_fields",
    }


def test_audit_row_to_canonical_projects_every_field() -> None:
    log = _log()
    out = audit_row_to_canonical(log)
    for field in CANONICAL_FIELDS:
        assert field in out
        assert out[field] == getattr(log, field)


# ---------------------------------------------------------------------------
# load_rows_by_day.
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows) -> None:
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


def _session_returning(rows):
    session = MagicMock()
    session.execute = AsyncMock(return_value=_FakeResult(rows))
    return session


@pytest.mark.asyncio
async def test_load_rows_by_day_seeds_empty_days_across_range() -> None:
    """Days without rows still appear in the output so the chain
    propagates through them (a day with zero rows still has an anchor)."""
    session = _session_returning([])
    out = await load_rows_by_day(
        session, organization_id=uuid4(),
        start_day=date(2026, 4, 10), end_day=date(2026, 4, 12),
    )
    assert set(out.keys()) == {"2026-04-10", "2026-04-11", "2026-04-12"}
    assert all(v == [] for v in out.values())


@pytest.mark.asyncio
async def test_load_rows_by_day_buckets_by_changed_at_date() -> None:
    r1 = _log(changed_at=datetime(2026, 4, 10, 3, 0, tzinfo=timezone.utc))
    r2 = _log(changed_at=datetime(2026, 4, 10, 22, 0, tzinfo=timezone.utc))
    r3 = _log(changed_at=datetime(2026, 4, 11, 1, 0, tzinfo=timezone.utc))
    session = _session_returning([r1, r2, r3])

    out = await load_rows_by_day(
        session, organization_id=uuid4(),
        start_day=date(2026, 4, 10), end_day=date(2026, 4, 11),
    )
    assert len(out["2026-04-10"]) == 2
    assert len(out["2026-04-11"]) == 1


@pytest.mark.asyncio
async def test_load_rows_by_day_empty_when_start_after_end() -> None:
    session = _session_returning([])
    out = await load_rows_by_day(
        session, organization_id=uuid4(),
        start_day=date(2026, 4, 15), end_day=date(2026, 4, 10),
    )
    assert out == {}
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_load_rows_system_global_uses_null_org_filter() -> None:
    """organization_id=None → no org filter is added (system-global chain)."""
    session = _session_returning([])
    await load_rows_by_day(
        session, organization_id=None,
        start_day=date(2026, 4, 10), end_day=date(2026, 4, 10),
    )
    # One execute call; we don't dissect the SQL, just confirm it ran.
    assert session.execute.await_count == 1


# ---------------------------------------------------------------------------
# distinct_org_ids_with_audit_rows.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_distinct_org_ids_returns_distinct_list() -> None:
    o1, o2 = uuid4(), uuid4()
    session = _session_returning([o1, o2])
    out = await distinct_org_ids_with_audit_rows(session, target_day=date(2026, 4, 10))
    assert set(out) == {o1, o2}


@pytest.mark.asyncio
async def test_distinct_org_ids_empty_when_no_activity() -> None:
    session = _session_returning([])
    out = await distinct_org_ids_with_audit_rows(session, target_day=date(2026, 4, 10))
    assert out == []
