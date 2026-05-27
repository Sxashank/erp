"""ApplicationQueryService — formal lender ↔ borrower bounce-back.

Three operations:

1. ``raise(...)`` — lender raises a query. Application status flips to
   ``ADDITIONAL_INFO_REQUIRED``. Lifecycle event ``QUERY_RAISED`` emitted.

2. ``respond(...)`` — borrower (portal user) replies. Query status flips
   to ``RESPONDED``. Application status flips back to ``SUBMITTED`` so it
   re-enters the review queue. Lifecycle event ``BORROWER_RESPONDED``.

3. ``resolve(...)`` — lender accepts the response and closes the query.
   Application status flips to ``UNDER_REVIEW``. Lifecycle event
   ``QUERY_RESOLVED``.

A separate ``raise(...)`` call after a ``resolve(...)`` (i.e. the lender
wants more info even after a borrower response) creates a new query row
with the next ``query_number``. The bounce-back is naturally an ordered
list of queries, not a thread on a single row.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ValidationException,
)
from app.models.lending.application_query import (
    ApplicationQueryRaisedReason,
    ApplicationQueryStatus,
    LosApplicationQuery,
)
from app.models.lending.lifecycle_event import (
    LifecycleActorKind,
    LifecycleSubjectType,
)
from app.services.lending.lifecycle_service import LifecycleService

logger = logging.getLogger(__name__)


# Application statuses that allow a new query to be raised. Out-of-this-set
# means the application is already terminal (rejected / withdrawn / etc.)
# or post-sanction — raising a query at that point is nonsense.
_QUERY_ALLOWED_STATUSES = {"SUBMITTED", "UNDER_REVIEW", "ADDITIONAL_INFO_REQUIRED"}


class ApplicationQueryService:
    """The formal mechanism for the back-and-forth between lender and borrower."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def raise_query(
        self,
        *,
        organization_id: UUID,
        application_id: UUID,
        raised_by_user_id: UUID,
        query_text: str,
        raised_reason_code: ApplicationQueryRaisedReason = ApplicationQueryRaisedReason.OTHER,
        required_attachments: list[str] | None = None,
        sla_hours: int | None = None,
    ) -> LosApplicationQuery:
        """Lender raises a query against an application.

        Side effects:
        - Application status flips to ``ADDITIONAL_INFO_REQUIRED``.
        - ``QUERY_RAISED`` lifecycle event emitted.
        - SLA clock starts (``sla_due_at = now + sla_hours``).
        """
        from app.models.lending.application import LoanApplication

        application = await self.session.get(LoanApplication, application_id)
        if application is None:
            raise NotFoundException(
                detail=f"Application {application_id} not found",
                error_code="APPLICATION_NOT_FOUND",
            )
        if application.organization_id != organization_id:
            raise NotFoundException(
                detail="Application not found in current organisation",
                error_code="APPLICATION_NOT_FOUND",
            )

        current_status = (
            application.status.value
            if hasattr(application.status, "value")
            else str(application.status)
        )
        if current_status not in _QUERY_ALLOWED_STATUSES:
            raise ValidationException(
                f"Cannot raise a query when application is in {current_status} status. "
                f"Allowed: {sorted(_QUERY_ALLOWED_STATUSES)}.",
                error_code="QUERY_RAISE_WRONG_STATUS",
            )

        # Determine the next query_number for this application
        count_q = select(func.count(LosApplicationQuery.id)).where(
            LosApplicationQuery.application_id == application_id
        )
        existing_count = (await self.session.execute(count_q)).scalar() or 0
        next_number = existing_count + 1

        now = datetime.now(timezone.utc)
        sla_due_at = now + timedelta(hours=sla_hours) if sla_hours else None

        query = LosApplicationQuery(
            organization_id=organization_id,
            application_id=application_id,
            query_number=next_number,
            raised_by_id=raised_by_user_id,
            raised_at=now,
            raised_reason_code=raised_reason_code,
            query_text=query_text,
            required_attachments=required_attachments or [],
            sla_due_at=sla_due_at,
            status=ApplicationQueryStatus.RAISED,
        )
        self.session.add(query)
        await self.session.flush()

        # Move the application into ADDITIONAL_INFO_REQUIRED
        previous_status = current_status
        from app.models.lending.enums import ApplicationStatus

        application.status = ApplicationStatus.ADDITIONAL_INFO_REQUIRED

        correlation_id = uuid4()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.APPLICATION,
            subject_id=application_id,
            event_type="QUERY_RAISED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=raised_by_user_id,
            business_number=getattr(application, "application_number", None),
            state_from=previous_status,
            state_to="ADDITIONAL_INFO_REQUIRED",
            reason_code=raised_reason_code.value,
            reason_text=query_text,
            payload={
                "query_id": str(query.id),
                "query_number": next_number,
                "required_attachments": list(required_attachments or []),
                "sla_due_at": sla_due_at.isoformat() if sla_due_at else None,
            },
            correlation_id=correlation_id,
        )

        await self.session.flush()
        return query

    async def respond_to_query(
        self,
        *,
        organization_id: UUID,
        query_id: UUID,
        portal_user_id: UUID,
        response_text: str,
        response_attachments: list[dict[str, Any]] | None = None,
    ) -> LosApplicationQuery:
        """Borrower replies via portal. Application moves back to SUBMITTED."""
        query = await self.session.get(LosApplicationQuery, query_id)
        if query is None or query.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Query {query_id} not found",
                error_code="APPLICATION_QUERY_NOT_FOUND",
            )
        if query.status not in (
            ApplicationQueryStatus.RAISED,
            ApplicationQueryStatus.RESPONDED,  # allow updating the response before lender acts
        ):
            raise ValidationException(
                f"Cannot respond when query is {query.status.value}.",
                error_code="QUERY_RESPOND_WRONG_STATUS",
            )

        now = datetime.now(timezone.utc)
        query.responded_by_id = portal_user_id
        query.responded_at = now
        query.response_text = response_text
        query.response_attachments = response_attachments or []
        query.status = ApplicationQueryStatus.RESPONDED

        # Flip the application back to SUBMITTED so it shows up in the lender's
        # review queue again. (Only if no other queries are still open.)
        from app.models.lending.application import LoanApplication
        from app.models.lending.enums import ApplicationStatus

        application = await self.session.get(LoanApplication, query.application_id)
        if application is not None:
            other_open = await self.session.execute(
                select(func.count(LosApplicationQuery.id)).where(
                    LosApplicationQuery.application_id == query.application_id,
                    LosApplicationQuery.id != query_id,
                    LosApplicationQuery.status.in_(
                        [
                            ApplicationQueryStatus.RAISED,
                            ApplicationQueryStatus.RE_REVIEW,
                        ]
                    ),
                )
            )
            other_open_count = other_open.scalar() or 0
            previous_status = (
                application.status.value
                if hasattr(application.status, "value")
                else str(application.status)
            )
            if other_open_count == 0:
                application.status = ApplicationStatus.SUBMITTED
                new_status = "SUBMITTED"
            else:
                new_status = previous_status
        else:
            new_status = None
            previous_status = None

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.APPLICATION,
            subject_id=query.application_id,
            event_type="BORROWER_RESPONDED",
            actor_kind=LifecycleActorKind.BORROWER,
            actor_user_id=None,  # portal user is not in mst_user
            actor_role="BORROWER",
            business_number=(
                getattr(application, "application_number", None) if application else None
            ),
            state_from=previous_status,
            state_to=new_status,
            reason_text=response_text,
            payload={
                "query_id": str(query_id),
                "query_number": query.query_number,
                "portal_user_id": str(portal_user_id),
                "attachment_count": len(response_attachments or []),
            },
        )
        await self.session.flush()
        return query

    async def resolve_query(
        self,
        *,
        organization_id: UUID,
        query_id: UUID,
        resolved_by_user_id: UUID,
        resolution_remark: str | None = None,
        move_to_under_review: bool = True,
    ) -> LosApplicationQuery:
        """Lender accepts the borrower's response and closes the query."""
        query = await self.session.get(LosApplicationQuery, query_id)
        if query is None or query.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Query {query_id} not found",
                error_code="APPLICATION_QUERY_NOT_FOUND",
            )
        if query.status not in (
            ApplicationQueryStatus.RESPONDED,
            ApplicationQueryStatus.RE_REVIEW,
        ):
            raise ValidationException(
                f"Cannot resolve a query in {query.status.value} status.",
                error_code="QUERY_RESOLVE_WRONG_STATUS",
            )

        now = datetime.now(timezone.utc)
        query.status = ApplicationQueryStatus.RESOLVED
        query.resolved_by_id = resolved_by_user_id
        query.resolved_at = now
        query.resolution_remark = resolution_remark

        from app.models.lending.application import LoanApplication
        from app.models.lending.enums import ApplicationStatus

        application = await self.session.get(LoanApplication, query.application_id)
        previous_status = (
            application.status.value
            if application and hasattr(application.status, "value")
            else str(application.status) if application else None
        )
        new_status = previous_status
        if move_to_under_review and application is not None:
            application.status = ApplicationStatus.UNDER_REVIEW
            new_status = "UNDER_REVIEW"

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.APPLICATION,
            subject_id=query.application_id,
            event_type="QUERY_RESOLVED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=resolved_by_user_id,
            business_number=(
                getattr(application, "application_number", None) if application else None
            ),
            state_from=previous_status,
            state_to=new_status,
            reason_text=resolution_remark,
            payload={
                "query_id": str(query_id),
                "query_number": query.query_number,
            },
        )
        await self.session.flush()
        return query

    async def list_for_application(
        self,
        *,
        organization_id: UUID,
        application_id: UUID,
    ) -> list[LosApplicationQuery]:
        stmt = (
            select(LosApplicationQuery)
            .where(
                LosApplicationQuery.organization_id == organization_id,
                LosApplicationQuery.application_id == application_id,
            )
            .order_by(LosApplicationQuery.query_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, *, organization_id: UUID, query_id: UUID) -> LosApplicationQuery:
        query = await self.session.get(LosApplicationQuery, query_id)
        if query is None or query.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Query {query_id} not found",
                error_code="APPLICATION_QUERY_NOT_FOUND",
            )
        return query

    async def scan_lapsed(self, *, organization_id: UUID) -> int:
        """Mark queries past their SLA window as LAPSED. Returns count.

        Called by the daily SLA-breach Arq job.
        """
        now = datetime.now(timezone.utc)
        stmt = select(LosApplicationQuery).where(
            LosApplicationQuery.organization_id == organization_id,
            LosApplicationQuery.status == ApplicationQueryStatus.RAISED,
            LosApplicationQuery.sla_due_at.isnot(None),
            LosApplicationQuery.sla_due_at < now,
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for q in rows:
            q.status = ApplicationQueryStatus.LAPSED
            await self.lifecycle.record_event(
                organization_id=organization_id,
                subject_type=LifecycleSubjectType.APPLICATION,
                subject_id=q.application_id,
                event_type="QUERY_LAPSED",
                actor_kind=LifecycleActorKind.SYSTEM,
                actor_role="SLA_BREACH_JOB",
                payload={
                    "query_id": str(q.id),
                    "query_number": q.query_number,
                    "sla_due_at": q.sla_due_at.isoformat() if q.sla_due_at else None,
                },
            )
        await self.session.flush()
        return len(rows)
