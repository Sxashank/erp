"""Add Treasury enhancement tables for investments and risk management.

Revision ID: z29_treasury_enhancement
Revises: z28_hr_enhancement
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z29_treasury_enhancement'
down_revision: Union[str, None] = 'z28_hr_enhancement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create investment_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE investment_type AS ENUM (
                'fixed_deposit', 'mutual_fund', 'bond', 'debenture', 'commercial_paper',
                'treasury_bill', 'government_security', 'equity', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create investment_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE investment_status AS ENUM (
                'active', 'matured', 'redeemed', 'renewed', 'cancelled', 'defaulted'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create risk_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_type AS ENUM (
                'market', 'credit', 'liquidity', 'operational', 'interest_rate', 'currency'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create mst_investment_category table
    op.create_table(
        'mst_investment_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('investment_type', sa.String(30), nullable=False),
        sa.Column('rbi_classification', sa.String(100), nullable=True),
        sa.Column('slr_applicable', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('htc_eligible', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('htcs_eligible', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('fvtpl_eligible', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('risk_weight_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('provisioning_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_investment_category_org', 'mst_investment_category', ['organization_id'])
    op.create_index('ix_mst_investment_category_code', 'mst_investment_category', ['organization_id', 'code'], unique=True)

    # Create txn_investment table
    op.create_table(
        'txn_investment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('investment_number', sa.String(50), nullable=False),
        sa.Column('investment_name', sa.String(255), nullable=False),
        sa.Column('investment_type', sa.String(30), nullable=False),
        sa.Column('issuer_name', sa.String(255), nullable=True),
        sa.Column('isin_code', sa.String(20), nullable=True),
        sa.Column('scrip_code', sa.String(20), nullable=True),
        sa.Column('counterparty_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purchase_date', sa.Date, nullable=False),
        sa.Column('maturity_date', sa.Date, nullable=True),
        sa.Column('face_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('purchase_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('units', sa.Numeric(18, 6), nullable=True),
        sa.Column('coupon_rate', sa.Numeric(6, 4), nullable=True),
        sa.Column('yield_rate', sa.Numeric(6, 4), nullable=True),
        sa.Column('interest_frequency', sa.String(20), nullable=True),
        sa.Column('last_interest_date', sa.Date, nullable=True),
        sa.Column('next_interest_date', sa.Date, nullable=True),
        sa.Column('accrued_interest', sa.Numeric(18, 4), nullable=True),
        sa.Column('current_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('market_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('unrealized_gain_loss', sa.Numeric(18, 4), nullable=True),
        sa.Column('valuation_date', sa.Date, nullable=True),
        sa.Column('classification', sa.String(20), nullable=True),
        sa.Column('credit_rating', sa.String(20), nullable=True),
        sa.Column('rating_agency', sa.String(50), nullable=True),
        sa.Column('rating_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('maturity_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('maturity_proceeds', sa.Numeric(18, 4), nullable=True),
        sa.Column('redemption_date', sa.Date, nullable=True),
        sa.Column('redemption_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('realized_gain_loss', sa.Numeric(18, 4), nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['mst_investment_category.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_investment_org', 'txn_investment', ['organization_id'])
    op.create_index('ix_txn_investment_number', 'txn_investment', ['investment_number'], unique=True)
    op.create_index('ix_txn_investment_type', 'txn_investment', ['investment_type'])
    op.create_index('ix_txn_investment_status', 'txn_investment', ['status'])
    op.create_index('ix_txn_investment_maturity', 'txn_investment', ['maturity_date'])

    # Create txn_investment_transaction table
    op.create_table(
        'txn_investment_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.String(30), nullable=False),
        sa.Column('transaction_date', sa.Date, nullable=False),
        sa.Column('units', sa.Numeric(18, 6), nullable=True),
        sa.Column('price_per_unit', sa.Numeric(18, 6), nullable=True),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('charges', sa.Numeric(12, 4), nullable=True),
        sa.Column('tax', sa.Numeric(12, 4), nullable=True),
        sa.Column('net_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['investment_id'], ['txn_investment.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_investment_transaction_investment', 'txn_investment_transaction', ['investment_id'])
    op.create_index('ix_txn_investment_transaction_type', 'txn_investment_transaction', ['transaction_type'])
    op.create_index('ix_txn_investment_transaction_date', 'txn_investment_transaction', ['transaction_date'])

    # Create txn_risk_position table
    op.create_table(
        'txn_risk_position',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_date', sa.Date, nullable=False),
        sa.Column('risk_type', sa.String(30), nullable=False),
        sa.Column('asset_class', sa.String(50), nullable=True),
        sa.Column('portfolio_type', sa.String(50), nullable=True),
        sa.Column('exposure_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('risk_weighted_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('var_1day_95', sa.Numeric(18, 4), nullable=True),
        sa.Column('var_1day_99', sa.Numeric(18, 4), nullable=True),
        sa.Column('var_10day_99', sa.Numeric(18, 4), nullable=True),
        sa.Column('expected_shortfall', sa.Numeric(18, 4), nullable=True),
        sa.Column('stress_loss', sa.Numeric(18, 4), nullable=True),
        sa.Column('limit_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('utilization_percent', sa.Numeric(6, 2), nullable=True),
        sa.Column('breach_flag', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_risk_position_org', 'txn_risk_position', ['organization_id'])
    op.create_index('ix_txn_risk_position_date', 'txn_risk_position', ['position_date'])
    op.create_index('ix_txn_risk_position_type', 'txn_risk_position', ['risk_type'])

    # Create txn_var_calculation table
    op.create_table(
        'txn_var_calculation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calculation_date', sa.Date, nullable=False),
        sa.Column('calculation_method', sa.String(50), nullable=False),
        sa.Column('confidence_level', sa.Numeric(5, 2), nullable=False),
        sa.Column('holding_period_days', sa.Integer, nullable=False, server_default='1'),
        sa.Column('lookback_days', sa.Integer, nullable=True),
        sa.Column('portfolio_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('var_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('var_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('expected_shortfall', sa.Numeric(18, 4), nullable=True),
        sa.Column('component_var', postgresql.JSONB, nullable=True),
        sa.Column('marginal_var', postgresql.JSONB, nullable=True),
        sa.Column('backtesting_result', sa.Boolean, nullable=True),
        sa.Column('backtesting_exceptions', sa.Integer, nullable=True),
        sa.Column('model_parameters', postgresql.JSONB, nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_var_calculation_org', 'txn_var_calculation', ['organization_id'])
    op.create_index('ix_txn_var_calculation_date', 'txn_var_calculation', ['calculation_date'])

    # Create txn_stress_test table
    op.create_table(
        'txn_stress_test',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_date', sa.Date, nullable=False),
        sa.Column('scenario_name', sa.String(255), nullable=False),
        sa.Column('scenario_type', sa.String(50), nullable=False),
        sa.Column('scenario_description', sa.Text, nullable=True),
        sa.Column('base_portfolio_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('stressed_portfolio_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('impact_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('impact_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('interest_rate_shock', sa.Numeric(6, 4), nullable=True),
        sa.Column('credit_spread_shock', sa.Numeric(6, 4), nullable=True),
        sa.Column('fx_rate_shock', sa.Numeric(8, 4), nullable=True),
        sa.Column('equity_shock', sa.Numeric(8, 4), nullable=True),
        sa.Column('scenario_parameters', postgresql.JSONB, nullable=True),
        sa.Column('component_impact', postgresql.JSONB, nullable=True),
        sa.Column('capital_impact', sa.Numeric(18, 4), nullable=True),
        sa.Column('liquidity_impact', sa.Numeric(18, 4), nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_stress_test_org', 'txn_stress_test', ['organization_id'])
    op.create_index('ix_txn_stress_test_date', 'txn_stress_test', ['test_date'])
    op.create_index('ix_txn_stress_test_scenario', 'txn_stress_test', ['scenario_type'])

    # Create txn_gap_analysis table
    op.create_table(
        'txn_gap_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_date', sa.Date, nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('time_bucket', sa.String(50), nullable=False),
        sa.Column('bucket_start_days', sa.Integer, nullable=False),
        sa.Column('bucket_end_days', sa.Integer, nullable=False),
        sa.Column('rate_sensitive_assets', sa.Numeric(18, 4), nullable=True),
        sa.Column('rate_sensitive_liabilities', sa.Numeric(18, 4), nullable=True),
        sa.Column('gap_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('cumulative_gap', sa.Numeric(18, 4), nullable=True),
        sa.Column('gap_ratio', sa.Numeric(8, 4), nullable=True),
        sa.Column('weighted_gap', sa.Numeric(18, 4), nullable=True),
        sa.Column('nii_impact_100bps', sa.Numeric(18, 4), nullable=True),
        sa.Column('eve_impact_100bps', sa.Numeric(18, 4), nullable=True),
        sa.Column('asset_details', postgresql.JSONB, nullable=True),
        sa.Column('liability_details', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_gap_analysis_org', 'txn_gap_analysis', ['organization_id'])
    op.create_index('ix_txn_gap_analysis_date', 'txn_gap_analysis', ['analysis_date'])
    op.create_index('ix_txn_gap_analysis_type', 'txn_gap_analysis', ['analysis_type'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_gap_analysis')
    op.drop_table('txn_stress_test')
    op.drop_table('txn_var_calculation')
    op.drop_table('txn_risk_position')
    op.drop_table('txn_investment_transaction')
    op.drop_table('txn_investment')
    op.drop_table('mst_investment_category')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS risk_type")
    op.execute("DROP TYPE IF EXISTS investment_status")
    op.execute("DROP TYPE IF EXISTS investment_type")
