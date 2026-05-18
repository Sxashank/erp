"""Add advocate website column required by ContactMixin.

Revision ID: zzc10_add_advocate_website
Revises: zzc9_align_advocate_law_firm_columns
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zzc10_add_advocate_website"
down_revision = "zzc9_align_advocate_law_firm_columns"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return column in {col["name"] for col in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("mst_advocate", "website"):
        op.add_column("mst_advocate", sa.Column("website", sa.String(255)))


def downgrade() -> None:
    if _has_column("mst_advocate", "website"):
        op.drop_column("mst_advocate", "website")
