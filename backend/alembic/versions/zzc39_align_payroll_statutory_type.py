"""Align payroll statutory type to ORM string type.

Revision ID: zzc39_align_payroll_statutory_type
Revises: zzc38_align_payroll_master_columns
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc39_align_payroll_statutory_type"
down_revision = "zzc38_align_payroll_master_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "payroll_statutory_setup",
        "statutory_type",
        type_=sa.String(length=20),
        postgresql_using="statutory_type::text",
    )


def downgrade() -> None:
    pass
