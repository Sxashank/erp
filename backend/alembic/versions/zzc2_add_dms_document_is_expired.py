"""Add DMS document expiry flag used by portal uploads."""

from alembic import op

revision = "zzc2_add_dms_document_is_expired"
down_revision = "zzc1_align_manual_uat_portal_and_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS dms_document
        ADD COLUMN IF NOT EXISTS is_expired BOOLEAN NOT NULL DEFAULT FALSE
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS dms_document DROP COLUMN IF EXISTS is_expired")
