"""Align portal notification and security release fields for manual UAT."""

from alembic import op

revision = "zzc1_align_manual_uat_portal_and_security"
down_revision = "zzc0_add_bank_statement_soft_delete_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS los_loan_security
        ADD COLUMN IF NOT EXISTS release_date DATE
        """)
    op.execute("""
        ALTER TABLE IF EXISTS portal_notification
        ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50),
        ADD COLUMN IF NOT EXISTS reference_id UUID,
        ADD COLUMN IF NOT EXISTS is_sent BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS delivery_error TEXT,
        ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS portal_notification DROP COLUMN IF EXISTS expires_at")
    op.execute("ALTER TABLE IF EXISTS portal_notification DROP COLUMN IF EXISTS delivery_error")
    op.execute("ALTER TABLE IF EXISTS portal_notification DROP COLUMN IF EXISTS is_sent")
    op.execute("ALTER TABLE IF EXISTS portal_notification DROP COLUMN IF EXISTS reference_id")
    op.execute("ALTER TABLE IF EXISTS portal_notification DROP COLUMN IF EXISTS reference_type")
    op.execute("ALTER TABLE IF EXISTS los_loan_security DROP COLUMN IF EXISTS release_date")
