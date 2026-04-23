"""Add Fixed Assets Phase 3 and Phase 4 tables.

This migration adds:
- Physical Verification tables
- IT Act Block Summary
- Lease Accounting tables (Ind AS 116)
- AMC and Maintenance tables
- Insurance tables
- Approval Workflow tables
- FA Configuration table
- Audit context column

Revision ID: z19_fa_phase3_phase4
Revises: z18_add_row_level_security
Create Date: 2026-01-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z19_fa_phase3_phase4'
down_revision: Union[str, None] = 'z18_add_row_level_security'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================
    # Create ENUMs
    # =========================================

    # Physical Verification enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pvstatus AS ENUM ('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pventrystatus AS ENUM ('PENDING', 'VERIFIED', 'NOT_FOUND', 'DISCREPANCY');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE discrepancystatus AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'WRITTEN_OFF');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Lease enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE leasestatus AS ENUM ('DRAFT', 'ACTIVE', 'TERMINATED', 'EXPIRED', 'MODIFIED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE leasetype AS ENUM ('FINANCE', 'OPERATING', 'SHORT_TERM', 'LOW_VALUE');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentfrequency AS ENUM ('MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentschedulestatus AS ENUM ('SCHEDULED', 'PAID', 'PARTIAL', 'OVERDUE', 'WAIVED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE leasemodificationtype AS ENUM ('EXTENSION', 'TERMINATION', 'SCOPE_CHANGE', 'PAYMENT_CHANGE', 'RATE_CHANGE');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Maintenance enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE amcstatus AS ENUM ('DRAFT', 'ACTIVE', 'EXPIRED', 'CANCELLED', 'RENEWED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE amctype AS ENUM ('COMPREHENSIVE', 'NON_COMPREHENSIVE', 'WARRANTY_EXTENSION');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE maintenancestatus AS ENUM ('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE maintenancetype AS ENUM ('CORRECTIVE', 'PREVENTIVE', 'EMERGENCY', 'INSPECTION');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE maintenancepriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Insurance enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE insurancepolicystatus AS ENUM ('DRAFT', 'ACTIVE', 'EXPIRED', 'CANCELLED', 'CLAIMED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE insurancetype AS ENUM ('FIRE', 'THEFT', 'COMPREHENSIVE', 'MACHINERY_BREAKDOWN', 'ALL_RISK');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE claimstatus AS ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'SETTLED', 'WITHDRAWN');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Approval workflow enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approvalworkflowtype AS ENUM (
                'FA_ASSET_CREATION', 'FA_ASSET_CAPITALIZATION', 'FA_ASSET_DISPOSAL',
                'FA_ASSET_TRANSFER', 'FA_REVALUATION', 'FA_IMPAIRMENT',
                'FA_DEPRECIATION_RUN', 'FA_LEASE_ACTIVATION', 'FA_LEASE_TERMINATION',
                'FA_LEASE_MODIFICATION', 'FA_INSURANCE_CLAIM_SETTLEMENT'
            );
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approvalrequeststatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'RETURNED', 'CANCELLED', 'EXPIRED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approvalaction AS ENUM ('APPROVE', 'REJECT', 'RETURN', 'ESCALATE');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # =========================================
    # Physical Verification Tables
    # =========================================

    op.create_table(
        'txn_pv_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_reference', sa.String(50), nullable=False),
        sa.Column('schedule_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('planned_start_date', sa.Date(), nullable=False),
        sa.Column('planned_end_date', sa.Date(), nullable=False),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='pvstatus', create_type=False), nullable=False),
        sa.Column('total_assets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('verified_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discrepancy_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('not_found_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['mst_department.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['mst_asset_category.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'schedule_reference', name='uq_pv_schedule_org_ref'),
    )
    op.create_index('ix_txn_pv_schedule_organization_id', 'txn_pv_schedule', ['organization_id'])
    op.create_index('ix_txn_pv_schedule_status', 'txn_pv_schedule', ['status'])

    op.create_table(
        'txn_pv_entry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'VERIFIED', 'NOT_FOUND', 'DISCREPANCY', name='pventrystatus', create_type=False), nullable=False),
        sa.Column('verification_date', sa.Date(), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('physical_location', sa.String(200), nullable=True),
        sa.Column('physical_condition', sa.String(100), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),
        sa.Column('photo_urls', postgresql.JSONB(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['txn_pv_schedule.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('schedule_id', 'asset_id', name='uq_pv_entry_schedule_asset'),
    )
    op.create_index('ix_txn_pv_entry_schedule_id', 'txn_pv_entry', ['schedule_id'])
    op.create_index('ix_txn_pv_entry_asset_id', 'txn_pv_entry', ['asset_id'])
    op.create_index('ix_txn_pv_entry_status', 'txn_pv_entry', ['status'])

    op.create_table(
        'txn_pv_discrepancy',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('discrepancy_type', sa.String(50), nullable=False),
        sa.Column('expected_value', sa.Text(), nullable=True),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('variance_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('status', postgresql.ENUM('OPEN', 'INVESTIGATING', 'RESOLVED', 'WRITTEN_OFF', name='discrepancystatus', create_type=False), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entry_id'], ['txn_pv_entry.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_pv_discrepancy_entry_id', 'txn_pv_discrepancy', ['entry_id'])
    op.create_index('ix_txn_pv_discrepancy_status', 'txn_pv_discrepancy', ['status'])

    # =========================================
    # IT Act Block Summary Table
    # =========================================

    op.create_table(
        'txn_it_block_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('financial_year', sa.String(9), nullable=False),
        sa.Column('block_type', sa.String(20), nullable=False),
        sa.Column('opening_wdv', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('additions', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('disposals', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('depreciation_base', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('depreciation_rate', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('depreciation_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('additional_depreciation', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_depreciation', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('closing_wdv', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('asset_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'financial_year', 'block_type', name='uq_it_block_org_fy_block'),
    )
    op.create_index('ix_txn_it_block_summary_organization_id', 'txn_it_block_summary', ['organization_id'])
    op.create_index('ix_txn_it_block_summary_financial_year', 'txn_it_block_summary', ['financial_year'])

    # =========================================
    # Lease Accounting Tables (Ind AS 116)
    # =========================================

    op.create_table(
        'txn_lease',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lease_number', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lessor_name', sa.String(200), nullable=False),
        sa.Column('lessor_address', sa.Text(), nullable=True),
        sa.Column('lease_type', postgresql.ENUM('FINANCE', 'OPERATING', 'SHORT_TERM', 'LOW_VALUE', name='leasetype', create_type=False), nullable=False),
        sa.Column('commencement_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('lease_term_months', sa.Integer(), nullable=False),
        sa.Column('payment_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL', name='paymentfrequency', create_type=False), nullable=False),
        sa.Column('payment_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_day_of_month', sa.Integer(), nullable=True),
        sa.Column('incremental_borrowing_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('implicit_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('lease_liability_initial', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('lease_liability_current', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('roua_initial_value', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('roua_current_value', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('roua_accumulated_depreciation', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('initial_direct_costs', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('restoration_costs', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('prepaid_lease_payments', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_interest_expense', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_payments_made', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('next_payment_date', sa.Date(), nullable=True),
        sa.Column('last_payment_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'ACTIVE', 'TERMINATED', 'EXPIRED', 'MODIFIED', name='leasestatus', create_type=False), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('termination_reason', sa.Text(), nullable=True),
        sa.Column('gl_roua_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_liability_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_interest_expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_depreciation_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_roua_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_liability_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_interest_expense_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_depreciation_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'lease_number', name='uq_lease_org_number'),
    )
    op.create_index('ix_txn_lease_organization_id', 'txn_lease', ['organization_id'])
    op.create_index('ix_txn_lease_asset_id', 'txn_lease', ['asset_id'])
    op.create_index('ix_txn_lease_status', 'txn_lease', ['status'])

    op.create_table(
        'txn_lease_payment_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lease_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('payment_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('principal_component', sa.Numeric(18, 2), nullable=False),
        sa.Column('interest_component', sa.Numeric(18, 2), nullable=False),
        sa.Column('opening_liability', sa.Numeric(18, 2), nullable=False),
        sa.Column('closing_liability', sa.Numeric(18, 2), nullable=False),
        sa.Column('status', postgresql.ENUM('SCHEDULED', 'PAID', 'PARTIAL', 'OVERDUE', 'WAIVED', name='paymentschedulestatus', create_type=False), nullable=False),
        sa.Column('paid_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('payment_reference', sa.String(100), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('interest_posted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('interest_voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lease_id'], ['txn_lease.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['interest_voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('lease_id', 'period_number', name='uq_lease_payment_period'),
    )
    op.create_index('ix_txn_lease_payment_schedule_lease_id', 'txn_lease_payment_schedule', ['lease_id'])
    op.create_index('ix_txn_lease_payment_schedule_due_date', 'txn_lease_payment_schedule', ['due_date'])
    op.create_index('ix_txn_lease_payment_schedule_status', 'txn_lease_payment_schedule', ['status'])

    op.create_table(
        'txn_lease_modification',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lease_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('modification_date', sa.Date(), nullable=False),
        sa.Column('modification_type', postgresql.ENUM('EXTENSION', 'TERMINATION', 'SCOPE_CHANGE', 'PAYMENT_CHANGE', 'RATE_CHANGE', name='leasemodificationtype', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_end_date', sa.Date(), nullable=True),
        sa.Column('new_end_date', sa.Date(), nullable=True),
        sa.Column('old_payment_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('new_payment_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('old_discount_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('new_discount_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('liability_adjustment', sa.Numeric(18, 2), nullable=True),
        sa.Column('roua_adjustment', sa.Numeric(18, 2), nullable=True),
        sa.Column('gain_loss', sa.Numeric(18, 2), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lease_id'], ['txn_lease.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_lease_modification_lease_id', 'txn_lease_modification', ['lease_id'])

    # =========================================
    # Maintenance and AMC Tables
    # =========================================

    op.create_table(
        'txn_amc_contract',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contract_number', sa.String(50), nullable=False),
        sa.Column('contract_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amc_type', postgresql.ENUM('COMPREHENSIVE', 'NON_COMPREHENSIVE', 'WARRANTY_EXTENSION', name='amctype', create_type=False), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('contract_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL', name='paymentfrequency', create_type=False), nullable=False),
        sa.Column('payment_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_paid', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('next_payment_date', sa.Date(), nullable=True),
        sa.Column('coverage_details', sa.Text(), nullable=True),
        sa.Column('exclusions', sa.Text(), nullable=True),
        sa.Column('response_time_hours', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'ACTIVE', 'EXPIRED', 'CANCELLED', 'RENEWED', name='amcstatus', create_type=False), nullable=False),
        sa.Column('renewed_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['renewed_from_id'], ['txn_amc_contract.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'contract_number', name='uq_amc_org_contract_number'),
    )
    op.create_index('ix_txn_amc_contract_organization_id', 'txn_amc_contract', ['organization_id'])
    op.create_index('ix_txn_amc_contract_vendor_id', 'txn_amc_contract', ['vendor_id'])
    op.create_index('ix_txn_amc_contract_status', 'txn_amc_contract', ['status'])

    # AMC-Asset linking table
    op.create_table(
        'txn_amc_contract_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contract_id'], ['txn_amc_contract.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('contract_id', 'asset_id', name='uq_amc_contract_asset'),
    )

    op.create_table(
        'txn_maintenance_request',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_number', sa.String(50), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amc_contract_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('maintenance_type', postgresql.ENUM('CORRECTIVE', 'PREVENTIVE', 'EMERGENCY', 'INSPECTION', name='maintenancetype', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='maintenancepriority', create_type=False), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reported_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reported_date', sa.Date(), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='maintenancestatus', create_type=False), nullable=False),
        sa.Column('labor_cost', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('parts_cost', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('other_cost', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_cost', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('downtime_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('work_performed', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['amc_contract_id'], ['txn_amc_contract.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reported_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_vendor_id'], ['mst_vendor.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'request_number', name='uq_maintenance_org_request_number'),
    )
    op.create_index('ix_txn_maintenance_request_organization_id', 'txn_maintenance_request', ['organization_id'])
    op.create_index('ix_txn_maintenance_request_asset_id', 'txn_maintenance_request', ['asset_id'])
    op.create_index('ix_txn_maintenance_request_status', 'txn_maintenance_request', ['status'])

    op.create_table(
        'txn_asset_warranty',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warranty_type', sa.String(50), nullable=False),
        sa.Column('provider_name', sa.String(200), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('coverage_details', sa.Text(), nullable=True),
        sa.Column('warranty_number', sa.String(100), nullable=True),
        sa.Column('contact_info', sa.Text(), nullable=True),
        sa.Column('is_extended', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extended_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['extended_from_id'], ['txn_asset_warranty.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_asset_warranty_asset_id', 'txn_asset_warranty', ['asset_id'])

    # =========================================
    # Insurance Tables
    # =========================================

    op.create_table(
        'txn_insurance_policy',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_number', sa.String(50), nullable=False),
        sa.Column('policy_name', sa.String(200), nullable=True),
        sa.Column('insurance_type', postgresql.ENUM('FIRE', 'THEFT', 'COMPREHENSIVE', 'MACHINERY_BREAKDOWN', 'ALL_RISK', name='insurancetype', create_type=False), nullable=False),
        sa.Column('insurer_name', sa.String(200), nullable=False),
        sa.Column('insurer_address', sa.Text(), nullable=True),
        sa.Column('broker_name', sa.String(200), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('sum_insured', sa.Numeric(18, 2), nullable=False),
        sa.Column('base_premium', sa.Numeric(18, 2), nullable=False),
        sa.Column('gst_rate', sa.Numeric(5, 2), nullable=False, server_default='18.00'),
        sa.Column('gst_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('stamp_duty', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_premium', sa.Numeric(18, 2), nullable=False),
        sa.Column('premium_paid', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('deductible_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('deductible_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('coverage_details', sa.Text(), nullable=True),
        sa.Column('exclusions', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'ACTIVE', 'EXPIRED', 'CANCELLED', 'CLAIMED', name='insurancepolicystatus', create_type=False), nullable=False),
        sa.Column('renewed_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['renewed_from_id'], ['txn_insurance_policy.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'policy_number', name='uq_insurance_org_policy_number'),
    )
    op.create_index('ix_txn_insurance_policy_organization_id', 'txn_insurance_policy', ['organization_id'])
    op.create_index('ix_txn_insurance_policy_status', 'txn_insurance_policy', ['status'])

    # Insurance-Asset linking table
    op.create_table(
        'txn_insurance_policy_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insured_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_id'], ['txn_insurance_policy.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('policy_id', 'asset_id', name='uq_insurance_policy_asset'),
    )

    op.create_table(
        'txn_insurance_claim',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('claim_number', sa.String(50), nullable=False),
        sa.Column('incident_date', sa.Date(), nullable=False),
        sa.Column('incident_description', sa.Text(), nullable=False),
        sa.Column('claim_date', sa.Date(), nullable=False),
        sa.Column('claim_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('approved_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('deductible_applied', sa.Numeric(18, 2), nullable=True),
        sa.Column('settlement_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('settlement_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'SETTLED', 'WITHDRAWN', name='claimstatus', create_type=False), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('supporting_documents', postgresql.JSONB(), nullable=True),
        sa.Column('surveyor_name', sa.String(200), nullable=True),
        sa.Column('surveyor_report_date', sa.Date(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['txn_insurance_policy.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'claim_number', name='uq_insurance_org_claim_number'),
    )
    op.create_index('ix_txn_insurance_claim_organization_id', 'txn_insurance_claim', ['organization_id'])
    op.create_index('ix_txn_insurance_claim_policy_id', 'txn_insurance_claim', ['policy_id'])
    op.create_index('ix_txn_insurance_claim_status', 'txn_insurance_claim', ['status'])

    # =========================================
    # Approval Workflow Tables
    # =========================================

    op.create_table(
        'mst_approval_workflow',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', postgresql.ENUM(
            'FA_ASSET_CREATION', 'FA_ASSET_CAPITALIZATION', 'FA_ASSET_DISPOSAL',
            'FA_ASSET_TRANSFER', 'FA_REVALUATION', 'FA_IMPAIRMENT',
            'FA_DEPRECIATION_RUN', 'FA_LEASE_ACTIVATION', 'FA_LEASE_TERMINATION',
            'FA_LEASE_MODIFICATION', 'FA_INSURANCE_CLAIM_SETTLEMENT',
            name='approvalworkflowtype', create_type=False), nullable=False),
        sa.Column('workflow_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('threshold_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('threshold_operator', sa.String(10), nullable=True),
        sa.Column('approval_levels', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('auto_approve_below_threshold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('send_email_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('escalation_hours', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'workflow_type', name='uq_approval_workflow_org_type'),
    )
    op.create_index('ix_mst_approval_workflow_organization_id', 'mst_approval_workflow', ['organization_id'])
    op.create_index('ix_mst_approval_workflow_workflow_type', 'mst_approval_workflow', ['workflow_type'])

    op.create_table(
        'mst_approval_workflow_level',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('approver_type', sa.String(20), nullable=False),
        sa.Column('approver_role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approver_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('can_skip', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['mst_approval_workflow.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_role_id'], ['mst_role.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approver_user_id'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('workflow_id', 'level', name='uq_workflow_level'),
    )
    op.create_index('ix_mst_approval_workflow_level_workflow_id', 'mst_approval_workflow_level', ['workflow_id'])

    op.create_table(
        'txn_approval_request',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_number', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_reference', sa.String(100), nullable=True),
        sa.Column('entity_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('current_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_levels', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'RETURNED', 'CANCELLED', 'EXPIRED', name='approvalrequeststatus', create_type=False), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('final_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('final_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('approval_chain', postgresql.JSONB(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['mst_approval_workflow.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['requested_by'], ['mst_user.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['final_approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'request_number', name='uq_approval_org_request_number'),
    )
    op.create_index('ix_txn_approval_request_organization_id', 'txn_approval_request', ['organization_id'])
    op.create_index('ix_txn_approval_request_workflow_id', 'txn_approval_request', ['workflow_id'])
    op.create_index('ix_txn_approval_request_entity', 'txn_approval_request', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_approval_request_status', 'txn_approval_request', ['status'])

    op.create_table(
        'txn_approval_request_action',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('action', postgresql.ENUM('APPROVE', 'REJECT', 'RETURN', 'ESCALATE', name='approvalaction', create_type=False), nullable=False),
        sa.Column('action_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['request_id'], ['txn_approval_request.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_by'], ['mst_user.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_approval_request_action_request_id', 'txn_approval_request_action', ['request_id'])

    # =========================================
    # FA Configuration Table
    # =========================================

    op.create_table(
        'mst_fa_configuration',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        # Asset Code Format
        sa.Column('asset_code_prefix', sa.String(10), nullable=False, server_default='FA'),
        sa.Column('asset_code_format', sa.String(100), nullable=False, server_default='{prefix}/{category}/{year}/{sequence:05d}'),
        sa.Column('asset_code_separator', sa.String(1), nullable=False, server_default='/'),
        sa.Column('auto_generate_code', sa.Boolean(), nullable=False, server_default='true'),
        # Financial Year
        sa.Column('fy_start_month', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('fy_start_day', sa.Integer(), nullable=False, server_default='1'),
        # Approval Thresholds
        sa.Column('creation_approval_threshold', sa.Numeric(18, 2), nullable=False, server_default='1000000.00'),
        sa.Column('disposal_approval_threshold', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('revaluation_approval_threshold', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('transfer_requires_approval', sa.Boolean(), nullable=False, server_default='true'),
        # Depreciation
        sa.Column('days_in_year', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('pro_rata_method', sa.String(20), nullable=False, server_default='DAILY'),
        sa.Column('min_asset_value_for_depreciation', sa.Numeric(18, 2), nullable=False, server_default='5000.00'),
        sa.Column('depreciation_posting_auto_approve', sa.Boolean(), nullable=False, server_default='false'),
        # Alerts
        sa.Column('amc_expiry_reminder_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('insurance_expiry_reminder_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('warranty_expiry_reminder_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('lease_expiry_reminder_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('lease_payment_reminder_days', sa.Integer(), nullable=False, server_default='7'),
        # Physical Verification
        sa.Column('pv_frequency_months', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('pv_tolerance_percentage', sa.Numeric(5, 2), nullable=False, server_default='5.00'),
        # GL Integration
        sa.Column('auto_post_capitalization', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_post_disposal', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_post_depreciation', sa.Boolean(), nullable=False, server_default='true'),
        # Pagination
        sa.Column('default_page_size', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('max_page_size', sa.Integer(), nullable=False, server_default='200'),
        # Custom
        sa.Column('custom_settings', postgresql.JSONB(), nullable=True),
        sa.Column('notification_emails', postgresql.JSONB(), nullable=True),
        # Audit columns
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', name='uq_fa_config_org'),
    )
    op.create_index('ix_mst_fa_configuration_organization_id', 'mst_fa_configuration', ['organization_id'])

    # =========================================
    # Background Job Table
    # =========================================

    # Job ENUMs
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_status_enum AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_type_enum AS ENUM (
                'BULK_ASSET_IMPORT', 'BULK_ASSET_UPDATE', 'BULK_ASSET_TRANSFER',
                'BULK_ASSET_DISPOSE', 'ASSET_EXPORT', 'DEPRECIATION_RUN',
                'REPORT_GENERATION', 'DATA_MIGRATION', 'BATCH_GL_POSTING'
            );
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.create_table(
        'txn_background_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Job identification
        sa.Column('job_type', postgresql.ENUM('BULK_ASSET_IMPORT', 'BULK_ASSET_UPDATE', 'BULK_ASSET_TRANSFER',
                  'BULK_ASSET_DISPOSE', 'ASSET_EXPORT', 'DEPRECIATION_RUN', 'REPORT_GENERATION',
                  'DATA_MIGRATION', 'BATCH_GL_POSTING', name='job_type_enum', create_type=False), nullable=False),
        sa.Column('job_name', sa.String(200), nullable=False),
        sa.Column('job_description', sa.Text(), nullable=True),
        # Status tracking
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED',
                  name='job_status_enum', create_type=False), nullable=False, server_default='PENDING'),
        # Progress tracking
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        # Input/Output data
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        # Result file
        sa.Column('result_file_path', sa.String(500), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_background_job_org_status', 'txn_background_job', ['organization_id', 'status'])
    op.create_index('ix_background_job_org_type', 'txn_background_job', ['organization_id', 'job_type'])
    op.create_index('ix_background_job_created', 'txn_background_job', ['created_at'])

    # =========================================
    # Add IT Act fields to fixed asset
    # =========================================

    op.add_column('mst_fixed_asset', sa.Column('it_act_block', sa.String(20), nullable=True))
    op.add_column('mst_fixed_asset', sa.Column('it_act_rate', sa.Numeric(5, 2), nullable=True))
    op.add_column('mst_fixed_asset', sa.Column('it_accumulated_depreciation', sa.Numeric(18, 2), nullable=False, server_default='0.00'))
    op.add_column('mst_fixed_asset', sa.Column('it_wdv_value', sa.Numeric(18, 2), nullable=False, server_default='0.00'))
    op.add_column('mst_fixed_asset', sa.Column('it_last_depreciation_date', sa.Date(), nullable=True))
    op.add_column('mst_fixed_asset', sa.Column('it_last_depreciation_fy', sa.String(9), nullable=True))
    op.add_column('mst_fixed_asset', sa.Column('is_additional_depreciation_eligible', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('mst_fixed_asset', sa.Column('additional_depreciation_claimed', sa.Numeric(18, 2), nullable=False, server_default='0.00'))
    op.add_column('mst_fixed_asset', sa.Column('is_fully_depreciated', sa.Boolean(), nullable=False, server_default='false'))

    # =========================================
    # Add audit_context to audit log
    # =========================================

    op.add_column('txn_audit_log', sa.Column('audit_context', postgresql.JSONB(), nullable=True,
                  comment='Additional context: financial impact, GL entries, approval chain, etc.'))


def downgrade() -> None:
    # Drop audit_context column
    op.drop_column('txn_audit_log', 'audit_context')

    # Drop IT Act columns from fixed asset
    op.drop_column('mst_fixed_asset', 'is_fully_depreciated')
    op.drop_column('mst_fixed_asset', 'additional_depreciation_claimed')
    op.drop_column('mst_fixed_asset', 'is_additional_depreciation_eligible')
    op.drop_column('mst_fixed_asset', 'it_last_depreciation_fy')
    op.drop_column('mst_fixed_asset', 'it_last_depreciation_date')
    op.drop_column('mst_fixed_asset', 'it_wdv_value')
    op.drop_column('mst_fixed_asset', 'it_accumulated_depreciation')
    op.drop_column('mst_fixed_asset', 'it_act_rate')
    op.drop_column('mst_fixed_asset', 'it_act_block')

    # Drop tables in reverse order
    op.drop_table('txn_background_job')
    op.drop_table('mst_fa_configuration')
    op.drop_table('txn_approval_request_action')
    op.drop_table('txn_approval_request')
    op.drop_table('mst_approval_workflow_level')
    op.drop_table('mst_approval_workflow')
    op.drop_table('txn_insurance_claim')
    op.drop_table('txn_insurance_policy_asset')
    op.drop_table('txn_insurance_policy')
    op.drop_table('txn_asset_warranty')
    op.drop_table('txn_maintenance_request')
    op.drop_table('txn_amc_contract_asset')
    op.drop_table('txn_amc_contract')
    op.drop_table('txn_lease_modification')
    op.drop_table('txn_lease_payment_schedule')
    op.drop_table('txn_lease')
    op.drop_table('txn_it_block_summary')
    op.drop_table('txn_pv_discrepancy')
    op.drop_table('txn_pv_entry')
    op.drop_table('txn_pv_schedule')

    # Drop ENUMs
    op.execute('DROP TYPE IF EXISTS job_type_enum')
    op.execute('DROP TYPE IF EXISTS job_status_enum')
    op.execute('DROP TYPE IF EXISTS approvalaction')
    op.execute('DROP TYPE IF EXISTS approvalrequeststatus')
    op.execute('DROP TYPE IF EXISTS approvalworkflowtype')
    op.execute('DROP TYPE IF EXISTS claimstatus')
    op.execute('DROP TYPE IF EXISTS insurancetype')
    op.execute('DROP TYPE IF EXISTS insurancepolicystatus')
    op.execute('DROP TYPE IF EXISTS maintenancepriority')
    op.execute('DROP TYPE IF EXISTS maintenancetype')
    op.execute('DROP TYPE IF EXISTS maintenancestatus')
    op.execute('DROP TYPE IF EXISTS amctype')
    op.execute('DROP TYPE IF EXISTS amcstatus')
    op.execute('DROP TYPE IF EXISTS leasemodificationtype')
    op.execute('DROP TYPE IF EXISTS paymentschedulestatus')
    op.execute('DROP TYPE IF EXISTS paymentfrequency')
    op.execute('DROP TYPE IF EXISTS leasetype')
    op.execute('DROP TYPE IF EXISTS leasestatus')
    op.execute('DROP TYPE IF EXISTS discrepancystatus')
    op.execute('DROP TYPE IF EXISTS pventrystatus')
    op.execute('DROP TYPE IF EXISTS pvstatus')
