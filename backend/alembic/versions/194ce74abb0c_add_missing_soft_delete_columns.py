"""add_missing_soft_delete_columns

Revision ID: 194ce74abb0c
Revises: f6274ffb4ba5
Create Date: 2026-01-12 01:13:33.449567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '194ce74abb0c'
down_revision: Union[str, None] = 'f6274ffb4ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing soft delete columns to txn_payment_allocation
    op.add_column('txn_payment_allocation', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('txn_payment_allocation', sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key for deleted_by
    op.create_foreign_key(
        'fk_payment_allocation_deleted_by',
        'txn_payment_allocation', 'mst_user',
        ['deleted_by'], ['id'],
        ondelete='SET NULL'
    )

    # Add missing soft delete columns to txn_bank_reconciliation
    op.add_column('txn_bank_reconciliation', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('txn_bank_reconciliation', sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('txn_bank_reconciliation', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    # Add foreign key for deleted_by
    op.create_foreign_key(
        'fk_bank_reconciliation_deleted_by',
        'txn_bank_reconciliation', 'mst_user',
        ['deleted_by'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove from txn_bank_reconciliation
    op.drop_constraint('fk_bank_reconciliation_deleted_by', 'txn_bank_reconciliation', type_='foreignkey')
    op.drop_column('txn_bank_reconciliation', 'is_active')
    op.drop_column('txn_bank_reconciliation', 'deleted_by')
    op.drop_column('txn_bank_reconciliation', 'deleted_at')

    # Remove from txn_payment_allocation
    op.drop_constraint('fk_payment_allocation_deleted_by', 'txn_payment_allocation', type_='foreignkey')
    op.drop_column('txn_payment_allocation', 'deleted_by')
    op.drop_column('txn_payment_allocation', 'deleted_at')
