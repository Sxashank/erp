"""Align bank statement soft-delete columns with ORM.

The BankStatement ORM includes SoftDeleteMixin and VersionedMixin fields.
Older databases created by the original BRS migration do not have
``is_active`` and ``version``, which breaks dashboard matching summaries.
"""

from alembic import op

revision = "zzc0_add_bank_statement_soft_delete_columns"
down_revision = "zzb0_add_subvention_claim_release_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS txn_bank_statement
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """)
    op.execute("""
        ALTER TABLE IF EXISTS txn_bank_statement
        ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS txn_bank_statement DROP COLUMN IF EXISTS version")
    op.execute("ALTER TABLE IF EXISTS txn_bank_statement DROP COLUMN IF EXISTS is_active")
