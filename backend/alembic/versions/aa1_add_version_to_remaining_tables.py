"""Add `version` column for optimistic locking to 9 remaining tables.

Revision ID: aa1_version_9_tables
Revises: aa0_idempotency_key
Create Date: 2026-04-23

Closes STAGE-4-PENDING-002. Every table below had `Base` + a Timestamp/Audit
mixin but not `VersionedMixin`; we're now adding the `version` column and
backfilling to 1 for existing rows so the ORM's optimistic-lock check
doesn't fail on day-one loads.

See CLAUDE.md §6.3 and `scripts/audit_optimistic_locking.py`.
"""

import sqlalchemy as sa

from alembic import op

revision = "aa1_version_9_tables"
down_revision = "aa0_idempotency_key"
branch_labels = None
depends_on = None


TABLES_TO_VERSION = [
    "gst_gstn_session",
    "gst_gstr2b_data",
    "gst_itc_mismatch",
    "gst_return_filing",
    "hris_clearance_checklist",
    "hris_fnf_settlement",
    "hris_separation",
    "hris_separation_clearance",
    "lending_credit_account",
]


def _table_exists(conn, table_name: str) -> bool:
    """Skip non-existent tables — older deploys missed creating some HRIS/GST
    auxiliary tables. The CREATE for those tables lives in a later migration
    that brings the version column with it, so this pass becomes a no-op
    on fresh DBs."""
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = :name"
        ),
        {"name": table_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    for table in TABLES_TO_VERSION:
        if not _table_exists(conn, table):
            continue
        op.add_column(
            table,
            sa.Column(
                "version",
                sa.Integer,
                nullable=False,
                server_default=sa.text("1"),
                comment="Record version for optimistic locking",
            ),
        )
        # Drop the server_default after backfill so future inserts use
        # the Python-side default from the ORM (VersionedMixin sets 1).
        op.alter_column(table, "version", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    for table in reversed(TABLES_TO_VERSION):
        if not _table_exists(conn, table):
            continue
        op.drop_column(table, "version")
