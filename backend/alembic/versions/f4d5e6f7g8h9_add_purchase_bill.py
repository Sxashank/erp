"""Add purchase bill tables.

Revision ID: f4d5e6f7g8h9
Revises: e3c4d5e6f7g8
Create Date: 2024-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4d5e6f7g8h9'
down_revision: Union[str, None] = 'e3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bill status enum
    bill_status_enum = postgresql.ENUM(
        'DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED',
        name='billstatus',
        create_type=False
    )
    bill_status_enum.create(op.get_bind(), checkfirst=True)

    # Create payment status enum
    payment_status_enum = postgresql.ENUM(
        'UNPAID', 'PARTIALLY_PAID', 'PAID',
        name='paymentstatus',
        create_type=False
    )
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    # Create supply type enum
    supply_type_enum = postgresql.ENUM(
        'INTRA_STATE', 'INTER_STATE',
        name='supplytype',
        create_type=False
    )
    supply_type_enum.create(op.get_bind(), checkfirst=True)

    # Create purchase bill table
    op.create_table(
        'txn_purchase_bill',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bill_number', sa.String(50), nullable=False),
        sa.Column('vendor_invoice_number', sa.String(100), nullable=True),
        sa.Column('vendor_invoice_date', sa.Date(), nullable=True),
        sa.Column('bill_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column('tds_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('round_off', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('balance_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),

        # GST Details
        sa.Column('is_reverse_charge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supply_type', postgresql.ENUM('INTRA_STATE', 'INTER_STATE', name='supplytype', create_type=False), nullable=True),
        sa.Column('vendor_gstin', sa.String(15), nullable=True),
        sa.Column('place_of_supply', sa.String(2), nullable=True),

        # Status & Workflow
        sa.Column('status', postgresql.ENUM('DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED', name='billstatus', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('payment_status', postgresql.ENUM('UNPAID', 'PARTIALLY_PAID', 'PAID', name='paymentstatus', create_type=False), nullable=False, server_default='UNPAID'),

        # GL Integration
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_posted', sa.Boolean(), nullable=False, server_default='false'),

        # Narration & Reference
        sa.Column('narration', sa.Text(), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True),

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
        sa.ForeignKeyConstraint(['vendor_id'], ['mst_vendor.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for purchase bill
    op.create_index('ix_txn_purchase_bill_bill_number', 'txn_purchase_bill', ['bill_number'])
    op.create_index('ix_txn_purchase_bill_organization_id', 'txn_purchase_bill', ['organization_id'])
    op.create_index('ix_txn_purchase_bill_vendor_id', 'txn_purchase_bill', ['vendor_id'])
    op.create_index('ix_txn_purchase_bill_bill_date', 'txn_purchase_bill', ['bill_date'])
    op.create_index('ix_txn_purchase_bill_due_date', 'txn_purchase_bill', ['due_date'])
    op.create_index('ix_txn_purchase_bill_status', 'txn_purchase_bill', ['status'])
    op.create_index('ix_txn_purchase_bill_payment_status', 'txn_purchase_bill', ['payment_status'])

    # Create unique constraint for bill number within organization
    op.create_unique_constraint('uq_purchase_bill_org_number', 'txn_purchase_bill', ['organization_id', 'bill_number'])

    # Create purchase bill line table
    op.create_table(
        'txn_purchase_bill_line',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bill_id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(['bill_id'], ['txn_purchase_bill.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gst_rate_id'], ['mst_gst_rate.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['expense_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for purchase bill line
    op.create_index('ix_txn_purchase_bill_line_bill_id', 'txn_purchase_bill_line', ['bill_id'])


def downgrade() -> None:
    # Drop purchase bill line indexes and table
    op.drop_index('ix_txn_purchase_bill_line_bill_id', table_name='txn_purchase_bill_line')
    op.drop_table('txn_purchase_bill_line')

    # Drop purchase bill indexes
    op.drop_index('ix_txn_purchase_bill_payment_status', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_status', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_due_date', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_bill_date', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_vendor_id', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_organization_id', table_name='txn_purchase_bill')
    op.drop_index('ix_txn_purchase_bill_bill_number', table_name='txn_purchase_bill')

    # Drop unique constraint
    op.drop_constraint('uq_purchase_bill_org_number', 'txn_purchase_bill', type_='unique')

    # Drop purchase bill table
    op.drop_table('txn_purchase_bill')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS supplytype')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS billstatus')
