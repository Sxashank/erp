"""Add trs_investment (treasury investment portfolio) table.

Holds individual treasury investment instruments owned by an NBFC —
G-Sec, SDL, T-Bill, corporate bonds, NCDs, CP, CD, mutual funds.
Distinct from `trs_alm_asset` which holds aggregated ALM-bucket
snapshots, not per-instrument detail.

Columns follow the existing treasury codebase style: enum values are
stored as `String`, validated by Python-side `enum.Enum` types defined
in `app.models.lending.enums` — keeps migrations regulator-friendly
(no PG-side enum churn) and lets us add new instrument types without
DDL.

Multi-tenant by `organization_id` + Postgres RLS (set in a later
migration if RLS is reapplied; the existing `z18_add_row_level_security`
policy template applies to any table with `organization_id` once the
relevant trigger / policy is created — out of scope for this migration).

Revision ID: zz3_add_trs_investment
Revises: zz2_softdelete_write_off
Create Date: 2026-05-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zz3_add_trs_investment"
down_revision: str | None = "zz2_softdelete_write_off"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trs_investment",
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
        sa.Column("investment_number", sa.String(length=50), nullable=False),
        # ----- Classification
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=10), nullable=False),
        # ----- Instrument details
        sa.Column("issuer", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("isin", sa.String(length=20), nullable=True),
        # ----- Pricing & quantity
        sa.Column("face_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("purchase_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("units", sa.Numeric(18, 4), nullable=False),
        # ----- Yield
        sa.Column(
            "coupon_rate",
            sa.Numeric(9, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "ytm",
            sa.Numeric(9, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("coupon_frequency", sa.String(length=20), nullable=False),
        # ----- Dates
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("maturity_date", sa.Date(), nullable=True),
        # ----- Counterparty & narrative
        sa.Column("broker", sa.String(length=200), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        # ----- Lifecycle
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("current_value", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "accrued_interest",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("sale_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("sale_date", sa.Date(), nullable=True),
        sa.Column("realized_gain_loss", sa.Numeric(18, 2), nullable=True),
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
            name="fk_trs_investment_organization",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_trs_investment_created_by",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_trs_investment_updated_by",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_trs_investment_deleted_by",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "investment_number",
            name="uq_trs_investment_number",
        ),
    )

    op.create_index(
        "ix_trs_investment_org",
        "trs_investment",
        ["organization_id"],
    )
    op.create_index(
        "ix_trs_investment_org_status",
        "trs_investment",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_trs_investment_org_category",
        "trs_investment",
        ["organization_id", "category"],
    )
    op.create_index(
        "ix_trs_investment_org_type",
        "trs_investment",
        ["organization_id", "type"],
    )
    op.create_index(
        "ix_trs_investment_maturity",
        "trs_investment",
        ["maturity_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_trs_investment_maturity", table_name="trs_investment")
    op.drop_index("ix_trs_investment_org_type", table_name="trs_investment")
    op.drop_index("ix_trs_investment_org_category", table_name="trs_investment")
    op.drop_index("ix_trs_investment_org_status", table_name="trs_investment")
    op.drop_index("ix_trs_investment_org", table_name="trs_investment")
    op.drop_table("trs_investment")
