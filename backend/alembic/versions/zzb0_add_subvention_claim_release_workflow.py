"""Add explicit release workflow fields to subvention claims.

Scheme claims should move through VERIFIED -> RELEASE_IN_PROGRESS ->
RELEASED. Existing legacy PAID rows are migrated to RELEASED so the
portal and admin IIF surfaces share one scheme-neutral lifecycle.
"""

import sqlalchemy as sa

from alembic import op

revision = "zzb0_add_subvention_claim_release_workflow"
down_revision = "zza4_add_fund_deployment_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "txn_subvention_claim",
        sa.Column("release_initiated_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "txn_subvention_claim",
        sa.Column(
            "release_instruction_reference",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "txn_subvention_claim",
        sa.Column(
            "release_instruction_notes",
            sa.String(length=500),
            nullable=True,
        ),
    )
    op.execute("""
        UPDATE txn_subvention_claim
        SET status = 'RELEASED'
        WHERE status = 'PAID'
        """)


def downgrade() -> None:
    op.execute("""
        UPDATE txn_subvention_claim
        SET status = 'PAID'
        WHERE status = 'RELEASED'
        """)
    op.drop_column("txn_subvention_claim", "release_instruction_notes")
    op.drop_column("txn_subvention_claim", "release_instruction_reference")
    op.drop_column("txn_subvention_claim", "release_initiated_date")
