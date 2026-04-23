"""create_workflow_tables

Revision ID: o3p4q5r6s7t8
Revises: n2o3p4q5r6s7
Create Date: 2026-01-12 17:00:00.000000

Create workflow engine tables for customizable approval workflows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'o3p4q5r6s7t8'
down_revision: Union[str, None] = 'n2o3p4q5r6s7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    workflow_entity_type = postgresql.ENUM(
        'VOUCHER', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'JOURNAL_ENTRY',
        name='workflowentitytype',
        create_type=False
    )
    workflow_entity_type.create(op.get_bind(), checkfirst=True)

    workflow_step_type = postgresql.ENUM(
        'APPROVAL', 'NOTIFICATION', 'CONDITIONAL', 'PARALLEL_GATE',
        name='workflowsteptype',
        create_type=False
    )
    workflow_step_type.create(op.get_bind(), checkfirst=True)

    approval_mode = postgresql.ENUM(
        'SEQUENTIAL', 'PARALLEL_ANY', 'PARALLEL_ALL',
        name='approvalmode',
        create_type=False
    )
    approval_mode.create(op.get_bind(), checkfirst=True)

    approver_type = postgresql.ENUM(
        'USER', 'ROLE', 'DESIGNATION', 'DEPARTMENT_HEAD', 'REPORTING_MANAGER', 'DYNAMIC',
        name='approvertype',
        create_type=False
    )
    approver_type.create(op.get_bind(), checkfirst=True)

    escalation_type = postgresql.ENUM(
        'NOTIFY', 'REASSIGN', 'AUTO_APPROVE', 'AUTO_REJECT',
        name='escalationtype',
        create_type=False
    )
    escalation_type.create(op.get_bind(), checkfirst=True)

    workflow_instance_status = postgresql.ENUM(
        'PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'CANCELLED', 'ESCALATED',
        name='workflowinstancestatus',
        create_type=False
    )
    workflow_instance_status.create(op.get_bind(), checkfirst=True)

    task_status = postgresql.ENUM(
        'PENDING', 'APPROVED', 'REJECTED', 'ESCALATED', 'SKIPPED',
        name='taskstatus',
        create_type=False
    )
    task_status.create(op.get_bind(), checkfirst=True)

    step_action = postgresql.ENUM(
        'NEXT', 'COMPLETE', 'GOTO', 'REJECT', 'PREVIOUS',
        name='stepaction',
        create_type=False
    )
    step_action.create(op.get_bind(), checkfirst=True)

    # Create wf_notification_template table (needed first for FK references)
    op.create_table(
        'wf_notification_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('VOUCHER', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'JOURNAL_ENTRY', name='workflowentitytype', create_type=False), nullable=True),
        sa.Column('email_subject', sa.String(500), nullable=False),
        sa.Column('email_body', sa.Text, nullable=False),
        sa.Column('notification_title', sa.String(200), nullable=True),
        sa.Column('notification_body', sa.Text, nullable=True),
        sa.Column('available_variables', postgresql.ARRAY(sa.String), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_notification_template_org', 'wf_notification_template', ['organization_id'])
    op.create_index('ix_wf_notification_template_code', 'wf_notification_template', ['code'])

    # Create wf_workflow_definition table
    op.create_table(
        'wf_workflow_definition',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('entity_type', postgresql.ENUM('VOUCHER', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'JOURNAL_ENTRY', name='workflowentitytype', create_type=False), nullable=False),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('priority', sa.Integer, default=0, nullable=False),
        sa.Column('activation_conditions', postgresql.JSONB, nullable=True),
        sa.Column('allow_parallel_branches', sa.Boolean, default=False, nullable=False),
        sa.Column('require_comments_on_reject', sa.Boolean, default=True, nullable=False),
        sa.Column('notify_initiator_on_complete', sa.Boolean, default=True, nullable=False),
        sa.Column('allow_withdrawal', sa.Boolean, default=True, nullable=False),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_definition_org', 'wf_workflow_definition', ['organization_id'])
    op.create_index('ix_wf_definition_entity_type', 'wf_workflow_definition', ['entity_type'])
    op.create_index('ix_wf_definition_code', 'wf_workflow_definition', ['code'])
    op.create_index('ix_wf_definition_org_entity', 'wf_workflow_definition', ['organization_id', 'entity_type'])
    op.create_index('ix_wf_definition_org_code', 'wf_workflow_definition', ['organization_id', 'code'], unique=True)

    # Create wf_workflow_step table
    op.create_table(
        'wf_workflow_step',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_definition.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('step_type', postgresql.ENUM('APPROVAL', 'NOTIFICATION', 'CONDITIONAL', 'PARALLEL_GATE', name='workflowsteptype', create_type=False), nullable=False, server_default='APPROVAL'),
        sa.Column('approval_mode', postgresql.ENUM('SEQUENTIAL', 'PARALLEL_ANY', 'PARALLEL_ALL', name='approvalmode', create_type=False), nullable=False, server_default='SEQUENTIAL'),
        sa.Column('parent_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('branch_name', sa.String(100), nullable=True),
        sa.Column('entry_conditions', postgresql.JSONB, nullable=True),
        sa.Column('exit_conditions', postgresql.JSONB, nullable=True),
        sa.Column('on_approve_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('on_reject_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('on_approve_action', postgresql.ENUM('NEXT', 'COMPLETE', 'GOTO', 'REJECT', 'PREVIOUS', name='stepaction', create_type=False), nullable=False, server_default='NEXT'),
        sa.Column('on_reject_action', postgresql.ENUM('NEXT', 'COMPLETE', 'GOTO', 'REJECT', 'PREVIOUS', name='stepaction', create_type=False), nullable=False, server_default='REJECT'),
        sa.Column('allow_delegation', sa.Boolean, default=False, nullable=False),
        sa.Column('sla_hours', sa.Integer, nullable=True),
        sa.Column('reminder_hours', sa.Integer, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_step_definition', 'wf_workflow_step', ['workflow_definition_id'])

    # Create wf_approval_rule table
    op.create_table(
        'wf_approval_rule',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence', sa.Integer, default=1, nullable=False),
        sa.Column('approver_type', postgresql.ENUM('USER', 'ROLE', 'DESIGNATION', 'DEPARTMENT_HEAD', 'REPORTING_MANAGER', 'DYNAMIC', name='approvertype', create_type=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_role.id', ondelete='SET NULL'), nullable=True),
        sa.Column('designation', sa.String(100), nullable=True),
        sa.Column('dynamic_field', sa.String(200), nullable=True),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('can_self_approve', sa.Boolean, default=False, nullable=False),
        sa.Column('fallback_to_admin', sa.Boolean, default=True, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_approval_rule_step', 'wf_approval_rule', ['workflow_step_id'])

    # Create wf_escalation_rule table
    op.create_table(
        'wf_escalation_rule',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.Integer, default=1, nullable=False),
        sa.Column('timeout_hours', sa.Integer, nullable=False),
        sa.Column('escalation_type', postgresql.ENUM('NOTIFY', 'REASSIGN', 'AUTO_APPROVE', 'AUTO_REJECT', name='escalationtype', create_type=False), nullable=False),
        sa.Column('escalate_to_type', postgresql.ENUM('USER', 'ROLE', 'DESIGNATION', 'DEPARTMENT_HEAD', 'REPORTING_MANAGER', 'DYNAMIC', name='approvertype', create_type=False), nullable=True),
        sa.Column('escalate_to_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('escalate_to_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_role.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notify_current_approver', sa.Boolean, default=True, nullable=False),
        sa.Column('notify_initiator', sa.Boolean, default=False, nullable=False),
        sa.Column('notification_template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_notification_template.id', ondelete='SET NULL'), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_escalation_rule_step', 'wf_escalation_rule', ['workflow_step_id'])

    # Create wf_workflow_instance table
    op.create_table(
        'wf_workflow_instance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_definition.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('VOUCHER', 'PURCHASE_BILL', 'SALES_INVOICE', 'PAYMENT', 'JOURNAL_ENTRY', name='workflowentitytype', create_type=False), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_reference', sa.String(100), nullable=False),
        sa.Column('current_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('current_step_number', sa.Integer, default=1, nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'CANCELLED', 'ESCALATED', name='workflowinstancestatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('context_data', postgresql.JSONB, nullable=True),
        sa.Column('active_parallel_branches', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('completed_parallel_branches', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cancellation_reason', sa.String(500), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_instance_definition', 'wf_workflow_instance', ['workflow_definition_id'])
    op.create_index('ix_wf_instance_org', 'wf_workflow_instance', ['organization_id'])
    op.create_index('ix_wf_instance_entity_type', 'wf_workflow_instance', ['entity_type'])
    op.create_index('ix_wf_instance_entity_id', 'wf_workflow_instance', ['entity_id'])
    op.create_index('ix_wf_instance_status', 'wf_workflow_instance', ['status'])
    op.create_index('ix_wf_instance_entity', 'wf_workflow_instance', ['entity_type', 'entity_id'])
    op.create_index('ix_wf_instance_org_status', 'wf_workflow_instance', ['organization_id', 'status'])

    # Create wf_workflow_task table
    op.create_table(
        'wf_workflow_task',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workflow_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ESCALATED', 'SKIPPED', name='taskstatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('action_taken', sa.String(50), nullable=True),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('acted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delegated_from', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('delegated_reason', sa.String(500), nullable=True),
        sa.Column('delegated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_level', sa.Integer, default=0, nullable=False),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_from', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_overdue', sa.Boolean, default=False, nullable=False),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sequence', sa.Integer, default=1, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_task_instance', 'wf_workflow_task', ['workflow_instance_id'])
    op.create_index('ix_wf_task_step', 'wf_workflow_task', ['workflow_step_id'])
    op.create_index('ix_wf_task_assigned_to', 'wf_workflow_task', ['assigned_to'])
    op.create_index('ix_wf_task_status', 'wf_workflow_task', ['status'])
    op.create_index('ix_wf_task_assignee_status', 'wf_workflow_task', ['assigned_to', 'status'])
    op.create_index('ix_wf_task_due', 'wf_workflow_task', ['due_at'])

    # Create wf_workflow_history table
    op.create_table(
        'wf_workflow_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('action_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=False),
        sa.Column('action_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('from_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_step.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('action_metadata', postgresql.JSONB, nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_task.id', ondelete='SET NULL'), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_wf_history_instance', 'wf_workflow_history', ['workflow_instance_id'])
    op.create_index('ix_wf_history_action', 'wf_workflow_history', ['action'])
    op.create_index('ix_wf_history_instance_action', 'wf_workflow_history', ['workflow_instance_id', 'action_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('wf_workflow_history')
    op.drop_table('wf_workflow_task')
    op.drop_table('wf_workflow_instance')
    op.drop_table('wf_escalation_rule')
    op.drop_table('wf_approval_rule')
    op.drop_table('wf_workflow_step')
    op.drop_table('wf_workflow_definition')
    op.drop_table('wf_notification_template')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS stepaction")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS workflowinstancestatus")
    op.execute("DROP TYPE IF EXISTS escalationtype")
    op.execute("DROP TYPE IF EXISTS approvertype")
    op.execute("DROP TYPE IF EXISTS approvalmode")
    op.execute("DROP TYPE IF EXISTS workflowsteptype")
    op.execute("DROP TYPE IF EXISTS workflowentitytype")
