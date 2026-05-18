"""Add DMS extracted metadata column used by document refresh."""

from alembic import op

revision = "zzc4_add_dms_document_extracted_metadata"
down_revision = "zzc3_add_dms_document_version_label"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS dms_document
        ADD COLUMN IF NOT EXISTS extracted_metadata JSONB
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS dms_document DROP COLUMN IF EXISTS extracted_metadata")
