"""Add cost center table.

Revision ID: z9_cost_center
Revises: z8_add_tds_return
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z9_cost_center'
down_revision = 'z8_add_tds_return'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cost center table
    op.create_table(
        'mst_cost_center',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Identification
        sa.Column('code', sa.String(20), nullable=False, comment='Unique code within organization'),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Hierarchy
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Parent cost center for hierarchy'),
        sa.Column('level', sa.Integer, nullable=False, server_default='0', comment='Hierarchy level (0 = root)'),
        sa.Column('path', sa.String(500), nullable=True, comment="Full path for hierarchy queries (e.g., '/root/dept/subdept')"),

        # Classification
        sa.Column('category', sa.String(50), nullable=True, comment='Category: DEPARTMENT, PROJECT, BRANCH, PRODUCT_LINE, etc.'),
        sa.Column('cost_type', sa.String(20), nullable=True, comment='Type: DIRECT, INDIRECT, OVERHEAD'),

        # Budget control
        sa.Column('has_budget', sa.Boolean, nullable=False, server_default='false', comment='Whether budget tracking is enabled'),
        sa.Column('annual_budget', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='Annual budget amount'),
        sa.Column('budget_variance_threshold', sa.Numeric(5, 2), nullable=False, server_default='10.00', comment='Variance percentage to trigger alerts'),

        # Allocation settings
        sa.Column('is_allocatable', sa.Boolean, nullable=False, server_default='true', comment='Can expenses be allocated to this cost center'),
        sa.Column('allocation_basis', sa.String(50), nullable=True, comment='Basis for cost allocation: DIRECT, HEADCOUNT, AREA, REVENUE, etc.'),
        sa.Column('allocation_percentage', sa.Numeric(5, 2), nullable=False, server_default='100.00', comment='Default allocation percentage'),

        # Responsible person
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Manager responsible for this cost center'),
        sa.Column('manager_name', sa.String(200), nullable=True),

        # Validity period
        sa.Column('effective_from', sa.Date, nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('effective_to', sa.Date, nullable=True, comment='End date (null = currently active)'),

        # GL account mapping
        sa.Column('default_expense_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Default expense account for this cost center'),

        # External reference
        sa.Column('external_code', sa.String(50), nullable=True, comment='External system reference code'),

        # Additional metadata
        sa.Column('extra_data', postgresql.JSONB, nullable=True),

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
        sa.ForeignKeyConstraint(['parent_id'], ['mst_cost_center.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_cost_center_organization_id', 'mst_cost_center', ['organization_id'])
    op.create_index('ix_cost_center_parent_id', 'mst_cost_center', ['parent_id'])
    op.create_index('ix_cost_center_code', 'mst_cost_center', ['code'])
    op.create_index('ix_cost_center_org_code', 'mst_cost_center', ['organization_id', 'code'], unique=True)
    op.create_index('ix_cost_center_path', 'mst_cost_center', ['path'])
    op.create_index('ix_cost_center_category', 'mst_cost_center', ['category'])
    op.create_index('ix_cost_center_has_budget', 'mst_cost_center', ['has_budget'])
    op.create_index('ix_cost_center_is_allocatable', 'mst_cost_center', ['is_allocatable'])
    op.create_index('ix_cost_center_is_active', 'mst_cost_center', ['is_active'])

    # Note: cost_center_id column on txn_gl_entry is already added in z6
    # Just create the FK constraint here now that the cost_center table exists
    op.create_foreign_key(
        'fk_gl_entry_cost_center',
        'txn_gl_entry',
        'mst_cost_center',
        ['cost_center_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop the FK constraint (column/index are in z6 downgrade)
    op.drop_constraint('fk_gl_entry_cost_center', 'txn_gl_entry', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_cost_center_is_active', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_is_allocatable', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_has_budget', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_category', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_path', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_org_code', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_code', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_parent_id', table_name='mst_cost_center')
    op.drop_index('ix_cost_center_organization_id', table_name='mst_cost_center')

    # Drop table
    op.drop_table('mst_cost_center')
