"""Schemas for lifecycle events + application queries — camelCase wire."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from app.models.lending.application_query import (
    ApplicationQueryRaisedReason,
    ApplicationQueryStatus,
)
from app.models.lending.lifecycle_event import (
    LifecycleActorKind,
    LifecycleSubjectType,
)
from app.schemas.base import CamelSchema


class LifecycleEventResponse(CamelSchema):
    """One lifecycle event row — what the timeline UI renders."""

    id: UUID
    event_at: datetime

    actor_user_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    actor_kind: LifecycleActorKind

    subject_type: LifecycleSubjectType
    subject_id: UUID
    business_number: Optional[str] = None

    event_type: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None

    payload: dict[str, Any] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    regulatory_tags: list[str] = Field(default_factory=list)
    borrower_visible: bool

    correlation_id: Optional[UUID] = None


class LifecycleTimelineResponse(CamelSchema):
    """List wrapper — total + items for the timeline view."""

    items: list[LifecycleEventResponse]
    total: int


# ---------------------------------------------------------------------------
# Application queries (bounce-back)
# ---------------------------------------------------------------------------


class RaiseQueryRequest(CamelSchema):
    """Lender raises a query on an application."""

    query_text: str = Field(..., min_length=1)
    raised_reason_code: ApplicationQueryRaisedReason = ApplicationQueryRaisedReason.OTHER
    required_attachments: list[str] = Field(default_factory=list)
    sla_hours: Optional[int] = Field(default=None, ge=1, le=720)


class RespondToQueryRequest(CamelSchema):
    """Borrower (portal user) responds to a query."""

    response_text: str = Field(..., min_length=1)
    response_attachments: list[dict[str, Any]] = Field(default_factory=list)


class ResolveQueryRequest(CamelSchema):
    """Lender closes a query as resolved."""

    resolution_remark: Optional[str] = None
    move_to_under_review: bool = True


class ApplicationQueryResponse(CamelSchema):
    id: UUID
    application_id: UUID
    query_number: int

    raised_by_id: UUID
    raised_at: datetime
    raised_reason_code: ApplicationQueryRaisedReason
    query_text: str
    required_attachments: list[str]
    sla_due_at: Optional[datetime] = None

    status: ApplicationQueryStatus
    responded_by_id: Optional[UUID] = None
    responded_at: Optional[datetime] = None
    response_text: Optional[str] = None
    response_attachments: list[dict[str, Any]] = Field(default_factory=list)

    resolved_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_remark: Optional[str] = None


class ApplicationQueryListResponse(CamelSchema):
    items: list[ApplicationQueryResponse]
    total: int
