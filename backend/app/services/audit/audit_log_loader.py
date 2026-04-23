"""Loader that turns `AuditLog` rows into the canonical shape expected by
`hash_chain_service.persist_day_chain` + `verify_stored_chain`.

Extracted so the chain service stays pure and the scheduler job stays
thin. See STAGE-5-PENDING-002 closure.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Mapping, Optional
from uuid import UUID

from sqlalchemy import and_, asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.audit_log import AuditLog


# Ordered tuple — matters because `canonicalise_row` sorts by key anyway,
# but listing the canonical fields in one place prevents silent drift.
CANONICAL_FIELDS = (
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
)


def audit_row_to_canonical(log: AuditLog) -> Mapping[str, object]:
    """Project an ORM AuditLog row into the canonical dict the chain uses."""
    return {field: getattr(log, field) for field in CANONICAL_FIELDS}


async def load_rows_by_day(
    session: AsyncSession,
    *,
    organization_id: Optional[UUID],
    start_day: date,
    end_day: date,
) -> dict[str, list[Mapping[str, object]]]:
    """Return ISO-date → list of canonical rows for [start_day, end_day].

    Rows are sorted by (changed_at ASC, id ASC) — that order is part of
    the canonical hash input. Days with no rows map to an empty list
    (anchor still advances).
    """
    if start_day > end_day:
        return {}

    start_ts = datetime.combine(start_day, time.min, tzinfo=timezone.utc)
    end_ts = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=timezone.utc)

    clauses = [AuditLog.changed_at >= start_ts, AuditLog.changed_at < end_ts]
    if organization_id is not None:
        clauses.append(AuditLog.organization_id == organization_id)

    result = await session.execute(
        select(AuditLog)
        .where(and_(*clauses))
        .order_by(asc(AuditLog.changed_at), asc(AuditLog.id))
    )
    rows = list(result.scalars().all())

    by_day: dict[str, list[Mapping[str, object]]] = {}
    day = start_day
    while day <= end_day:
        by_day[day.isoformat()] = []
        day += timedelta(days=1)
    for r in rows:
        key = r.changed_at.date().isoformat()
        by_day.setdefault(key, []).append(audit_row_to_canonical(r))
    return by_day


async def distinct_org_ids_with_audit_rows(
    session: AsyncSession,
    *,
    target_day: date,
) -> list[Optional[UUID]]:
    """IDs of orgs (including NULL for system-global) that wrote audit rows on
    `target_day`. Used by the daily scheduler so only active tenants get a row."""
    start_ts = datetime.combine(target_day, time.min, tzinfo=timezone.utc)
    end_ts = start_ts + timedelta(days=1)
    result = await session.execute(
        select(AuditLog.organization_id)
        .where(and_(AuditLog.changed_at >= start_ts, AuditLog.changed_at < end_ts))
        .distinct()
    )
    return [row for row in result.scalars().all()]
