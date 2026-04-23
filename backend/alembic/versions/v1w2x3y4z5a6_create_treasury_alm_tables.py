"""Create Treasury & ALM tables

Revision ID: v1w2x3y4z5a6
Revises: u9v0w1x2y3z4
Create Date: 2025-01-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'v1w2x3y4z5a6'
down_revision: Union[str, None] = 'u9v0w1x2y3z4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Phase 4 enums with idempotent DO blocks

    # Lender/Borrowing enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE lender_type AS ENUM (
                'BANK', 'NBFC', 'DFI', 'MUTUAL_FUND', 'INSURANCE_COMPANY',
                'PENSION_FUND', 'FII', 'NCD', 'COMMERCIAL_PAPER',
                'SUBORDINATED_DEBT', 'TIER_2_CAPITAL', 'ECB', 'RELATED_PARTY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE lender_status AS ENUM (
                'ACTIVE', 'INACTIVE', 'BLOCKED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE borrowing_type AS ENUM (
                'TERM_LOAN', 'WORKING_CAPITAL', 'CASH_CREDIT', 'OVERDRAFT',
                'NCD', 'SUBORDINATED_DEBT', 'COMMERCIAL_PAPER', 'REFINANCE',
                'SECURITIZATION', 'DIRECT_ASSIGNMENT', 'CO_LENDING', 'ECB'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE borrowing_status AS ENUM (
                'PROPOSED', 'SANCTIONED', 'DOCUMENTATION', 'ACTIVE',
                'FULLY_DRAWN', 'REPAYING', 'CLOSED', 'CANCELLED', 'PREPAID'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE borrowing_security_type AS ENUM (
                'UNSECURED', 'HYPOTHECATION', 'PLEDGE', 'MORTGAGE',
                'ASSIGNMENT', 'GUARANTEE'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE drawdown_status AS ENUM (
                'REQUESTED', 'APPROVED', 'DISBURSED', 'REJECTED', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE borrowing_rate_type AS ENUM (
                'FIXED', 'FLOATING', 'MCLR_LINKED', 'REPO_LINKED', 'TBILL_LINKED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE borrowing_payment_type AS ENUM (
                'INTEREST', 'PRINCIPAL', 'PREPAYMENT', 'COMMITMENT_FEE', 'OTHER_CHARGES'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ALM enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alm_bucket AS ENUM (
                'DAY_1', 'DAYS_2_7', 'DAYS_8_14', 'DAYS_15_28', 'DAYS_29_3M',
                'MONTHS_3_6', 'MONTHS_6_12', 'YEARS_1_3', 'YEARS_3_5', 'OVER_5_YEARS'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alm_category AS ENUM (
                'ASSET', 'LIABILITY', 'OFF_BALANCE_SHEET'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alm_asset_type AS ENUM (
                'CASH', 'BANK_BALANCE', 'INVESTMENTS_HTM', 'INVESTMENTS_AFS',
                'INVESTMENTS_HFT', 'LOANS_STANDARD', 'LOANS_NPA',
                'FIXED_ASSETS', 'OTHER_ASSETS'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alm_liability_type AS ENUM (
                'BORROWINGS_BANK', 'BORROWINGS_NCD', 'BORROWINGS_CP',
                'BORROWINGS_SUBORDINATED', 'DEPOSITS', 'OTHER_LIABILITIES', 'EQUITY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE irs_shock_type AS ENUM (
                'PARALLEL_UP_100', 'PARALLEL_UP_200', 'PARALLEL_DOWN_100',
                'PARALLEL_DOWN_200', 'STEEPENER', 'FLATTENER'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Exposure/Risk enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE exposure_limit_type AS ENUM (
                'SINGLE_BORROWER', 'GROUP_BORROWER', 'SECTOR', 'INDUSTRY',
                'GEOGRAPHY', 'RATING', 'PRODUCT', 'LENDER', 'UNSECURED', 'RELATED_PARTY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE exposure_status AS ENUM (
                'WITHIN_LIMIT', 'NEAR_LIMIT', 'BREACH', 'EXCEPTION_APPROVED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE liquidity_ratio_type AS ENUM (
                'LCR', 'NSFR', 'CUMULATIVE_GAP', 'STRUCTURAL_LIQUIDITY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE covenant_type AS ENUM (
                'CRAR', 'NPA_RATIO', 'PROVISION_COVERAGE', 'LEVERAGE_RATIO',
                'INTEREST_COVERAGE', 'ASSET_LIABILITY_MISMATCH', 'CONCENTRATION_LIMIT'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE covenant_status AS ENUM (
                'COMPLIANT', 'NON_COMPLIANT', 'WAIVER_OBTAINED', 'CURE_PERIOD'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # =========================================================================
    # Lender Table
    # =========================================================================
    op.create_table(
        'trs_lender',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lender_code', sa.String(30), nullable=False),
        sa.Column('lender_name', sa.String(200), nullable=False),
        sa.Column('lender_type', sa.String(50), nullable=False),
        sa.Column('pan', sa.String(20), nullable=True),
        sa.Column('cin', sa.String(25), nullable=True),
        sa.Column('gstin', sa.String(20), nullable=True),
        sa.Column('rbi_registration', sa.String(50), nullable=True),
        sa.Column('registered_address', sa.Text(), nullable=True),
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('contact_email', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('bank_account_number', sa.String(30), nullable=True),
        sa.Column('bank_ifsc', sa.String(15), nullable=True),
        sa.Column('external_rating', sa.String(20), nullable=True),
        sa.Column('rating_agency', sa.String(50), nullable=True),
        sa.Column('rating_date', sa.Date(), nullable=True),
        sa.Column('total_sanction_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('available_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'lender_code', name='uq_trs_lender_code'),
    )
    op.create_index('ix_trs_lender_org_type', 'trs_lender', ['organization_id', 'lender_type'])
    op.create_index('ix_trs_lender_org_status', 'trs_lender', ['organization_id', 'status'])

    # =========================================================================
    # Borrowing Table
    # =========================================================================
    op.create_table(
        'trs_borrowing',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('borrowing_number', sa.String(50), nullable=False),
        sa.Column('borrowing_type', sa.String(50), nullable=False),
        sa.Column('sanction_date', sa.Date(), nullable=False),
        sa.Column('sanction_reference', sa.String(100), nullable=True),
        sa.Column('sanctioned_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='INR', nullable=True),
        sa.Column('drawn_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('available_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('principal_outstanding', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('rate_type', sa.String(30), nullable=False),
        sa.Column('base_rate_name', sa.String(50), nullable=True),
        sa.Column('base_rate_value', sa.Numeric(8, 4), nullable=True),
        sa.Column('spread_bps', sa.Integer(), server_default='0', nullable=True),
        sa.Column('effective_rate', sa.Numeric(8, 4), nullable=False),
        sa.Column('rate_reset_frequency', sa.String(30), nullable=True),
        sa.Column('next_rate_reset_date', sa.Date(), nullable=True),
        sa.Column('day_count_convention', sa.String(20), server_default='ACT_365', nullable=True),
        sa.Column('interest_payment_frequency', sa.String(20), server_default='MONTHLY', nullable=True),
        sa.Column('principal_payment_frequency', sa.String(20), server_default='QUARTERLY', nullable=True),
        sa.Column('tenure_months', sa.Integer(), nullable=False),
        sa.Column('moratorium_months', sa.Integer(), server_default='0', nullable=True),
        sa.Column('first_interest_date', sa.Date(), nullable=True),
        sa.Column('first_principal_date', sa.Date(), nullable=True),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('security_type', sa.String(30), server_default='UNSECURED', nullable=True),
        sa.Column('security_description', sa.Text(), nullable=True),
        sa.Column('security_cover_required', sa.Numeric(5, 2), nullable=True),
        sa.Column('processing_fee_percent', sa.Numeric(5, 4), nullable=True),
        sa.Column('commitment_fee_percent', sa.Numeric(5, 4), nullable=True),
        sa.Column('prepayment_penalty_percent', sa.Numeric(5, 4), nullable=True),
        sa.Column('financial_covenants', postgresql.JSONB(), nullable=True),
        sa.Column('reporting_requirements', postgresql.JSONB(), nullable=True),
        sa.Column('sanction_letter_path', sa.String(500), nullable=True),
        sa.Column('agreement_date', sa.Date(), nullable=True),
        sa.Column('agreement_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(30), server_default='SANCTIONED', nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.ForeignKeyConstraint(['lender_id'], ['trs_lender.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'borrowing_number', name='uq_trs_borrowing_number'),
    )
    op.create_index('ix_trs_borrowing_org_lender', 'trs_borrowing', ['organization_id', 'lender_id'])
    op.create_index('ix_trs_borrowing_org_status', 'trs_borrowing', ['organization_id', 'status'])
    op.create_index('ix_trs_borrowing_maturity', 'trs_borrowing', ['maturity_date'])

    # =========================================================================
    # Borrowing Tranche Table
    # =========================================================================
    op.create_table(
        'trs_borrowing_tranche',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('borrowing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tranche_number', sa.Integer(), nullable=False),
        sa.Column('request_date', sa.Date(), nullable=False),
        sa.Column('requested_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('disbursement_date', sa.Date(), nullable=True),
        sa.Column('disbursed_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('principal_outstanding', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('effective_rate', sa.Numeric(8, 4), nullable=True),
        sa.Column('utr_number', sa.String(50), nullable=True),
        sa.Column('bank_reference', sa.String(100), nullable=True),
        sa.Column('status', sa.String(30), server_default='REQUESTED', nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['borrowing_id'], ['trs_borrowing.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('borrowing_id', 'tranche_number', name='uq_trs_tranche_number'),
    )
    op.create_index('ix_trs_tranche_status', 'trs_borrowing_tranche', ['status'])

    # =========================================================================
    # Borrowing Schedule Table
    # =========================================================================
    op.create_table(
        'trs_borrowing_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('borrowing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tranche_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('principal_due', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('interest_due', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('total_due', sa.Numeric(18, 2), nullable=False),
        sa.Column('principal_paid', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('interest_paid', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('total_paid', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('opening_balance', sa.Numeric(18, 2), nullable=False),
        sa.Column('closing_balance', sa.Numeric(18, 2), nullable=False),
        sa.Column('status', sa.String(20), server_default='NOT_DUE', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['borrowing_id'], ['trs_borrowing.id']),
        sa.ForeignKeyConstraint(['tranche_id'], ['trs_borrowing_tranche.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_schedule_borrowing', 'trs_borrowing_schedule', ['borrowing_id'])
    op.create_index('ix_trs_schedule_due_date', 'trs_borrowing_schedule', ['due_date'])
    op.create_index('ix_trs_schedule_status', 'trs_borrowing_schedule', ['status'])

    # =========================================================================
    # Borrowing Payment Table
    # =========================================================================
    op.create_table(
        'trs_borrowing_payment',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('borrowing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payment_type', sa.String(30), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('value_date', sa.Date(), nullable=False),
        sa.Column('principal_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('interest_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('fee_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_mode', sa.String(20), nullable=False),
        sa.Column('utr_number', sa.String(50), nullable=True),
        sa.Column('bank_reference', sa.String(100), nullable=True),
        sa.Column('from_bank_account', sa.String(30), nullable=True),
        sa.Column('interest_from_date', sa.Date(), nullable=True),
        sa.Column('interest_to_date', sa.Date(), nullable=True),
        sa.Column('days_counted', sa.Integer(), nullable=True),
        sa.Column('rate_applied', sa.Numeric(8, 4), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['borrowing_id'], ['trs_borrowing.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['trs_borrowing_schedule.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_payment_borrowing', 'trs_borrowing_payment', ['borrowing_id'])
    op.create_index('ix_trs_payment_date', 'trs_borrowing_payment', ['payment_date'])

    # =========================================================================
    # Borrowing Covenant Table
    # =========================================================================
    op.create_table(
        'trs_borrowing_covenant',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('borrowing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('covenant_type', sa.String(50), nullable=False),
        sa.Column('covenant_description', sa.Text(), nullable=False),
        sa.Column('threshold_type', sa.String(20), nullable=False),
        sa.Column('threshold_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('threshold_min', sa.Numeric(18, 4), nullable=True),
        sa.Column('threshold_max', sa.Numeric(18, 4), nullable=True),
        sa.Column('testing_frequency', sa.String(20), server_default='QUARTERLY', nullable=True),
        sa.Column('next_test_date', sa.Date(), nullable=True),
        sa.Column('current_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('last_tested_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(30), server_default='COMPLIANT', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['borrowing_id'], ['trs_borrowing.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_covenant_borrowing', 'trs_borrowing_covenant', ['borrowing_id'])
    op.create_index('ix_trs_covenant_type', 'trs_borrowing_covenant', ['covenant_type'])

    # =========================================================================
    # ALM Position Table
    # =========================================================================
    op.create_table(
        'trs_alm_position',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_date', sa.Date(), nullable=False),
        sa.Column('total_assets', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('total_liabilities', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('net_position', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('bucket_analysis', postgresql.JSONB(), nullable=True),
        sa.Column('cumulative_gap_1_year', sa.Numeric(18, 2), nullable=True),
        sa.Column('cumulative_gap_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_final', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'position_date', name='uq_trs_alm_position_date'),
    )
    op.create_index('ix_trs_alm_position_org', 'trs_alm_position', ['organization_id'])

    # =========================================================================
    # ALM Asset Table
    # =========================================================================
    op.create_table(
        'trs_alm_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('alm_bucket', sa.String(30), nullable=False),
        sa.Column('book_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('market_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('rate_sensitive_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('non_rate_sensitive_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('weighted_avg_rate', sa.Numeric(8, 4), nullable=True),
        sa.Column('weighted_avg_maturity_days', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_count', sa.Integer(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['trs_alm_position.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_alm_asset_position', 'trs_alm_asset', ['position_id'])
    op.create_index('ix_trs_alm_asset_bucket', 'trs_alm_asset', ['alm_bucket'])

    # =========================================================================
    # ALM Liability Table
    # =========================================================================
    op.create_table(
        'trs_alm_liability',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('liability_type', sa.String(50), nullable=False),
        sa.Column('alm_bucket', sa.String(30), nullable=False),
        sa.Column('book_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('rate_sensitive_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('non_rate_sensitive_amount', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('weighted_avg_rate', sa.Numeric(8, 4), nullable=True),
        sa.Column('weighted_avg_maturity_days', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_count', sa.Integer(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['trs_alm_position.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_alm_liability_position', 'trs_alm_liability', ['position_id'])
    op.create_index('ix_trs_alm_liability_bucket', 'trs_alm_liability', ['alm_bucket'])

    # =========================================================================
    # IRS Analysis Table
    # =========================================================================
    op.create_table(
        'trs_irs_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('analysis_date', sa.Date(), nullable=False),
        sa.Column('shock_type', sa.String(30), nullable=False),
        sa.Column('shock_bps', sa.Integer(), nullable=False),
        sa.Column('rate_sensitive_assets', sa.Numeric(18, 2), nullable=False),
        sa.Column('rate_sensitive_liabilities', sa.Numeric(18, 2), nullable=False),
        sa.Column('rate_sensitivity_gap', sa.Numeric(18, 2), nullable=False),
        sa.Column('nii_impact', sa.Numeric(18, 2), nullable=False),
        sa.Column('nii_impact_percent', sa.Numeric(8, 4), nullable=False),
        sa.Column('ev_impact', sa.Numeric(18, 2), nullable=True),
        sa.Column('ev_impact_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('bucket_analysis', postgresql.JSONB(), nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.ForeignKeyConstraint(['position_id'], ['trs_alm_position.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_irs_org', 'trs_irs_analysis', ['organization_id'])
    op.create_index('ix_trs_irs_date', 'trs_irs_analysis', ['analysis_date'])

    # =========================================================================
    # Exposure Limit Table
    # =========================================================================
    op.create_table(
        'trs_exposure_limit',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('limit_type', sa.String(50), nullable=False),
        sa.Column('limit_key', sa.String(100), nullable=False),
        sa.Column('limit_description', sa.Text(), nullable=True),
        sa.Column('regulatory_limit_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('regulatory_limit_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('internal_limit_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('internal_limit_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('warning_threshold_percent', sa.Numeric(5, 2), server_default='80', nullable=True),
        sa.Column('current_exposure', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('current_exposure_percent', sa.Numeric(8, 4), server_default='0', nullable=True),
        sa.Column('exposure_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(30), server_default='WITHIN_LIMIT', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'limit_type', 'limit_key', name='uq_trs_exposure_limit'),
    )
    op.create_index('ix_trs_exposure_limit_org', 'trs_exposure_limit', ['organization_id'])

    # =========================================================================
    # Exposure Tracking Table
    # =========================================================================
    op.create_table(
        'trs_exposure_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('limit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('borrowing_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('exposure_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('funded_exposure', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('non_funded_exposure', sa.Numeric(18, 2), server_default='0', nullable=True),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['limit_id'], ['trs_exposure_limit.id']),
        sa.ForeignKeyConstraint(['entity_id'], ['los_entity.id']),
        sa.ForeignKeyConstraint(['loan_account_id'], ['lms_loan_account.id']),
        sa.ForeignKeyConstraint(['borrowing_id'], ['trs_borrowing.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trs_exposure_tracking_limit', 'trs_exposure_tracking', ['limit_id'])
    op.create_index('ix_trs_exposure_tracking_entity', 'trs_exposure_tracking', ['entity_id'])
    op.create_index('ix_trs_exposure_tracking_loan', 'trs_exposure_tracking', ['loan_account_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_trs_exposure_tracking_loan', table_name='trs_exposure_tracking')
    op.drop_index('ix_trs_exposure_tracking_entity', table_name='trs_exposure_tracking')
    op.drop_index('ix_trs_exposure_tracking_limit', table_name='trs_exposure_tracking')
    op.drop_table('trs_exposure_tracking')

    op.drop_index('ix_trs_exposure_limit_org', table_name='trs_exposure_limit')
    op.drop_table('trs_exposure_limit')

    op.drop_index('ix_trs_irs_date', table_name='trs_irs_analysis')
    op.drop_index('ix_trs_irs_org', table_name='trs_irs_analysis')
    op.drop_table('trs_irs_analysis')

    op.drop_index('ix_trs_alm_liability_bucket', table_name='trs_alm_liability')
    op.drop_index('ix_trs_alm_liability_position', table_name='trs_alm_liability')
    op.drop_table('trs_alm_liability')

    op.drop_index('ix_trs_alm_asset_bucket', table_name='trs_alm_asset')
    op.drop_index('ix_trs_alm_asset_position', table_name='trs_alm_asset')
    op.drop_table('trs_alm_asset')

    op.drop_index('ix_trs_alm_position_org', table_name='trs_alm_position')
    op.drop_table('trs_alm_position')

    op.drop_index('ix_trs_covenant_type', table_name='trs_borrowing_covenant')
    op.drop_index('ix_trs_covenant_borrowing', table_name='trs_borrowing_covenant')
    op.drop_table('trs_borrowing_covenant')

    op.drop_index('ix_trs_payment_date', table_name='trs_borrowing_payment')
    op.drop_index('ix_trs_payment_borrowing', table_name='trs_borrowing_payment')
    op.drop_table('trs_borrowing_payment')

    op.drop_index('ix_trs_schedule_status', table_name='trs_borrowing_schedule')
    op.drop_index('ix_trs_schedule_due_date', table_name='trs_borrowing_schedule')
    op.drop_index('ix_trs_schedule_borrowing', table_name='trs_borrowing_schedule')
    op.drop_table('trs_borrowing_schedule')

    op.drop_index('ix_trs_tranche_status', table_name='trs_borrowing_tranche')
    op.drop_table('trs_borrowing_tranche')

    op.drop_index('ix_trs_borrowing_maturity', table_name='trs_borrowing')
    op.drop_index('ix_trs_borrowing_org_status', table_name='trs_borrowing')
    op.drop_index('ix_trs_borrowing_org_lender', table_name='trs_borrowing')
    op.drop_table('trs_borrowing')

    op.drop_index('ix_trs_lender_org_status', table_name='trs_lender')
    op.drop_index('ix_trs_lender_org_type', table_name='trs_lender')
    op.drop_table('trs_lender')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS covenant_status')
    op.execute('DROP TYPE IF EXISTS covenant_type')
    op.execute('DROP TYPE IF EXISTS liquidity_ratio_type')
    op.execute('DROP TYPE IF EXISTS exposure_status')
    op.execute('DROP TYPE IF EXISTS exposure_limit_type')
    op.execute('DROP TYPE IF EXISTS irs_shock_type')
    op.execute('DROP TYPE IF EXISTS alm_liability_type')
    op.execute('DROP TYPE IF EXISTS alm_asset_type')
    op.execute('DROP TYPE IF EXISTS alm_category')
    op.execute('DROP TYPE IF EXISTS alm_bucket')
    op.execute('DROP TYPE IF EXISTS borrowing_payment_type')
    op.execute('DROP TYPE IF EXISTS borrowing_rate_type')
    op.execute('DROP TYPE IF EXISTS drawdown_status')
    op.execute('DROP TYPE IF EXISTS borrowing_security_type')
    op.execute('DROP TYPE IF EXISTS borrowing_status')
    op.execute('DROP TYPE IF EXISTS borrowing_type')
    op.execute('DROP TYPE IF EXISTS lender_status')
    op.execute('DROP TYPE IF EXISTS lender_type')
