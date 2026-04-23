"""Add workflow_instance_id FK to entities.

Revision ID: p4q5r6s7t8u9
Revises: o3p4q5r6s7t8
Create Date: 2024-01-12 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p4q5r6s7t8u9'
down_revision: Union[str, None] = 'o3p4q5r6s7t8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add workflow_instance_id to txn_voucher
    op.add_column(
        'txn_voucher',
        sa.Column(
            'workflow_instance_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_foreign_key(
        'fk_voucher_workflow_instance',
        'txn_voucher',
        'wf_workflow_instance',
        ['workflow_instance_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_txn_voucher_workflow_instance_id',
        'txn_voucher',
        ['workflow_instance_id'],
    )

    # Add workflow_instance_id to txn_purchase_bill
    op.add_column(
        'txn_purchase_bill',
        sa.Column(
            'workflow_instance_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_foreign_key(
        'fk_purchase_bill_workflow_instance',
        'txn_purchase_bill',
        'wf_workflow_instance',
        ['workflow_instance_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_txn_purchase_bill_workflow_instance_id',
        'txn_purchase_bill',
        ['workflow_instance_id'],
    )

    # Add workflow_instance_id to txn_sales_invoice
    op.add_column(
        'txn_sales_invoice',
        sa.Column(
            'workflow_instance_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_foreign_key(
        'fk_sales_invoice_workflow_instance',
        'txn_sales_invoice',
        'wf_workflow_instance',
        ['workflow_instance_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_txn_sales_invoice_workflow_instance_id',
        'txn_sales_invoice',
        ['workflow_instance_id'],
    )

    # Add workflow_instance_id to txn_payment
    op.add_column(
        'txn_payment',
        sa.Column(
            'workflow_instance_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        )
    )
    op.create_foreign_key(
        'fk_payment_workflow_instance',
        'txn_payment',
        'wf_workflow_instance',
        ['workflow_instance_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_txn_payment_workflow_instance_id',
        'txn_payment',
        ['workflow_instance_id'],
    )


def downgrade() -> None:
    # Remove from txn_payment
    op.drop_index('ix_txn_payment_workflow_instance_id', table_name='txn_payment')
    op.drop_constraint('fk_payment_workflow_instance', 'txn_payment', type_='foreignkey')
    op.drop_column('txn_payment', 'workflow_instance_id')

    # Remove from txn_sales_invoice
    op.drop_index('ix_txn_sales_invoice_workflow_instance_id', table_name='txn_sales_invoice')
    op.drop_constraint('fk_sales_invoice_workflow_instance', 'txn_sales_invoice', type_='foreignkey')
    op.drop_column('txn_sales_invoice', 'workflow_instance_id')

    # Remove from txn_purchase_bill
    op.drop_index('ix_txn_purchase_bill_workflow_instance_id', table_name='txn_purchase_bill')
    op.drop_constraint('fk_purchase_bill_workflow_instance', 'txn_purchase_bill', type_='foreignkey')
    op.drop_column('txn_purchase_bill', 'workflow_instance_id')

    # Remove from txn_voucher
    op.drop_index('ix_txn_voucher_workflow_instance_id', table_name='txn_voucher')
    op.drop_constraint('fk_voucher_workflow_instance', 'txn_voucher', type_='foreignkey')
    op.drop_column('txn_voucher', 'workflow_instance_id')
