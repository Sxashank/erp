"""Add TDS Return table for quarterly filing.

Revision ID: z8_add_tds_return
Revises: z7_add_tds_challan
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z8_add_tds_return'
down_revision = 'z7_add_tds_challan'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE return_type AS ENUM ('24Q', '26Q', '27Q', '27EQ');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    op.execute("""


        DO $$ BEGIN


            CREATE TYPE return_status AS ENUM ('DRAFT', 'VALIDATED', 'GENERATED', 'UPLOADED', 'ACCEPTED', 'FILED', 'REVISED', 'REJECTED');


        EXCEPTION WHEN duplicate_object THEN null; END $$;


    """)

    op.execute("""


        DO $$ BEGIN


            CREATE TYPE quarter AS ENUM ('Q1', 'Q2', 'Q3', 'Q4');


        EXCEPTION WHEN duplicate_object THEN null; END $$;


    """)

    # Create txn_tds_return table
    op.create_table(
        'txn_tds_return',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),

        # Organization
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Return identification
        sa.Column('return_type', postgresql.ENUM('24Q', '26Q', '27Q', '27EQ', name='return_type', create_type=False), nullable=False),
        sa.Column('financial_year_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('financial_year', sa.String(10), nullable=False),
        sa.Column('assessment_year', sa.String(10), nullable=False),
        sa.Column('quarter', postgresql.ENUM('Q1', 'Q2', 'Q3', 'Q4', name='quarter', create_type=False), nullable=False),
        sa.Column('period_from', sa.Date(), nullable=False),
        sa.Column('period_to', sa.Date(), nullable=False),

        # Status
        sa.Column('status', postgresql.ENUM('DRAFT', 'VALIDATED', 'GENERATED', 'UPLOADED', 'ACCEPTED', 'FILED', 'REVISED', 'REJECTED', name='return_status', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('is_original', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revision_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('original_return_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Deductor details
        sa.Column('deductor_tan', sa.String(10), nullable=False),
        sa.Column('deductor_name', sa.String(200), nullable=False),
        sa.Column('deductor_pan', sa.String(10), nullable=True),
        sa.Column('deductor_type', sa.String(20), nullable=True),
        sa.Column('deductor_category', sa.String(5), nullable=True),
        sa.Column('deductor_address', sa.Text(), nullable=True),
        sa.Column('deductor_city', sa.String(100), nullable=True),
        sa.Column('deductor_state', sa.String(50), nullable=True),
        sa.Column('deductor_pincode', sa.String(10), nullable=True),
        sa.Column('deductor_email', sa.String(100), nullable=True),
        sa.Column('deductor_phone', sa.String(20), nullable=True),

        # Responsible person
        sa.Column('responsible_person_name', sa.String(200), nullable=True),
        sa.Column('responsible_person_designation', sa.String(100), nullable=True),
        sa.Column('responsible_person_address', sa.Text(), nullable=True),
        sa.Column('responsible_person_pan', sa.String(10), nullable=True),

        # Summary amounts
        sa.Column('total_challans', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_deductees', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_paid', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_tds_deducted', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_tds_deposited', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_interest', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('total_late_fee', sa.Numeric(18, 2), nullable=False, server_default='0.00'),

        # File generation
        sa.Column('file_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_name', sa.String(200), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),

        # Filing details
        sa.Column('provisional_receipt_number', sa.String(50), nullable=True),
        sa.Column('token_number', sa.String(50), nullable=True),
        sa.Column('acknowledgment_number', sa.String(50), nullable=True),
        sa.Column('filed_date', sa.Date(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),

        # Due date
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('is_late', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('days_late', sa.Integer(), nullable=False, server_default='0'),

        # Validation
        sa.Column('validation_errors', postgresql.JSONB(), nullable=True),
        sa.Column('validation_warnings', postgresql.JSONB(), nullable=True),
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),

        # Additional
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
        sa.ForeignKeyConstraint(['financial_year_id'], ['mst_financial_year.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['original_return_id'], ['txn_tds_return.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('ix_tds_return_organization_id', 'txn_tds_return', ['organization_id'])
    op.create_index('ix_tds_return_return_type', 'txn_tds_return', ['return_type'])
    op.create_index('ix_tds_return_financial_year_id', 'txn_tds_return', ['financial_year_id'])
    op.create_index('ix_tds_return_quarter', 'txn_tds_return', ['quarter'])
    op.create_index('ix_tds_return_status', 'txn_tds_return', ['status'])
    op.create_index('ix_tds_return_original_return_id', 'txn_tds_return', ['original_return_id'])
    op.create_index('ix_tds_return_due_date', 'txn_tds_return', ['due_date'])

    # Composite indexes
    op.create_index(
        'ix_tds_return_org_type_fy_quarter',
        'txn_tds_return',
        ['organization_id', 'return_type', 'financial_year', 'quarter']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_tds_return_org_type_fy_quarter', 'txn_tds_return')
    op.drop_index('ix_tds_return_due_date', 'txn_tds_return')
    op.drop_index('ix_tds_return_original_return_id', 'txn_tds_return')
    op.drop_index('ix_tds_return_status', 'txn_tds_return')
    op.drop_index('ix_tds_return_quarter', 'txn_tds_return')
    op.drop_index('ix_tds_return_financial_year_id', 'txn_tds_return')
    op.drop_index('ix_tds_return_return_type', 'txn_tds_return')
    op.drop_index('ix_tds_return_organization_id', 'txn_tds_return')

    # Drop table
    op.drop_table('txn_tds_return')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS quarter")
    op.execute("DROP TYPE IF EXISTS return_status")
    op.execute("DROP TYPE IF EXISTS return_type")
