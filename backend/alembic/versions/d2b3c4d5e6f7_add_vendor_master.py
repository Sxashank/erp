"""Add vendor master table.

Revision ID: d2b3c4d5e6f7
Revises: c1a2b3c4d5e6
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd2b3c4d5e6f7'
down_revision: Union[str, None] = 'c1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vendor type enum
    vendor_type_enum = postgresql.ENUM(
        'SUPPLIER', 'CONTRACTOR', 'SERVICE_PROVIDER', 'OTHERS',
        name='vendortype',
        create_type=False
    )
    vendor_type_enum.create(op.get_bind(), checkfirst=True)

    # Create GST registration type enum
    gst_reg_type_enum = postgresql.ENUM(
        'REGULAR', 'COMPOSITION', 'UNREGISTERED', 'SEZ', 'DEEMED_EXPORT', 'OVERSEAS',
        name='gstregistrationtype',
        create_type=False
    )
    gst_reg_type_enum.create(op.get_bind(), checkfirst=True)

    # Create payment mode preference enum
    payment_mode_enum = postgresql.ENUM(
        'CASH', 'CHEQUE', 'NEFT', 'RTGS', 'UPI', 'BANK_TRANSFER',
        name='paymentmodepreference',
        create_type=False
    )
    payment_mode_enum.create(op.get_bind(), checkfirst=True)

    # Create balance type enum
    balance_type_enum = postgresql.ENUM(
        'DR', 'CR',
        name='balancetype',
        create_type=False
    )
    balance_type_enum.create(op.get_bind(), checkfirst=True)

    # Create vendor table
    op.create_table(
        'mst_vendor',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('vendor_type', postgresql.ENUM('SUPPLIER', 'CONTRACTOR', 'SERVICE_PROVIDER', 'OTHERS', name='vendortype', create_type=False), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Tax & Compliance
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('gst_registration_type', postgresql.ENUM('REGULAR', 'COMPOSITION', 'UNREGISTERED', 'SEZ', 'DEEMED_EXPORT', 'OVERSEAS', name='gstregistrationtype', create_type=False), nullable=True),
        sa.Column('msme_registered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('msme_number', sa.String(20), nullable=True),
        sa.Column('tds_applicable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tds_section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tds_rate_override', sa.Numeric(5, 2), nullable=True),

        # Contact & Address
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('mobile', sa.String(20), nullable=True),
        sa.Column('address_line1', sa.String(200), nullable=True),
        sa.Column('address_line2', sa.String(200), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state_code', sa.String(2), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('country', sa.String(50), nullable=False, server_default='India'),

        # Banking Details
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_account_number', sa.String(50), nullable=True),
        sa.Column('bank_ifsc_code', sa.String(11), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('payment_mode_preference', postgresql.ENUM('CASH', 'CHEQUE', 'NEFT', 'RTGS', 'UPI', 'BANK_TRANSFER', name='paymentmodepreference', create_type=False), nullable=True),

        # Financial Settings
        sa.Column('control_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payment_terms_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('credit_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('credit_limit', sa.Numeric(18, 2), nullable=True),
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
        sa.ForeignKeyConstraint(['tds_section_id'], ['mst_tds_section.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['control_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['expense_account_id'], ['mst_account.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_terms_id'], ['mst_payment_terms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_mst_vendor_code', 'mst_vendor', ['code'])
    op.create_index('ix_mst_vendor_organization_id', 'mst_vendor', ['organization_id'])
    op.create_index('ix_mst_vendor_name', 'mst_vendor', ['name'])
    op.create_index('ix_mst_vendor_gstin', 'mst_vendor', ['gstin'])
    op.create_index('ix_mst_vendor_pan', 'mst_vendor', ['pan'])
    op.create_index('ix_mst_vendor_is_active', 'mst_vendor', ['is_active'])

    # Create unique constraint for code within organization
    op.create_unique_constraint('uq_vendor_org_code', 'mst_vendor', ['organization_id', 'code'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_mst_vendor_is_active', table_name='mst_vendor')
    op.drop_index('ix_mst_vendor_pan', table_name='mst_vendor')
    op.drop_index('ix_mst_vendor_gstin', table_name='mst_vendor')
    op.drop_index('ix_mst_vendor_name', table_name='mst_vendor')
    op.drop_index('ix_mst_vendor_organization_id', table_name='mst_vendor')
    op.drop_index('ix_mst_vendor_code', table_name='mst_vendor')

    # Drop unique constraint
    op.drop_constraint('uq_vendor_org_code', 'mst_vendor', type_='unique')

    # Drop table
    op.drop_table('mst_vendor')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS balancetype')
    op.execute('DROP TYPE IF EXISTS paymentmodepreference')
    op.execute('DROP TYPE IF EXISTS gstregistrationtype')
    op.execute('DROP TYPE IF EXISTS vendortype')
