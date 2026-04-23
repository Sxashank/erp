"""Add Account Aggregator consent and data tables.

Revision ID: z3_add_account_aggregator_tables
Revises: z2_add_nach_tables
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z3_add_account_aggregator_tables'
down_revision: Union[str, None] = 'z2_add_nach_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create AA Provider enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aaprovider AS ENUM (
                'FINVU', 'ONEMONEY', 'SETU', 'NADL', 'CAMS_FINSERV', 'PERFIOS'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Consent Status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aaconsentstatus AS ENUM (
                'PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'PAUSED', 'REVOKED', 'EXPIRED', 'FAILED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Consent Purpose enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aaconsentpurpose AS ENUM (
                'WEALTH_MANAGEMENT', 'UNDERWRITING', 'MONITORING', 'BANK_STATEMENT_ANALYSIS',
                'INCOME_VERIFICATION', 'ACCOUNT_AGGREGATION', 'TAX_FILING'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Consent Mode enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aaconsentmode AS ENUM (
                'VIEW', 'STORE', 'QUERY', 'STREAM'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Fetch Frequency enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aafetchfrequency AS ENUM (
                'ONETIME', 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'AS_AVAILABLE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA FI Type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aafitype AS ENUM (
                'DEPOSIT', 'TERM_DEPOSIT', 'RECURRING_DEPOSIT', 'SIP', 'CP', 'GOVT_SECURITIES',
                'EQUITIES', 'BONDS', 'DEBENTURES', 'MUTUAL_FUNDS', 'ETF', 'IDR', 'CIS', 'AIF',
                'INSURANCE_POLICIES', 'NPS', 'INVIT', 'REIT', 'GSTR1_3B', 'OTHER'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Fetch Session Status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aafetchsessionstatus AS ENUM (
                'INITIATED', 'PENDING', 'FETCHING', 'PARTIAL', 'COMPLETED', 'FAILED', 'EXPIRED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create AA Data Status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aadatastatus AS ENUM (
                'RECEIVED', 'PROCESSING', 'PROCESSED', 'IMPORTED', 'FAILED', 'EXPIRED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create lms_aa_consent table
    op.create_table(
        'lms_aa_consent',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Customer/Entity reference
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('loan_application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Customer identification for AA
        sa.Column('customer_id', sa.String(100), nullable=False),  # VUA (Virtual User Address)
        sa.Column('customer_name', sa.String(200), nullable=True),
        sa.Column('customer_mobile', sa.String(15), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        # AA Provider details
        sa.Column('provider', postgresql.ENUM('FINVU', 'ONEMONEY', 'SETU', 'NADL', 'CAMS_FINSERV', 'PERFIOS',
                                               name='aaprovider', create_type=False), nullable=False),
        sa.Column('consent_handle', sa.String(100), nullable=True, unique=True),
        sa.Column('consent_id', sa.String(100), nullable=True, unique=True),
        # Consent purpose and scope
        sa.Column('purpose', postgresql.ENUM('WEALTH_MANAGEMENT', 'UNDERWRITING', 'MONITORING', 'BANK_STATEMENT_ANALYSIS',
                                              'INCOME_VERIFICATION', 'ACCOUNT_AGGREGATION', 'TAX_FILING',
                                              name='aaconsentpurpose', create_type=False),
                  nullable=False, server_default='UNDERWRITING'),
        sa.Column('purpose_description', sa.Text(), nullable=True),
        sa.Column('consent_mode', postgresql.ENUM('VIEW', 'STORE', 'QUERY', 'STREAM',
                                                   name='aaconsentmode', create_type=False),
                  nullable=False, server_default='VIEW'),
        # FI Types requested (JSONB array of fi types)
        sa.Column('fi_types', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Data range
        sa.Column('fi_data_from', sa.Date(), nullable=True),
        sa.Column('fi_data_to', sa.Date(), nullable=True),
        # Fetch configuration
        sa.Column('fetch_frequency', postgresql.ENUM('ONETIME', 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'AS_AVAILABLE',
                                                      name='aafetchfrequency', create_type=False),
                  nullable=False, server_default='ONETIME'),
        sa.Column('fetch_frequency_value', sa.Integer(), nullable=True),
        # Consent validity
        sa.Column('consent_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consent_expiry', sa.DateTime(timezone=True), nullable=True),
        # Data life
        sa.Column('data_life_unit', sa.String(20), nullable=True),
        sa.Column('data_life_value', sa.Integer(), nullable=True),
        # Status tracking
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'PAUSED', 'REVOKED', 'EXPIRED', 'FAILED',
                                             name='aaconsentstatus', create_type=False),
                  nullable=False, server_default='PENDING'),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        # Consent URL
        sa.Column('consent_url', sa.String(500), nullable=True),
        sa.Column('redirect_url', sa.String(500), nullable=True),
        # Timestamps and audit
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        # Error tracking
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Metadata
        sa.Column('aa_response', postgresql.JSONB(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        # Standard audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['los_entity.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['loan_application_id'], ['los_loan_application.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['loan_account_id'], ['lms_loan_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for lms_aa_consent
    op.create_index('ix_aa_consent_org_id', 'lms_aa_consent', ['organization_id'])
    op.create_index('ix_aa_consent_org_status', 'lms_aa_consent', ['organization_id', 'status'])
    op.create_index('ix_aa_consent_customer', 'lms_aa_consent', ['customer_id'])
    op.create_index('ix_aa_consent_handle', 'lms_aa_consent', ['consent_handle'])
    op.create_index('ix_aa_consent_entity', 'lms_aa_consent', ['entity_id'])
    op.create_index('ix_aa_consent_provider', 'lms_aa_consent', ['provider'])
    op.create_index('ix_aa_consent_status', 'lms_aa_consent', ['status'])

    # Create lms_aa_fetch_session table
    op.create_table(
        'lms_aa_fetch_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Session identifiers from AA
        sa.Column('session_id', sa.String(100), nullable=True, unique=True),
        sa.Column('data_session_id', sa.String(100), nullable=True),
        # FI Types being fetched
        sa.Column('fi_types_requested', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Date range for this fetch
        sa.Column('data_from', sa.Date(), nullable=True),
        sa.Column('data_to', sa.Date(), nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM('INITIATED', 'PENDING', 'FETCHING', 'PARTIAL', 'COMPLETED', 'FAILED', 'EXPIRED',
                                             name='aafetchsessionstatus', create_type=False),
                  nullable=False, server_default='INITIATED'),
        # Counts
        sa.Column('total_accounts_requested', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accounts_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accounts_failed', sa.Integer(), nullable=False, server_default='0'),
        # Timestamps
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('data_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        # Error tracking
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        # AA Response
        sa.Column('aa_response', postgresql.JSONB(), nullable=True),
        # Standard audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['consent_id'], ['lms_aa_consent.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
    )

    # Create indexes for lms_aa_fetch_session
    op.create_index('ix_aa_fetch_session_consent', 'lms_aa_fetch_session', ['consent_id'])
    op.create_index('ix_aa_fetch_session_org_id', 'lms_aa_fetch_session', ['organization_id'])
    op.create_index('ix_aa_fetch_session_status', 'lms_aa_fetch_session', ['status'])
    op.create_index('ix_aa_fetch_session_session_id', 'lms_aa_fetch_session', ['session_id'])

    # Create lms_aa_bank_account table
    op.create_table(
        'lms_aa_bank_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fetch_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Entity reference
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        # FI Type
        sa.Column('fi_type', postgresql.ENUM('DEPOSIT', 'TERM_DEPOSIT', 'RECURRING_DEPOSIT', 'SIP', 'CP', 'GOVT_SECURITIES',
                                              'EQUITIES', 'BONDS', 'DEBENTURES', 'MUTUAL_FUNDS', 'ETF', 'IDR', 'CIS', 'AIF',
                                              'INSURANCE_POLICIES', 'NPS', 'INVIT', 'REIT', 'GSTR1_3B', 'OTHER',
                                              name='aafitype', create_type=False),
                  nullable=False, server_default='DEPOSIT'),
        # FIP (Financial Information Provider) details
        sa.Column('fip_id', sa.String(50), nullable=True),
        sa.Column('fip_name', sa.String(200), nullable=True),
        # Account details
        sa.Column('account_type', sa.String(50), nullable=True),
        sa.Column('account_number_masked', sa.String(50), nullable=True),
        sa.Column('account_ref_number', sa.String(100), nullable=True),
        sa.Column('ifsc_code', sa.String(20), nullable=True),
        sa.Column('branch', sa.String(200), nullable=True),
        # Account holder
        sa.Column('holder_name', sa.String(300), nullable=True),
        sa.Column('holder_pan', sa.String(20), nullable=True),
        sa.Column('holder_mobile', sa.String(15), nullable=True),
        sa.Column('holder_email', sa.String(255), nullable=True),
        sa.Column('holder_dob', sa.Date(), nullable=True),
        sa.Column('holder_type', sa.String(50), nullable=True),
        # Balance information
        sa.Column('current_balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('available_balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('balance_as_on', sa.DateTime(timezone=True), nullable=True),
        # For term deposits / FDs
        sa.Column('opening_date', sa.Date(), nullable=True),
        sa.Column('maturity_date', sa.Date(), nullable=True),
        sa.Column('maturity_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('interest_rate', sa.Numeric(8, 4), nullable=True),
        sa.Column('principal_amount', sa.Numeric(18, 2), nullable=True),
        # Data status
        sa.Column('status', postgresql.ENUM('RECEIVED', 'PROCESSING', 'PROCESSED', 'IMPORTED', 'FAILED', 'EXPIRED',
                                             name='aadatastatus', create_type=False),
                  nullable=False, server_default='RECEIVED'),
        # Raw data from AA
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('profile_data', postgresql.JSONB(), nullable=True),
        sa.Column('summary_data', postgresql.JSONB(), nullable=True),
        # Data fetch timestamp
        sa.Column('data_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_from', sa.Date(), nullable=True),
        sa.Column('data_to', sa.Date(), nullable=True),
        # Standard audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fetch_session_id'], ['lms_aa_fetch_session.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['los_entity.id'], ondelete='SET NULL'),
    )

    # Create indexes for lms_aa_bank_account
    op.create_index('ix_aa_bank_account_session', 'lms_aa_bank_account', ['fetch_session_id'])
    op.create_index('ix_aa_bank_account_org_id', 'lms_aa_bank_account', ['organization_id'])
    op.create_index('ix_aa_bank_account_entity', 'lms_aa_bank_account', ['entity_id'])
    op.create_index('ix_aa_bank_account_fi_type', 'lms_aa_bank_account', ['fi_type'])
    op.create_index('ix_aa_bank_account_fip', 'lms_aa_bank_account', ['fip_id'])

    # Create lms_aa_bank_transaction table
    op.create_table(
        'lms_aa_bank_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Transaction details
        sa.Column('txn_id', sa.String(100), nullable=True),
        sa.Column('txn_type', sa.String(20), nullable=False),  # DEBIT, CREDIT
        sa.Column('mode', sa.String(50), nullable=True),  # UPI, NEFT, IMPS, CASH, etc.
        # Amount
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        # Balance after transaction
        sa.Column('balance_after', sa.Numeric(18, 2), nullable=True),
        # Transaction date/time
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('transaction_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_date', sa.Date(), nullable=True),
        # Narration/Description
        sa.Column('narration', sa.Text(), nullable=True),
        sa.Column('reference', sa.String(200), nullable=True),
        # Counterparty details
        sa.Column('counterparty_name', sa.String(200), nullable=True),
        sa.Column('counterparty_account', sa.String(50), nullable=True),
        sa.Column('counterparty_ifsc', sa.String(20), nullable=True),
        # Categorization
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('sub_category', sa.String(100), nullable=True),
        # Raw data
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        # Standard audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['bank_account_id'], ['lms_aa_bank_account.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
    )

    # Create indexes for lms_aa_bank_transaction
    op.create_index('ix_aa_bank_txn_account', 'lms_aa_bank_transaction', ['bank_account_id'])
    op.create_index('ix_aa_bank_txn_org_id', 'lms_aa_bank_transaction', ['organization_id'])
    op.create_index('ix_aa_bank_txn_date', 'lms_aa_bank_transaction', ['transaction_date'])
    op.create_index('ix_aa_bank_txn_type', 'lms_aa_bank_transaction', ['txn_type'])
    op.create_index('ix_aa_bank_txn_account_date', 'lms_aa_bank_transaction', ['bank_account_id', 'transaction_date'])

    # Create lms_aa_consent_log table
    op.create_table(
        'lms_aa_consent_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Event details
        sa.Column('event_type', sa.String(50), nullable=False),  # CREATED, APPROVED, REVOKED, etc.
        sa.Column('old_status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'PAUSED', 'REVOKED', 'EXPIRED', 'FAILED',
                                                 name='aaconsentstatus', create_type=False), nullable=True),
        sa.Column('new_status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'PAUSED', 'REVOKED', 'EXPIRED', 'FAILED',
                                                 name='aaconsentstatus', create_type=False), nullable=True),
        # Event source
        sa.Column('source', sa.String(50), nullable=True),  # USER, WEBHOOK, SYSTEM
        # Details
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('aa_response', postgresql.JSONB(), nullable=True),
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['consent_id'], ['lms_aa_consent.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for lms_aa_consent_log
    op.create_index('ix_aa_consent_log_consent', 'lms_aa_consent_log', ['consent_id'])
    op.create_index('ix_aa_consent_log_event', 'lms_aa_consent_log', ['event_type'])
    op.create_index('ix_aa_consent_log_created', 'lms_aa_consent_log', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('lms_aa_consent_log')
    op.drop_table('lms_aa_bank_transaction')
    op.drop_table('lms_aa_bank_account')
    op.drop_table('lms_aa_fetch_session')
    op.drop_table('lms_aa_consent')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS aadatastatus")
    op.execute("DROP TYPE IF EXISTS aafetchsessionstatus")
    op.execute("DROP TYPE IF EXISTS aafitype")
    op.execute("DROP TYPE IF EXISTS aafetchfrequency")
    op.execute("DROP TYPE IF EXISTS aaconsentmode")
    op.execute("DROP TYPE IF EXISTS aaconsentpurpose")
    op.execute("DROP TYPE IF EXISTS aaconsentstatus")
    op.execute("DROP TYPE IF EXISTS aaprovider")
