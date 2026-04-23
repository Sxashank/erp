"""Add audit_day_anchor table (STAGE-5-PENDING-002 closure).

Revision ID: aa2_audit_day_anchor
Revises: aa1_version_9_tables
Create Date: 2026-04-23

Persists the daily audit-integrity anchor. See CLAUDE.md §8.5.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "aa2_audit_day_anchor"
down_revision = "aa1_version_9_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_day_anchor",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column(
            "previous_anchor",
            sa.String(64),
            nullable=False,
            comment="Hex SHA-256 anchor from the prior day (genesis = 64 zeros)",
        ),
        sa.Column(
            "anchor",
            sa.String(64),
            nullable=False,
            comment="Hex SHA-256 anchor for this day",
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_audit_day_anchor_org_day",
        "audit_day_anchor",
        ["organization_id", "day"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_day_anchor_org_day", table_name="audit_day_anchor")
    op.drop_table("audit_day_anchor")
