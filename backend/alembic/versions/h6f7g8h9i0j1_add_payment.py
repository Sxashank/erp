"""Add payment tables.

Revision ID: h6f7g8h9i0j1
Revises: g5e6f7g8h9i0
Create Date: 2024-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h6f7g8h9i0j1'
down_revision: Union[str, None] = 'g5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums using raw SQL with DO block for idempotency
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymenttype AS ENUM ('VENDOR_PAYMENT', 'CUSTOMER_RECEIPT', 'ADVANCE_PAYMENT', 'ADVANCE_RECEIPT', 'REFUND_PAYMENT', 'REFUND_RECEIPT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE partytype AS ENUM ('VENDOR', 'CUSTOMER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentmode AS ENUM ('CASH', 'CHEQUE', 'NEFT', 'RTGS', 'IMPS', 'UPI', 'BANK_TRANSFER', 'DEMAND_DRAFT', 'CREDIT_CARD', 'DEBIT_CARD');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentstatus AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'POSTED', 'CANCELLED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chequestatus AS ENUM ('ISSUED', 'DEPOSITED', 'CLEARED', 'BOUNCED', 'CANCELLED', 'RETURNED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documenttype AS ENUM ('PURCHASE_BILL', 'SALES_INVOICE', 'DEBIT_NOTE', 'CREDIT_NOTE', 'ADVANCE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create txn_payment table
    op.create_table(
        'txn_payment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),

        # Basic Info
        sa.Column('payment_number', sa.String(50), nullable=False, index=True),
        sa.Column('payment_date', sa.Date, nullable=False, index=True),
        sa.Column('payment_type', postgresql.ENUM(
            'VENDOR_PAYMENT', 'CUSTOMER_RECEIPT', 'ADVANCE_PAYMENT',
            'ADVANCE_RECEIPT', 'REFUND_PAYMENT', 'REFUND_RECEIPT',
            name='paymenttype', create_type=False
        ), nullable=False, index=True),

        # Party Info
        sa.Column('party_type', postgresql.ENUM('VENDOR', 'CUSTOMER', name='partytype', create_type=False), nullable=False, index=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=True, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_customer.id'), nullable=True, index=True),

        # Organization & Unit
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False, index=True),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_unit.id'), nullable=True),

        # Payment Details
        sa.Column('payment_mode', postgresql.ENUM(
            'CASH', 'CHEQUE', 'NEFT', 'RTGS', 'IMPS', 'UPI',
            'BANK_TRANSFER', 'DEMAND_DRAFT', 'CREDIT_CARD', 'DEBIT_CARD',
            name='paymentmode', create_type=False
        ), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id'), nullable=True),
        sa.Column('cash_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id'), nullable=True),

        # Amounts
        sa.Column('amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('tds_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('tds_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_tds_section.id'), nullable=True),
        sa.Column('tds_rate', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('write_off_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('currency_code', sa.String(3), nullable=False, default='INR'),
        sa.Column('exchange_rate', sa.Numeric(12, 6), nullable=False, default=1),

        # Cheque Details
        sa.Column('cheque_number', sa.String(20), nullable=True),
        sa.Column('cheque_date', sa.Date, nullable=True),
        sa.Column('cheque_bank_name', sa.String(100), nullable=True),
        sa.Column('cheque_branch', sa.String(100), nullable=True),
        sa.Column('cheque_status', postgresql.ENUM(
            'ISSUED', 'DEPOSITED', 'CLEARED', 'BOUNCED', 'CANCELLED', 'RETURNED',
            name='chequestatus', create_type=False
        ), nullable=True),
        sa.Column('cheque_cleared_date', sa.Date, nullable=True),
        sa.Column('cheque_bounced_date', sa.Date, nullable=True),
        sa.Column('cheque_bounced_reason', sa.String(200), nullable=True),

        # Transaction Reference
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('narration', sa.Text, nullable=True),

        # Status & Workflow
        sa.Column('status', postgresql.ENUM(
            'DRAFT', 'SUBMITTED', 'APPROVED', 'POSTED', 'CANCELLED',
            name='paymentstatus', create_type=False
        ), nullable=False, default='DRAFT', index=True),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime, nullable=True),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('cancellation_reason', sa.String(500), nullable=True),

        # GL Integration
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id'), nullable=True),
        sa.Column('is_posted', sa.Boolean, nullable=False, default=False),
        sa.Column('posted_at', sa.DateTime, nullable=True),
        sa.Column('posted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),

        # Audit fields
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(party_type = 'VENDOR' AND vendor_id IS NOT NULL AND customer_id IS NULL) OR "
            "(party_type = 'CUSTOMER' AND customer_id IS NOT NULL AND vendor_id IS NULL)",
            name='ck_payment_party_consistency'
        ),
    )

    # Create indexes
    op.create_index('ix_txn_payment_org_date', 'txn_payment', ['organization_id', 'payment_date'])
    op.create_index('ix_txn_payment_party', 'txn_payment', ['party_type', 'vendor_id', 'customer_id'])

    # Create txn_payment_allocation table
    op.create_table(
        'txn_payment_allocation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_payment.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('document_type', postgresql.ENUM(
            'PURCHASE_BILL', 'SALES_INVOICE', 'DEBIT_NOTE', 'CREDIT_NOTE', 'ADVANCE',
            name='documenttype', create_type=False
        ), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('document_number', sa.String(50), nullable=False),
        sa.Column('document_date', sa.Date, nullable=False),
        sa.Column('document_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('outstanding_before', sa.Numeric(18, 2), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('allocation_date', sa.Date, nullable=False),

        # Audit fields
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('allocated_amount > 0', name='ck_allocation_positive_amount'),
    )

    # Create index for document lookup
    op.create_index('ix_payment_allocation_doc', 'txn_payment_allocation', ['document_type', 'document_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_payment_allocation_doc', table_name='txn_payment_allocation')
    op.drop_table('txn_payment_allocation')

    op.drop_index('ix_txn_payment_party', table_name='txn_payment')
    op.drop_index('ix_txn_payment_org_date', table_name='txn_payment')
    op.drop_table('txn_payment')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS documenttype')
    op.execute('DROP TYPE IF EXISTS chequestatus')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymentmode')
    op.execute('DROP TYPE IF EXISTS partytype')
    op.execute('DROP TYPE IF EXISTS paymenttype')
