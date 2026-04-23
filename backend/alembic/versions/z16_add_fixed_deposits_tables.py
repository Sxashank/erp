"""Add Fixed Deposits tables

Revision ID: z16_add_fixed_deposits
Revises: z15_add_compliance_tables
Create Date: 2026-01-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z16_add_fixed_deposits'
down_revision: Union[str, None] = 'z15_add_compliance_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fdinterestpayoutfrequency AS ENUM (
                'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'ON_MATURITY'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fdcompoundingfrequency AS ENUM (
                'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'SIMPLE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fdcustomercategory AS ENUM (
                'GENERAL', 'SENIOR_CITIZEN', 'STAFF', 'NRI', 'CORPORATE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fdstatus AS ENUM (
                'DRAFT', 'PENDING_APPROVAL', 'ACTIVE', 'MATURED',
                'PREMATURE_CLOSED', 'RENEWED', 'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fdtransactiontype AS ENUM (
                'DEPOSIT', 'INTEREST_PAYOUT', 'INTEREST_CAPITALIZATION',
                'TDS_DEDUCTION', 'MATURITY_PAYOUT', 'PREMATURE_PAYOUT',
                'RENEWAL', 'LOAN_DISBURSEMENT', 'LOAN_REPAYMENT', 'PENALTY'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create FD Product table
    op.create_table(
        'fd_product',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('product_code', sa.String(20), nullable=False),
        sa.Column('product_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('min_tenure_days', sa.Integer, nullable=False, default=7),
        sa.Column('max_tenure_days', sa.Integer, nullable=False, default=3650),
        sa.Column('min_amount', sa.Numeric(18, 2), nullable=False, default=1000),
        sa.Column('max_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('interest_payout_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'ON_MATURITY', name='fdinterestpayoutfrequency', create_type=False), nullable=False, default='QUARTERLY'),
        sa.Column('compounding_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'SIMPLE', name='fdcompoundingfrequency', create_type=False), nullable=False, default='QUARTERLY'),
        sa.Column('allow_premature_withdrawal', sa.Boolean, nullable=False, default=True),
        sa.Column('premature_penalty_rate', sa.Numeric(5, 2), nullable=True, default=1.00),
        sa.Column('allow_auto_renewal', sa.Boolean, nullable=False, default=True),
        sa.Column('auto_renewal_tenure_days', sa.Integer, nullable=True),
        sa.Column('allow_loan_against_fd', sa.Boolean, nullable=False, default=True),
        sa.Column('max_loan_percentage', sa.Numeric(5, 2), nullable=True, default=90.00),
        sa.Column('loan_interest_premium', sa.Numeric(5, 2), nullable=True, default=2.00),
        sa.Column('tds_applicable', sa.Boolean, nullable=False, default=True),
        sa.Column('tds_threshold', sa.Numeric(18, 2), nullable=False, default=40000),
        sa.Column('fd_liability_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id'), nullable=True),
        sa.Column('interest_expense_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id'), nullable=True),
        sa.Column('tds_payable_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id'), nullable=True),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_product_organization_id', 'fd_product', ['organization_id'])
    op.create_unique_constraint('uq_fd_product_org_code', 'fd_product', ['organization_id', 'product_code'])

    # Create FD Interest Slab table
    op.create_table(
        'fd_interest_slab',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_product.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_category', postgresql.ENUM('GENERAL', 'SENIOR_CITIZEN', 'STAFF', 'NRI', 'CORPORATE', name='fdcustomercategory', create_type=False), nullable=False, default='GENERAL'),
        sa.Column('min_tenure_days', sa.Integer, nullable=False),
        sa.Column('max_tenure_days', sa.Integer, nullable=False),
        sa.Column('min_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_interest_slab_product_id', 'fd_interest_slab', ['product_id'])

    # Create Fixed Deposit table
    op.create_table(
        'fd_fixed_deposit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('fd_number', sa.String(30), nullable=False, unique=True),
        sa.Column('certificate_number', sa.String(50), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_product.id'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id'), nullable=False),
        sa.Column('customer_category', postgresql.ENUM('GENERAL', 'SENIOR_CITIZEN', 'STAFF', 'NRI', 'CORPORATE', name='fdcustomercategory', create_type=False), nullable=False, default='GENERAL'),
        sa.Column('deposit_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('deposit_date', sa.Date, nullable=False),
        sa.Column('value_date', sa.Date, nullable=False),
        sa.Column('tenure_days', sa.Integer, nullable=False),
        sa.Column('maturity_date', sa.Date, nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('interest_payout_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'ON_MATURITY', name='fdinterestpayoutfrequency', create_type=False), nullable=False),
        sa.Column('compounding_frequency', postgresql.ENUM('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'SIMPLE', name='fdcompoundingfrequency', create_type=False), nullable=False),
        sa.Column('maturity_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('accrued_interest', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('paid_interest', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('tds_deducted', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('interest_payout_mode', sa.String(20), nullable=False, default='BANK_TRANSFER'),
        sa.Column('payout_bank_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('auto_renew', sa.Boolean, nullable=False, default=False),
        sa.Column('renewal_tenure_days', sa.Integer, nullable=True),
        sa.Column('renewal_count', sa.Integer, nullable=False, default=0),
        sa.Column('parent_fd_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_fixed_deposit.id'), nullable=True),
        sa.Column('has_loan', sa.Boolean, nullable=False, default=False),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PENDING_APPROVAL', 'ACTIVE', 'MATURED', 'PREMATURE_CLOSED', 'RENEWED', 'CANCELLED', name='fdstatus', create_type=False), nullable=False, default='DRAFT'),
        sa.Column('last_interest_calc_date', sa.Date, nullable=True),
        sa.Column('last_interest_payout_date', sa.Date, nullable=True),
        sa.Column('closed_date', sa.Date, nullable=True),
        sa.Column('closure_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('closure_remarks', sa.Text, nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_unit.id'), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_fixed_deposit_organization_id', 'fd_fixed_deposit', ['organization_id'])
    op.create_index('ix_fd_fixed_deposit_customer_id', 'fd_fixed_deposit', ['customer_id'])
    op.create_index('ix_fd_fixed_deposit_product_id', 'fd_fixed_deposit', ['product_id'])
    op.create_index('ix_fd_fixed_deposit_status', 'fd_fixed_deposit', ['status'])
    op.create_index('ix_fd_fixed_deposit_maturity_date', 'fd_fixed_deposit', ['maturity_date'])

    # Create FD Interest Accrual table
    op.create_table(
        'fd_interest_accrual',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fixed_deposit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_fixed_deposit.id', ondelete='CASCADE'), nullable=False),
        sa.Column('accrual_date', sa.Date, nullable=False),
        sa.Column('period_from', sa.Date, nullable=False),
        sa.Column('period_to', sa.Date, nullable=False),
        sa.Column('days', sa.Integer, nullable=False),
        sa.Column('principal_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('interest_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('cumulative_interest', sa.Numeric(18, 2), nullable=False),
        sa.Column('is_paid', sa.Boolean, nullable=False, default=False),
        sa.Column('paid_date', sa.Date, nullable=True),
        sa.Column('payment_reference', sa.String(50), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_interest_accrual_fixed_deposit_id', 'fd_interest_accrual', ['fixed_deposit_id'])
    op.create_index('ix_fd_interest_accrual_accrual_date', 'fd_interest_accrual', ['accrual_date'])

    # Create FD Transaction table
    op.create_table(
        'fd_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fixed_deposit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_fixed_deposit.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_date', sa.Date, nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('DEPOSIT', 'INTEREST_PAYOUT', 'INTEREST_CAPITALIZATION', 'TDS_DEDUCTION', 'MATURITY_PAYOUT', 'PREMATURE_PAYOUT', 'RENEWAL', 'LOAN_DISBURSEMENT', 'LOAN_REPAYMENT', 'PENALTY', name='fdtransactiontype', create_type=False), nullable=False),
        sa.Column('description', sa.String(200), nullable=False),
        sa.Column('debit_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('credit_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('balance', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_mode', sa.String(20), nullable=True),
        sa.Column('reference_number', sa.String(50), nullable=True),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id'), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_transaction_fixed_deposit_id', 'fd_transaction', ['fixed_deposit_id'])
    op.create_index('ix_fd_transaction_date', 'fd_transaction', ['transaction_date'])

    # Create FD Nominee table
    op.create_table(
        'fd_nominee',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fixed_deposit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fd_fixed_deposit.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nominee_name', sa.String(200), nullable=False),
        sa.Column('relationship', sa.String(50), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('share_percentage', sa.Numeric(5, 2), nullable=False, default=100),
        sa.Column('address_line1', sa.String(200), nullable=True),
        sa.Column('address_line2', sa.String(200), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('is_minor', sa.Boolean, nullable=False, default=False),
        sa.Column('guardian_name', sa.String(200), nullable=True),
        sa.Column('guardian_relationship', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fd_nominee_fixed_deposit_id', 'fd_nominee', ['fixed_deposit_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('fd_nominee')
    op.drop_table('fd_transaction')
    op.drop_table('fd_interest_accrual')
    op.drop_table('fd_fixed_deposit')
    op.drop_table('fd_interest_slab')
    op.drop_table('fd_product')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS fdtransactiontype')
    op.execute('DROP TYPE IF EXISTS fdstatus')
    op.execute('DROP TYPE IF EXISTS fdcustomercategory')
    op.execute('DROP TYPE IF EXISTS fdcompoundingfrequency')
    op.execute('DROP TYPE IF EXISTS fdinterestpayoutfrequency')
