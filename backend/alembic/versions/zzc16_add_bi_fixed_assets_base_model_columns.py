"""Add missing BaseModel columns to BI and fixed-assets tables.

Revision ID: zzc16_add_bi_fixed_assets_base_model_columns
Revises: zzc15_reconcile_approval_workflow_tables
Create Date: 2026-05-17
"""

from alembic import op

revision = "zzc16_add_bi_fixed_assets_base_model_columns"
down_revision = "zzc15_reconcile_approval_workflow_tables"
branch_labels = None
depends_on = None


FIXED_ASSET_TABLES = (
    "mst_asset_category",
    "mst_fixed_asset",
    "txn_depreciation_run",
    "txn_depreciation",
    "txn_asset_transfer",
    "txn_asset_revaluation",
)

BI_TABLES = (
    "bi_dashboard",
    "bi_dashboard_widget",
    "bi_dashboard_role_access",
    "bi_chart_definition",
    "bi_chart_role_access",
    "bi_data_source",
)


def upgrade() -> None:
    for table_name in FIXED_ASSET_TABLES:
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"
        )

    for table_name in BI_TABLES:
        op.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES mst_user(id) ON DELETE SET NULL"
        )
        op.execute(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"
        )


def downgrade() -> None:
    for table_name in reversed(BI_TABLES):
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS version")
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS deleted_by")
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS deleted_at")

    for table_name in reversed(FIXED_ASSET_TABLES):
        op.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS version")
