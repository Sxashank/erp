"""Align DMS folder table with ORM model.

Revision ID: zzc13_align_dms_folder_columns
Revises: zzc12_align_legal_expense_columns
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc13_align_dms_folder_columns"
down_revision = "zzc12_align_legal_expense_columns"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return column in {col["name"] for col in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("dms_folder", "inherit_access"):
        op.add_column(
            "dms_folder",
            sa.Column("inherit_access", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if not _has_column("dms_folder", "total_size"):
        op.add_column(
            "dms_folder",
            sa.Column("total_size", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("dms_folder", "folder_metadata"):
        op.add_column("dms_folder", sa.Column("folder_metadata", postgresql.JSONB()))


def downgrade() -> None:
    for column in ["inherit_access", "total_size", "folder_metadata"]:
        if _has_column("dms_folder", column):
            op.drop_column("dms_folder", column)
