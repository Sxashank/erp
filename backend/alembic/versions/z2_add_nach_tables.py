"""Add NACH batch and transaction tables.

Revision ID: z2_add_nach_tables
Revises: z1_add_integration_config_tables
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z2_add_nach_tables'
down_revision: Union[str, None] = 'z1_add_integration_config_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create NACH batch status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nachbatchstatus AS ENUM (
                'CREATED', 'VALIDATED', 'FILE_GENERATED', 'SUBMITTED',
                'PROCESSING', 'RESPONSE_RECEIVED', 'COMPLETED', 'FAILED', 'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create NACH transaction status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nachtransactionstatus AS ENUM (
                'PENDING', 'INCLUDED', 'SUBMITTED', 'SUCCESS',
                'BOUNCED', 'REJECTED', 'CANCELLED', 'RETRY_SCHEDULED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create NACH return code enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nachreturncode AS ENUM (
                '00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                '10', '11', '12', '13', '14', '15', '99'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create NACH file format enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nachfileformat AS ENUM (
                'ACH_DEBIT', 'ACH_CREDIT', 'MANDATE_REGISTER',
                'MANDATE_MODIFY', 'MANDATE_CANCEL'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create lms_nach_batch table
    op.create_table(
        'lms_nach_batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_reference', sa.String(50), nullable=False),
        sa.Column('batch_date', sa.Date(), nullable=False),
        sa.Column('debit_date', sa.Date(), nullable=False),
        sa.Column('integration_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('file_format', postgresql.ENUM('ACH_DEBIT', 'ACH_CREDIT', 'MANDATE_REGISTER',
                                                   'MANDATE_MODIFY', 'MANDATE_CANCEL',
                                                   name='nachfileformat', create_type=False),
                  nullable=False, server_default='ACH_DEBIT'),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(20, 2), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_amount', sa.Numeric(20, 2), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_amount', sa.Numeric(20, 2), nullable=False, server_default='0'),
        sa.Column('pending_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_name', sa.String(200), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_checksum', sa.String(64), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submission_reference', sa.String(100), nullable=True),
        sa.Column('response_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_file_name', sa.String(200), nullable=True),
        sa.Column('response_file_path', sa.String(500), nullable=True),
        sa.Column('status', postgresql.ENUM('CREATED', 'VALIDATED', 'FILE_GENERATED', 'SUBMITTED',
                                             'PROCESSING', 'RESPONSE_RECEIVED', 'COMPLETED', 'FAILED', 'CANCELLED',
                                             name='nachbatchstatus', create_type=False),
                  nullable=False, server_default='CREATED'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integration_config_id'], ['sys_integration_config.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('batch_reference', name='uq_nach_batch_reference'),
    )

    # Create indexes for lms_nach_batch
    op.create_index('ix_lms_nach_batch_organization_id', 'lms_nach_batch', ['organization_id'])
    op.create_index('ix_lms_nach_batch_batch_reference', 'lms_nach_batch', ['batch_reference'])
    op.create_index('ix_lms_nach_batch_batch_date', 'lms_nach_batch', ['batch_date'])
    op.create_index('ix_lms_nach_batch_debit_date', 'lms_nach_batch', ['debit_date'])
    op.create_index('ix_lms_nach_batch_status', 'lms_nach_batch', ['status'])
    op.create_index('ix_lms_nach_batch_org_date', 'lms_nach_batch', ['organization_id', 'batch_date'])
    op.create_index('ix_lms_nach_batch_org_status', 'lms_nach_batch', ['organization_id', 'status'])

    # Create lms_nach_transaction table
    op.create_table(
        'lms_nach_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loan_mandate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('installment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transaction_reference', sa.String(50), nullable=False),
        sa.Column('umrn', sa.String(50), nullable=False),
        sa.Column('account_number', sa.String(50), nullable=False),
        sa.Column('ifsc_code', sa.String(11), nullable=False),
        sa.Column('account_holder_name', sa.String(200), nullable=False),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('debit_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('debit_date', sa.Date(), nullable=False),
        sa.Column('narration', sa.String(100), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'INCLUDED', 'SUBMITTED', 'SUCCESS',
                                             'BOUNCED', 'REJECTED', 'CANCELLED', 'RETRY_SCHEDULED',
                                             name='nachtransactionstatus', create_type=False),
                  nullable=False, server_default='PENDING'),
        sa.Column('bank_reference', sa.String(50), nullable=True),
        sa.Column('return_code', postgresql.ENUM('00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                  '10', '11', '12', '13', '14', '15', '99',
                                                  name='nachreturncode', create_type=False),
                  nullable=True),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('receipt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_date', sa.Date(), nullable=True),
        sa.Column('original_transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bounce_charges_applied', sa.Numeric(20, 2), nullable=False, server_default='0'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['batch_id'], ['lms_nach_batch.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['loan_account_id'], ['lms_loan_account.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['loan_mandate_id'], ['lms_loan_mandate.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['installment_id'], ['lms_schedule_installment.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['receipt_id'], ['lms_loan_receipt.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['original_transaction_id'], ['lms_nach_transaction.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('transaction_reference', name='uq_nach_transaction_reference'),
    )

    # Create indexes for lms_nach_transaction
    op.create_index('ix_lms_nach_txn_batch_id', 'lms_nach_transaction', ['batch_id'])
    op.create_index('ix_lms_nach_txn_loan_account_id', 'lms_nach_transaction', ['loan_account_id'])
    op.create_index('ix_lms_nach_txn_loan_mandate_id', 'lms_nach_transaction', ['loan_mandate_id'])
    op.create_index('ix_lms_nach_txn_transaction_reference', 'lms_nach_transaction', ['transaction_reference'])
    op.create_index('ix_lms_nach_txn_umrn', 'lms_nach_transaction', ['umrn'])
    op.create_index('ix_lms_nach_txn_debit_date', 'lms_nach_transaction', ['debit_date'])
    op.create_index('ix_lms_nach_txn_status', 'lms_nach_transaction', ['status'])
    op.create_index('ix_lms_nach_txn_batch_status', 'lms_nach_transaction', ['batch_id', 'status'])
    op.create_index('ix_lms_nach_txn_debit_status', 'lms_nach_transaction', ['debit_date', 'status'])
    op.create_index('ix_lms_nach_txn_retry', 'lms_nach_transaction', ['next_retry_date', 'status'])

    # Create lms_nach_mandate_log table
    op.create_table(
        'lms_nach_mandate_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loan_mandate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation', postgresql.ENUM('ACH_DEBIT', 'ACH_CREDIT', 'MANDATE_REGISTER',
                                                'MANDATE_MODIFY', 'MANDATE_CANCEL',
                                                name='nachfileformat', create_type=False), nullable=False),
        sa.Column('request_reference', sa.String(100), nullable=False),
        sa.Column('request_date', sa.Date(), nullable=False),
        sa.Column('request_payload', postgresql.JSONB(), nullable=True),
        sa.Column('response_date', sa.Date(), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(), nullable=True),
        sa.Column('is_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_code', sa.String(20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('umrn_assigned', sa.String(50), nullable=True),
        sa.Column('integration_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['loan_mandate_id'], ['lms_loan_mandate.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integration_config_id'], ['sys_integration_config.id'], ondelete='SET NULL'),
    )

    # Create indexes for lms_nach_mandate_log
    op.create_index('ix_lms_mandate_log_org_id', 'lms_nach_mandate_log', ['organization_id'])
    op.create_index('ix_lms_mandate_log_mandate_id', 'lms_nach_mandate_log', ['loan_mandate_id'])
    op.create_index('ix_lms_mandate_log_request_ref', 'lms_nach_mandate_log', ['request_reference'])
    op.create_index('ix_lms_mandate_log_org_date', 'lms_nach_mandate_log', ['organization_id', 'request_date'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('lms_nach_mandate_log')
    op.drop_table('lms_nach_transaction')
    op.drop_table('lms_nach_batch')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS nachfileformat")
    op.execute("DROP TYPE IF EXISTS nachreturncode")
    op.execute("DROP TYPE IF EXISTS nachtransactionstatus")
    op.execute("DROP TYPE IF EXISTS nachbatchstatus")
