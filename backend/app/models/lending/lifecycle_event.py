"""LoanLifecycleEvent — the single immutable spine for every action on a
loan from lead-creation to final closure.

This is the platform's strength: a `subject_type + subject_id` lookup
returns the entire history (lender + borrower + system events) on one
ribbon. Borrower portal + admin LMS both render off this same table.

Design constraints (per plan §"Asset-class agnostic design"):
- `event_type` is **TEXT, not enum** — operators add new event types
  (e.g. HIGHWAY_TOLL_AGREEMENT_REGISTERED) without a code change.
- `subject_type` IS an enum because the platform genuinely treats those
  domain kinds differently (loan account vs application has different
  lifecycle phases). Adding a new subject means real code changes.
- Append-only: no UPDATE / DELETE allowed from app code. Corrections are
  separate compensating events. Enforced by absence of update methods on
  the service + a postgres trigger added in a follow-up migration.
- Per CLAUDE.md §3.4: `organization_id` always set; RLS via
  `app.current_org_id` GUC.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LifecycleSubjectType(str, PyEnum):
    """The domain kind a lifecycle event refers to.

    Kept as a Python enum because adding a new subject type implies real
    code branches (the timeline UI groups events by subject phase). For
    new sub-categories, prefer reusing an existing subject + a fresh
    event_type code.
    """

    APPLICATION = "APPLICATION"
    SANCTION = "SANCTION"
    LOAN_ACCOUNT = "LOAN_ACCOUNT"
    DISBURSEMENT = "DISBURSEMENT"
    RECEIPT = "RECEIPT"
    RESTRUCTURE = "RESTRUCTURE"
    OTS = "OTS"
    LEGAL_CASE = "LEGAL_CASE"
    NACH_MANDATE = "NACH_MANDATE"
    CERTIFICATE = "CERTIFICATE"
    TAKEOVER = "TAKEOVER"
    TRANSFER_OUT = "TRANSFER_OUT"
    WRITE_OFF = "WRITE_OFF"
    INTEREST_REVIVAL = "INTEREST_REVIVAL"
    RATE_RESET = "RATE_RESET"


class LifecycleActorKind(str, PyEnum):
    """Who initiated the event."""

    LENDER = "LENDER"  # internal staff
    BORROWER = "BORROWER"  # portal user from the borrower entity
    SYSTEM = "SYSTEM"  # scheduled job / automated rule
    EXTERNAL = "EXTERNAL"  # webhook from a vendor (eSign, bureau, etc.)


class LoanLifecycleEvent(BaseModel):
    """Single append-only row per action on any loan-domain subject."""

    __tablename__ = "txn_loan_lifecycle_event"
    __table_args__ = (
        Index(
            "ix_txn_loan_lifecycle_event_subject_at",
            "subject_type",
            "subject_id",
            "event_at",
        ),
        Index(
            "ix_txn_loan_lifecycle_event_org_at",
            "organization_id",
            "event_at",
        ),
        Index("ix_txn_loan_lifecycle_event_actor", "actor_user_id"),
        Index("ix_txn_loan_lifecycle_event_type", "event_type"),
        Index("ix_txn_loan_lifecycle_event_correlation", "correlation_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Actor — who caused this. user_id is nullable for SYSTEM / EXTERNAL events.
    actor_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Role the actor was wearing — e.g. CREDIT_OFFICER, BORROWER_DIRECTOR, SYSTEM_NPA_JOB",
    )
    actor_kind: Mapped[LifecycleActorKind] = mapped_column(
        SAEnum(LifecycleActorKind, name="lifecycle_actor_kind"),
        nullable=False,
    )

    # Subject — what this event happened to
    subject_type: Mapped[LifecycleSubjectType] = mapped_column(
        SAEnum(LifecycleSubjectType, name="lifecycle_subject_type"),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="No FK constraint — subject_type drives the table; lifecycle outlives source rows on soft-delete.",
    )
    business_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Denormalised business id (loan account number, application ref) for fast listing.",
    )

    # The action itself — TEXT, extensible via mst_lifecycle_event_catalog without migration.
    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Catalog code (e.g. APPLICATION_SUBMITTED, KFS_ISSUED, RATE_RESET_APPLIED).",
    )

    state_from: Mapped[Optional[str]] = mapped_column(
        String(60),
        nullable=True,
    )
    state_to: Mapped[Optional[str]] = mapped_column(
        String(60),
        nullable=True,
    )

    reason_code: Mapped[Optional[str]] = mapped_column(
        String(80),
        nullable=True,
        comment="Optional machine-readable cause; FE can localise.",
    )
    reason_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text rationale supplied by the actor.",
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Event-specific structured data (before/after diff, amounts, etc.).",
    )
    attachments: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of {dms_document_id, file_name, mime_type} for documents tied to this event.",
    )

    regulatory_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(60)),
        nullable=False,
        default=list,
        comment="Tags surfaced to regulators (KFS_ISSUED, SARFAESI_13_2, OTS_APPROVED, etc.).",
    )
    borrower_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Drives the portal-side timeline filter. Defaults to False — opt-in per event type.",
    )

    correlation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Groups events from one logical workflow (e.g. a single restructure flow emits several rows with the same id).",
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(80),
        nullable=True,
        comment="When the source mutation used Idempotency-Key, persist it here for replay tracing.",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LoanLifecycleEvent {self.event_type} "
            f"{self.subject_type.value}:{self.subject_id} at {self.event_at}>"
        )
