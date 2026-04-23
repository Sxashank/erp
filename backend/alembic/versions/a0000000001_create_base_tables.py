"""Create base tables - Organization, User, Unit, Role, Permission

Revision ID: a0000000001
Revises:
Create Date: 2026-01-13 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0000000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Organization table first (without audit FK constraints)
    op.create_table('mst_organization',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('legal_name', sa.String(length=300), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cin', sa.String(length=25), nullable=True),
        sa.Column('pan', sa.String(length=10), nullable=False),
        sa.Column('tan', sa.String(length=10), nullable=True),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('rbi_registration', sa.String(length=50), nullable=True),
        sa.Column('reg_address_line1', sa.String(length=255), nullable=True),
        sa.Column('reg_address_line2', sa.String(length=255), nullable=True),
        sa.Column('reg_city', sa.String(length=100), nullable=True),
        sa.Column('reg_district', sa.String(length=100), nullable=True),
        sa.Column('reg_state_code', sa.String(length=2), nullable=True),
        sa.Column('reg_pincode', sa.String(length=10), nullable=True),
        sa.Column('reg_country', sa.String(length=50), server_default='India', nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('base_currency', sa.String(length=3), server_default='INR', nullable=False),
        sa.Column('financial_year_start_month', sa.Integer(), server_default='4', nullable=False),
        sa.Column('logo_path', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cin'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('pan'),
        sa.UniqueConstraint('tan')
    )
    op.create_index(op.f('ix_mst_organization_code'), 'mst_organization', ['code'], unique=True)
    op.create_index(op.f('ix_mst_organization_status'), 'mst_organization', ['status'], unique=False)

    # 2. Create User table
    op.create_table('mst_user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('employee_code', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('auth_type', sa.String(length=20), server_default='LOCAL', nullable=False),
        sa.Column('mfa_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('mfa_secret', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(length=50), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('must_change_password', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='Asia/Kolkata', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_code'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_mst_user_username'), 'mst_user', ['username'], unique=True)
    op.create_index(op.f('ix_mst_user_email'), 'mst_user', ['email'], unique=True)
    op.create_index(op.f('ix_mst_user_status'), 'mst_user', ['status'], unique=False)

    # 3. Create Unit table
    op.create_table('mst_unit',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_type', sa.String(length=30), server_default='BRANCH', nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('path', sa.String(length=500), nullable=True),
        sa.Column('is_separate_accounting', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('gst_state_code', sa.String(length=2), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state_code', sa.String(length=2), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=50), server_default='India', nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('manager_name', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('is_head_office', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_mst_unit_code'), 'mst_unit', ['code'], unique=True)
    op.create_index(op.f('ix_mst_unit_organization_id'), 'mst_unit', ['organization_id'], unique=False)
    op.create_index(op.f('ix_mst_unit_parent_unit_id'), 'mst_unit', ['parent_unit_id'], unique=False)
    op.create_index(op.f('ix_mst_unit_path'), 'mst_unit', ['path'], unique=False)
    op.create_index(op.f('ix_mst_unit_status'), 'mst_unit', ['status'], unique=False)

    # 4. Add FK constraint from User to Unit (now that Unit exists)
    op.create_foreign_key(
        'fk_mst_user_default_unit_id',
        'mst_user',
        'mst_unit',
        ['default_unit_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 5. Add audit FK constraints to Organization (now that User exists)
    op.create_foreign_key(
        'fk_mst_organization_created_by',
        'mst_organization',
        'mst_user',
        ['created_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_mst_organization_updated_by',
        'mst_organization',
        'mst_user',
        ['updated_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_mst_organization_deleted_by',
        'mst_organization',
        'mst_user',
        ['deleted_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # 6. Add audit FK constraints to User (self-referencing)
    op.create_foreign_key(
        'fk_mst_user_created_by',
        'mst_user',
        'mst_user',
        ['created_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_mst_user_updated_by',
        'mst_user',
        'mst_user',
        ['updated_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_mst_user_deleted_by',
        'mst_user',
        'mst_user',
        ['deleted_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # 7. Create Permission table
    op.create_table('mst_permission',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_mst_permission_code'), 'mst_permission', ['code'], unique=True)
    op.create_index(op.f('ix_mst_permission_module'), 'mst_permission', ['module'], unique=False)

    # 8. Create Role table
    op.create_table('mst_role',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_mst_role_code'), 'mst_role', ['code'], unique=True)

    # 9. Create Role-Permission mapping table
    op.create_table('map_role_permission',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['mst_permission.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    op.create_index(op.f('ix_map_role_permission_role_id'), 'map_role_permission', ['role_id'], unique=False)
    op.create_index(op.f('ix_map_role_permission_permission_id'), 'map_role_permission', ['permission_id'], unique=False)

    # 10. Create User-Role mapping table
    op.create_table('map_user_role',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['mst_role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('user_id', 'role_id', 'unit_id', name='uq_user_role_unit'),
    )
    op.create_index(op.f('ix_map_user_role_user_id'), 'map_user_role', ['user_id'], unique=False)
    op.create_index(op.f('ix_map_user_role_role_id'), 'map_user_role', ['role_id'], unique=False)
    op.create_index(op.f('ix_map_user_role_unit_id'), 'map_user_role', ['unit_id'], unique=False)

    # 11. Create User Session table
    op.create_table('mst_user_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_mst_user_session_user_id'), 'mst_user_session', ['user_id'], unique=False)
    op.create_index(op.f('ix_mst_user_session_refresh_token_hash'), 'mst_user_session', ['refresh_token_hash'], unique=True)


def downgrade() -> None:
    op.drop_table('mst_user_session')
    op.drop_table('map_user_role')
    op.drop_table('map_role_permission')
    op.drop_table('mst_role')
    op.drop_table('mst_permission')

    # Drop FK constraints from organization
    op.drop_constraint('fk_mst_organization_created_by', 'mst_organization', type_='foreignkey')
    op.drop_constraint('fk_mst_organization_updated_by', 'mst_organization', type_='foreignkey')
    op.drop_constraint('fk_mst_organization_deleted_by', 'mst_organization', type_='foreignkey')

    # Drop FK constraints from user
    op.drop_constraint('fk_mst_user_created_by', 'mst_user', type_='foreignkey')
    op.drop_constraint('fk_mst_user_updated_by', 'mst_user', type_='foreignkey')
    op.drop_constraint('fk_mst_user_deleted_by', 'mst_user', type_='foreignkey')
    op.drop_constraint('fk_mst_user_default_unit_id', 'mst_user', type_='foreignkey')

    op.drop_table('mst_unit')
    op.drop_table('mst_user')
    op.drop_table('mst_organization')
