"""Reconcile HRIS, payroll, and ESS BaseModel columns.

Revision ID: zzc27_reconcile_hris_payroll_ess_base_columns
Revises: zzc26_reconcile_fixed_deposit_base_columns
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc27_reconcile_hris_payroll_ess_base_columns"
down_revision = "zzc26_reconcile_fixed_deposit_base_columns"
branch_labels = None
depends_on = None


TABLES = (
    "hris_employee",
    "hris_employee_document",
    "hris_employee_family",
    "hris_employee_bank_account",
    "hris_employee_education",
    "hris_employee_experience",
    "hris_employee_statutory",
    "hris_employee_lifecycle_event",
    "hris_shift",
    "hris_holiday_calendar",
    "hris_holiday",
    "hris_leave_type",
    "hris_leave_balance",
    "hris_leave_application",
    "hris_leave_encashment",
    "hris_attendance_punch",
    "hris_attendance",
    "hris_attendance_regularization",
    "hris_daily_attendance_summary",
    "hris_monthly_attendance_summary",
    "hris_separation",
    "hris_clearance_checklist",
    "hris_separation_clearance",
    "hris_fnf_settlement",
    "payroll_salary_component",
    "payroll_salary_structure",
    "payroll_salary_structure_component",
    "payroll_employee_salary",
    "payroll_employee_salary_component",
    "payroll_statutory_setup",
    "payroll_batch",
    "payroll_payslip",
    "payroll_payslip_component",
    "payroll_statutory",
    "ess_user",
    "ess_session",
    "ess_device",
    "ess_otp",
    "ess_profile_update_request",
    "ess_it_declaration",
    "ess_it_declaration_item",
    "ess_hra_receipt",
    "ess_attendance_regularization",
    "ess_reimbursement_claim",
    "ess_reimbursement_line_item",
    "ess_reimbursement_approval",
    "ess_helpdesk_ticket",
    "ess_ticket_comment",
    "ess_ticket_history",
)


def _add_base_columns(table_name: str) -> None:
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS created_by UUID")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS updated_by UUID")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS deleted_by UUID")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1")


def upgrade() -> None:
    for table_name in TABLES:
        _add_base_columns(table_name)


def downgrade() -> None:
    for table_name in reversed(TABLES):
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS version")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS is_active")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS deleted_by")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS deleted_at")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS updated_by")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS updated_at")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS created_by")
        op.execute(f"ALTER TABLE IF EXISTS {table_name} DROP COLUMN IF EXISTS created_at")
