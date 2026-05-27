"""Enforce one live IIF claim per enrollment period.

Revision ID: zzc67_iif_claim_period_uniqueness
Revises: zzc66_document_studio_and_dms_filing
Create Date: 2026-05-26
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc67_iif_claim_period_uniqueness"
down_revision = "zzc66_document_studio_and_dms_filing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "txn_subvention_claim",
        sa.Column(
            "calculation_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    # Development data may contain old duplicate draft/submitted rows. Keep the
    # earliest row as the canonical claim and cancel the rest before adding the
    # database invariant.
    op.execute("""
        WITH ranked AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY organization_id, enrollment_id, period_start, period_end
                    ORDER BY created_at ASC, id ASC
                ) AS row_rank
            FROM txn_subvention_claim
            WHERE deleted_at IS NULL
              AND status <> 'CANCELLED'
        )
        UPDATE txn_subvention_claim c
        SET
            status = 'CANCELLED',
            rejection_reason = COALESCE(
                c.rejection_reason,
                'Auto-cancelled during migration: duplicate live claim period.'
            ),
            updated_at = now()
        FROM ranked r
        WHERE c.id = r.id
          AND r.row_rank > 1
        """)
    op.create_index(
        "uq_txn_subvention_claim_live_period",
        "txn_subvention_claim",
        ["organization_id", "enrollment_id", "period_start", "period_end"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND status <> 'CANCELLED'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_txn_subvention_claim_live_period",
        table_name="txn_subvention_claim",
    )
    op.drop_column("txn_subvention_claim", "calculation_snapshot")
