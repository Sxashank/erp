"""Audit hash-chain service (STAGE-5-PENDING-002 closure).

Thin layer over `app.core.audit_hash_chain` that reads/writes the
`audit_day_anchor` table. Used by:
  - The nightly APScheduler job `compute_audit_anchors_job` (00:15 IST).
  - The `/api/v1/audit/verify-chain` admin endpoint.

The scheduler hook is added to `app.services.workflow.background_tasks`
so it lifts off with the existing escalation/digest jobs — no new runtime.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Mapping
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_hash_chain import (
    GENESIS_ANCHOR,
    DayChainResult,
    build_chain,
    verify_chain,
)
from app.models.core.audit_day_anchor import AuditDayAnchor

logger = structlog.get_logger("audit.hash_chain")


async def get_last_anchor(
    session: AsyncSession,
    *,
    organization_id: UUID | None,
) -> str:
    """Return the most-recent anchor for the org, or GENESIS_ANCHOR if none."""
    q = (
        select(AuditDayAnchor)
        .where(AuditDayAnchor.organization_id == organization_id)
        .order_by(AuditDayAnchor.day.desc())
        .limit(1)
    )
    row = (await session.execute(q)).scalar_one_or_none()
    return row.anchor if row else GENESIS_ANCHOR


async def persist_day_chain(
    session: AsyncSession,
    *,
    organization_id: UUID | None,
    rows_by_day: Mapping[str, Iterable[Mapping[str, object]]],
    seed: str | None = None,
) -> list[DayChainResult]:
    """Compute anchors for the given days and persist them.

    `seed` defaults to the last stored anchor for the org (or genesis).
    Idempotent: if a row already exists for (org, day) the service updates
    `anchor` + `row_count` in place.
    """
    base = seed or await get_last_anchor(session, organization_id=organization_id)
    results = build_chain(rows_by_day=rows_by_day, seed=base)

    for r in results:
        existing = (
            await session.execute(
                select(AuditDayAnchor).where(
                    AuditDayAnchor.organization_id == organization_id,
                    AuditDayAnchor.day == date.fromisoformat(r.day),
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                AuditDayAnchor(
                    organization_id=organization_id,
                    day=date.fromisoformat(r.day),
                    row_count=r.row_count,
                    previous_anchor=r.previous_anchor,
                    anchor=r.anchor,
                )
            )
        else:
            existing.row_count = r.row_count
            existing.previous_anchor = r.previous_anchor
            existing.anchor = r.anchor

    await session.commit()
    logger.info(
        "audit_hash_chain_persisted",
        organization_id=str(organization_id) if organization_id else None,
        day_count=len(results),
    )
    return results


async def verify_stored_chain(
    session: AsyncSession,
    *,
    organization_id: UUID | None,
    rows_by_day: Mapping[str, Iterable[Mapping[str, object]]],
    seed: str | None = None,
) -> list[str]:
    """Re-compute anchors over `rows_by_day` and compare to stored values.

    Returns the list of ISO-date strings whose stored anchor disagrees with
    the freshly-computed one. Empty list ⇒ chain intact."""
    q = (
        select(AuditDayAnchor)
        .where(AuditDayAnchor.organization_id == organization_id)
        .order_by(AuditDayAnchor.day.asc())
    )
    rows = (await session.execute(q)).scalars().all()
    expected = {row.day.isoformat(): row.anchor for row in rows}

    base = seed or (rows[0].previous_anchor if rows else GENESIS_ANCHOR)
    return verify_chain(
        rows_by_day=rows_by_day,
        expected_anchors=expected,
        seed=base,
    )


def yesterday_iso() -> str:
    """Helper for the nightly job — previous calendar day in ISO."""
    return (date.today() - timedelta(days=1)).isoformat()
