"""Add fin_capital_snapshot — historical CRAR / Tier-1 / Tier-2 series.

Point-in-time CRAR snapshot per NBFC (tenant) for the regulatory
dashboard's CRAR-trend chart. One row per `(organization_id,
snapshot_date)`. The matching ORM lives at
`app/models/finance/capital_snapshot.py`; the service that writes rows
is `RegulatoryReportService.record_capital_snapshot` (call from a
daily/monthly job — wiring deferred).

Multi-tenant via `organization_id`; an RLS policy is expected to be
applied by the existing tenancy template (out of scope for this
migration, matches the rest of the `fin_*` table family).

Revision ID: zz4_add_fin_capital_snapshot
Revises: zz3_add_trs_investment
Create Date: 2026-05-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zz4_add_fin_capital_snapshot"
down_revision: str | None = "zz3_add_trs_investment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fin_capital_snapshot",
        # ----- Identity / mixins (BaseModel + AuditMixin + SoftDelete + Versioned)
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        # ----- Capital amounts (₹) — NUMERIC(18,2)
        sa.Column(
            "tier_1_capital",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "tier_2_capital",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_capital",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # ----- RWA amounts (₹)
        sa.Column(
            "credit_risk_rwa",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "market_risk_rwa",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "operational_risk_rwa",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_rwa",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # ----- Ratios (%) — NUMERIC(9,4)
        sa.Column(
            "crar",
            sa.Numeric(9, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "tier_1_ratio",
            sa.Numeric(9, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # ----- AuditMixin
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        # ----- SoftDeleteMixin
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        # ----- VersionedMixin
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        # ----- Constraints
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_fin_capital_snapshot_organization",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_fin_capital_snapshot_created_by",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_fin_capital_snapshot_updated_by",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_fin_capital_snapshot_deleted_by",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "snapshot_date",
            name="uq_fin_capital_snapshot_org_date",
        ),
    )

    op.create_index(
        "ix_fin_capital_snapshot_org",
        "fin_capital_snapshot",
        ["organization_id"],
    )
    op.create_index(
        "ix_fin_capital_snapshot_org_date",
        "fin_capital_snapshot",
        ["organization_id", "snapshot_date"],
    )
    op.create_index(
        "ix_fin_capital_snapshot_date",
        "fin_capital_snapshot",
        ["snapshot_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_fin_capital_snapshot_date", table_name="fin_capital_snapshot")
    op.drop_index("ix_fin_capital_snapshot_org_date", table_name="fin_capital_snapshot")
    op.drop_index("ix_fin_capital_snapshot_org", table_name="fin_capital_snapshot")
    op.drop_table("fin_capital_snapshot")
