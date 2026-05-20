"""Align leave category enum with current HRIS constants.

Revision ID: zzc34_align_leave_category_enum
Revises: zzc33_add_loan_product_sub_category
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc34_align_leave_category_enum"
down_revision = "zzc33_add_loan_product_sub_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for value in ("COMPENSATORY", "LOP"):
        op.execute(f"ALTER TYPE leave_category_enum ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL does not support dropping enum values without recreating the
    # type, which can be unsafe once leave rows exist. Keep downgrade as no-op.
    pass
