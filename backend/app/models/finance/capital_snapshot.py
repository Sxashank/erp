"""Capital Snapshot model — historical CRAR series.

Each row is a point-in-time persisted CRAR computation for one NBFC
(tenant). The Regulatory Dashboard's CRAR-trend chart reads from this
table; a daily/monthly job (see `record_capital_snapshot` on
`RegulatoryReportService`) is expected to insert one row per snapshot
date. Records are immutable in business terms — re-running for the same
date should upsert by `(organization_id, snapshot_date)`.

Mirrors the column shape returned by `generate_crar_report` so the chart
can plot `crar` + `tier_1_ratio` directly without re-aggregation.

See CLAUDE.md §3.4 (every mutable table has `organization_id`), §4.9
(CRAR + Tier-1 / Tier-2 / RWA accounting), §6.2 (NUMERIC(18,2) for INR;
NUMERIC(9,4) for ratios).
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class CapitalSnapshot(BaseModel):
    """Point-in-time CRAR + capital position for an organization."""

    __tablename__ = "fin_capital_snapshot"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Business date for this snapshot",
    )

    # Capital components (₹)
    tier_1_capital: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tier-1 capital total at snapshot date",
    )
    tier_2_capital: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tier-2 capital total at snapshot date",
    )
    total_capital: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tier-1 + Tier-2",
    )

    # Risk-weighted assets (₹)
    credit_risk_rwa: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    market_risk_rwa: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    operational_risk_rwa: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_rwa: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Ratios (%) — stored to avoid re-deriving for trend lines.
    crar: Mapped[Decimal] = mapped_column(
        Numeric(9, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Total capital / RWA × 100",
    )
    tier_1_ratio: Mapped[Decimal] = mapped_column(
        Numeric(9, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Tier-1 capital / RWA × 100",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "snapshot_date",
            name="uq_fin_capital_snapshot_org_date",
        ),
        Index(
            "ix_fin_capital_snapshot_org_date",
            "organization_id",
            "snapshot_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CapitalSnapshot(date={self.snapshot_date}, "
            f"crar={self.crar}, t1={self.tier_1_ratio})>"
        )
