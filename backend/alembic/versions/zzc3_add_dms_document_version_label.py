"""Add DMS document version label column used by uploads."""

from alembic import op

revision = "zzc3_add_dms_document_version_label"
down_revision = "zzc2_add_dms_document_is_expired"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS dms_document_version
        ADD COLUMN IF NOT EXISTS version_label VARCHAR(100)
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS dms_document_version DROP COLUMN IF EXISTS version_label")
