"""Relax legacy inventory columns superseded by current ORM fields.

Revision ID: zzc42_relax_legacy_inventory_columns
Revises: zzc41_align_inventory_master_columns
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc42_relax_legacy_inventory_columns"
down_revision = "zzc41_align_inventory_master_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in ("mst_item_category", "mst_warehouse", "mst_item_master"):
        op.alter_column(table_name, "code", existing_type=sa.String(), nullable=True)
        op.alter_column(table_name, "name", existing_type=sa.String(), nullable=True)
    op.alter_column("mst_item_master", "primary_uom", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    pass
