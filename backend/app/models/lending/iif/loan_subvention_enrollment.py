"""Loan-account ↔ subvention-scheme enrollment.

Records a loan account's enrolment into a scheme (e.g. IIF) and the
running totals of claims raised / paid against it. Acts as the
aggregate root for child ``SubventionClaim`` rows.

Per CLAUDE.md §3.4, every row carries ``organization_id`` and is
filtered by Postgres RLS on ``app.current_org_id``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.iif.subvention_scheme import SubventionScheme
    from app.models.lending.loan_account import LoanAccount


class LoanSubventionEnrollment(BaseModel):
    """One row per (loan_account, scheme) — active when status==ENROLLED."""

    __tablename__ = "los_loan_subvention_enrollment"
    __table_args__ = (
        # We can't put a unique constraint on (loan_account_id,
        # scheme_id) directly because soft-deleted rows must not block
        # new enrolments. Express it as a partial unique index in the
        # migration (filtered on deleted_at IS NULL); we also include
        # the regular non-unique indexes below for fast lookup.
        Index("ix_los_lse_org", "organization_id"),
        Index("ix_los_lse_loan", "loan_account_id"),
        Index("ix_los_lse_scheme", "scheme_id"),
        Index("ix_los_lse_status", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scheme_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_subvention_scheme.id", ondelete="RESTRICT"),
        nullable=False,
    )

    enrolled_date: Mapped[date] = mapped_column(Date, nullable=False)

    # SubventionEnrollmentStatus value.
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING_APPROVAL",
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Running totals (kept in-sync by SubventionClaimService).
    total_claimed_to_date: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    total_paid_to_date: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships — explicitly lazy="raise" so accidental implicit
    # I/O is caught early. Use ``selectinload`` in the service.
    loan_account: Mapped[LoanAccount] = relationship(
        "LoanAccount",
        foreign_keys=[loan_account_id],
        lazy="raise",
    )
    scheme: Mapped[SubventionScheme] = relationship(
        "SubventionScheme",
        foreign_keys=[scheme_id],
        lazy="raise",
    )
