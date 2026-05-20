"""Align payroll salary structure component calculation type.

Revision ID: zzc40_align_salary_structure_component_type
Revises: zzc39_align_payroll_statutory_type
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc40_align_salary_structure_component_type"
down_revision = "zzc39_align_payroll_statutory_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "payroll_salary_structure_component",
        "calculation_type",
        type_=sa.String(length=30),
        postgresql_using="calculation_type::text",
    )


def downgrade() -> None:
    pass
