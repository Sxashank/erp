"""LifecycleService — the single entry point for emitting loan-domain events.

Every domain service (application, sanction, disbursement, receipt, NPA,
restructure, OTS, NACH, certificate, takeover, etc.) calls
``record_event(...)`` from this service whenever an action happens on a
loan-domain subject. The unified timeline UI + every report pulls from the
same row set.

Why a single emit method instead of inlining inserts in each service:
- One place to enforce the borrower-visible default rule.
- One place to attach the correlation_id of the current workflow.
- One place to hash-chain into the daily audit anchor (Stage 5).
- Easier to test: every service's "lifecycle parity" test asserts that
  exactly N rows landed via this entry point.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.lifecycle_event import (
    LifecycleActorKind,
    LifecycleSubjectType,
    LoanLifecycleEvent,
)

logger = logging.getLogger(__name__)


# Events that the borrower should see by default on their portal timeline.
# Anything not in this set is lender-internal and stays hidden unless the
# caller passes borrower_visible=True explicitly. This keeps borrower
# pages clean (no "Internal audit memo created" rows) while staying
# transparent on action-relevant items.
_DEFAULT_BORROWER_VISIBLE: frozenset[str] = frozenset(
    {
        "APPLICATION_SUBMITTED",
        "QUERY_RAISED",
        "BORROWER_RESPONDED",
        "QUERY_RESOLVED",
        "KFS_ISSUED",
        "KFS_ACKNOWLEDGED",
        "SANCTION_LETTER_ISSUED",
        "SANCTION_ACCEPTED",
        "AGREEMENT_ESIGN_INITIATED",
        "AGREEMENT_ESIGN_COMPLETED",
        "DISBURSEMENT_PROCESSED",
        "SCHEDULE_GENERATED",
        "RECEIPT_RECORDED",
        "RECEIPT_BOUNCED",
        "RATE_RESET_DUE",
        "RATE_RESET_APPLIED",
        "RATE_RESET_BORROWER_CHOICE",
        "STATEMENT_ISSUED",
        "INTEREST_CERT_ISSUED",
        "PROVISIONAL_INTEREST_CERT_ISSUED",
        "NDC_ISSUED",
        "FORECLOSURE_QUOTE_ISSUED",
        "PREPAYMENT_QUOTE_ISSUED",
        "PREPAYMENT_RECEIVED",
        "FORECLOSED",
        "RESTRUCTURE_APPROVED",
        "OTS_BORROWER_ACCEPTED",
        "OTS_COMPLETED",
        "NACH_REGISTERED",
        "NACH_BOUNCED",
        "TAKEOVER_LETTER_ISSUED",
        "TAKEOVER_COMPLETED",
        "ORIGINAL_DOCS_RELEASED",
        "CLOSED_NORMAL",
        "CLOSED_FORECLOSED",
        "CLOSED_TAKEOVER",
        "CLOSED_OTS",
    }
)


class LifecycleService:
    """Records and queries loan-domain lifecycle events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        *,
        organization_id: UUID,
        subject_type: LifecycleSubjectType,
        subject_id: UUID,
        event_type: str,
        actor_kind: LifecycleActorKind,
        actor_user_id: UUID | None = None,
        actor_role: str | None = None,
        business_number: str | None = None,
        state_from: str | None = None,
        state_to: str | None = None,
        reason_code: str | None = None,
        reason_text: str | None = None,
        payload: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        regulatory_tags: list[str] | None = None,
        borrower_visible: bool | None = None,
        correlation_id: UUID | None = None,
        idempotency_key: str | None = None,
        event_at: datetime | None = None,
    ) -> LoanLifecycleEvent:
        """Append one immutable row to ``txn_loan_lifecycle_event``.

        Most callers only need to pass: organization_id, subject_type,
        subject_id, event_type, actor_kind, plus whatever business
        payload makes sense. Sensible defaults fill the rest.
        """
        if borrower_visible is None:
            borrower_visible = event_type in _DEFAULT_BORROWER_VISIBLE

        row = LoanLifecycleEvent(
            organization_id=organization_id,
            event_at=event_at or datetime.now(timezone.utc),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            actor_kind=actor_kind,
            subject_type=subject_type,
            subject_id=subject_id,
            business_number=business_number,
            event_type=event_type,
            state_from=state_from,
            state_to=state_to,
            reason_code=reason_code,
            reason_text=reason_text,
            payload=payload or {},
            attachments=attachments or [],
            regulatory_tags=regulatory_tags or [],
            borrower_visible=borrower_visible,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        self.session.add(row)
        await self.session.flush()
        logger.info(
            "lifecycle.recorded type=%s subject=%s:%s actor=%s",
            event_type,
            subject_type.value,
            subject_id,
            actor_kind.value,
        )
        return row

    async def list_for_subject(
        self,
        *,
        subject_type: LifecycleSubjectType,
        subject_id: UUID,
        organization_id: UUID,
        borrower_visible_only: bool = False,
        limit: int = 500,
    ) -> list[LoanLifecycleEvent]:
        """Return events for a single subject in reverse-chronological order.

        ``borrower_visible_only=True`` drives the portal timeline. Admin
        timeline omits this filter.
        """
        stmt = (
            select(LoanLifecycleEvent)
            .where(
                LoanLifecycleEvent.subject_type == subject_type,
                LoanLifecycleEvent.subject_id == subject_id,
                LoanLifecycleEvent.organization_id == organization_id,
            )
            .order_by(desc(LoanLifecycleEvent.event_at))
            .limit(limit)
        )
        if borrower_visible_only:
            stmt = stmt.where(LoanLifecycleEvent.borrower_visible.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_loan_account(
        self,
        *,
        loan_account_id: UUID,
        organization_id: UUID,
        application_id: UUID | None = None,
        sanction_id: UUID | None = None,
        borrower_visible_only: bool = False,
        limit: int = 1000,
    ) -> list[LoanLifecycleEvent]:
        """Aggregate timeline across application → sanction → loan account.

        Loan accounts inherit their pre-existence from the application +
        sanction that birthed them, so the timeline UI shows the whole
        story end-to-end. Pass the upstream ids when available.
        """
        ids_by_subject: dict[LifecycleSubjectType, list[UUID]] = {
            LifecycleSubjectType.LOAN_ACCOUNT: [loan_account_id],
        }
        if application_id is not None:
            ids_by_subject[LifecycleSubjectType.APPLICATION] = [application_id]
        if sanction_id is not None:
            ids_by_subject[LifecycleSubjectType.SANCTION] = [sanction_id]

        # Build one OR'd query — far cheaper than N round-trips.
        from sqlalchemy import and_, or_

        clauses = []
        for subj, ids in ids_by_subject.items():
            clauses.append(
                and_(
                    LoanLifecycleEvent.subject_type == subj,
                    LoanLifecycleEvent.subject_id.in_(ids),
                )
            )
        stmt = (
            select(LoanLifecycleEvent)
            .where(
                LoanLifecycleEvent.organization_id == organization_id,
                or_(*clauses),
            )
            .order_by(desc(LoanLifecycleEvent.event_at))
            .limit(limit)
        )
        if borrower_visible_only:
            stmt = stmt.where(LoanLifecycleEvent.borrower_visible.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
