"""Align payroll master tables with current ORM fields.

Revision ID: zzc38_align_payroll_master_columns
Revises: zzc37_relax_updated_at_nullability
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "zzc38_align_payroll_master_columns"
down_revision = "zzc37_relax_updated_at_nullability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payroll_salary_structure", sa.Column("effective_from", sa.Date(), nullable=True))
    op.add_column("payroll_salary_structure", sa.Column("effective_to", sa.Date(), nullable=True))
    op.add_column(
        "payroll_salary_structure",
        sa.Column("payment_mode", sa.String(length=20), nullable=False, server_default="BANK"),
    )
    op.add_column(
        "payroll_salary_structure",
        sa.Column("pay_frequency", sa.String(length=20), nullable=False, server_default="MONTHLY"),
    )

    op.add_column("payroll_salary_structure_component", sa.Column("value", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE payroll_salary_structure_component SET value = default_value WHERE value IS NULL")

    for column_name in (
        "pf_employer_rate",
        "pf_employee_rate",
        "pf_admin_charge_rate",
        "pf_edli_rate",
        "eps_employer_rate",
        "esi_employer_rate",
        "esi_employee_rate",
    ):
        op.add_column("payroll_statutory_setup", sa.Column(column_name, sa.Numeric(5, 2), nullable=True))

    for column_name in ("pf_wage_ceiling", "eps_wage_ceiling", "esi_wage_ceiling"):
        op.add_column("payroll_statutory_setup", sa.Column(column_name, sa.Numeric(18, 2), nullable=True))

    op.add_column("payroll_statutory_setup", sa.Column("pt_state", sa.String(length=50), nullable=True))
    op.add_column("payroll_statutory_setup", sa.Column("pt_slabs", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "payroll_statutory_setup",
        sa.Column("lwf_employer_contribution", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "payroll_statutory_setup",
        sa.Column("lwf_employee_contribution", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column("payroll_statutory_setup", sa.Column("lwf_frequency", sa.String(length=20), nullable=True))
    op.add_column("payroll_statutory_setup", sa.Column("effective_to", sa.Date(), nullable=True))


def downgrade() -> None:
    for table_name, columns in (
        (
            "payroll_statutory_setup",
            (
                "effective_to",
                "lwf_frequency",
                "lwf_employee_contribution",
                "lwf_employer_contribution",
                "pt_slabs",
                "pt_state",
                "esi_wage_ceiling",
                "eps_wage_ceiling",
                "pf_wage_ceiling",
                "esi_employee_rate",
                "esi_employer_rate",
                "eps_employer_rate",
                "pf_edli_rate",
                "pf_admin_charge_rate",
                "pf_employee_rate",
                "pf_employer_rate",
            ),
        ),
        ("payroll_salary_structure_component", ("value",)),
        ("payroll_salary_structure", ("pay_frequency", "payment_mode", "effective_to", "effective_from")),
    ):
        for column_name in columns:
            op.drop_column(table_name, column_name)
