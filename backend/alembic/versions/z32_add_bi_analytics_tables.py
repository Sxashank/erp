"""Add BI/Analytics module tables.

Revision ID: z32_bi_analytics
Revises: z31_kyc_compliance
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z32_bi_analytics'
down_revision: Union[str, None] = 'z31_kyc_compliance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create widget_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE widget_type AS ENUM (
                'KPI_CARD', 'LINE_CHART', 'BAR_CHART', 'PIE_CHART', 'DONUT_CHART',
                'AREA_CHART', 'DATA_TABLE', 'TEXT_MARKDOWN', 'GAUGE_PROGRESS'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create chart_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chart_type AS ENUM (
                'LINE', 'BAR', 'PIE', 'DONUT', 'AREA', 'GAUGE', 'KPI', 'TABLE'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create bi_module enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bi_module AS ENUM (
                'FINANCE', 'LENDING', 'HR', 'TREASURY', 'PROCUREMENT',
                'INVENTORY', 'TAX', 'COLLECTIONS', 'LEGAL', 'PORTAL'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create datasource_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE datasource_type AS ENUM (
                'API_ENDPOINT', 'SQL_QUERY', 'STATIC'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create api_method enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE api_method AS ENUM ('GET', 'POST');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create bi_data_source table
    op.create_table(
        'bi_data_source',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_type', sa.String(20), nullable=False),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('api_method', sa.String(10), nullable=True),
        sa.Column('query_template', sa.Text, nullable=True),
        sa.Column('static_data', postgresql.JSONB, nullable=True),
        sa.Column('parameters_schema', postgresql.JSONB, nullable=True),
        sa.Column('response_transform', postgresql.JSONB, nullable=True),
        sa.Column('cache_ttl_seconds', sa.Integer, nullable=True, server_default='300'),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_data_source_code', 'bi_data_source', ['code'], unique=True)
    op.create_index('ix_bi_data_source_org', 'bi_data_source', ['organization_id'])

    # Create bi_chart_definition table
    op.create_table(
        'bi_chart_definition',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('module', sa.String(20), nullable=False),
        sa.Column('chart_type', sa.String(20), nullable=False),
        sa.Column('default_data_source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('data_mapping', postgresql.JSONB, nullable=True),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='false'),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['default_data_source_id'], ['bi_data_source.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_chart_code_unique', 'bi_chart_definition', ['code'], unique=True)
    op.create_index('ix_bi_chart_org_module', 'bi_chart_definition', ['organization_id', 'module'])
    op.create_index('ix_bi_chart_module', 'bi_chart_definition', ['module'])

    # Create bi_chart_role_access table
    op.create_table(
        'bi_chart_role_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('chart_definition_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chart_definition_id'], ['bi_chart_definition.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_chart_role_access_unique', 'bi_chart_role_access', ['chart_definition_id', 'role_id'], unique=True)
    op.create_index('ix_bi_chart_role_access_chart', 'bi_chart_role_access', ['chart_definition_id'])
    op.create_index('ix_bi_chart_role_access_role', 'bi_chart_role_access', ['role_id'])

    # Create bi_dashboard table
    op.create_table(
        'bi_dashboard',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('layout_config', postgresql.JSONB, nullable=True),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('auto_refresh', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('refresh_interval_seconds', sa.Integer, nullable=False, server_default='60'),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_dashboard_org_code', 'bi_dashboard', ['organization_id', 'code'], unique=True)
    op.create_index('ix_bi_dashboard_org', 'bi_dashboard', ['organization_id'])

    # Create bi_dashboard_widget table
    op.create_table(
        'bi_dashboard_widget',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dashboard_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_key', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('widget_type', sa.String(20), nullable=False),
        sa.Column('chart_definition_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('grid_x', sa.Integer, nullable=False, server_default='0'),
        sa.Column('grid_y', sa.Integer, nullable=False, server_default='0'),
        sa.Column('grid_w', sa.Integer, nullable=False, server_default='4'),
        sa.Column('grid_h', sa.Integer, nullable=False, server_default='3'),
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['bi_dashboard.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chart_definition_id'], ['bi_chart_definition.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['data_source_id'], ['bi_data_source.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_widget_dashboard_key', 'bi_dashboard_widget', ['dashboard_id', 'widget_key'], unique=True)
    op.create_index('ix_bi_widget_dashboard', 'bi_dashboard_widget', ['dashboard_id'])
    op.create_index('ix_bi_widget_chart', 'bi_dashboard_widget', ['chart_definition_id'])

    # Create bi_dashboard_role_access table
    op.create_table(
        'bi_dashboard_role_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dashboard_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('can_view', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('can_edit', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('show_on_landing', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('landing_order', sa.Integer, nullable=False, server_default='0'),
        # Audit columns
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['bi_dashboard.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id']),
    )
    op.create_index('ix_bi_dashboard_role_access_unique', 'bi_dashboard_role_access', ['dashboard_id', 'role_id'], unique=True)
    op.create_index('ix_bi_dashboard_role_landing', 'bi_dashboard_role_access', ['role_id', 'show_on_landing'])
    op.create_index('ix_bi_dashboard_role_access_dashboard', 'bi_dashboard_role_access', ['dashboard_id'])
    op.create_index('ix_bi_dashboard_role_access_role', 'bi_dashboard_role_access', ['role_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('bi_dashboard_role_access')
    op.drop_table('bi_dashboard_widget')
    op.drop_table('bi_dashboard')
    op.drop_table('bi_chart_role_access')
    op.drop_table('bi_chart_definition')
    op.drop_table('bi_data_source')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS api_method")
    op.execute("DROP TYPE IF EXISTS datasource_type")
    op.execute("DROP TYPE IF EXISTS bi_module")
    op.execute("DROP TYPE IF EXISTS chart_type")
    op.execute("DROP TYPE IF EXISTS widget_type")
