"""Add fixed assets tables.

Revision ID: z12_fixed_assets
Revises: z11_cost_center_fk
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z12_fixed_assets'
down_revision = 'z11_cost_center_fk'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create asset_type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE assettype AS ENUM ('TANGIBLE', 'INTANGIBLE', 'RIGHT_OF_USE');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create depreciation_method enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE depreciationmethod AS ENUM ('SLM', 'WDV', 'UNIT_OF_PRODUCTION', 'NO_DEPRECIATION');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create asset_acquisition_type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE assetacquisitiontype AS ENUM ('PURCHASE', 'LEASE', 'DONATION', 'TRANSFER_IN', 'CONSTRUCTED', 'GIFT');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create asset_status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE assetstatus AS ENUM ('DRAFT', 'ACTIVE', 'DISPOSED', 'TRANSFERRED', 'UNDER_MAINTENANCE', 'FULLY_DEPRECIATED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create asset_disposal_type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE assetdisposaltype AS ENUM ('SALE', 'SCRAP', 'WRITE_OFF', 'TRANSFER_OUT', 'DONATION', 'EXCHANGE');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create depreciation_type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE depreciationtype AS ENUM ('REGULAR', 'ADDITIONAL', 'REVERSAL', 'CATCH_UP');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create asset_transfer_status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE assettransferstatus AS ENUM ('PENDING', 'APPROVED', 'COMPLETED', 'REJECTED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create revaluation_type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE revaluationtype AS ENUM ('INCREASE', 'DECREASE', 'IMPAIRMENT');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Create mst_asset_category table
    op.create_table(
        'mst_asset_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_code', sa.String(20), nullable=False),
        sa.Column('category_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('asset_type', postgresql.ENUM('TANGIBLE', 'INTANGIBLE', 'RIGHT_OF_USE', name='assettype', create_type=False), nullable=False),
        sa.Column('depreciation_method', postgresql.ENUM('SLM', 'WDV', 'UNIT_OF_PRODUCTION', 'NO_DEPRECIATION', name='depreciationmethod', create_type=False), nullable=False),
        sa.Column('useful_life_years', sa.Integer(), nullable=False, default=5),
        sa.Column('residual_value_pct', sa.Numeric(5, 2), nullable=False, default=5.00),
        sa.Column('depreciation_rate_slm', sa.Numeric(5, 2), nullable=False, default=0.00),
        sa.Column('depreciation_rate_wdv', sa.Numeric(5, 2), nullable=False, default=0.00),
        sa.Column('it_act_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('it_act_block', sa.String(10), nullable=True),
        sa.Column('capitalization_threshold', sa.Numeric(18, 2), nullable=False, default=5000.00),
        sa.Column('gl_asset_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_accum_dep_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_dep_expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_disposal_gain_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_disposal_loss_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_revaluation_reserve_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_impairment_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requires_insurance', sa.Boolean(), nullable=False, default=False),
        sa.Column('requires_amc', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_category_id'], ['mst_asset_category.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_asset_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_accum_dep_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_dep_expense_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_disposal_gain_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gl_disposal_loss_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'category_code', name='uq_asset_category_org_code'),
    )
    op.create_index('ix_mst_asset_category_organization_id', 'mst_asset_category', ['organization_id'])
    op.create_index('ix_mst_asset_category_parent_category_id', 'mst_asset_category', ['parent_category_id'])

    # Create mst_fixed_asset table
    op.create_table(
        'mst_fixed_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_code', sa.String(30), nullable=False),
        sa.Column('asset_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('custodian_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acquisition_date', sa.Date(), nullable=False),
        sa.Column('put_to_use_date', sa.Date(), nullable=True),
        sa.Column('acquisition_type', postgresql.ENUM('PURCHASE', 'LEASE', 'DONATION', 'TRANSFER_IN', 'CONSTRUCTED', 'GIFT', name='assetacquisitiontype', create_type=False), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('po_number', sa.String(50), nullable=True),
        sa.Column('acquisition_cost', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('installation_cost', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('other_costs', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('total_cost', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('residual_value', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('depreciable_value', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('useful_life_months', sa.Integer(), nullable=False, default=60),
        sa.Column('depreciation_method', postgresql.ENUM('SLM', 'WDV', 'UNIT_OF_PRODUCTION', 'NO_DEPRECIATION', name='depreciationmethod', create_type=False), nullable=False),
        sa.Column('depreciation_rate', sa.Numeric(5, 2), nullable=False, default=0.00),
        sa.Column('accumulated_depreciation', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('wdv_value', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('last_depreciation_date', sa.Date(), nullable=True),
        sa.Column('depreciation_start_date', sa.Date(), nullable=True),
        sa.Column('revaluation_amount', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('impairment_amount', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('warranty_start_date', sa.Date(), nullable=True),
        sa.Column('warranty_expiry_date', sa.Date(), nullable=True),
        sa.Column('insurance_policy_number', sa.String(50), nullable=True),
        sa.Column('insurance_provider', sa.String(100), nullable=True),
        sa.Column('insurance_expiry_date', sa.Date(), nullable=True),
        sa.Column('insured_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('amc_vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amc_start_date', sa.Date(), nullable=True),
        sa.Column('amc_expiry_date', sa.Date(), nullable=True),
        sa.Column('amc_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('parent_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_component', sa.Boolean(), nullable=False, default=False),
        sa.Column('disposal_date', sa.Date(), nullable=True),
        sa.Column('disposal_type', postgresql.ENUM('SALE', 'SCRAP', 'WRITE_OFF', 'TRANSFER_OUT', 'DONATION', 'EXCHANGE', name='assetdisposaltype', create_type=False), nullable=True),
        sa.Column('disposal_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('disposal_gain_loss', sa.Numeric(18, 2), nullable=True),
        sa.Column('disposal_remarks', sa.Text(), nullable=True),
        sa.Column('disposal_voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('capitalization_voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'ACTIVE', 'DISPOSED', 'TRANSFERRED', 'UNDER_MAINTENANCE', 'FULLY_DEPRECIATED', name='assetstatus', create_type=False), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['mst_asset_category.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['location_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['mst_department.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['amc_vendor_id'], ['mst_vendor.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_asset_id'], ['mst_fixed_asset.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['disposal_voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['capitalization_voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'asset_code', name='uq_fixed_asset_org_code'),
    )
    op.create_index('ix_mst_fixed_asset_organization_id', 'mst_fixed_asset', ['organization_id'])
    op.create_index('ix_mst_fixed_asset_category_id', 'mst_fixed_asset', ['category_id'])
    op.create_index('ix_mst_fixed_asset_location_id', 'mst_fixed_asset', ['location_id'])
    op.create_index('ix_mst_fixed_asset_status', 'mst_fixed_asset', ['status'])
    op.create_index('ix_mst_fixed_asset_acquisition_date', 'mst_fixed_asset', ['acquisition_date'])

    # Create txn_depreciation_run table
    op.create_table(
        'txn_depreciation_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('depreciation_period', sa.String(7), nullable=False),
        sa.Column('period_from', sa.Date(), nullable=False),
        sa.Column('period_to', sa.Date(), nullable=False),
        sa.Column('total_assets', sa.Integer(), nullable=False, default=0),
        sa.Column('total_depreciation', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('processed_assets', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_assets', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('run_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['run_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['posted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'depreciation_period', name='uq_depreciation_run_org_period'),
    )
    op.create_index('ix_txn_depreciation_run_organization_id', 'txn_depreciation_run', ['organization_id'])
    op.create_index('ix_txn_depreciation_run_depreciation_period', 'txn_depreciation_run', ['depreciation_period'])

    # Create txn_depreciation table
    op.create_table(
        'txn_depreciation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('depreciation_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('depreciation_period', sa.String(7), nullable=False),
        sa.Column('period_from', sa.Date(), nullable=False),
        sa.Column('period_to', sa.Date(), nullable=False),
        sa.Column('days_in_period', sa.Integer(), nullable=False),
        sa.Column('opening_wdv', sa.Numeric(18, 2), nullable=False),
        sa.Column('depreciation_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('depreciation_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('accumulated_depreciation', sa.Numeric(18, 2), nullable=False),
        sa.Column('closing_wdv', sa.Numeric(18, 2), nullable=False),
        sa.Column('depreciation_type', postgresql.ENUM('REGULAR', 'ADDITIONAL', 'REVERSAL', 'CATCH_UP', name='depreciationtype', create_type=False), nullable=False),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_posted', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_reversed', sa.Boolean(), nullable=False, default=False),
        sa.Column('reversal_of_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reversed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depreciation_run_id'], ['txn_depreciation_run.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reversal_of_id'], ['txn_depreciation.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reversed_by_id'], ['txn_depreciation.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('asset_id', 'depreciation_period', 'depreciation_type', name='uq_depreciation_asset_period_type'),
    )
    op.create_index('ix_txn_depreciation_asset_id', 'txn_depreciation', ['asset_id'])
    op.create_index('ix_txn_depreciation_depreciation_run_id', 'txn_depreciation', ['depreciation_run_id'])
    op.create_index('ix_txn_depreciation_depreciation_period', 'txn_depreciation', ['depreciation_period'])

    # Create txn_asset_transfer table
    op.create_table(
        'txn_asset_transfer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transfer_date', sa.Date(), nullable=False),
        sa.Column('transfer_reference', sa.String(50), nullable=True),
        sa.Column('from_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_custodian_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_custodian_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'COMPLETED', 'REJECTED', name='assettransferstatus', create_type=False), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_location_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_location_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['from_department_id'], ['mst_department.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_department_id'], ['mst_department.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requested_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['completed_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_asset_transfer_asset_id', 'txn_asset_transfer', ['asset_id'])
    op.create_index('ix_txn_asset_transfer_transfer_date', 'txn_asset_transfer', ['transfer_date'])
    op.create_index('ix_txn_asset_transfer_status', 'txn_asset_transfer', ['status'])

    # Create txn_asset_revaluation table
    op.create_table(
        'txn_asset_revaluation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('revaluation_date', sa.Date(), nullable=False),
        sa.Column('revaluation_type', postgresql.ENUM('INCREASE', 'DECREASE', 'IMPAIRMENT', name='revaluationtype', create_type=False), nullable=False),
        sa.Column('previous_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('new_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('revaluation_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('previous_accumulated_depreciation', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('new_accumulated_depreciation', sa.Numeric(18, 2), nullable=False, default=0.00),
        sa.Column('valuer_name', sa.String(200), nullable=True),
        sa.Column('valuation_report_number', sa.String(100), nullable=True),
        sa.Column('valuation_report_date', sa.Date(), nullable=True),
        sa.Column('valuation_method', sa.String(100), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['mst_fixed_asset.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_txn_asset_revaluation_asset_id', 'txn_asset_revaluation', ['asset_id'])
    op.create_index('ix_txn_asset_revaluation_revaluation_date', 'txn_asset_revaluation', ['revaluation_date'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('txn_asset_revaluation')
    op.drop_table('txn_asset_transfer')
    op.drop_table('txn_depreciation')
    op.drop_table('txn_depreciation_run')
    op.drop_table('mst_fixed_asset')
    op.drop_table('mst_asset_category')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS revaluationtype')
    op.execute('DROP TYPE IF EXISTS assettransferstatus')
    op.execute('DROP TYPE IF EXISTS depreciationtype')
    op.execute('DROP TYPE IF EXISTS assetdisposaltype')
    op.execute('DROP TYPE IF EXISTS assetstatus')
    op.execute('DROP TYPE IF EXISTS assetacquisitiontype')
    op.execute('DROP TYPE IF EXISTS depreciationmethod')
    op.execute('DROP TYPE IF EXISTS assettype')
