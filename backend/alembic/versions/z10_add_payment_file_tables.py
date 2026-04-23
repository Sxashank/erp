"""Add payment file tables.

Revision ID: z10_payment_file
Revises: z9_cost_center
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z10_payment_file'
down_revision = 'z9_cost_center'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment file table
    op.create_table(
        'txn_payment_file',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),

        # File identification
        sa.Column('file_reference', sa.String(50), nullable=False, unique=True, comment='Unique file reference number'),
        sa.Column('file_format', sa.String(10), nullable=False, comment='NEFT, RTGS, IMPS, UPI'),

        # Payment date
        sa.Column('payment_date', sa.Date, nullable=False),

        # Status
        sa.Column('status', sa.String(30), nullable=False, server_default='DRAFT',
                  comment='DRAFT, GENERATED, DOWNLOADED, UPLOADED, PROCESSING, COMPLETED, FAILED, PARTIALLY_COMPLETED'),

        # Aggregates
        sa.Column('total_transactions', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('successful_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer, nullable=False, server_default='0'),

        # File content
        sa.Column('file_content', sa.Text, nullable=True, comment='Generated file content'),
        sa.Column('checksum', sa.String(64), nullable=True, comment='File checksum for integrity'),

        # Timestamps
        sa.Column('file_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_uploaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),

        # Description
        sa.Column('description', sa.String(500), nullable=True),

        # Bank response
        sa.Column('bank_batch_id', sa.String(50), nullable=True, comment='Batch ID returned by bank'),
        sa.Column('bank_response', postgresql.JSONB, nullable=True, comment='Full bank response'),

        # Audit fields
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_bank_account_id'], ['mst_organization_bank_account.id'], ondelete='RESTRICT'),
    )

    # Create indexes for payment file
    op.create_index('ix_payment_file_organization_id', 'txn_payment_file', ['organization_id'])
    op.create_index('ix_payment_file_bank_account_id', 'txn_payment_file', ['organization_bank_account_id'])
    op.create_index('ix_payment_file_reference', 'txn_payment_file', ['file_reference'], unique=True)
    op.create_index('ix_payment_file_format', 'txn_payment_file', ['file_format'])
    op.create_index('ix_payment_file_payment_date', 'txn_payment_file', ['payment_date'])
    op.create_index('ix_payment_file_status', 'txn_payment_file', ['status'])
    op.create_index('ix_payment_file_is_active', 'txn_payment_file', ['is_active'])

    # Create payment file transaction table
    op.create_table(
        'txn_payment_file_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('payment_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Sequence
        sa.Column('sequence_number', sa.Integer, nullable=False),

        # Beneficiary details
        sa.Column('beneficiary_name', sa.String(100), nullable=False),
        sa.Column('beneficiary_account_number', sa.String(34), nullable=False),
        sa.Column('beneficiary_ifsc', sa.String(11), nullable=False),
        sa.Column('beneficiary_bank_name', sa.String(100), nullable=True),

        # Amount
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),

        # Narration
        sa.Column('narration', sa.String(100), nullable=True),

        # Contact
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('mobile', sa.String(20), nullable=True),

        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING', comment='PENDING, SUCCESS, FAILED, REJECTED'),

        # Bank reference
        sa.Column('bank_reference', sa.String(50), nullable=True, comment='UTR/RRN from bank'),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('return_code', sa.String(10), nullable=True, comment='Bank return code'),

        # Processing timestamp
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),

        # Audit fields
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['payment_file_id'], ['txn_payment_file.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['txn_payment.id'], ondelete='RESTRICT'),
    )

    # Create indexes for payment file transaction
    op.create_index('ix_payment_file_txn_file_id', 'txn_payment_file_transaction', ['payment_file_id'])
    op.create_index('ix_payment_file_txn_payment_id', 'txn_payment_file_transaction', ['payment_id'])
    op.create_index('ix_payment_file_txn_status', 'txn_payment_file_transaction', ['status'])
    op.create_index('ix_payment_file_txn_sequence', 'txn_payment_file_transaction', ['payment_file_id', 'sequence_number'])
    op.create_index('ix_payment_file_txn_is_active', 'txn_payment_file_transaction', ['is_active'])


def downgrade() -> None:
    # Drop payment file transaction indexes
    op.drop_index('ix_payment_file_txn_is_active', table_name='txn_payment_file_transaction')
    op.drop_index('ix_payment_file_txn_sequence', table_name='txn_payment_file_transaction')
    op.drop_index('ix_payment_file_txn_status', table_name='txn_payment_file_transaction')
    op.drop_index('ix_payment_file_txn_payment_id', table_name='txn_payment_file_transaction')
    op.drop_index('ix_payment_file_txn_file_id', table_name='txn_payment_file_transaction')

    # Drop payment file transaction table
    op.drop_table('txn_payment_file_transaction')

    # Drop payment file indexes
    op.drop_index('ix_payment_file_is_active', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_status', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_payment_date', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_format', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_reference', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_bank_account_id', table_name='txn_payment_file')
    op.drop_index('ix_payment_file_organization_id', table_name='txn_payment_file')

    # Drop payment file table
    op.drop_table('txn_payment_file')
