"""Add payroll tables

Revision ID: z14_add_payroll_tables
Revises: z13_hris_tables
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z14_add_payroll_tables'
down_revision = 'z13_hris_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types with duplicate handling
    op.execute("DO $$ BEGIN CREATE TYPE componenttype AS ENUM ('EARNING', 'DEDUCTION'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE calculationtype AS ENUM ('FIXED', 'PERCENTAGE', 'FORMULA'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE componentcategory AS ENUM ('BASIC', 'ALLOWANCE', 'REIMBURSEMENT', 'BONUS', 'STATUTORY', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE payrollbatchstatus AS ENUM ('DRAFT', 'PROCESSING', 'PROCESSED', 'APPROVED', 'PAID', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE payslipstatus AS ENUM ('DRAFT', 'PROCESSED', 'APPROVED', 'PAID', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE employeesalarystatus AS ENUM ('ACTIVE', 'SUPERSEDED', 'DRAFT'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE statutorytype AS ENUM ('PF', 'ESI', 'PT', 'TDS', 'LWF', 'GRATUITY'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create salary_component table
    op.create_table(
        'payroll_salary_component',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('component_code', sa.String(20), nullable=False),
        sa.Column('component_name', sa.String(100), nullable=False),
        sa.Column('component_type', postgresql.ENUM('EARNING', 'DEDUCTION', name='componenttype', create_type=False), nullable=False),
        sa.Column('category', postgresql.ENUM('BASIC', 'ALLOWANCE', 'REIMBURSEMENT', 'BONUS', 'STATUTORY', 'OTHER', name='componentcategory', create_type=False), nullable=False, server_default='OTHER'),
        sa.Column('calculation_type', postgresql.ENUM('FIXED', 'PERCENTAGE', 'FORMULA', name='calculationtype', create_type=False), nullable=False, server_default='FIXED'),
        sa.Column('percentage_of', sa.String(20), nullable=True),
        sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True),
        sa.Column('formula', sa.Text, nullable=True),
        sa.Column('is_taxable', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_pro_rated', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('affects_pf', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('affects_esi', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('affects_pt', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'component_code', name='uq_salary_component_org_code'),
    )
    op.create_index('ix_salary_component_org', 'payroll_salary_component', ['organization_id'])

    # Create salary_structure table
    op.create_table(
        'payroll_salary_structure',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('structure_code', sa.String(20), nullable=False),
        sa.Column('structure_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('ctc_from', sa.Numeric(18, 2), nullable=True),
        sa.Column('ctc_to', sa.Numeric(18, 2), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'structure_code', name='uq_salary_structure_org_code'),
    )
    op.create_index('ix_salary_structure_org', 'payroll_salary_structure', ['organization_id'])

    # Create salary_structure_component table
    op.create_table(
        'payroll_salary_structure_component',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('structure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_salary_structure.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_salary_component.id'), nullable=False),
        sa.Column('calculation_type', postgresql.ENUM('FIXED', 'PERCENTAGE', 'FORMULA', name='calculationtype', create_type=False), nullable=False, server_default='FIXED'),
        sa.Column('default_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('percentage_of', sa.String(20), nullable=True),
        sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True),
        sa.Column('formula', sa.Text, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
    )
    op.create_index('ix_structure_component_structure', 'payroll_salary_structure_component', ['structure_id'])

    # Create employee_salary table
    op.create_table(
        'payroll_employee_salary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hris_employee.id'), nullable=False),
        sa.Column('structure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_salary_structure.id'), nullable=True),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('gross_salary', sa.Numeric(18, 2), nullable=False),
        sa.Column('net_salary', sa.Numeric(18, 2), nullable=False),
        sa.Column('ctc', sa.Numeric(18, 2), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'SUPERSEDED', 'DRAFT', name='employeesalarystatus', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('revision_number', sa.Integer, nullable=False, server_default='1'),
        sa.Column('previous_salary_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_employee_salary.id'), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
    )
    op.create_index('ix_employee_salary_employee', 'payroll_employee_salary', ['employee_id'])
    op.create_index('ix_employee_salary_status', 'payroll_employee_salary', ['status'])

    # Create employee_salary_component table
    op.create_table(
        'payroll_employee_salary_component',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_salary_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_employee_salary.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_salary_component.id'), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('calculation_type', postgresql.ENUM('FIXED', 'PERCENTAGE', 'FORMULA', name='calculationtype', create_type=False), nullable=False, server_default='FIXED'),
        sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
    )
    op.create_index('ix_emp_salary_component_salary', 'payroll_employee_salary_component', ['employee_salary_id'])

    # Create statutory_setup table
    op.create_table(
        'payroll_statutory_setup',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('statutory_type', postgresql.ENUM('PF', 'ESI', 'PT', 'TDS', 'LWF', 'GRATUITY', name='statutorytype', create_type=False), nullable=False),
        sa.Column('employer_contribution_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('employee_contribution_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('wage_ceiling', sa.Numeric(18, 2), nullable=True),
        sa.Column('admin_charges_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_applicable', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('config_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
    )
    op.create_index('ix_statutory_setup_org', 'payroll_statutory_setup', ['organization_id'])

    # Create payroll_batch table
    op.create_table(
        'payroll_batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('batch_reference', sa.String(50), nullable=False),
        sa.Column('payroll_month', sa.Integer, nullable=False),
        sa.Column('payroll_year', sa.Integer, nullable=False),
        sa.Column('pay_period_from', sa.Date, nullable=False),
        sa.Column('pay_period_to', sa.Date, nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PROCESSING', 'PROCESSED', 'APPROVED', 'PAID', 'CANCELLED', name='payrollbatchstatus', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('total_employees', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_gross', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_deductions', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_net', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_employer_contribution', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'payroll_month', 'payroll_year', name='uq_payroll_batch_org_month_year'),
    )
    op.create_index('ix_payroll_batch_org', 'payroll_batch', ['organization_id'])
    op.create_index('ix_payroll_batch_year_month', 'payroll_batch', ['payroll_year', 'payroll_month'])

    # Create payslip table
    op.create_table(
        'payroll_payslip',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_batch.id'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hris_employee.id'), nullable=False),
        sa.Column('employee_salary_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_employee_salary.id'), nullable=False),
        sa.Column('payroll_month', sa.Integer, nullable=False),
        sa.Column('payroll_year', sa.Integer, nullable=False),
        sa.Column('working_days', sa.Numeric(5, 2), nullable=False),
        sa.Column('paid_days', sa.Numeric(5, 2), nullable=False),
        sa.Column('lop_days', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('basic_salary', sa.Numeric(18, 2), nullable=False),
        sa.Column('gross_earnings', sa.Numeric(18, 2), nullable=False),
        sa.Column('total_deductions', sa.Numeric(18, 2), nullable=False),
        sa.Column('net_salary', sa.Numeric(18, 2), nullable=False),
        sa.Column('employer_pf', sa.Numeric(18, 2), nullable=True),
        sa.Column('employer_esi', sa.Numeric(18, 2), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PROCESSED', 'APPROVED', 'PAID', 'CANCELLED', name='payslipstatus', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('batch_id', 'employee_id', name='uq_payslip_batch_employee'),
    )
    op.create_index('ix_payslip_batch', 'payroll_payslip', ['batch_id'])
    op.create_index('ix_payslip_employee', 'payroll_payslip', ['employee_id'])

    # Create payslip_component table
    op.create_table(
        'payroll_payslip_component',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('payslip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_payslip.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_salary_component.id'), nullable=False),
        sa.Column('component_name', sa.String(100), nullable=False),
        sa.Column('component_type', postgresql.ENUM('EARNING', 'DEDUCTION', name='componenttype', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('is_arrear', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_payslip_component_payslip', 'payroll_payslip_component', ['payslip_id'])

    # Create payroll_statutory table (for statutory breakdown per payslip)
    op.create_table(
        'payroll_statutory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('payslip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_payslip.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statutory_type', postgresql.ENUM('PF', 'ESI', 'PT', 'TDS', 'LWF', 'GRATUITY', name='statutorytype', create_type=False), nullable=False),
        sa.Column('employee_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('employer_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('wage_base', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_payroll_statutory_payslip', 'payroll_statutory', ['payslip_id'])


def downgrade() -> None:
    op.drop_table('payroll_statutory')
    op.drop_table('payroll_payslip_component')
    op.drop_table('payroll_payslip')
    op.drop_table('payroll_batch')
    op.drop_table('payroll_statutory_setup')
    op.drop_table('payroll_employee_salary_component')
    op.drop_table('payroll_employee_salary')
    op.drop_table('payroll_salary_structure_component')
    op.drop_table('payroll_salary_structure')
    op.drop_table('payroll_salary_component')

    op.execute("DROP TYPE IF EXISTS statutorytype")
    op.execute("DROP TYPE IF EXISTS employeesalarystatus")
    op.execute("DROP TYPE IF EXISTS payslipstatus")
    op.execute("DROP TYPE IF EXISTS payrollbatchstatus")
    op.execute("DROP TYPE IF EXISTS componentcategory")
    op.execute("DROP TYPE IF EXISTS calculationtype")
    op.execute("DROP TYPE IF EXISTS componenttype")
