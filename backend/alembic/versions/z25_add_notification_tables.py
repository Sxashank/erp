"""Add notification system tables.

Revision ID: z25_notification
Revises: z24_add_vendor_portal_tables
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z25_notification'
down_revision: Union[str, None] = 'z24_add_vendor_portal_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notification_channel enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_channel AS ENUM ('email', 'sms', 'push', 'in_app', 'webhook');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create notification_priority enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_priority AS ENUM ('low', 'normal', 'high', 'urgent');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create notification_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'read', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create notification_category enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_category AS ENUM (
                'system', 'security', 'loan', 'payment', 'collection',
                'approval', 'document', 'hr', 'compliance', 'marketing', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create notification_template_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_template_type AS ENUM (
                'transactional', 'promotional', 'reminder', 'alert', 'report'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create sys_notification_template table
    op.create_table(
        'sys_notification_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='other'),
        sa.Column('template_type', sa.String(50), nullable=False, server_default='transactional'),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body_template', sa.Text, nullable=False),
        sa.Column('html_template', sa.Text, nullable=True),
        sa.Column('sms_template', sa.String(500), nullable=True),
        sa.Column('push_template', sa.String(500), nullable=True),
        sa.Column('channels', postgresql.ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('default_priority', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
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
    op.create_index('ix_sys_notification_template_org_code', 'sys_notification_template', ['organization_id', 'code'], unique=True)
    op.create_index('ix_sys_notification_template_category', 'sys_notification_template', ['category'])

    # Create notification_template_variable table
    op.create_table(
        'notification_template_variable',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variable_name', sa.String(100), nullable=False),
        sa.Column('variable_type', sa.String(50), nullable=False, server_default='string'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('default_value', sa.String(500), nullable=True),
        sa.Column('is_required', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('validation_regex', sa.String(255), nullable=True),
        sa.Column('sample_value', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['template_id'], ['sys_notification_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_template_variable_template', 'notification_template_variable', ['template_id'])

    # Create txn_notification table
    op.create_table(
        'txn_notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_email', sa.String(255), nullable=True),
        sa.Column('recipient_phone', sa.String(20), nullable=True),
        sa.Column('recipient_device_token', sa.String(500), nullable=True),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='other'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('html_body', sa.Text, nullable=True),
        sa.Column('action_url', sa.String(1000), nullable=True),
        sa.Column('action_label', sa.String(100), nullable=True),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['sys_notification_template.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_notification_org', 'txn_notification', ['organization_id'])
    op.create_index('ix_txn_notification_user', 'txn_notification', ['user_id'])
    op.create_index('ix_txn_notification_status', 'txn_notification', ['status'])
    op.create_index('ix_txn_notification_entity', 'txn_notification', ['entity_type', 'entity_id'])
    op.create_index('ix_txn_notification_scheduled', 'txn_notification', ['scheduled_at'])

    # Create notification_preference table
    op.create_table(
        'notification_preference',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('email_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('push_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('in_app_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('quiet_hours_start', sa.Time, nullable=True),
        sa.Column('quiet_hours_end', sa.Time, nullable=True),
        sa.Column('frequency', sa.String(20), nullable=False, server_default='immediate'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_preference_user_category', 'notification_preference', ['user_id', 'category'], unique=True)

    # Create notification_log table
    op.create_table(
        'notification_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_details', postgresql.JSONB, nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('provider_response', postgresql.JSONB, nullable=True),
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
        sa.ForeignKeyConstraint(['notification_id'], ['txn_notification.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_log_notification', 'notification_log', ['notification_id'])
    op.create_index('ix_notification_log_event', 'notification_log', ['event_type'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('notification_log')
    op.drop_table('notification_preference')
    op.drop_table('txn_notification')
    op.drop_table('notification_template_variable')
    op.drop_table('sys_notification_template')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS notification_template_type")
    op.execute("DROP TYPE IF EXISTS notification_category")
    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_priority")
    op.execute("DROP TYPE IF EXISTS notification_channel")
