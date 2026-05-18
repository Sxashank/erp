"""Add SoftDeleteMixin + VersionedMixin columns to col_write_off.

Companion to zz1 — the write-off table was missed in the first sweep
(the column-name guess was `col_write_off_record` but the real table is
`col_write_off`). Surfaced when the recovery-summary endpoint queried
``col_write_off.is_active`` and got UndefinedColumnError.

Revision ID: zz2_softdelete_write_off
Revises: zz1_collections_softdelete
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zz2_softdelete_write_off"
down_revision = "zz1_collections_softdelete"
branch_labels = None
depends_on = None


TABLES = ["col_write_off"]


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    cols = {c["name"] for c in insp.get_columns(table)}
    return column in cols


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def upgrade() -> None:
    for tbl in TABLES:
        if not _table_exists(tbl):
            continue
        if not _has_column(tbl, "deleted_at"):
            op.add_column(tbl, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column(tbl, "deleted_by"):
            op.add_column(
                tbl,
                sa.Column("deleted_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            )
        if not _has_column(tbl, "is_active"):
            op.add_column(
                tbl,
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            )
        if not _has_column(tbl, "version"):
            op.add_column(
                tbl,
                sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            )


def downgrade() -> None:
    for tbl in TABLES:
        if not _table_exists(tbl):
            continue
        for col in ("version", "is_active", "deleted_by", "deleted_at"):
            if _has_column(tbl, col):
                op.drop_column(tbl, col)
