"""Relax stale updated_at NOT NULL constraints.

Revision ID: zzc37_relax_updated_at_nullability
Revises: zzc36_align_payroll_component_string_types
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc37_relax_updated_at_nullability"
down_revision = "zzc36_align_payroll_component_string_types"
branch_labels = None
depends_on = None


TABLES = (
    "bi_chart_definition",
    "bi_chart_role_access",
    "bi_dashboard",
    "bi_dashboard_role_access",
    "bi_dashboard_widget",
    "bi_data_source",
    "compliance_document",
    "compliance_instance",
    "compliance_item",
    "compliance_reminder",
    "lending_credit_account",
    "lending_credit_enquiry",
    "lending_credit_pull",
    "payroll_batch",
    "payroll_employee_salary",
    "payroll_payslip",
    "payroll_salary_component",
    "payroll_salary_structure",
    "payroll_statutory_setup",
    "trs_alm_asset",
    "trs_alm_liability",
    "trs_alm_position",
    "trs_borrowing",
    "trs_borrowing_covenant",
    "trs_borrowing_payment",
    "trs_borrowing_schedule",
    "trs_borrowing_tranche",
    "trs_exposure_limit",
    "trs_exposure_tracking",
    "trs_irs_analysis",
    "trs_lender",
)


def _table_exists(conn, table_name: str) -> bool:
    return (
        conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = current_schema() AND table_name = :table_name"
            ),
            {"table_name": table_name},
        ).scalar()
        is not None
    )


def upgrade() -> None:
    conn = op.get_bind()
    for table_name in TABLES:
        if not _table_exists(conn, table_name):
            continue
        op.alter_column(table_name, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    pass
