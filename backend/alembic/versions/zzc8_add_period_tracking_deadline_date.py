"""Add deadline date expected by legal analytics.

Revision ID: zzc8_add_period_tracking_deadline_date
Revises: zzc7_add_legal_case_organization_id
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zzc8_add_period_tracking_deadline_date"
down_revision = "zzc7_add_legal_case_organization_id"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return column in {col["name"] for col in insp.get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return index in {idx["name"] for idx in insp.get_indexes(table)}


def upgrade() -> None:
    if not _has_column("txn_period_tracking", "deadline_date"):
        op.add_column(
            "txn_period_tracking",
            sa.Column("deadline_date", sa.Date(), nullable=True),
        )

    if _has_column("txn_period_tracking", "due_date"):
        op.execute("""
            UPDATE txn_period_tracking
            SET deadline_date = due_date
            WHERE deadline_date IS NULL
            """)

    if not _has_index("txn_period_tracking", "ix_period_track_deadline"):
        op.create_index(
            "ix_period_track_deadline",
            "txn_period_tracking",
            ["deadline_date"],
        )


def downgrade() -> None:
    if _has_index("txn_period_tracking", "ix_period_track_deadline"):
        op.drop_index("ix_period_track_deadline", table_name="txn_period_tracking")
    if _has_column("txn_period_tracking", "deadline_date"):
        op.drop_column("txn_period_tracking", "deadline_date")
