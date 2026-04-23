"""Add KYC and Compliance enhancement tables.

Revision ID: z31_kyc_compliance
Revises: z30_procurement
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z31_kyc_compliance'
down_revision: Union[str, None] = 'z30_procurement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create kyc_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kyc_status AS ENUM (
                'pending', 'in_progress', 'verified', 'rejected', 'expired', 'rekyc_required'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create ckyc_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ckyc_status AS ENUM (
                'not_initiated', 'search_pending', 'found', 'not_found',
                'download_pending', 'downloaded', 'upload_pending', 'uploaded', 'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create credit_bureau_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE credit_bureau_status AS ENUM (
                'pending', 'submitted', 'received', 'failed', 'error'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create document_verification_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_verification_status AS ENUM (
                'pending', 'verified', 'rejected', 'expired', 'superseded'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create mst_kyc_document_type table
    op.create_table(
        'mst_kyc_document_type',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('document_category', sa.String(50), nullable=False),
        sa.Column('entity_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_poi', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_poa', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('validity_months', sa.Integer, nullable=True),
        sa.Column('allowed_file_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('max_file_size_mb', sa.Integer, nullable=True),
        sa.Column('verification_required', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ocr_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_kyc_document_type_org', 'mst_kyc_document_type', ['organization_id'])
    op.create_index('ix_mst_kyc_document_type_code', 'mst_kyc_document_type', ['organization_id', 'code'], unique=True)
    op.create_index('ix_mst_kyc_document_type_category', 'mst_kyc_document_type', ['document_category'])

    # Create txn_kyc_document table
    op.create_table(
        'txn_kyc_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('checksum', sa.String(128), nullable=True),
        sa.Column('issue_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('issuing_authority', sa.String(255), nullable=True),
        sa.Column('verification_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_remarks', sa.String(500), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('ocr_data', postgresql.JSONB, nullable=True),
        sa.Column('extracted_data', postgresql.JSONB, nullable=True),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_type_id'], ['mst_kyc_document_type.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['verified_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['superseded_by'], ['txn_kyc_document.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_kyc_document_org', 'txn_kyc_document', ['organization_id'])
    op.create_index('ix_txn_kyc_document_type', 'txn_kyc_document', ['document_type_id'])
    op.create_index('ix_txn_kyc_document_entity', 'txn_kyc_document', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_kyc_document_status', 'txn_kyc_document', ['verification_status'])
    op.create_index('ix_txn_kyc_document_expiry', 'txn_kyc_document', ['expiry_date'])

    # Create txn_ckyc_record table
    op.create_table(
        'txn_ckyc_record',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ckyc_number', sa.String(20), nullable=True),
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('aadhaar_ref', sa.String(16), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('father_name', sa.String(255), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='not_initiated'),
        sa.Column('search_request_id', sa.String(100), nullable=True),
        sa.Column('search_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('search_response', postgresql.JSONB, nullable=True),
        sa.Column('download_request_id', sa.String(100), nullable=True),
        sa.Column('download_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('download_response', postgresql.JSONB, nullable=True),
        sa.Column('ckyc_xml_path', sa.String(1000), nullable=True),
        sa.Column('ckyc_pdf_path', sa.String(1000), nullable=True),
        sa.Column('ckyc_image_path', sa.String(1000), nullable=True),
        sa.Column('upload_request_id', sa.String(100), nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_response', postgresql.JSONB, nullable=True),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_refresh_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_ckyc_record_org', 'txn_ckyc_record', ['organization_id'])
    op.create_index('ix_txn_ckyc_record_entity', 'txn_ckyc_record', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_ckyc_record_ckyc_number', 'txn_ckyc_record', ['ckyc_number'])
    op.create_index('ix_txn_ckyc_record_pan', 'txn_ckyc_record', ['pan'])
    op.create_index('ix_txn_ckyc_record_status', 'txn_ckyc_record', ['status'])

    # Create txn_credit_bureau_pull table
    op.create_table(
        'txn_credit_bureau_pull',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bureau_type', sa.String(20), nullable=False),
        sa.Column('pull_type', sa.String(20), nullable=False, server_default='soft'),
        sa.Column('purpose', sa.String(100), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('mobile', sa.String(15), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('request_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_payload', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('response_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_payload', postgresql.JSONB, nullable=True),
        sa.Column('credit_score', sa.Integer, nullable=True),
        sa.Column('score_range_min', sa.Integer, nullable=True),
        sa.Column('score_range_max', sa.Integer, nullable=True),
        sa.Column('score_factors', postgresql.JSONB, nullable=True),
        sa.Column('total_accounts', sa.Integer, nullable=True),
        sa.Column('active_accounts', sa.Integer, nullable=True),
        sa.Column('overdue_accounts', sa.Integer, nullable=True),
        sa.Column('total_balance', sa.Numeric(18, 4), nullable=True),
        sa.Column('total_overdue', sa.Numeric(18, 4), nullable=True),
        sa.Column('enquiry_count_6m', sa.Integer, nullable=True),
        sa.Column('enquiry_count_12m', sa.Integer, nullable=True),
        sa.Column('report_pdf_path', sa.String(1000), nullable=True),
        sa.Column('report_xml_path', sa.String(1000), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('consent_id', sa.String(100), nullable=True),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_charges', sa.Numeric(10, 4), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_credit_bureau_pull_org', 'txn_credit_bureau_pull', ['organization_id'])
    op.create_index('ix_txn_credit_bureau_pull_entity', 'txn_credit_bureau_pull', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_credit_bureau_pull_bureau', 'txn_credit_bureau_pull', ['bureau_type'])
    op.create_index('ix_txn_credit_bureau_pull_status', 'txn_credit_bureau_pull', ['status'])
    op.create_index('ix_txn_credit_bureau_pull_pan', 'txn_credit_bureau_pull', ['pan'])
    op.create_index('ix_txn_credit_bureau_pull_date', 'txn_credit_bureau_pull', ['request_date'])

    # Create txn_credit_score_history table
    op.create_table(
        'txn_credit_score_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pull_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bureau_type', sa.String(20), nullable=False),
        sa.Column('score_date', sa.Date, nullable=False),
        sa.Column('credit_score', sa.Integer, nullable=False),
        sa.Column('score_change', sa.Integer, nullable=True),
        sa.Column('total_balance', sa.Numeric(18, 4), nullable=True),
        sa.Column('total_overdue', sa.Numeric(18, 4), nullable=True),
        sa.Column('active_accounts', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['pull_id'], ['txn_credit_bureau_pull.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_credit_score_history_entity', 'txn_credit_score_history', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_credit_score_history_date', 'txn_credit_score_history', ['score_date'])

    # Create txn_kyc_checklist table
    op.create_table(
        'txn_kyc_checklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checklist_item', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_completed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verification_status', sa.String(20), nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('display_order', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['completed_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['txn_kyc_document.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_kyc_checklist_org', 'txn_kyc_checklist', ['organization_id'])
    op.create_index('ix_txn_kyc_checklist_entity', 'txn_kyc_checklist', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_kyc_checklist_completed', 'txn_kyc_checklist', ['is_completed'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_kyc_checklist')
    op.drop_table('txn_credit_score_history')
    op.drop_table('txn_credit_bureau_pull')
    op.drop_table('txn_ckyc_record')
    op.drop_table('txn_kyc_document')
    op.drop_table('mst_kyc_document_type')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS document_verification_status")
    op.execute("DROP TYPE IF EXISTS credit_bureau_status")
    op.execute("DROP TYPE IF EXISTS ckyc_status")
    op.execute("DROP TYPE IF EXISTS kyc_status")
