"""Add sales invoice tables.

Revision ID: g5e6f7g8h9i0
Revises: f4d5e6f7g8h9
Create Date: 2024-01-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g5e6f7g8h9i0'
down_revision: Union[str, None] = 'f4d5e6f7g8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create invoice status enum
    invoice_status_enum = postgresql.ENUM(
        'DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED',
        name='invoicestatus',
        create_type=False
    )
    invoice_status_enum.create(op.get_bind(), checkfirst=True)

    # Create receipt status enum
    receipt_status_enum = postgresql.ENUM(
        'UNRECEIVED', 'PARTIALLY_RECEIVED', 'RECEIVED',
        name='receiptstatus',
        create_type=False
    )
    receipt_status_enum.create(op.get_bind(), checkfirst=True)

    # Create invoice supply type enum
    invoice_supply_type_enum = postgresql.ENUM(
        'INTRA_STATE', 'INTER_STATE', 'EXPORT', 'SEZ',
        name='invoicesupplytype',
        create_type=False
    )
    invoice_supply_type_enum.create(op.get_bind(), checkfirst=True)

    # Create e-invoice status enum
    e_invoice_status_enum = postgresql.ENUM(
        'NOT_APPLICABLE', 'PENDING', 'GENERATED', 'CANCELLED',
        name='einvoicestatus',
        create_type=False
    )
    e_invoice_status_enum.create(op.get_bind(), checkfirst=True)

    # Create sales invoice table
    op.create_table(
        'txn_sales_invoice',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Amounts
        sa.Column('subtotal', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('taxable_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('cgst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('sgst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('igst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('cess_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('tcs_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('round_off', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('balance_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),

        # GST Details
        sa.Column('is_reverse_charge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supply_type', postgresql.ENUM('INTRA_STATE', 'INTER_STATE', 'EXPORT', 'SEZ', name='invoicesupplytype', create_type=False), nullable=True),
        sa.Column('customer_gstin', sa.String(15), nullable=True),
        sa.Column('place_of_supply', sa.String(2), nullable=True),

        # E-Invoice Details
        sa.Column('e_invoice_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('irn', sa.String(64), nullable=True),
        sa.Column('irn_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qr_code', sa.Text(), nullable=True),
        sa.Column('e_invoice_status', postgresql.ENUM('NOT_APPLICABLE', 'PENDING', 'GENERATED', 'CANCELLED', name='einvoicestatus', create_type=False), nullable=False, server_default='NOT_APPLICABLE'),
        sa.Column('ack_number', sa.String(50), nullable=True),
        sa.Column('ack_date', sa.DateTime(timezone=True), nullable=True),

        # Status & Workflow
        sa.Column('status', postgresql.ENUM('DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED', name='invoicestatus', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('receipt_status', postgresql.ENUM('UNRECEIVED', 'PARTIALLY_RECEIVED', 'RECEIVED', name='receiptstatus', create_type=False), nullable=False, server_default='UNRECEIVED'),

        # GL Integration
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_posted', sa.Boolean(), nullable=False, server_default='false'),

        # Narration & Reference
        sa.Column('narration', sa.Text(), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('po_number', sa.String(100), nullable=True),
        sa.Column('po_date', sa.Date(), nullable=True),

        # Shipping Details
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('transporter_name', sa.String(200), nullable=True),
        sa.Column('vehicle_number', sa.String(20), nullable=True),
        sa.Column('eway_bill_number', sa.String(20), nullable=True),
        sa.Column('eway_bill_date', sa.Date(), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['customer_id'], ['mst_customer.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for sales invoice
    op.create_index('ix_txn_sales_invoice_invoice_number', 'txn_sales_invoice', ['invoice_number'])
    op.create_index('ix_txn_sales_invoice_organization_id', 'txn_sales_invoice', ['organization_id'])
    op.create_index('ix_txn_sales_invoice_customer_id', 'txn_sales_invoice', ['customer_id'])
    op.create_index('ix_txn_sales_invoice_invoice_date', 'txn_sales_invoice', ['invoice_date'])
    op.create_index('ix_txn_sales_invoice_due_date', 'txn_sales_invoice', ['due_date'])
    op.create_index('ix_txn_sales_invoice_status', 'txn_sales_invoice', ['status'])
    op.create_index('ix_txn_sales_invoice_receipt_status', 'txn_sales_invoice', ['receipt_status'])

    # Create unique constraint for invoice number within organization
    op.create_unique_constraint('uq_sales_invoice_org_number', 'txn_sales_invoice', ['organization_id', 'invoice_number'])

    # Create sales invoice line table
    op.create_table(
        'txn_sales_invoice_line',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('hsn_sac_code', sa.String(20), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('taxable_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('gst_rate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cgst_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('cgst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('sgst_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('sgst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('igst_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('igst_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('cess_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('cess_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('revenue_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['invoice_id'], ['txn_sales_invoice.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_rate_id'], ['mst_gst_rate.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['revenue_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for sales invoice line
    op.create_index('ix_txn_sales_invoice_line_invoice_id', 'txn_sales_invoice_line', ['invoice_id'])


def downgrade() -> None:
    # Drop sales invoice line indexes and table
    op.drop_index('ix_txn_sales_invoice_line_invoice_id', table_name='txn_sales_invoice_line')
    op.drop_table('txn_sales_invoice_line')

    # Drop sales invoice indexes
    op.drop_index('ix_txn_sales_invoice_receipt_status', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_status', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_due_date', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_invoice_date', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_customer_id', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_organization_id', table_name='txn_sales_invoice')
    op.drop_index('ix_txn_sales_invoice_invoice_number', table_name='txn_sales_invoice')

    # Drop unique constraint
    op.drop_constraint('uq_sales_invoice_org_number', 'txn_sales_invoice', type_='unique')

    # Drop sales invoice table
    op.drop_table('txn_sales_invoice')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS einvoicestatus')
    op.execute('DROP TYPE IF EXISTS invoicesupplytype')
    op.execute('DROP TYPE IF EXISTS receiptstatus')
    op.execute('DROP TYPE IF EXISTS invoicestatus')
