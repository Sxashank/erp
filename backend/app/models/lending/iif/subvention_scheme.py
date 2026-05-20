"""Subvention scheme master.

Represents an interest-subvention scheme such as the IIF (Interest
Incentivization Fund) administered under the Maritime Development Fund.
Designed so multiple schemes (or notifiable variants — e.g. a shorter
half-yearly version of IIF, or a future port-side incentive) can
coexist.

``organization_id`` is intentionally nullable: a NULL row is a
platform-wide scheme that every NBFC inherits (the seeded IIF row is
exactly that). When an NBFC needs to override (e.g. internal cap), they
copy the row and set their own ``organization_id``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SubventionScheme(BaseModel):
    """Master row defining a subvention / interest-incentive scheme."""

    __tablename__ = "mst_subvention_scheme"
    __table_args__ = (
        # Per-org uniqueness on scheme_code; the NULL-org rows form their
        # own implicit "platform" set (Postgres treats NULL as distinct
        # in unique indexes, which is exactly what we want — multiple
        # platform schemes coexist by code).
        UniqueConstraint(
            "organization_id",
            "scheme_code",
            name="uq_mst_subvention_scheme_org_code",
        ),
        Index("ix_mst_subvention_scheme_org", "organization_id"),
        Index("ix_mst_subvention_scheme_code", "scheme_code"),
    )

    # ----- Tenant -------------------------------------------------------------

    # Nullable — NULL means platform-wide / default scheme. Every tenant
    # may also create their own override row by populating this column.
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
    )

    # ----- Identity -----------------------------------------------------------

    scheme_code: Mapped[str] = mapped_column(String(50), nullable=False)
    scheme_name: Mapped[str] = mapped_column(String(200), nullable=False)

    administering_ministry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    implementing_agency: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ----- Economics ----------------------------------------------------------

    # Flat 3% in IIF. 4dp precision matches our standard rate column.
    subvention_rate_percent: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False)
    # Per-beneficiary lifetime cap — IIF is ₹1,000 crore.
    max_subvention_per_beneficiary: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    # Total scheme corpus — IIF is ₹5,000 crore.
    scheme_corpus: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    # ----- Eligibility window -------------------------------------------------

    # IIFLoanType values, stored as JSONB list of strings.
    eligible_loan_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    max_tenure_term_loan_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_tenure_working_capital_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scheme_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheme_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    # How long after scheme_start_date a sanction can still qualify.
    # IIF is 36 months (within 3 years of scheme approval).
    eligibility_window_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ----- Claim / disqualification ------------------------------------------

    # ClaimFrequency value (QUARTERLY, HALF_YEARLY, YEARLY).
    claim_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    # DPD threshold beyond which a loan is "Stage-1" and the incentive
    # is suspended. IIF default is 30 days.
    npa_disqualification_dpd_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # ----- Configurable scheme rules -----------------------------------------

    # Calculation, eligibility, documents, workflow and fund rules are
    # intentionally JSONB so future Ministry notifications can be configured
    # without another schema change. Services still validate known keys.
    calculation_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    required_documents: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    workflow_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    fund_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
