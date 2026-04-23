"""Add DMS (Document Management System) tables.

Revision ID: z26_dms
Revises: z25_notification
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z26_dms'
down_revision: Union[str, None] = 'z25_notification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create document_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_status AS ENUM ('active', 'archived', 'deleted', 'pending_review');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create document_access_level enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_access_level AS ENUM ('private', 'organization', 'department', 'public');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create dms_folder table
    op.create_table(
        'dms_folder',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('path', sa.String(2000), nullable=False),
        sa.Column('level', sa.Integer, nullable=False, server_default='0'),
        sa.Column('folder_type', sa.String(50), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('access_level', sa.String(20), nullable=False, server_default='organization'),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('document_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['dms_folder.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_folder_org', 'dms_folder', ['organization_id'])
    op.create_index('ix_dms_folder_parent', 'dms_folder', ['parent_id'])
    op.create_index('ix_dms_folder_path', 'dms_folder', ['path'])
    op.create_index('ix_dms_folder_entity', 'dms_folder', ['entity_type', 'entity_id'])

    # Create dms_document table
    op.create_table(
        'dms_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_extension', sa.String(20), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=False, server_default='local'),
        sa.Column('checksum', sa.String(128), nullable=True),
        sa.Column('document_type', sa.String(50), nullable=True),
        sa.Column('document_subtype', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('access_level', sa.String(20), nullable=False, server_default='organization'),
        sa.Column('current_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_ocr_processed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('download_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['dms_folder.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_document_org', 'dms_document', ['organization_id'])
    op.create_index('ix_dms_document_folder', 'dms_document', ['folder_id'])
    op.create_index('ix_dms_document_code', 'dms_document', ['code'])
    op.create_index('ix_dms_document_status', 'dms_document', ['status'])
    op.create_index('ix_dms_document_entity', 'dms_document', ['entity_type', 'entity_id'])
    op.create_index('ix_dms_document_type', 'dms_document', ['document_type'])

    # Create dms_document_version table
    op.create_table(
        'dms_document_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('change_notes', sa.String(1000), nullable=True),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('checksum', sa.String(128), nullable=True),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['document_id'], ['dms_document.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_document_version_doc', 'dms_document_version', ['document_id'])
    op.create_index('ix_dms_document_version_number', 'dms_document_version', ['document_id', 'version_number'], unique=True)

    # Create dms_document_access table
    op.create_table(
        'dms_document_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('can_view', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('can_download', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('can_edit', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_delete', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_share', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['document_id'], ['dms_document.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['mst_department.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_document_access_doc', 'dms_document_access', ['document_id'])
    op.create_index('ix_dms_document_access_user', 'dms_document_access', ['user_id'])

    # Create dms_document_history table
    op.create_table(
        'dms_document_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('action_details', postgresql.JSONB, nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['document_id'], ['dms_document.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_document_history_doc', 'dms_document_history', ['document_id'])
    op.create_index('ix_dms_document_history_action', 'dms_document_history', ['action'])

    # Create dms_folder_access table
    op.create_table(
        'dms_folder_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('can_view', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('can_upload', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_create_subfolder', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_edit', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_delete', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['folder_id'], ['dms_folder.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['mst_department.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_folder_access_folder', 'dms_folder_access', ['folder_id'])
    op.create_index('ix_dms_folder_access_user', 'dms_folder_access', ['user_id'])

    # Create dms_tag table
    op.create_table(
        'dms_tag',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
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
    op.create_index('ix_dms_tag_org', 'dms_tag', ['organization_id'])
    op.create_index('ix_dms_tag_slug', 'dms_tag', ['organization_id', 'slug'], unique=True)
    op.create_index('ix_dms_tag_category', 'dms_tag', ['category'])

    # Create dms_document_tag table
    op.create_table(
        'dms_document_tag',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['document_id'], ['dms_document.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['dms_tag.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dms_document_tag_doc', 'dms_document_tag', ['document_id'])
    op.create_index('ix_dms_document_tag_tag', 'dms_document_tag', ['tag_id'])
    op.create_index('ix_dms_document_tag_unique', 'dms_document_tag', ['document_id', 'tag_id'], unique=True)


def downgrade() -> None:
    # Drop tables
    op.drop_table('dms_document_tag')
    op.drop_table('dms_tag')
    op.drop_table('dms_folder_access')
    op.drop_table('dms_document_history')
    op.drop_table('dms_document_access')
    op.drop_table('dms_document_version')
    op.drop_table('dms_document')
    op.drop_table('dms_folder')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS document_access_level")
    op.execute("DROP TYPE IF EXISTS document_status")
