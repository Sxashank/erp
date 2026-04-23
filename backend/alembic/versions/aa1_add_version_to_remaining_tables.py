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


def upgrade() -> None:
    for table in TABLES_TO_VERSION:
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
    for table in reversed(TABLES_TO_VERSION):
        op.drop_column(table, "version")
