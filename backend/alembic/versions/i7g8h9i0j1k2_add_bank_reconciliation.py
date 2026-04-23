"""Add bank reconciliation tables.

Revision ID: i7g8h9i0j1k2
Revises: h6f7g8h9i0j1
Create Date: 2024-01-15 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i7g8h9i0j1k2'
down_revision: Union[str, None] = 'h6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums using DO blocks for idempotency
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statementtransactiontype AS ENUM ('CREDIT', 'DEBIT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reconciliationstatus AS ENUM ('UNRECONCILED', 'MATCHED', 'PARTIALLY_MATCHED', 'RECONCILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bankreconciliationstatus AS ENUM ('DRAFT', 'IN_PROGRESS', 'COMPLETED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create txn_bank_statement table
    op.create_table(
        'txn_bank_statement',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('value_date', sa.Date(), nullable=False),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transaction_type', postgresql.ENUM('CREDIT', 'DEBIT', name='statementtransactiontype', create_type=False), nullable=False),
        sa.Column('debit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('credit_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('running_balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('cheque_number', sa.String(20), nullable=True),
        sa.Column('utr_number', sa.String(50), nullable=True),
        sa.Column('bank_transaction_id', sa.String(100), nullable=True),
        sa.Column('reconciliation_status', postgresql.ENUM('UNRECONCILED', 'MATCHED', 'PARTIALLY_MATCHED', 'RECONCILED', name='reconciliationstatus', create_type=False), nullable=False, server_default='UNRECONCILED'),
        sa.Column('reconciled_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('reconciled_voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reconciled_at', sa.DateTime(), nullable=True),
        sa.Column('reconciled_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('import_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('import_row_number', sa.Integer(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        # Foreign keys
        sa.ForeignKeyConstraint(['bank_account_id'], ['mst_account.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.ForeignKeyConstraint(['reconciled_voucher_id'], ['txn_voucher.id']),
        sa.ForeignKeyConstraint(['reconciled_by_id'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['mst_user.id']),
        # Check constraint
        sa.CheckConstraint(
            '(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)',
            name='ck_bank_stmt_amount_exclusive'
        ),
    )

    # Create indexes for txn_bank_statement
    op.create_index('ix_bank_statement_bank_account_id', 'txn_bank_statement', ['bank_account_id'])
    op.create_index('ix_bank_statement_organization_id', 'txn_bank_statement', ['organization_id'])
    op.create_index('ix_bank_statement_transaction_date', 'txn_bank_statement', ['transaction_date'])
    op.create_index('ix_bank_statement_reference_number', 'txn_bank_statement', ['reference_number'])
    op.create_index('ix_bank_statement_reconciliation_status', 'txn_bank_statement', ['reconciliation_status'])
    op.create_index('ix_bank_stmt_account_date', 'txn_bank_statement', ['bank_account_id', 'transaction_date'])
    op.create_index('ix_bank_stmt_import', 'txn_bank_statement', ['import_batch_id', 'import_row_number'])

    # Create txn_bank_statement_match table
    op.create_table(
        'txn_bank_statement_match',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matched_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('match_date', sa.Date(), nullable=False),
        sa.Column('match_type', sa.String(20), nullable=False, server_default='MANUAL'),
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        # Foreign keys
        sa.ForeignKeyConstraint(['statement_id'], ['txn_bank_statement.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voucher_id'], ['txn_voucher.id']),
        # Check constraint
        sa.CheckConstraint('matched_amount > 0', name='ck_match_positive_amount'),
    )

    # Create indexes for txn_bank_statement_match
    op.create_index('ix_bank_statement_match_statement_id', 'txn_bank_statement_match', ['statement_id'])
    op.create_index('ix_bank_statement_match_voucher_id', 'txn_bank_statement_match', ['voucher_id'])

    # Create txn_bank_reconciliation table
    op.create_table(
        'txn_bank_reconciliation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reconciliation_date', sa.Date(), nullable=False),
        sa.Column('from_date', sa.Date(), nullable=False),
        sa.Column('to_date', sa.Date(), nullable=False),
        sa.Column('statement_opening_balance', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('statement_closing_balance', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('book_balance', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('deposits_in_transit', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('outstanding_cheques', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('bank_charges', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('bank_interest', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('other_adjustments', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('reconciled_balance', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('difference', sa.Numeric(18, 2), nullable=False, server_default='0.00'),
        sa.Column('status', postgresql.ENUM('DRAFT', 'IN_PROGRESS', 'COMPLETED', name='bankreconciliationstatus', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        # Foreign keys
        sa.ForeignKeyConstraint(['bank_account_id'], ['mst_account.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id']),
        sa.ForeignKeyConstraint(['completed_by_id'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['mst_user.id']),
    )

    # Create indexes for txn_bank_reconciliation
    op.create_index('ix_bank_reconciliation_bank_account_id', 'txn_bank_reconciliation', ['bank_account_id'])
    op.create_index('ix_bank_reconciliation_organization_id', 'txn_bank_reconciliation', ['organization_id'])
    op.create_index('ix_bank_recon_account_date', 'txn_bank_reconciliation', ['bank_account_id', 'reconciliation_date'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_bank_reconciliation')
    op.drop_table('txn_bank_statement_match')
    op.drop_table('txn_bank_statement')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS bankreconciliationstatus')
    op.execute('DROP TYPE IF EXISTS reconciliationstatus')
    op.execute('DROP TYPE IF EXISTS statementtransactiontype')
