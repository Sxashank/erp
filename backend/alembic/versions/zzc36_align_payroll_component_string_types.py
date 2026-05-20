"""Align payroll component code columns to ORM string types.

Revision ID: zzc36_align_payroll_component_string_types
Revises: zzc35_align_payroll_salary_component_columns
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc36_align_payroll_component_string_types"
down_revision = "zzc35_align_payroll_salary_component_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "payroll_salary_component",
        "component_type",
        type_=sa.String(length=20),
        postgresql_using="component_type::text",
    )
    op.alter_column(
        "payroll_salary_component",
        "category",
        type_=sa.String(length=20),
        postgresql_using="category::text",
    )
    op.alter_column(
        "payroll_salary_component",
        "calculation_type",
        type_=sa.String(length=30),
        postgresql_using="calculation_type::text",
    )


def downgrade() -> None:
    pass
