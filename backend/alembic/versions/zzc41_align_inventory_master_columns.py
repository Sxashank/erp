"""Align inventory master columns with current ORM.

Revision ID: zzc41_align_inventory_master_columns
Revises: zzc40_align_salary_structure_component_type
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "zzc41_align_inventory_master_columns"
down_revision = "zzc40_align_salary_structure_component_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mst_item_category", sa.Column("category_code", sa.String(length=20), nullable=True))
    op.add_column("mst_item_category", sa.Column("category_name", sa.String(length=100), nullable=True))
    op.add_column("mst_item_category", sa.Column("parent_category_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "mst_item_category",
        sa.Column("is_stockable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "mst_item_category",
        sa.Column("requires_serial_number", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "mst_item_category",
        sa.Column("requires_batch_number", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("mst_item_category", sa.Column("gl_inventory_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("mst_item_category", sa.Column("gl_expense_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_item_category_parent_category_id",
        "mst_item_category",
        "mst_item_category",
        ["parent_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_item_category_gl_inventory_account_id",
        "mst_item_category",
        "mst_account",
        ["gl_inventory_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_item_category_gl_expense_account_id",
        "mst_item_category",
        "mst_account",
        ["gl_expense_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("mst_warehouse", sa.Column("warehouse_code", sa.String(length=20), nullable=True))
    op.add_column("mst_warehouse", sa.Column("warehouse_name", sa.String(length=100), nullable=True))
    op.add_column(
        "mst_warehouse",
        sa.Column("allow_negative_stock", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.add_column("mst_item_master", sa.Column("item_code", sa.String(length=50), nullable=True))
    op.add_column("mst_item_master", sa.Column("item_name", sa.String(length=200), nullable=True))
    op.add_column("mst_item_master", sa.Column("uom", sa.String(length=20), nullable=True))
    op.add_column(
        "mst_item_master",
        sa.Column("is_stockable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "mst_item_master",
        sa.Column("requires_serial_number", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "mst_item_master",
        sa.Column("requires_batch_number", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("mst_item_master", sa.Column("model_number", sa.String(length=100), nullable=True))
    op.add_column("mst_item_master", sa.Column("minimum_stock_level", sa.Numeric(18, 4), nullable=True))
    op.add_column("mst_item_master", sa.Column("maximum_stock_level", sa.Numeric(18, 4), nullable=True))
    op.add_column("mst_item_master", sa.Column("reorder_quantity", sa.Numeric(18, 4), nullable=True))
    op.add_column("mst_item_master", sa.Column("gl_inventory_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("mst_item_master", sa.Column("gl_expense_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_item_master_gl_inventory_account_id",
        "mst_item_master",
        "mst_account",
        ["gl_inventory_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_item_master_gl_expense_account_id",
        "mst_item_master",
        "mst_account",
        ["gl_expense_account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    for constraint_name, table_name in (
        ("fk_item_master_gl_expense_account_id", "mst_item_master"),
        ("fk_item_master_gl_inventory_account_id", "mst_item_master"),
        ("fk_item_category_gl_expense_account_id", "mst_item_category"),
        ("fk_item_category_gl_inventory_account_id", "mst_item_category"),
        ("fk_item_category_parent_category_id", "mst_item_category"),
    ):
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")

    for column_name in (
        "gl_expense_account_id",
        "gl_inventory_account_id",
        "reorder_quantity",
        "maximum_stock_level",
        "minimum_stock_level",
        "model_number",
        "requires_batch_number",
        "requires_serial_number",
        "is_stockable",
        "uom",
        "item_name",
        "item_code",
    ):
        op.drop_column("mst_item_master", column_name)

    for column_name in ("allow_negative_stock", "warehouse_name", "warehouse_code"):
        op.drop_column("mst_warehouse", column_name)

    for column_name in (
        "gl_expense_account_id",
        "gl_inventory_account_id",
        "requires_batch_number",
        "requires_serial_number",
        "is_stockable",
        "parent_category_id",
        "category_name",
        "category_code",
    ):
        op.drop_column("mst_item_category", column_name)
