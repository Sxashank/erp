"""add_audit_trail_tables

Revision ID: k9i0j1k2l3m4
Revises: 194ce74abb0c
Create Date: 2026-01-12 13:30:00.000000

MCA April 2023 compliant audit trail tables for field-level change tracking.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'k9i0j1k2l3m4'
down_revision: Union[str, None] = '194ce74abb0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create txn_audit_log table
    op.create_table(
        'txn_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_reference', sa.String(100), nullable=True,
                  comment='Human-readable reference (voucher number, invoice number, etc.)'),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='User ID who made the change'),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True,
                  comment='Previous field values before change'),
        sa.Column('new_values', postgresql.JSONB, nullable=True,
                  comment='New field values after change'),
        sa.Column('changed_fields', postgresql.ARRAY(sa.String), nullable=True,
                  comment='List of field names that were changed'),
        sa.Column('change_reason', sa.Text, nullable=True,
                  comment='User-provided justification for the change'),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        comment='MCA-compliant audit trail - IMMUTABLE table'
    )

    # Create indexes for txn_audit_log
    op.create_index('ix_audit_entity', 'txn_audit_log', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_org_timestamp', 'txn_audit_log', ['organization_id', 'changed_at'])
    op.create_index('ix_audit_changed_by', 'txn_audit_log', ['changed_by'])
    op.create_index('ix_audit_log_organization_id', 'txn_audit_log', ['organization_id'])

    # Create txn_line_item_history table
    op.create_table(
        'txn_line_item_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_audit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('line_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='Original line item ID'),
        sa.Column('line_number', sa.Integer, nullable=False,
                  comment='Line number within the transaction'),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['parent_audit_id'], ['txn_audit_log.id'], ondelete='CASCADE'),
        comment='Line item change history - linked to parent audit log'
    )

    # Create indexes for txn_line_item_history
    op.create_index('ix_line_history_parent', 'txn_line_item_history', ['parent_audit_id'])
    op.create_index('ix_line_history_line', 'txn_line_item_history', ['entity_type', 'line_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_line_history_line', 'txn_line_item_history')
    op.drop_index('ix_line_history_parent', 'txn_line_item_history')

    # Drop txn_line_item_history table
    op.drop_table('txn_line_item_history')

    # Drop indexes for txn_audit_log
    op.drop_index('ix_audit_log_organization_id', 'txn_audit_log')
    op.drop_index('ix_audit_changed_by', 'txn_audit_log')
    op.drop_index('ix_audit_org_timestamp', 'txn_audit_log')
    op.drop_index('ix_audit_entity', 'txn_audit_log')

    # Drop txn_audit_log table
    op.drop_table('txn_audit_log')
