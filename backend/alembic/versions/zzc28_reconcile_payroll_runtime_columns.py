"""Reconcile payroll runtime columns with ORM models.

Revision ID: zzc28_reconcile_payroll_runtime_columns
Revises: zzc27_reconcile_hris_payroll_ess_base_columns
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc28_reconcile_payroll_runtime_columns"
down_revision = "zzc27_reconcile_hris_payroll_ess_base_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS payroll_batch ADD COLUMN IF NOT EXISTS batch_number VARCHAR(30)")
    op.execute(
        """
        UPDATE payroll_batch
        SET batch_number = COALESCE(batch_number, batch_reference, 'PAY/LEGACY/000')
        WHERE batch_number IS NULL
        """
    )
    op.execute("ALTER TABLE IF EXISTS payroll_batch ALTER COLUMN batch_number SET DEFAULT 'PAY/LEGACY/000'")
    op.execute("ALTER TABLE IF EXISTS payroll_batch ALTER COLUMN batch_number SET NOT NULL")
    op.execute("ALTER TABLE IF EXISTS payroll_batch ADD COLUMN IF NOT EXISTS payment_date DATE")
    op.execute(
        "ALTER TABLE IF EXISTS payroll_batch "
        "ADD COLUMN IF NOT EXISTS total_employer_statutory NUMERIC(18, 2) NOT NULL DEFAULT 0"
    )
    op.execute(
        """
        UPDATE payroll_batch
        SET total_employer_statutory = COALESCE(total_employer_statutory, total_employer_contribution, 0)
        """
    )
    for column_name in (
        "total_pf_employee",
        "total_pf_employer",
        "total_esi_employee",
        "total_esi_employer",
        "total_pt",
        "total_tds",
    ):
        op.execute(
            f"ALTER TABLE IF EXISTS payroll_batch "
            f"ADD COLUMN IF NOT EXISTS {column_name} NUMERIC(18, 2) NOT NULL DEFAULT 0"
        )

    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS payslip_number VARCHAR(30)")
    op.execute(
        """
        UPDATE payroll_payslip
        SET payslip_number = COALESCE(payslip_number, id::text)
        WHERE payslip_number IS NULL
        """
    )
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ALTER COLUMN payslip_number SET DEFAULT 'PAYSLIP-LEGACY'")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ALTER COLUMN payslip_number SET NOT NULL")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS employee_code VARCHAR(20) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS employee_name VARCHAR(200) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS department_name VARCHAR(100)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS designation_name VARCHAR(100)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS pan_number VARCHAR(10)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS uan_number VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS esi_number VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS bank_account_number VARCHAR(30)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS bank_ifsc VARCHAR(15)")
    for column_name in (
        "days_present",
        "days_absent",
        "leave_days",
        "overtime_hours",
        "pf_wage",
        "esi_wage",
        "pt_wage",
        "taxable_income",
        "arrears_amount",
    ):
        op.execute(
            f"ALTER TABLE IF EXISTS payroll_payslip "
            f"ADD COLUMN IF NOT EXISTS {column_name} NUMERIC(18, 2) NOT NULL DEFAULT 0"
        )
    op.execute(
        "ALTER TABLE IF EXISTS payroll_payslip "
        "ADD COLUMN IF NOT EXISTS gross_salary NUMERIC(18, 2) NOT NULL DEFAULT 0"
    )
    op.execute(
        "UPDATE payroll_payslip SET gross_salary = COALESCE(NULLIF(gross_salary, 0), gross_earnings, 0)"
    )
    op.execute(
        "ALTER TABLE IF EXISTS payroll_payslip "
        "ADD COLUMN IF NOT EXISTS total_earnings NUMERIC(18, 2) NOT NULL DEFAULT 0"
    )
    op.execute(
        "UPDATE payroll_payslip SET total_earnings = COALESCE(NULLIF(total_earnings, 0), gross_earnings, 0)"
    )
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS arrears_remarks VARCHAR(200)")
    op.execute(
        "ALTER TABLE IF EXISTS payroll_payslip "
        "ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(20) NOT NULL DEFAULT 'BANK'"
    )
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP")
    op.execute("ALTER TABLE IF EXISTS payroll_payslip ADD COLUMN IF NOT EXISTS remarks TEXT")


def downgrade() -> None:
    for column_name in (
        "remarks",
        "paid_at",
        "payment_reference",
        "payment_mode",
        "arrears_remarks",
        "total_earnings",
        "gross_salary",
        "arrears_amount",
        "taxable_income",
        "pt_wage",
        "esi_wage",
        "pf_wage",
        "overtime_hours",
        "leave_days",
        "days_absent",
        "days_present",
        "bank_ifsc",
        "bank_account_number",
        "esi_number",
        "uan_number",
        "pan_number",
        "designation_name",
        "department_name",
        "employee_name",
        "employee_code",
        "payslip_number",
    ):
        op.execute(f"ALTER TABLE IF EXISTS payroll_payslip DROP COLUMN IF EXISTS {column_name}")

    for column_name in (
        "total_tds",
        "total_pt",
        "total_esi_employer",
        "total_esi_employee",
        "total_pf_employer",
        "total_pf_employee",
        "total_employer_statutory",
        "payment_date",
        "batch_number",
    ):
        op.execute(f"ALTER TABLE IF EXISTS payroll_batch DROP COLUMN IF EXISTS {column_name}")
