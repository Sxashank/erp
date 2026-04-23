"""Add Row-Level Security for multi-tenancy

Revision ID: z18_add_row_level_security
Revises: z17_add_version_columns
Create Date: 2026-01-15

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'z18_add_row_level_security'
down_revision: Union[str, None] = 'z17_add_version_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables with organization_id that need RLS policies
TENANT_TABLES = [
    # Finance tables
    ('mst_account', 'organization_id'),
    ('mst_account_group', 'organization_id'),
    ('mst_voucher_type', 'organization_id'),
    ('mst_financial_year', 'organization_id'),
    ('mst_financial_period', 'organization_id'),
    ('mst_cost_center', 'organization_id'),
    ('txn_voucher', 'organization_id'),
    ('txn_gl_entry', 'organization_id'),
    ('mst_recurring_voucher', 'organization_id'),
    ('mst_voucher_template', 'organization_id'),
    # AP/AR tables
    ('mst_payment_terms', 'organization_id'),
    ('mst_vendor', 'organization_id'),
    ('mst_customer', 'organization_id'),
    ('ap_purchase_bill', 'organization_id'),
    ('ar_sales_invoice', 'organization_id'),
    ('ap_payment', 'organization_id'),
    ('txn_bank_reconciliation', 'organization_id'),
    ('ap_payment_file', 'organization_id'),
    # GST tables
    ('mst_gst_registration', 'organization_id'),
    ('mst_gstn_config', 'organization_id'),
    ('txn_gstr1_filing', 'organization_id'),
    ('txn_gstr3b_filing', 'organization_id'),
    # TDS tables
    ('txn_tds_entry', 'organization_id'),
    ('txn_tds_challan', 'organization_id'),
    ('txn_tds_return', 'organization_id'),
    # Workflow tables
    ('wf_workflow_definition', 'organization_id'),
    ('wf_workflow_instance', 'organization_id'),
    # Lending tables
    ('ln_entity', 'organization_id'),
    ('ln_product', 'organization_id'),
    ('ln_application', 'organization_id'),
    ('ln_sanction', 'organization_id'),
    ('ln_loan_account', 'organization_id'),
    ('ln_collection_case', 'organization_id'),
    ('ln_treasury_position', 'organization_id'),
    ('ln_alm_report', 'organization_id'),
    ('ln_nach_mandate', 'organization_id'),
    ('ln_nach_batch', 'organization_id'),
    ('ln_aa_consent', 'organization_id'),
    ('ln_credit_pull', 'organization_id'),
    # Fixed Assets tables
    ('fa_asset_category', 'organization_id'),
    ('fa_fixed_asset', 'organization_id'),
    ('fa_depreciation_run', 'organization_id'),
    ('fa_physical_verification', 'organization_id'),
    # HRIS tables
    ('hr_shift', 'organization_id'),
    ('hr_employee', 'organization_id'),
    ('hr_leave_type', 'organization_id'),
    # Payroll tables
    ('py_salary_component', 'organization_id'),
    ('py_salary_structure', 'organization_id'),
    ('py_payroll_run', 'organization_id'),
    ('py_payslip', 'organization_id'),
    # Compliance tables
    ('cmp_compliance_category', 'organization_id'),
    ('cmp_compliance_requirement', 'organization_id'),
    ('cmp_compliance_task', 'organization_id'),
    ('cmp_regulatory_update', 'organization_id'),
    ('cmp_compliance_calendar', 'organization_id'),
    # Fixed Deposits tables
    ('fd_product', 'organization_id'),
    ('fd_fixed_deposit', 'organization_id'),
    # Organization tables (filter by own id)
    ('mst_unit', 'organization_id'),
    ('mst_department', 'organization_id'),
    ('mst_designation', 'organization_id'),
    ('mst_organization_address', 'organization_id'),
    ('mst_organization_bank_account', 'organization_id'),
    # Integration tables
    ('mst_integration_config', 'organization_id'),
    # Approval tables
    ('mst_approval_workflow', 'organization_id'),
    ('txn_approval_request', 'organization_id'),
]


def upgrade() -> None:
    # Enable RLS and create policies for each tenant table
    for table_name, org_column in TENANT_TABLES:
        # Use DO block to safely enable RLS only if table exists and has the column
        op.execute(f"""
            DO $$
            BEGIN
                -- Check if table exists and has the organization_id column
                IF EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table_name}' AND column_name = '{org_column}'
                ) THEN
                    -- Enable RLS on table
                    EXECUTE 'ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY';

                    -- Drop existing policy if exists (to make migration idempotent)
                    EXECUTE 'DROP POLICY IF EXISTS org_isolation_{table_name} ON {table_name}';

                    -- Create policy for organization isolation
                    EXECUTE 'CREATE POLICY org_isolation_{table_name} ON {table_name}
                        FOR ALL
                        USING (
                            {org_column}::text = current_setting(''app.current_org_id'', true)
                            OR current_setting(''app.current_org_id'', true) = ''''
                        )';
                END IF;
            END $$;
        """)

    # Note: The application user needs to NOT be the table owner for RLS to apply.
    # If the application connects as a superuser or table owner, RLS is bypassed.
    # For production, create a separate role for the application:
    #
    # CREATE ROLE app_user LOGIN PASSWORD 'secret';
    # GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
    # -- RLS will apply to app_user but not to the superuser/owner


def downgrade() -> None:
    # Disable RLS and drop policies
    for table_name, org_column in TENANT_TABLES:
        op.execute(f"""
            DO $$
            BEGIN
                -- Check if table exists
                IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table_name}') THEN
                    -- Drop the policy
                    EXECUTE 'DROP POLICY IF EXISTS org_isolation_{table_name} ON {table_name}';

                    -- Disable RLS
                    EXECUTE 'ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY';
                END IF;
            END $$;
        """)
