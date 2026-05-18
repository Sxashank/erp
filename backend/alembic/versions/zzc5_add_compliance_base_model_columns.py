"""Add missing BaseModel columns to compliance tables.

Revision ID: zzc5_add_compliance_base_model_columns
Revises: zzc4_add_dms_document_extracted_metadata
Create Date: 2026-05-14
"""

from alembic import op

revision = "zzc5_add_compliance_base_model_columns"
down_revision = "zzc4_add_dms_document_extracted_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in (
        "compliance_item",
        "compliance_instance",
        "compliance_document",
        "compliance_reminder",
    ):
        op.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES mst_user(id) ON DELETE SET NULL"
        )
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"
        )


def downgrade() -> None:
    for table_name in (
        "compliance_reminder",
        "compliance_document",
        "compliance_instance",
        "compliance_item",
    ):
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS version")
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS deleted_by")
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS deleted_at")
