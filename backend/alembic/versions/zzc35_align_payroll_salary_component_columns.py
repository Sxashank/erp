"""Align payroll salary component columns with ORM.

Revision ID: zzc35_align_payroll_salary_component_columns
Revises: zzc34_align_leave_category_enum
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc35_align_payroll_salary_component_columns"
down_revision = "zzc34_align_leave_category_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payroll_salary_component", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("payroll_salary_component", sa.Column("default_value", sa.Numeric(18, 2), nullable=True))
    op.add_column("payroll_salary_component", sa.Column("tax_exemption_limit", sa.Numeric(18, 2), nullable=True))
    op.add_column("payroll_salary_component", sa.Column("exemption_section", sa.String(length=20), nullable=True))
    op.add_column(
        "payroll_salary_component",
        sa.Column("is_part_of_basic", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "payroll_salary_component",
        sa.Column("is_part_of_gross", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "payroll_salary_component",
        sa.Column("is_part_of_ctc", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "payroll_salary_component",
        sa.Column("affects_gratuity", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "payroll_salary_component",
        sa.Column("show_on_payslip", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    for column_name in (
        "show_on_payslip",
        "affects_gratuity",
        "is_part_of_ctc",
        "is_part_of_gross",
        "is_part_of_basic",
        "exemption_section",
        "tax_exemption_limit",
        "default_value",
        "description",
    ):
        op.drop_column("payroll_salary_component", column_name)
