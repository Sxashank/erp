"""Treasury investment portfolio model.

Tracks individual investment holdings (G-Sec, SDL, T-Bill, corporate bonds,
NCDs, CP, CD, mutual funds) owned by an NBFC. Distinct from `ALMAsset` —
that one is an aggregated bucket-wise snapshot for ALM reporting; this one
is the per-instrument book of record.

Multi-tenant per CLAUDE.md §3.4: every row carries `organization_id` and is
isolated by Postgres RLS (`app.current_org_id`).

Money is `Numeric(18, 2)` (INR); units are `Numeric(18, 4)` to allow
fractional mutual-fund units; rates are `Numeric(9, 4)` per CLAUDE.md §6.2.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class TreasuryInvestment(BaseModel):
    """A single treasury investment holding (one ISIN / one MF folio)."""

    __tablename__ = "trs_investment"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "investment_number",
            name="uq_trs_investment_number",
        ),
        Index("ix_trs_investment_org", "organization_id"),
        Index("ix_trs_investment_org_status", "organization_id", "status"),
        Index("ix_trs_investment_org_category", "organization_id", "category"),
        Index("ix_trs_investment_org_type", "organization_id", "type"),
        Index("ix_trs_investment_maturity", "maturity_date"),
    )

    # ----- Tenant / identity --------------------------------------------------

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )
    investment_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # ----- Classification -----------------------------------------------------

    # `String` columns with Python-side enums — matches the existing treasury
    # codebase style (see Borrowing.borrowing_type etc.).
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # InvestmentType
    category: Mapped[str] = mapped_column(String(10), nullable=False)  # InvestmentCategory

    # ----- Instrument details -------------------------------------------------

    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(20))

    # ----- Pricing & quantity -------------------------------------------------

    face_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    # Fractional MF units → 4dp precision.
    units: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # ----- Yield --------------------------------------------------------------

    coupon_rate: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False, default=Decimal("0")
    )
    ytm: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False, default=Decimal("0"))
    coupon_frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # CouponFrequency

    # ----- Dates --------------------------------------------------------------

    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Mutual funds have no fixed maturity; nullable.
    maturity_date: Mapped[date | None] = mapped_column(Date)

    # ----- Counterparty & narrative ------------------------------------------

    broker: Mapped[str | None] = mapped_column(String(200))
    remarks: Mapped[str | None] = mapped_column(Text)

    # ----- Lifecycle ---------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )  # InvestmentStatus

    # Last marked-to-market valuation. Updated by valuation jobs (deferred).
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    accrued_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    # Sale realisation (set on `mark_matured` when sold rather than redeemed).
    sale_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    sale_date: Mapped[date | None] = mapped_column(Date)
    realized_gain_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # ----- Relationships ------------------------------------------------------

    organization: Mapped[Organization] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
