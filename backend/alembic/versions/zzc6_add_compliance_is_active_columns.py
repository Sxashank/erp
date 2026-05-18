"""Add missing is_active columns to compliance tables.

Revision ID: zzc6_add_compliance_is_active_columns
Revises: zzc5_add_compliance_base_model_columns
Create Date: 2026-05-14
"""

from alembic import op

revision = "zzc6_add_compliance_is_active_columns"
down_revision = "zzc5_add_compliance_base_model_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in (
        "compliance_item",
        "compliance_instance",
        "compliance_document",
        "compliance_reminder",
    ):
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true"
        )


def downgrade() -> None:
    for table_name in (
        "compliance_reminder",
        "compliance_document",
        "compliance_instance",
        "compliance_item",
    ):
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS is_active")
