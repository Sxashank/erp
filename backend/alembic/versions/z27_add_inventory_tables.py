"""Add Inventory module tables.

Revision ID: z27_inventory
Revises: z26_dms
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z27_inventory'
down_revision: Union[str, None] = 'z26_dms'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create inventory_transaction_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE inventory_transaction_type AS ENUM (
                'stock_in', 'stock_out', 'transfer_in', 'transfer_out',
                'adjustment_positive', 'adjustment_negative', 'return', 'damage'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create inventory_valuation_method enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE inventory_valuation_method AS ENUM ('fifo', 'lifo', 'weighted_average', 'standard');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create mst_item_category table
    op.create_table(
        'mst_item_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('level', sa.Integer, nullable=False, server_default='0'),
        sa.Column('path', sa.String(500), nullable=True),
        sa.Column('hsn_code', sa.String(20), nullable=True),
        sa.Column('default_tax_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('valuation_method', sa.String(20), nullable=True, server_default='weighted_average'),
        sa.Column('item_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['mst_item_category.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_item_category_org', 'mst_item_category', ['organization_id'])
    op.create_index('ix_mst_item_category_code', 'mst_item_category', ['organization_id', 'code'], unique=True)
    op.create_index('ix_mst_item_category_parent', 'mst_item_category', ['parent_id'])

    # Create mst_warehouse table
    op.create_table(
        'mst_warehouse',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('warehouse_type', sa.String(50), nullable=True),
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True, server_default='India'),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('total_capacity', sa.Numeric(15, 2), nullable=True),
        sa.Column('capacity_uom', sa.String(20), nullable=True),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_warehouse_org', 'mst_warehouse', ['organization_id'])
    op.create_index('ix_mst_warehouse_code', 'mst_warehouse', ['organization_id', 'code'], unique=True)

    # Create mst_item_master table
    op.create_table(
        'mst_item_master',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('item_type', sa.String(50), nullable=False, server_default='stock'),
        sa.Column('primary_uom', sa.String(20), nullable=False),
        sa.Column('secondary_uom', sa.String(20), nullable=True),
        sa.Column('conversion_factor', sa.Numeric(10, 4), nullable=True),
        sa.Column('hsn_code', sa.String(20), nullable=True),
        sa.Column('sac_code', sa.String(20), nullable=True),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('manufacturer', sa.String(255), nullable=True),
        sa.Column('standard_cost', sa.Numeric(15, 4), nullable=True),
        sa.Column('selling_price', sa.Numeric(15, 4), nullable=True),
        sa.Column('minimum_stock', sa.Numeric(15, 4), nullable=True),
        sa.Column('maximum_stock', sa.Numeric(15, 4), nullable=True),
        sa.Column('reorder_level', sa.Numeric(15, 4), nullable=True),
        sa.Column('reorder_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('lead_time_days', sa.Integer, nullable=True),
        sa.Column('shelf_life_days', sa.Integer, nullable=True),
        sa.Column('is_serialized', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_batch_tracked', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_perishable', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('gst_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('valuation_method', sa.String(20), nullable=True),
        sa.Column('specifications', postgresql.JSONB, nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['mst_item_category.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_item_master_org', 'mst_item_master', ['organization_id'])
    op.create_index('ix_mst_item_master_code', 'mst_item_master', ['organization_id', 'code'], unique=True)
    op.create_index('ix_mst_item_master_category', 'mst_item_master', ['category_id'])
    op.create_index('ix_mst_item_master_sku', 'mst_item_master', ['sku'])
    op.create_index('ix_mst_item_master_barcode', 'mst_item_master', ['barcode'])

    # Create txn_stock_balance table
    op.create_table(
        'txn_stock_balance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('reserved_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('available_qty', sa.Numeric(15, 4), nullable=False, server_default='0'),
        sa.Column('unit_cost', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('manufacturing_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('last_transaction_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['mst_item_master.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['mst_warehouse.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_stock_balance_org', 'txn_stock_balance', ['organization_id'])
    op.create_index('ix_txn_stock_balance_item_warehouse', 'txn_stock_balance', ['item_id', 'warehouse_id'])
    op.create_index('ix_txn_stock_balance_batch', 'txn_stock_balance', ['batch_number'])
    op.create_index('ix_txn_stock_balance_expiry', 'txn_stock_balance', ['expiry_date'])

    # Create txn_stock_transaction table
    op.create_table(
        'txn_stock_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_number', sa.String(50), nullable=False),
        sa.Column('transaction_type', sa.String(30), nullable=False),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('balance_before', sa.Numeric(15, 4), nullable=True),
        sa.Column('balance_after', sa.Numeric(15, 4), nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('is_posted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['mst_item_master.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['mst_warehouse.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_stock_transaction_org', 'txn_stock_transaction', ['organization_id'])
    op.create_index('ix_txn_stock_transaction_number', 'txn_stock_transaction', ['transaction_number'])
    op.create_index('ix_txn_stock_transaction_type', 'txn_stock_transaction', ['transaction_type'])
    op.create_index('ix_txn_stock_transaction_item', 'txn_stock_transaction', ['item_id'])
    op.create_index('ix_txn_stock_transaction_warehouse', 'txn_stock_transaction', ['warehouse_id'])
    op.create_index('ix_txn_stock_transaction_date', 'txn_stock_transaction', ['transaction_date'])
    op.create_index('ix_txn_stock_transaction_reference', 'txn_stock_transaction', ['reference_type', 'reference_id'])

    # Create txn_stock_transfer table
    op.create_table(
        'txn_stock_transfer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transfer_number', sa.String(50), nullable=False),
        sa.Column('transfer_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('from_warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('total_items', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_quantity', sa.Numeric(15, 4), nullable=True),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dispatched_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_warehouse_id'], ['mst_warehouse.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_warehouse_id'], ['mst_warehouse.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['initiated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dispatched_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_stock_transfer_org', 'txn_stock_transfer', ['organization_id'])
    op.create_index('ix_txn_stock_transfer_number', 'txn_stock_transfer', ['transfer_number'], unique=True)
    op.create_index('ix_txn_stock_transfer_status', 'txn_stock_transfer', ['status'])

    # Create txn_stock_transfer_item table
    op.create_table(
        'txn_stock_transfer_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('transfer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('requested_qty', sa.Numeric(15, 4), nullable=False),
        sa.Column('dispatched_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('received_qty', sa.Numeric(15, 4), nullable=True),
        sa.Column('unit_cost', sa.Numeric(15, 4), nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['transfer_id'], ['txn_stock_transfer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['mst_item_master.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_stock_transfer_item_transfer', 'txn_stock_transfer_item', ['transfer_id'])
    op.create_index('ix_txn_stock_transfer_item_item', 'txn_stock_transfer_item', ['item_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_stock_transfer_item')
    op.drop_table('txn_stock_transfer')
    op.drop_table('txn_stock_transaction')
    op.drop_table('txn_stock_balance')
    op.drop_table('mst_item_master')
    op.drop_table('mst_warehouse')
    op.drop_table('mst_item_category')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS inventory_valuation_method")
    op.execute("DROP TYPE IF EXISTS inventory_transaction_type")
