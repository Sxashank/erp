"""Add integration configuration tables.

Revision ID: z1_add_integration_config_tables
Revises: y_add_designation_columns
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z1_add_integration_config_tables'
down_revision: Union[str, None] = 'y_add_designation_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create integration type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE integrationtype AS ENUM (
                'NACH', 'ACCOUNT_AGGREGATOR', 'GSTN', 'CREDIT_BUREAU',
                'PAYMENT_GATEWAY', 'SMS_GATEWAY', 'EMAIL_GATEWAY', 'E_INVOICE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create integration provider enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE integrationprovider AS ENUM (
                'NPCI_DIRECT', 'RAZORPAY_NACH', 'CASHFREE_NACH', 'PAYU_NACH',
                'FINVU', 'ONEMONEY', 'SETU', 'YODLEE',
                'GSTN', 'CLEARTAX', 'ZOHO_GST',
                'CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF',
                'RAZORPAY', 'CASHFREE', 'PAYU', 'CCAVENUE', 'STRIPE',
                'MSG91', 'TWILIO', 'TEXTLOCAL',
                'SENDGRID', 'AWS_SES', 'MAILGUN',
                'NIC_EINVOICE', 'CLEARTAX_EINVOICE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create health status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE healthstatus AS ENUM ('HEALTHY', 'DEGRADED', 'DOWN', 'UNKNOWN');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create sys_integration_config table
    op.create_table(
        'sys_integration_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_type', postgresql.ENUM('NACH', 'ACCOUNT_AGGREGATOR', 'GSTN', 'CREDIT_BUREAU',
                                                       'PAYMENT_GATEWAY', 'SMS_GATEWAY', 'EMAIL_GATEWAY', 'E_INVOICE',
                                                       name='integrationtype', create_type=False), nullable=False),
        sa.Column('provider', postgresql.ENUM('NPCI_DIRECT', 'RAZORPAY_NACH', 'CASHFREE_NACH', 'PAYU_NACH',
                                               'FINVU', 'ONEMONEY', 'SETU', 'YODLEE',
                                               'GSTN', 'CLEARTAX', 'ZOHO_GST',
                                               'CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF',
                                               'RAZORPAY', 'CASHFREE', 'PAYU', 'CCAVENUE', 'STRIPE',
                                               'MSG91', 'TWILIO', 'TEXTLOCAL',
                                               'SENDGRID', 'AWS_SES', 'MAILGUN',
                                               'NIC_EINVOICE', 'CLEARTAX_EINVOICE',
                                               name='integrationprovider', create_type=False), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('config_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('sandbox_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('sandbox_url', sa.String(500), nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_secret', sa.String(255), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', postgresql.ENUM('HEALTHY', 'DEGRADED', 'DOWN', 'UNKNOWN',
                                                    name='healthstatus', create_type=False),
                  nullable=False, server_default='UNKNOWN'),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0'),
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
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'integration_type', 'provider',
                           name='uq_integration_org_type_provider'),
    )

    # Create indexes for sys_integration_config
    op.create_index('ix_sys_integration_config_organization_id', 'sys_integration_config', ['organization_id'])
    op.create_index('ix_sys_integration_config_integration_type', 'sys_integration_config', ['integration_type'])

    # Create sys_integration_log table
    op.create_table(
        'sys_integration_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('integration_type', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('is_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integration_config_id'], ['sys_integration_config.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['triggered_by'], ['mst_user.id'], ondelete='SET NULL'),
    )

    # Create indexes for sys_integration_log
    op.create_index('ix_sys_integration_log_organization_id', 'sys_integration_log', ['organization_id'])
    op.create_index('ix_sys_integration_log_integration_type', 'sys_integration_log', ['integration_type'])
    op.create_index('ix_sys_integration_log_request_id', 'sys_integration_log', ['request_id'])
    op.create_index('ix_sys_integration_log_created_at', 'sys_integration_log', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('sys_integration_log')
    op.drop_table('sys_integration_config')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS healthstatus")
    op.execute("DROP TYPE IF EXISTS integrationprovider")
    op.execute("DROP TYPE IF EXISTS integrationtype")
