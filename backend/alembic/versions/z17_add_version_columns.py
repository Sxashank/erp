"""Add version columns for optimistic locking

Revision ID: z17_add_version_columns
Revises: z16_add_fixed_deposits
Create Date: 2026-01-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'z17_add_version_columns'
down_revision: Union[str, None] = 'z16_add_fixed_deposits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All tables that inherit from BaseModel and need version columns
TABLES_TO_UPDATE = [
    # Auth tables
    'mst_user',
    'mst_role',
    'mst_permission',
    'mst_user_session',
    # Organization tables
    'mst_organization',
    'mst_organization_address',
    'mst_organization_bank_account',
    'mst_unit',
    'mst_department',
    'mst_designation',
    # Finance tables
    'mst_account_group',
    'mst_account',
    'mst_voucher_type',
    'mst_financial_year',
    'mst_financial_period',
    'mst_cost_center',
    'txn_voucher',
    'txn_voucher_line',
    'txn_gl_entry',
    'mst_recurring_voucher',
    'mst_voucher_template',
    # AP/AR tables
    'mst_payment_terms',
    'mst_vendor',
    'mst_customer',
    'ap_purchase_bill',
    'ap_purchase_bill_line',
    'ar_sales_invoice',
    'ar_sales_invoice_line',
    'ap_payment',
    'txn_payment_allocation',
    'txn_bank_reconciliation',
    'ap_payment_file',
    'ap_payment_file_item',
    # GST tables
    'mst_hsn_sac',
    'mst_gst_rate',
    'mst_gst_registration',
    'mst_gstn_config',
    'txn_gstr1_filing',
    'txn_gstr3b_filing',
    # TDS tables
    'mst_tds_section',
    'txn_tds_entry',
    'txn_tds_challan',
    'txn_tds_return',
    # Workflow tables
    'wf_workflow_definition',
    'wf_workflow_step',
    'wf_approval_rule',
    'wf_escalation_rule',
    'wf_notification_template',
    'wf_workflow_instance',
    'wf_workflow_task',
    'wf_workflow_history',
    # Lending tables
    'ln_entity',
    'ln_entity_kyc',
    'ln_entity_address',
    'ln_entity_bank_account',
    'ln_entity_document',
    'ln_rating_model',
    'ln_rating_factor',
    'ln_entity_rating',
    'ln_product',
    'ln_product_fee',
    'ln_product_document_checklist',
    'ln_application',
    'ln_application_document',
    'ln_application_history',
    'ln_sanction',
    'ln_sanction_condition',
    'ln_loan_account',
    'ln_disbursement',
    'ln_repayment_schedule',
    'ln_loan_transaction',
    'ln_loan_charge',
    'ln_collection_case',
    'ln_collection_action',
    'ln_collection_promise',
    'ln_treasury_position',
    'ln_alm_bucket',
    'ln_alm_report',
    'ln_nach_mandate',
    'ln_nach_batch',
    'ln_nach_presentation',
    'ln_aa_consent',
    'ln_aa_data_fetch',
    'ln_credit_pull',
    # Fixed Assets tables
    'fa_asset_category',
    'fa_fixed_asset',
    'fa_depreciation_run',
    'fa_depreciation_entry',
    'fa_asset_transfer',
    'fa_asset_revaluation',
    'fa_physical_verification',
    'fa_physical_verification_item',
    'fa_lease',
    'fa_lease_payment',
    'fa_maintenance_schedule',
    'fa_maintenance_log',
    'fa_insurance_policy',
    # HRIS tables
    'hr_shift',
    'hr_employee',
    'hr_employee_document',
    'hr_leave_type',
    'hr_leave_balance',
    'hr_leave_request',
    'hr_attendance',
    # Payroll tables
    'py_salary_component',
    'py_salary_structure',
    'py_salary_structure_component',
    'py_employee_salary',
    'py_employee_salary_component',
    'py_payroll_run',
    'py_payslip',
    'py_payslip_component',
    # Compliance tables
    'cmp_compliance_category',
    'cmp_compliance_requirement',
    'cmp_compliance_task',
    'cmp_compliance_document',
    'cmp_regulatory_update',
    'cmp_compliance_calendar',
    # Fixed Deposits tables
    'fd_product',
    'fd_interest_slab',
    'fd_fixed_deposit',
    'fd_interest_accrual',
    'fd_transaction',
    'fd_nominee',
    # Common tables
    'audit_log',
    'txn_line_item_history',
    'mst_integration_config',
    'mst_approval_workflow',
    'mst_approval_step',
    'txn_approval_request',
    'txn_approval_action',
]


def upgrade() -> None:
    # Add version column to all tables that exist
    for table_name in TABLES_TO_UPDATE:
        # Use DO block to safely add column only if table exists and column doesn't
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table_name}') THEN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table_name}' AND column_name = 'version'
                    ) THEN
                        ALTER TABLE {table_name} ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                        COMMENT ON COLUMN {table_name}.version IS 'Record version for optimistic locking';
                    END IF;
                END IF;
            END $$;
        """)


def downgrade() -> None:
    # Remove version column from all tables that have it
    for table_name in TABLES_TO_UPDATE:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table_name}' AND column_name = 'version'
                ) THEN
                    ALTER TABLE {table_name} DROP COLUMN version;
                END IF;
            END $$;
        """)
