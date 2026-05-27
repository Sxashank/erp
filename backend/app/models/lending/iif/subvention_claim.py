"""A single subvention claim raised against an enrollment.

One claim covers one period (typically a quarter under IIF). The
reference is auto-generated per scheme/period: e.g.
``IIF/2026Q1/00001`` for a Q1 (Apr–Jun) quarterly claim. Documents are
stored as a JSONB list of ``{name, path, uploaded_at}`` blobs — the
file bytes themselves live in DMS.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.iif.loan_subvention_enrollment import (
        LoanSubventionEnrollment,
    )


class SubventionClaim(BaseModel):
    """A single quarterly / period claim against an enrollment."""

    __tablename__ = "txn_subvention_claim"
    __table_args__ = (
        # claim_reference unique within an org.
        UniqueConstraint(
            "organization_id",
            "claim_reference",
            name="uq_txn_subvention_claim_org_ref",
        ),
        Index("ix_txn_subvention_claim_org", "organization_id"),
        Index("ix_txn_subvention_claim_enrollment", "enrollment_id"),
        Index("ix_txn_subvention_claim_reference", "claim_reference"),
        Index("ix_txn_subvention_claim_status", "status"),
        Index("ix_txn_subvention_claim_period", "period_start", "period_end"),
        Index(
            "uq_txn_subvention_claim_live_period",
            "organization_id",
            "enrollment_id",
            "period_start",
            "period_end",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND status <> 'CANCELLED'"),
            sqlite_where=text("deleted_at IS NULL AND status <> 'CANCELLED'"),
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_subvention_enrollment.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # e.g. "IIF/2026Q1/00001" (quarterly), "IIF/2026H1/00001" (half-yearly),
    # "IIF/2026/00001" (annual).
    claim_reference: Mapped[str] = mapped_column(String(50), nullable=False)

    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    # ClaimFrequency value mirrored from scheme at claim creation time
    # (snapshotting protects against scheme-level changes mid-life).
    claim_frequency: Mapped[str] = mapped_column(String(20), nullable=False)

    interest_paid_in_period: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    applicable_subvention_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # SubventionClaimStatus value.
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")

    submitted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_initiated_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    release_instruction_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    release_instruction_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    utr_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    declaration_signed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    declaration_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # [{name: str, path: str, uploaded_at: ISO8601 str, ...}]
    documents: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    calculation_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationship to the parent enrolment (loan + scheme are reached
    # through this for the response DTO and report).
    enrollment: Mapped[LoanSubventionEnrollment] = relationship(
        "LoanSubventionEnrollment",
        foreign_keys=[enrollment_id],
        lazy="raise",
    )
