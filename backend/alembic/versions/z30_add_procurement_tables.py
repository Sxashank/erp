"""Add Procurement module tables (RFQ, PO, GRN).

Revision ID: z30_procurement
Revises: z29_treasury_enhancement
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z30_procurement'
down_revision: Union[str, None] = 'z29_treasury_enhancement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rfq_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE rfq_status AS ENUM (
                'draft', 'published', 'open', 'closed', 'evaluation', 'awarded', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create po_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE po_status AS ENUM (
                'draft', 'pending_approval', 'approved', 'partially_received',
                'completed', 'cancelled', 'closed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create grn_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE grn_status AS ENUM (
                'draft', 'pending_qc', 'qc_approved', 'qc_rejected',
                'partial', 'complete', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create txn_rfq table
    op.create_table(
        'txn_rfq',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rfq_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('estimated_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('expected_delivery_date', sa.Date, nullable=True),
        sa.Column('delivery_location', sa.String(500), nullable=True),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('terms_conditions', sa.Text, nullable=True),
        sa.Column('vendor_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('quotation_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('awarded_vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('awarded_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('awarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('awarded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancellation_reason', sa.String(1000), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['awarded_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cancelled_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_rfq_org', 'txn_rfq', ['organization_id'])
    op.create_index('ix_txn_rfq_number', 'txn_rfq', ['rfq_number'], unique=True)
    op.create_index('ix_txn_rfq_status', 'txn_rfq', ['status'])
    op.create_index('ix_txn_rfq_dates', 'txn_rfq', ['start_date', 'end_date'])

    # Create txn_rfq_item table
    op.create_table(
        'txn_rfq_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(1000), nullable=False),
        sa.Column('specifications', sa.Text, nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('uom', sa.String(20), nullable=False),
        sa.Column('estimated_unit_price', sa.Numeric(15, 4), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['rfq_id'], ['txn_rfq.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_rfq_item_rfq', 'txn_rfq_item', ['rfq_id'])

    # Create txn_rfq_vendor table
    op.create_table(
        'txn_rfq_vendor',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('declined', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('declined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decline_reason', sa.String(500), nullable=True),
        sa.Column('quotation_submitted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('quotation_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['rfq_id'], ['txn_rfq.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_rfq_vendor_rfq', 'txn_rfq_vendor', ['rfq_id'])
    op.create_index('ix_txn_rfq_vendor_vendor', 'txn_rfq_vendor', ['vendor_id'])
    op.create_index('ix_txn_rfq_vendor_unique', 'txn_rfq_vendor', ['rfq_id', 'vendor_id'], unique=True)

    # Create txn_vendor_quotation table
    op.create_table(
        'txn_vendor_quotation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quotation_number', sa.String(50), nullable=False),
        sa.Column('quotation_date', sa.Date, nullable=False),
        sa.Column('validity_date', sa.Date, nullable=True),
        sa.Column('total_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('grand_total', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('delivery_days', sa.Integer, nullable=True),
        sa.Column('warranty_months', sa.Integer, nullable=True),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('is_shortlisted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_awarded', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('evaluation_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('evaluation_remarks', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['rfq_id'], ['txn_rfq.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_vendor_quotation_rfq', 'txn_vendor_quotation', ['rfq_id'])
    op.create_index('ix_txn_vendor_quotation_vendor', 'txn_vendor_quotation', ['vendor_id'])
    op.create_index('ix_txn_vendor_quotation_number', 'txn_vendor_quotation', ['quotation_number'])

    # Create txn_vendor_quotation_item table
    op.create_table(
        'txn_vendor_quotation_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rfq_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('tax_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('delivery_days', sa.Integer, nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['quotation_id'], ['txn_vendor_quotation.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rfq_item_id'], ['txn_rfq_item.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_vendor_quotation_item_quotation', 'txn_vendor_quotation_item', ['quotation_id'])
    op.create_index('ix_txn_vendor_quotation_item_rfq_item', 'txn_vendor_quotation_item', ['rfq_item_id'])

    # Create txn_purchase_order table
    op.create_table(
        'txn_purchase_order',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('po_number', sa.String(50), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('po_date', sa.Date, nullable=False),
        sa.Column('expected_delivery_date', sa.Date, nullable=True),
        sa.Column('delivery_location', sa.String(500), nullable=True),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('subtotal', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('discount_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('freight_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('total_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('grn_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('invoice_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('terms_conditions', sa.Text, nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_remarks', sa.String(1000), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.String(1000), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancellation_reason', sa.String(1000), nullable=True),
        sa.Column('vendor_acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('vendor_acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['rfq_id'], ['txn_rfq.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['txn_vendor_quotation.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rejected_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cancelled_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_purchase_order_org', 'txn_purchase_order', ['organization_id'])
    op.create_index('ix_txn_purchase_order_number', 'txn_purchase_order', ['po_number'], unique=True)
    op.create_index('ix_txn_purchase_order_vendor', 'txn_purchase_order', ['vendor_id'])
    op.create_index('ix_txn_purchase_order_status', 'txn_purchase_order', ['status'])
    op.create_index('ix_txn_purchase_order_date', 'txn_purchase_order', ['po_date'])

    # Create txn_purchase_order_item table
    op.create_table(
        'txn_purchase_order_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('po_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(1000), nullable=False),
        sa.Column('specifications', sa.Text, nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('uom', sa.String(20), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('tax_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('received_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('accepted_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('rejected_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('pending_qty', sa.Numeric(15, 4), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['po_id'], ['txn_purchase_order.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_purchase_order_item_po', 'txn_purchase_order_item', ['po_id'])

    # Create txn_grn table
    op.create_table(
        'txn_grn',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('grn_number', sa.String(50), nullable=False),
        sa.Column('po_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('received_date', sa.Date, nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_date', sa.Date, nullable=True),
        sa.Column('invoice_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('challan_number', sa.String(100), nullable=True),
        sa.Column('vehicle_number', sa.String(50), nullable=True),
        sa.Column('transport_mode', sa.String(50), nullable=True),
        sa.Column('total_items', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_received_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_accepted_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_rejected_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('qc_status', sa.String(20), nullable=True),
        sa.Column('qc_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qc_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('qc_remarks', sa.Text, nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('received_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_id'], ['txn_purchase_order.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['received_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['qc_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_grn_org', 'txn_grn', ['organization_id'])
    op.create_index('ix_txn_grn_number', 'txn_grn', ['grn_number'], unique=True)
    op.create_index('ix_txn_grn_po', 'txn_grn', ['po_id'])
    op.create_index('ix_txn_grn_vendor', 'txn_grn', ['vendor_id'])
    op.create_index('ix_txn_grn_status', 'txn_grn', ['status'])
    op.create_index('ix_txn_grn_date', 'txn_grn', ['received_date'])

    # Create txn_grn_item table
    op.create_table(
        'txn_grn_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('grn_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('po_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('received_qty', sa.Numeric(15, 4), nullable=False),
        sa.Column('accepted_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('rejected_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('serial_numbers', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('manufacturing_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('qc_status', sa.String(20), nullable=True),
        sa.Column('qc_remarks', sa.String(500), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['grn_id'], ['txn_grn.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_item_id'], ['txn_purchase_order_item.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_grn_item_grn', 'txn_grn_item', ['grn_id'])
    op.create_index('ix_txn_grn_item_po_item', 'txn_grn_item', ['po_item_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_grn_item')
    op.drop_table('txn_grn')
    op.drop_table('txn_purchase_order_item')
    op.drop_table('txn_purchase_order')
    op.drop_table('txn_vendor_quotation_item')
    op.drop_table('txn_vendor_quotation')
    op.drop_table('txn_rfq_vendor')
    op.drop_table('txn_rfq_item')
    op.drop_table('txn_rfq')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS grn_status")
    op.execute("DROP TYPE IF EXISTS po_status")
    op.execute("DROP TYPE IF EXISTS rfq_status")
