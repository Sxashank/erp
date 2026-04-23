"""Add customer master table.

Revision ID: e3c4d5e6f7g8
Revises: d2b3c4d5e6f7
Create Date: 2024-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e3c4d5e6f7g8'
down_revision: Union[str, None] = 'd2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create customer type enum
    customer_type_enum = postgresql.ENUM(
        'INDIVIDUAL', 'COMPANY', 'GOVERNMENT', 'OTHERS',
        name='customertype',
        create_type=False
    )
    customer_type_enum.create(op.get_bind(), checkfirst=True)

    # Create customer table
    op.create_table(
        'mst_customer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('customer_type', postgresql.ENUM('INDIVIDUAL', 'COMPANY', 'GOVERNMENT', 'OTHERS', name='customertype', create_type=False), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Tax & Compliance
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('gst_registration_type', postgresql.ENUM('REGULAR', 'COMPOSITION', 'UNREGISTERED', 'SEZ', 'DEEMED_EXPORT', 'OVERSEAS', name='gstregistrationtype', create_type=False), nullable=True),
        sa.Column('place_of_supply_state', sa.String(2), nullable=True),
        sa.Column('tcs_applicable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tcs_section_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Contact & Billing Address
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('mobile', sa.String(20), nullable=True),
        sa.Column('billing_address_line1', sa.String(200), nullable=True),
        sa.Column('billing_address_line2', sa.String(200), nullable=True),
        sa.Column('billing_city', sa.String(100), nullable=True),
        sa.Column('billing_state_code', sa.String(2), nullable=True),
        sa.Column('billing_pincode', sa.String(10), nullable=True),
        sa.Column('billing_country', sa.String(50), nullable=False, server_default='India'),

        # Shipping Address
        sa.Column('shipping_address_line1', sa.String(200), nullable=True),
        sa.Column('shipping_address_line2', sa.String(200), nullable=True),
        sa.Column('shipping_city', sa.String(100), nullable=True),
        sa.Column('shipping_state_code', sa.String(2), nullable=True),
        sa.Column('shipping_pincode', sa.String(10), nullable=True),
        sa.Column('shipping_country', sa.String(50), nullable=False, server_default='India'),

        # Banking Details
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_account_number', sa.String(50), nullable=True),
        sa.Column('bank_ifsc_code', sa.String(11), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('payment_mode_preference', postgresql.ENUM('CASH', 'CHEQUE', 'NEFT', 'RTGS', 'UPI', 'BANK_TRANSFER', name='paymentmodepreference', create_type=False), nullable=True),

        # Financial Settings
        sa.Column('control_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revenue_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payment_terms_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('credit_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('credit_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('credit_limit_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('currency_code', sa.String(3), nullable=False, server_default='INR'),

        # Balances
        sa.Column('opening_balance', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('opening_balance_type', postgresql.ENUM('DR', 'CR', name='balancetype', create_type=False), nullable=True),
        sa.Column('current_balance', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('current_balance_type', postgresql.ENUM('DR', 'CR', name='balancetype', create_type=False), nullable=True),

        # Notes
        sa.Column('remarks', sa.Text(), nullable=True),

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
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tcs_section_id'], ['mst_tds_section.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['control_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['revenue_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_terms_id'], ['mst_payment_terms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_mst_customer_code', 'mst_customer', ['code'])
    op.create_index('ix_mst_customer_organization_id', 'mst_customer', ['organization_id'])
    op.create_index('ix_mst_customer_name', 'mst_customer', ['name'])
    op.create_index('ix_mst_customer_gstin', 'mst_customer', ['gstin'])
    op.create_index('ix_mst_customer_is_active', 'mst_customer', ['is_active'])

    # Create unique constraint for code within organization
    op.create_unique_constraint('uq_customer_org_code', 'mst_customer', ['organization_id', 'code'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_mst_customer_is_active', table_name='mst_customer')
    op.drop_index('ix_mst_customer_gstin', table_name='mst_customer')
    op.drop_index('ix_mst_customer_name', table_name='mst_customer')
    op.drop_index('ix_mst_customer_organization_id', table_name='mst_customer')
    op.drop_index('ix_mst_customer_code', table_name='mst_customer')

    # Drop unique constraint
    op.drop_constraint('uq_customer_org_code', 'mst_customer', type_='unique')

    # Drop table
    op.drop_table('mst_customer')

    # Drop enum
    op.execute('DROP TYPE IF EXISTS customertype')
