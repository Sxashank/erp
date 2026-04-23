"""standardize_audit_column_names

Revision ID: f2c8b5ae0598
Revises: j8h9i0j1k2l3
Create Date: 2026-01-12 00:52:44.781669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2c8b5ae0598'
down_revision: Union[str, None] = 'j8h9i0j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Standardize audit column names to remove _id suffix
    # Tables with _id suffix: txn_bank_reconciliation, txn_bank_statement, txn_payment, txn_payment_allocation

    # txn_bank_reconciliation
    op.alter_column('txn_bank_reconciliation', 'created_by_id', new_column_name='created_by')
    op.alter_column('txn_bank_reconciliation', 'updated_by_id', new_column_name='updated_by')

    # txn_bank_statement
    op.alter_column('txn_bank_statement', 'created_by_id', new_column_name='created_by')
    op.alter_column('txn_bank_statement', 'updated_by_id', new_column_name='updated_by')
    op.alter_column('txn_bank_statement', 'deleted_by_id', new_column_name='deleted_by')

    # txn_payment
    op.alter_column('txn_payment', 'created_by_id', new_column_name='created_by')
    op.alter_column('txn_payment', 'updated_by_id', new_column_name='updated_by')
    op.alter_column('txn_payment', 'deleted_by_id', new_column_name='deleted_by')

    # txn_payment_allocation
    op.alter_column('txn_payment_allocation', 'created_by_id', new_column_name='created_by')
    op.alter_column('txn_payment_allocation', 'updated_by_id', new_column_name='updated_by')


def downgrade() -> None:
    # Revert: add _id suffix back

    # txn_payment_allocation
    op.alter_column('txn_payment_allocation', 'created_by', new_column_name='created_by_id')
    op.alter_column('txn_payment_allocation', 'updated_by', new_column_name='updated_by_id')

    # txn_payment
    op.alter_column('txn_payment', 'created_by', new_column_name='created_by_id')
    op.alter_column('txn_payment', 'updated_by', new_column_name='updated_by_id')
    op.alter_column('txn_payment', 'deleted_by', new_column_name='deleted_by_id')

    # txn_bank_statement
    op.alter_column('txn_bank_statement', 'created_by', new_column_name='created_by_id')
    op.alter_column('txn_bank_statement', 'updated_by', new_column_name='updated_by_id')
    op.alter_column('txn_bank_statement', 'deleted_by', new_column_name='deleted_by_id')

    # txn_bank_reconciliation
    op.alter_column('txn_bank_reconciliation', 'created_by', new_column_name='created_by_id')
    op.alter_column('txn_bank_reconciliation', 'updated_by', new_column_name='updated_by_id')
