"""Add GSTN Portal integration tables.

Revision ID: z4_add_gstn_portal
Revises: z3_add_account_aggregator_tables
Create Date: 2024-01-14

Tables created:
- gst_gstn_session: GSTN API session management
- gst_return_filing: GST return filing records
- gst_itc_mismatch: ITC reconciliation mismatches
- gst_gstr2b_data: Cached GSTR-2B invoice data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z4_add_gstn_portal'
down_revision = 'z3_add_account_aggregator_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL with proper error handling for existing types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gstreturntype AS ENUM ('GSTR1', 'GSTR2A', 'GSTR2B', 'GSTR3B', 'GSTR4', 'GSTR9', 'GSTR9C');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gstreturnstatus AS ENUM ('NOT_STARTED', 'DRAFT', 'VALIDATED', 'SUBMITTED', 'FILED', 'PENDING_PAYMENT', 'PAYMENT_DONE', 'ERROR');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gstnsessionstatus AS ENUM ('ACTIVE', 'OTP_PENDING', 'EXPIRED', 'INVALID');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE itcmismatchtype AS ENUM ('MISSING_IN_2B', 'MISSING_IN_BOOKS', 'AMOUNT_MISMATCH', 'GSTIN_MISMATCH', 'DATE_MISMATCH');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE itcmismatchresolution AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'SUPPLIER_ACTION', 'IGNORED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create gst_gstn_session table
    op.create_table(
        'gst_gstn_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gst_registration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gstin', sa.String(15), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'OTP_PENDING', 'EXPIRED', 'INVALID',
                                     name='gstnsessionstatus', create_type=False), nullable=False),
        sa.Column('auth_token', sa.Text, nullable=True),
        sa.Column('sek_key', sa.Text, nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('otp_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('otp_reference', sa.String(100), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_registration_id'], ['mst_gst_registration.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['initiated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_gstn_session_org_id', 'gst_gstn_session', ['organization_id'])
    op.create_index('ix_gstn_session_gst_reg_id', 'gst_gstn_session', ['gst_registration_id'])
    op.create_index('ix_gstn_session_gstin', 'gst_gstn_session', ['gstin'])
    op.create_index('ix_gstn_session_org_gstin', 'gst_gstn_session', ['organization_id', 'gstin'])
    op.create_index('ix_gstn_session_status_expires', 'gst_gstn_session', ['status', 'token_expires_at'])

    # Create gst_return_filing table
    op.create_table(
        'gst_return_filing',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gst_registration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gstin', sa.String(15), nullable=False),
        sa.Column('return_type', postgresql.ENUM('GSTR1', 'GSTR2A', 'GSTR2B', 'GSTR3B', 'GSTR4', 'GSTR9', 'GSTR9C',
                                          name='gstreturntype', create_type=False), nullable=False),
        sa.Column('return_period', sa.String(10), nullable=False),
        sa.Column('financial_year', sa.String(10), nullable=False),
        sa.Column('status', postgresql.ENUM('NOT_STARTED', 'DRAFT', 'VALIDATED', 'SUBMITTED', 'FILED',
                                     'PENDING_PAYMENT', 'PAYMENT_DONE', 'ERROR',
                                     name='gstreturnstatus', create_type=False), nullable=False),
        sa.Column('arn', sa.String(50), nullable=True),
        sa.Column('filing_date', sa.Date, nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('total_taxable_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_igst', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_cgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_sgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_cess', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_tax_liability', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_itc_claimed', sa.Numeric(18, 2), nullable=True),
        sa.Column('cash_payment', sa.Numeric(18, 2), nullable=True),
        sa.Column('invoice_count', sa.Integer, nullable=False, default=0),
        sa.Column('b2b_invoice_count', sa.Integer, nullable=False, default=0),
        sa.Column('b2c_invoice_count', sa.Integer, nullable=False, default=0),
        sa.Column('cdn_count', sa.Integer, nullable=False, default=0),
        sa.Column('summary_data', postgresql.JSONB, nullable=True),
        sa.Column('section_wise_data', postgresql.JSONB, nullable=True),
        sa.Column('error_details', postgresql.JSONB, nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('filed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prepared_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gstn_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('late_fee', sa.Numeric(18, 2), nullable=True),
        sa.Column('interest', sa.Numeric(18, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_registration_id'], ['mst_gst_registration.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prepared_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submitted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gstn_session_id'], ['gst_gstn_session.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'gstin', 'return_type', 'return_period',
                           name='uq_gst_return_filing_period'),
    )
    op.create_index('ix_gst_return_filing_org_id', 'gst_return_filing', ['organization_id'])
    op.create_index('ix_gst_return_filing_gst_reg_id', 'gst_return_filing', ['gst_registration_id'])
    op.create_index('ix_gst_return_filing_gstin', 'gst_return_filing', ['gstin'])
    op.create_index('ix_gst_return_filing_type', 'gst_return_filing', ['return_type'])
    op.create_index('ix_gst_return_filing_period', 'gst_return_filing', ['organization_id', 'return_period'])
    op.create_index('ix_gst_return_filing_type_status', 'gst_return_filing', ['return_type', 'status'])
    op.create_index('ix_gst_return_filing_arn', 'gst_return_filing', ['arn'])

    # Create gst_itc_mismatch table
    op.create_table(
        'gst_itc_mismatch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gst_registration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('return_period', sa.String(10), nullable=False),
        sa.Column('supplier_gstin', sa.String(15), nullable=False),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.Date, nullable=True),
        sa.Column('mismatch_type', postgresql.ENUM('MISSING_IN_2B', 'MISSING_IN_BOOKS', 'AMOUNT_MISMATCH',
                                           'GSTIN_MISMATCH', 'DATE_MISMATCH',
                                           name='itcmismatchtype', create_type=False), nullable=False),
        sa.Column('books_taxable_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('books_igst', sa.Numeric(18, 2), nullable=True),
        sa.Column('books_cgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('books_sgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('books_cess', sa.Numeric(18, 2), nullable=True),
        sa.Column('books_total_tax', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_taxable_value', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_igst', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_cgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_sgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_cess', sa.Numeric(18, 2), nullable=True),
        sa.Column('gstr2b_total_tax', sa.Numeric(18, 2), nullable=True),
        sa.Column('variance_taxable', sa.Numeric(18, 2), nullable=True),
        sa.Column('variance_igst', sa.Numeric(18, 2), nullable=True),
        sa.Column('variance_cgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('variance_sgst', sa.Numeric(18, 2), nullable=True),
        sa.Column('variance_total', sa.Numeric(18, 2), nullable=True),
        sa.Column('resolution_status', postgresql.ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'SUPPLIER_ACTION', 'IGNORED',
                                                name='itcmismatchresolution', create_type=False), nullable=False),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purchase_bill_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gstr2b_raw_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_registration_id'], ['mst_gst_registration.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['purchase_bill_id'], ['txn_purchase_bill.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_itc_mismatch_org_id', 'gst_itc_mismatch', ['organization_id'])
    op.create_index('ix_itc_mismatch_gst_reg_id', 'gst_itc_mismatch', ['gst_registration_id'])
    op.create_index('ix_itc_mismatch_period', 'gst_itc_mismatch', ['return_period'])
    op.create_index('ix_itc_mismatch_supplier', 'gst_itc_mismatch', ['supplier_gstin'])
    op.create_index('ix_itc_mismatch_period_supplier', 'gst_itc_mismatch', ['return_period', 'supplier_gstin'])
    op.create_index('ix_itc_mismatch_resolution', 'gst_itc_mismatch', ['organization_id', 'resolution_status'])
    op.create_index('ix_itc_mismatch_type', 'gst_itc_mismatch', ['organization_id', 'mismatch_type'])
    op.create_index('ix_itc_mismatch_purchase_bill', 'gst_itc_mismatch', ['purchase_bill_id'])

    # Create gst_gstr2b_data table
    op.create_table(
        'gst_gstr2b_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gst_registration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('return_period', sa.String(10), nullable=False),
        sa.Column('supplier_gstin', sa.String(15), nullable=False),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('supplier_filing_status', sa.String(20), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.Date, nullable=False),
        sa.Column('invoice_type', sa.String(10), nullable=False),
        sa.Column('place_of_supply', sa.String(2), nullable=True),
        sa.Column('reverse_charge', sa.Boolean, nullable=False, default=False),
        sa.Column('taxable_value', sa.Numeric(18, 2), nullable=False),
        sa.Column('igst', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('cgst', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('sgst', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('cess', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('itc_eligible', sa.Boolean, nullable=False, default=True),
        sa.Column('itc_claimed', sa.Boolean, nullable=False, default=False),
        sa.Column('is_matched', sa.Boolean, nullable=False, default=False),
        sa.Column('matched_purchase_bill_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('source_section', sa.String(20), nullable=True),
        sa.Column('raw_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_registration_id'], ['mst_gst_registration.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_purchase_bill_id'], ['txn_purchase_bill.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'return_period', 'supplier_gstin', 'invoice_number',
                           name='uq_gstr2b_invoice'),
    )
    op.create_index('ix_gstr2b_org_id', 'gst_gstr2b_data', ['organization_id'])
    op.create_index('ix_gstr2b_gst_reg_id', 'gst_gstr2b_data', ['gst_registration_id'])
    op.create_index('ix_gstr2b_period', 'gst_gstr2b_data', ['return_period'])
    op.create_index('ix_gstr2b_supplier', 'gst_gstr2b_data', ['supplier_gstin'])
    op.create_index('ix_gstr2b_period_gstin', 'gst_gstr2b_data', ['organization_id', 'return_period'])
    op.create_index('ix_gstr2b_supplier_period', 'gst_gstr2b_data', ['supplier_gstin', 'return_period'])
    op.create_index('ix_gstr2b_matched', 'gst_gstr2b_data', ['organization_id', 'is_matched'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('gst_gstr2b_data')
    op.drop_table('gst_itc_mismatch')
    op.drop_table('gst_return_filing')
    op.drop_table('gst_gstn_session')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS itcmismatchresolution')
    op.execute('DROP TYPE IF EXISTS itcmismatchtype')
    op.execute('DROP TYPE IF EXISTS gstnsessionstatus')
    op.execute('DROP TYPE IF EXISTS gstreturnstatus')
    op.execute('DROP TYPE IF EXISTS gstreturntype')
