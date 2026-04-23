"""Add Credit Bureau integration tables.

Revision ID: z5_add_credit_bureau
Revises: z4_add_gstn_portal
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z5_add_credit_bureau'
down_revision = 'z4_add_gstn_portal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL with proper error handling for existing types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_bureau AS ENUM ('CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_pull_type AS ENUM ('SOFT', 'HARD');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_pull_status AS ENUM ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'NO_HIT', 'EXPIRED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_account_type AS ENUM ('HOME_LOAN', 'AUTO_LOAN', 'PERSONAL_LOAN', 'CREDIT_CARD', 'BUSINESS_LOAN', 'GOLD_LOAN', 'EDUCATION_LOAN', 'PROPERTY_LOAN', 'CONSUMER_LOAN', 'TWO_WHEELER_LOAN', 'OVERDRAFT', 'OTHER');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_account_status AS ENUM ('ACTIVE', 'CLOSED', 'WRITTEN_OFF', 'SETTLED', 'SUIT_FILED', 'WILLFUL_DEFAULT');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE account_ownership AS ENUM ('INDIVIDUAL', 'JOINT', 'AUTHORIZED_USER', 'GUARANTOR');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # Create lending_credit_pull table
    op.create_table(
        'lending_credit_pull',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('loan_application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bureau', postgresql.ENUM('CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF', name='credit_bureau', create_type=False), nullable=False),
        sa.Column('pull_type', postgresql.ENUM('SOFT', 'HARD', name='credit_pull_type', create_type=False), nullable=False, server_default='SOFT'),
        sa.Column('customer_name', sa.String(200), nullable=False),
        sa.Column('pan_number', sa.String(10), nullable=True),
        sa.Column('aadhaar_last4', sa.String(4), nullable=True),
        sa.Column('mobile_number', sa.String(15), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('request_reference', sa.String(100), nullable=True),
        sa.Column('bureau_reference', sa.String(100), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'NO_HIT', 'EXPIRED', name='credit_pull_status', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('credit_score', sa.Integer(), nullable=True),
        sa.Column('score_version', sa.String(50), nullable=True),
        sa.Column('score_date', sa.Date(), nullable=True),
        sa.Column('total_accounts', sa.Integer(), nullable=True),
        sa.Column('active_accounts', sa.Integer(), nullable=True),
        sa.Column('total_sanctioned', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_outstanding', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_overdue', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_dpd_last_12m', sa.Integer(), nullable=True),
        sa.Column('max_dpd_last_24m', sa.Integer(), nullable=True),
        sa.Column('enquiries_last_30d', sa.Integer(), nullable=True),
        sa.Column('enquiries_last_12m', sa.Integer(), nullable=True),
        sa.Column('report_data', postgresql.JSONB(), nullable=True),
        sa.Column('report_xml', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('pulled_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('pulled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purpose', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.ForeignKeyConstraint(['entity_id'], ['los_entity.id']),
        sa.ForeignKeyConstraint(['loan_application_id'], ['los_loan_application.id']),
        sa.ForeignKeyConstraint(['pulled_by'], ['mst_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lending_credit_pull_organization_id', 'lending_credit_pull', ['organization_id'])
    op.create_index('ix_lending_credit_pull_entity_id', 'lending_credit_pull', ['entity_id'])
    op.create_index('ix_lending_credit_pull_loan_application_id', 'lending_credit_pull', ['loan_application_id'])
    op.create_index('ix_credit_pull_pan', 'lending_credit_pull', ['pan_number'])
    op.create_index('ix_credit_pull_org_entity', 'lending_credit_pull', ['organization_id', 'entity_id'])
    op.create_index('ix_credit_pull_status', 'lending_credit_pull', ['status'])

    # Create lending_credit_account table
    op.create_table(
        'lending_credit_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credit_pull_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_number_masked', sa.String(50), nullable=True),
        sa.Column('bureau_account_id', sa.String(100), nullable=True),
        sa.Column('institution_name', sa.String(200), nullable=True),
        sa.Column('institution_type', sa.String(50), nullable=True),
        sa.Column('account_type', postgresql.ENUM('HOME_LOAN', 'AUTO_LOAN', 'PERSONAL_LOAN', 'CREDIT_CARD', 'BUSINESS_LOAN', 'GOLD_LOAN', 'EDUCATION_LOAN', 'PROPERTY_LOAN', 'CONSUMER_LOAN', 'TWO_WHEELER_LOAN', 'OVERDRAFT', 'OTHER', name='credit_account_type', create_type=False), nullable=False, server_default='OTHER'),
        sa.Column('account_status', postgresql.ENUM('ACTIVE', 'CLOSED', 'WRITTEN_OFF', 'SETTLED', 'SUIT_FILED', 'WILLFUL_DEFAULT', name='credit_account_status', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('ownership', postgresql.ENUM('INDIVIDUAL', 'JOINT', 'AUTHORIZED_USER', 'GUARANTOR', name='account_ownership', create_type=False), nullable=False, server_default='INDIVIDUAL'),
        sa.Column('sanctioned_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('current_balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('overdue_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('emi_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('credit_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('cash_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('high_credit', sa.Numeric(18, 2), nullable=True),
        sa.Column('write_off_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('opened_date', sa.Date(), nullable=True),
        sa.Column('closed_date', sa.Date(), nullable=True),
        sa.Column('last_payment_date', sa.Date(), nullable=True),
        sa.Column('reported_date', sa.Date(), nullable=True),
        sa.Column('payment_frequency', sa.String(20), nullable=True),
        sa.Column('tenure_months', sa.Integer(), nullable=True),
        sa.Column('remaining_tenure', sa.Integer(), nullable=True),
        sa.Column('dpd_history', postgresql.JSONB(), nullable=True),
        sa.Column('max_dpd', sa.Integer(), nullable=True),
        sa.Column('is_secured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_dispute', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['credit_pull_id'], ['lending_credit_pull.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lending_credit_account_credit_pull_id', 'lending_credit_account', ['credit_pull_id'])
    op.create_index('ix_credit_account_type_status', 'lending_credit_account', ['account_type', 'account_status'])

    # Create lending_credit_enquiry table
    op.create_table(
        'lending_credit_enquiry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credit_pull_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enquiry_date', sa.Date(), nullable=True),
        sa.Column('institution_name', sa.String(200), nullable=True),
        sa.Column('enquiry_purpose', sa.String(100), nullable=True),
        sa.Column('enquiry_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['credit_pull_id'], ['lending_credit_pull.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lending_credit_enquiry_credit_pull_id', 'lending_credit_enquiry', ['credit_pull_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('lending_credit_enquiry')
    op.drop_table('lending_credit_account')
    op.drop_table('lending_credit_pull')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS account_ownership")
    op.execute("DROP TYPE IF EXISTS credit_account_status")
    op.execute("DROP TYPE IF EXISTS credit_account_type")
    op.execute("DROP TYPE IF EXISTS credit_pull_status")
    op.execute("DROP TYPE IF EXISTS credit_pull_type")
    op.execute("DROP TYPE IF EXISTS credit_bureau")
