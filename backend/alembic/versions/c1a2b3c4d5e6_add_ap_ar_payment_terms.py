"""Add AP/AR Payment Terms table

Revision ID: c1a2b3c4d5e6
Revises: bd17a32dbbd4
Create Date: 2026-01-11 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3c4d5e6'
down_revision: Union[str, None] = 'bd17a32dbbd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Payment Terms table
    op.create_table('mst_payment_terms',
        sa.Column('code', sa.String(length=20), nullable=False, comment='Payment terms code e.g. NET30, IMMEDIATE, COD'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Payment terms name e.g. Net 30 Days'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='Description of the payment terms'),
        sa.Column('days', sa.Integer(), nullable=False, comment='Number of days from invoice date for payment due'),
        sa.Column('discount_days', sa.Integer(), nullable=False, comment='Days within which early payment discount applies'),
        sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=False, comment='Early payment discount percentage'),
        sa.Column('organization_id', sa.UUID(), nullable=False, comment='Organization this payment terms belongs to'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mst_payment_terms_code'), 'mst_payment_terms', ['code'], unique=True)
    op.create_index(op.f('ix_mst_payment_terms_organization_id'), 'mst_payment_terms', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mst_payment_terms_organization_id'), table_name='mst_payment_terms')
    op.drop_index(op.f('ix_mst_payment_terms_code'), table_name='mst_payment_terms')
    op.drop_table('mst_payment_terms')
