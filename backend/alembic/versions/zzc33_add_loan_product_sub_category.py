"""Add loan product sub-category column.

Revision ID: zzc33_add_loan_product_sub_category
Revises: zzc32_add_missing_version_columns
Create Date: 2026-05-18
"""

import sqlalchemy as sa
from alembic import op


revision = "zzc33_add_loan_product_sub_category"
down_revision = "zzc32_add_missing_version_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sub_category" not in {column["name"] for column in inspector.get_columns("los_loan_product")}:
        op.add_column(
            "los_loan_product",
            sa.Column("sub_category", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sub_category" in {column["name"] for column in inspector.get_columns("los_loan_product")}:
        op.drop_column("los_loan_product", "sub_category")
