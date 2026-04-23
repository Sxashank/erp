"""Add compliance tables

Revision ID: z15_add_compliance_tables
Revises: z14_add_payroll_tables
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z15_add_compliance_tables'
down_revision = 'z14_add_payroll_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE regulatorybody AS ENUM ('RBI', 'SEBI', 'MCA', 'GST', 'INCOME_TAX', 'EPFO', 'ESIC', 'STATE', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE compliancefrequency AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'AS_REQUIRED', 'ONE_TIME'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE compliancestatus AS ENUM ('NOT_DUE', 'PENDING', 'IN_PROGRESS', 'PREPARED', 'UNDER_REVIEW', 'FILED', 'ACKNOWLEDGED', 'DELAYED', 'NOT_APPLICABLE'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE compliancepriority AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create compliance_item table
    op.create_table(
        'compliance_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('item_code', sa.String(30), nullable=False),
        sa.Column('item_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('regulatory_body', postgresql.ENUM('RBI', 'SEBI', 'MCA', 'GST', 'INCOME_TAX', 'EPFO', 'ESIC', 'STATE', 'OTHER', name='regulatorybody', create_type=False), nullable=False),
        sa.Column('regulation_reference', sa.String(100), nullable=True),
        sa.Column('section_reference', sa.String(100), nullable=True),
        sa.Column('frequency', postgresql.ENUM('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY', 'AS_REQUIRED', 'ONE_TIME', name='compliancefrequency', create_type=False), nullable=False, server_default='MONTHLY'),
        sa.Column('due_day', sa.Integer, nullable=True),
        sa.Column('due_month', sa.Integer, nullable=True),
        sa.Column('grace_days', sa.Integer, nullable=False, server_default='0'),
        sa.Column('priority', postgresql.ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='compliancepriority', create_type=False), nullable=False, server_default='MEDIUM'),
        sa.Column('penalty_type', sa.String(50), nullable=True),
        sa.Column('penalty_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('penalty_rate_per_day', sa.Numeric(10, 4), nullable=True),
        sa.Column('responsible_designation', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('required_documents', postgresql.JSONB, nullable=True),
        sa.Column('form_name', sa.String(50), nullable=True),
        sa.Column('filing_portal', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('effective_from', sa.Date, nullable=True),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'item_code', name='uq_compliance_item_org_code'),
    )
    op.create_index('ix_compliance_item_org', 'compliance_item', ['organization_id'])
    op.create_index('ix_compliance_item_body', 'compliance_item', ['regulatory_body'])

    # Create compliance_instance table
    op.create_table(
        'compliance_instance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('compliance_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_item.id'), nullable=False),
        sa.Column('period_year', sa.Integer, nullable=False),
        sa.Column('period_month', sa.Integer, nullable=True),
        sa.Column('period_quarter', sa.Integer, nullable=True),
        sa.Column('period_from', sa.Date, nullable=True),
        sa.Column('period_to', sa.Date, nullable=True),
        sa.Column('original_due_date', sa.Date, nullable=False),
        sa.Column('extended_due_date', sa.Date, nullable=True),
        sa.Column('actual_due_date', sa.Date, nullable=False),
        sa.Column('status', postgresql.ENUM('NOT_DUE', 'PENDING', 'IN_PROGRESS', 'PREPARED', 'UNDER_REVIEW', 'FILED', 'ACKNOWLEDGED', 'DELAYED', 'NOT_APPLICABLE', name='compliancestatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('filed_date', sa.Date, nullable=True),
        sa.Column('acknowledgment_number', sa.String(100), nullable=True),
        sa.Column('acknowledgment_date', sa.Date, nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('is_delayed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('delay_days', sa.Integer, nullable=True),
        sa.Column('penalty_paid', sa.Numeric(18, 2), nullable=True),
        sa.Column('penalty_reference', sa.String(100), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('reviewer', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('documents', postgresql.JSONB, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('internal_notes', sa.Text, nullable=True),
        sa.Column('reminder_days', sa.Integer, nullable=True),
        sa.Column('last_reminder_sent', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prepared_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('prepared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('filed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.UniqueConstraint('compliance_item_id', 'period_year', 'period_month', 'period_quarter', name='uq_compliance_instance_period'),
    )
    op.create_index('ix_compliance_instance_item', 'compliance_instance', ['compliance_item_id'])
    op.create_index('ix_compliance_instance_status', 'compliance_instance', ['status'])
    op.create_index('ix_compliance_instance_due', 'compliance_instance', ['actual_due_date'])

    # Create compliance_document table
    op.create_table(
        'compliance_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('document_name', sa.String(200), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_compliance_document_instance', 'compliance_document', ['instance_id'])

    # Create compliance_reminder table
    op.create_table(
        'compliance_reminder',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reminder_type', sa.String(50), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id'), nullable=True),
        sa.Column('recipient_email', sa.String(200), nullable=True),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivery_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_compliance_reminder_instance', 'compliance_reminder', ['instance_id'])


def downgrade() -> None:
    op.drop_table('compliance_reminder')
    op.drop_table('compliance_document')
    op.drop_table('compliance_instance')
    op.drop_table('compliance_item')

    op.execute("DROP TYPE IF EXISTS compliancepriority")
    op.execute("DROP TYPE IF EXISTS compliancestatus")
    op.execute("DROP TYPE IF EXISTS compliancefrequency")
    op.execute("DROP TYPE IF EXISTS regulatorybody")
