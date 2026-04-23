"""Add GL Entry table for audit trail.

Revision ID: z6_add_gl_entry
Revises: z5_add_credit_bureau
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z6_add_gl_entry'
down_revision = 'z5_add_credit_bureau'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE gl_entry_type AS ENUM ('NORMAL', 'REVERSAL', 'OPENING', 'CLOSING', 'ADJUSTMENT', 'ACCRUAL', 'DEPRECIATION', 'REVALUATION');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    op.execute("""


        DO $$ BEGIN


            CREATE TYPE gl_entry_source_type AS ENUM ('MANUAL', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'RECEIPT', 'LOAN_DISBURSEMENT', 'LOAN_RECEIPT', 'INTEREST_ACCRUAL', 'FEE_ACCRUAL', 'NPA_PROVISION', 'TDS', 'GST', 'DEPRECIATION', 'FOREX', 'BANK_CHARGES', 'IMPORT');


        EXCEPTION WHEN duplicate_object THEN null; END $$;


    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE balance_type AS ENUM ('DR', 'CR');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE party_type AS ENUM ('CUSTOMER', 'VENDOR', 'EMPLOYEE');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Create txn_gl_entry table
    op.create_table(
        'txn_gl_entry',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),

        # Voucher reference
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('voucher_line_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voucher_number', sa.String(50), nullable=False),
        sa.Column('voucher_date', sa.Date(), nullable=False),

        # Entry type and source
        sa.Column('entry_type', postgresql.ENUM('NORMAL', 'REVERSAL', 'OPENING', 'CLOSING', 'ADJUSTMENT', 'ACCRUAL', 'DEPRECIATION', 'REVALUATION', name='gl_entry_type', create_type=False), nullable=False, server_default='NORMAL'),
        sa.Column('source_type', postgresql.ENUM('MANUAL', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'RECEIPT', 'LOAN_DISBURSEMENT', 'LOAN_RECEIPT', 'INTEREST_ACCRUAL', 'FEE_ACCRUAL', 'NPA_PROVISION', 'TDS', 'GST', 'DEPRECIATION', 'FOREX', 'BANK_CHARGES', 'IMPORT', name='gl_entry_source_type', create_type=False), nullable=False, server_default='MANUAL'),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Account information
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_code', sa.String(20), nullable=False),
        sa.Column('account_name', sa.String(200), nullable=False),

        # Entry amounts
        sa.Column('debit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('credit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('balance_type', postgresql.ENUM('DR', 'CR', name='balance_type', create_type=False), nullable=False),

        # Currency
        sa.Column('currency_code', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('exchange_rate', sa.Numeric(18, 6), nullable=False, server_default='1.000000'),
        sa.Column('base_debit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('base_credit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),

        # Party/Sub-ledger
        sa.Column('party_type', postgresql.ENUM('CUSTOMER', 'VENDOR', 'EMPLOYEE', name='party_type', create_type=False), nullable=True),
        sa.Column('party_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('party_name', sa.String(200), nullable=True),

        # Cost center
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_center_code', sa.String(20), nullable=True),

        # Period information
        sa.Column('financial_year_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Narration
        sa.Column('narration', sa.Text(), nullable=True),

        # Reference
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('reference_date', sa.Date(), nullable=True),

        # Reversal tracking
        sa.Column('is_reversed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reversal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('original_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reversal_date', sa.Date(), nullable=True),

        # Posting information
        sa.Column('posting_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=False),

        # Running balance
        sa.Column('running_balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('running_balance_type', postgresql.ENUM('DR', 'CR', name='balance_type', create_type=False), nullable=True),

        # Sequence
        sa.Column('sequence_number', sa.Integer(), nullable=False),

        # Additional data
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),

        # Organization
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Foreign keys
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['voucher_line_id'], ['txn_voucher_line.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['account_id'], ['mst_account.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['financial_year_id'], ['mst_financial_year.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['period_id'], ['mst_financial_period.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reversal_entry_id'], ['txn_gl_entry.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['original_entry_id'], ['txn_gl_entry.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['posted_by'], ['mst_user.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    # Basic lookups
    op.create_index('ix_gl_entry_voucher_id', 'txn_gl_entry', ['voucher_id'])
    op.create_index('ix_gl_entry_voucher_line_id', 'txn_gl_entry', ['voucher_line_id'])
    op.create_index('ix_gl_entry_voucher_number', 'txn_gl_entry', ['voucher_number'])
    op.create_index('ix_gl_entry_voucher_date', 'txn_gl_entry', ['voucher_date'])
    op.create_index('ix_gl_entry_account_id', 'txn_gl_entry', ['account_id'])
    op.create_index('ix_gl_entry_party_id', 'txn_gl_entry', ['party_id'])
    op.create_index('ix_gl_entry_cost_center_id', 'txn_gl_entry', ['cost_center_id'])
    op.create_index('ix_gl_entry_financial_year_id', 'txn_gl_entry', ['financial_year_id'])
    op.create_index('ix_gl_entry_period_id', 'txn_gl_entry', ['period_id'])
    op.create_index('ix_gl_entry_organization_id', 'txn_gl_entry', ['organization_id'])
    op.create_index('ix_gl_entry_unit_id', 'txn_gl_entry', ['unit_id'])

    # Composite indexes for common queries
    op.create_index('ix_gl_entry_account_date', 'txn_gl_entry', ['account_id', 'voucher_date'])
    op.create_index('ix_gl_entry_party', 'txn_gl_entry', ['party_type', 'party_id', 'voucher_date'])
    op.create_index('ix_gl_entry_period', 'txn_gl_entry', ['period_id', 'account_id'])
    op.create_index('ix_gl_entry_cost_center', 'txn_gl_entry', ['cost_center_id', 'voucher_date'])
    op.create_index('ix_gl_entry_source', 'txn_gl_entry', ['source_type', 'source_id'])
    op.create_index('ix_gl_entry_org_account', 'txn_gl_entry', ['organization_id', 'account_id'])
    op.create_index('ix_gl_entry_fy_account', 'txn_gl_entry', ['financial_year_id', 'account_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_gl_entry_fy_account', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_org_account', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_source', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_cost_center', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_period', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_party', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_account_date', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_unit_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_organization_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_period_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_financial_year_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_cost_center_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_party_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_account_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_voucher_date', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_voucher_number', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_voucher_line_id', 'txn_gl_entry')
    op.drop_index('ix_gl_entry_voucher_id', 'txn_gl_entry')

    # Drop table
    op.drop_table('txn_gl_entry')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS gl_entry_source_type")
    op.execute("DROP TYPE IF EXISTS gl_entry_type")
