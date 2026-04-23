"""Add TDS Challan table for aggregating TDS payments.

Revision ID: z7_add_tds_challan
Revises: z6_add_gl_entry
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z7_add_tds_challan'
down_revision = 'z6_add_gl_entry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE challan_status AS ENUM ('DRAFT', 'PENDING', 'PAID', 'VERIFIED', 'CANCELLED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    op.execute("""


        DO $$ BEGIN


            CREATE TYPE challan_type AS ENUM ('281');


        EXCEPTION WHEN duplicate_object THEN null; END $$;


    """)

    # Create txn_tds_challan table
    op.create_table(
        'txn_tds_challan',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),

        # Challan identification
        sa.Column('challan_number', sa.String(50), nullable=True, unique=True),
        sa.Column('bsr_code', sa.String(10), nullable=True),
        sa.Column('serial_number', sa.String(20), nullable=True),

        # Organization
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # TDS Section
        sa.Column('tds_section_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Period
        sa.Column('financial_year_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_year', sa.String(10), nullable=False),
        sa.Column('period_from', sa.Date(), nullable=False),
        sa.Column('period_to', sa.Date(), nullable=False),

        # Amounts
        sa.Column('total_base_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_tds_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_surcharge', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_cess', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('interest_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('penalty_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('other_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),

        # Entry count
        sa.Column('entry_count', sa.Integer(), nullable=False, server_default='0'),

        # Status and payment
        sa.Column('status', postgresql.ENUM('DRAFT', 'PENDING', 'PAID', 'VERIFIED', 'CANCELLED', name='challan_status', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('payment_mode', sa.String(20), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('bank_account_number', sa.String(50), nullable=True),
        sa.Column('cheque_dd_number', sa.String(20), nullable=True),
        sa.Column('cheque_dd_date', sa.Date(), nullable=True),

        # OLTAS details
        sa.Column('oltas_acknowledgment', sa.String(50), nullable=True),
        sa.Column('oltas_status', sa.String(20), nullable=True),
        sa.Column('oltas_verified_at', sa.Date(), nullable=True),

        # Challan form details
        sa.Column('challan_type', postgresql.ENUM('281', name='challan_type', create_type=False), nullable=False, server_default='281'),
        sa.Column('minor_head', sa.String(10), nullable=True),

        # Deductor details
        sa.Column('deductor_tan', sa.String(10), nullable=False),
        sa.Column('deductor_name', sa.String(200), nullable=False),
        sa.Column('deductor_address', sa.Text(), nullable=True),

        # Return filing reference
        sa.Column('return_quarter', sa.String(10), nullable=True),
        sa.Column('is_included_in_return', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('return_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Additional details
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tds_section_id'], ['mst_tds_section.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['financial_year_id'], ['mst_financial_year.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('ix_tds_challan_challan_number', 'txn_tds_challan', ['challan_number'])
    op.create_index('ix_tds_challan_organization_id', 'txn_tds_challan', ['organization_id'])
    op.create_index('ix_tds_challan_tds_section_id', 'txn_tds_challan', ['tds_section_id'])
    op.create_index('ix_tds_challan_financial_year_id', 'txn_tds_challan', ['financial_year_id'])
    op.create_index('ix_tds_challan_status', 'txn_tds_challan', ['status'])
    op.create_index('ix_tds_challan_return_id', 'txn_tds_challan', ['return_id'])
    op.create_index('ix_tds_challan_period', 'txn_tds_challan', ['period_from', 'period_to'])
    op.create_index('ix_tds_challan_org_section_period', 'txn_tds_challan', ['organization_id', 'tds_section_id', 'period_from', 'period_to'])

    # Add challan_id column to txn_tds_entry
    op.add_column(
        'txn_tds_entry',
        sa.Column('challan_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index('ix_tds_entry_challan_id', 'txn_tds_entry', ['challan_id'])
    op.create_foreign_key(
        'fk_tds_entry_challan_id',
        'txn_tds_entry',
        'txn_tds_challan',
        ['challan_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove challan_id from txn_tds_entry
    op.drop_constraint('fk_tds_entry_challan_id', 'txn_tds_entry', type_='foreignkey')
    op.drop_index('ix_tds_entry_challan_id', 'txn_tds_entry')
    op.drop_column('txn_tds_entry', 'challan_id')

    # Drop indexes
    op.drop_index('ix_tds_challan_org_section_period', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_period', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_return_id', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_status', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_financial_year_id', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_tds_section_id', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_organization_id', 'txn_tds_challan')
    op.drop_index('ix_tds_challan_challan_number', 'txn_tds_challan')

    # Drop table
    op.drop_table('txn_tds_challan')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS challan_type")
    op.execute("DROP TYPE IF EXISTS challan_status")
