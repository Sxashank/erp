"""Audit-service helpers used at financial-mutation call sites.

CLAUDE.md §8.5 + Appendix C requires that financial mutations (voucher post,
receipt allocate, disbursement process, OTS approve, restructure approve,
write-off approve, payroll finalize, IIF claim release, etc.) emit a domain
audit row with before/after snapshots into ``txn_audit_log`` — distinct from
the HTTP envelope captured by ``AuditMiddleware``.

This module surfaces a thin async helper, :func:`record_financial_action`,
that wraps :class:`app.services.common.audit_service.AuditService.log_action`
with the conventions expected at every financial-mutation call site:

* the audit row joins the **same transaction** as the mutation — the helper
  does not commit; the request-level boundary handles that;
* the before/after snapshots are caller-supplied dict projections (4–8 fields
  that matter for the audit), NOT a dump of the entire ORM object;
* arbitrary ancillary context (e.g. per-installment receipt allocation
  breakdown, the writeoff principal/interest/penal split, the released UTR
  + paid_date) lands in ``audit_context``.

Keeping the call sites uniform makes the audit footprint reviewable and
makes a future refactor (e.g. moving to a streaming sink) a single-point
change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.audit_log import AuditLog
from app.services.common.audit_service import AuditService


async def record_financial_action(
    session: AsyncSession,
    *,
    organization_id: UUID,
    entity_type: str,
    entity_id: UUID,
    entity_reference: str | None,
    action: str,
    user_id: UUID,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    change_reason: str | None = None,
) -> AuditLog:
    """Write a domain audit row for a financial mutation.

    Joins the surrounding transaction (no commit issued here). Returns the
    persisted ``AuditLog`` so the caller can correlate downstream if needed.
    """
    service = AuditService(session)
    return await service.log_action(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_reference=entity_reference,
        action=action,
        user_id=user_id,
        old_values=dict(before) if before is not None else None,
        new_values=dict(after) if after is not None else None,
        change_reason=change_reason,
        audit_context=dict(metadata) if metadata is not None else None,
    )


__all__ = ["record_financial_action"]
