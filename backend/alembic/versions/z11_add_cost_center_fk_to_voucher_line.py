"""Add cost center foreign key to voucher line.

Revision ID: z11_cost_center_fk
Revises: z10_payment_file
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z11_cost_center_fk'
down_revision = 'z10_payment_file'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columns already exist from earlier migrations, just add indexes and FK constraints
    # Using IF NOT EXISTS for indexes

    # txn_voucher_line
    op.execute("CREATE INDEX IF NOT EXISTS ix_voucher_line_cost_center_id ON txn_voucher_line (cost_center_id)")
    op.create_foreign_key(
        'fk_voucher_line_cost_center',
        'txn_voucher_line',
        'mst_cost_center',
        ['cost_center_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # txn_sales_invoice_line
    op.execute("CREATE INDEX IF NOT EXISTS ix_sales_invoice_line_cost_center_id ON txn_sales_invoice_line (cost_center_id)")
    op.create_foreign_key(
        'fk_sales_invoice_line_cost_center',
        'txn_sales_invoice_line',
        'mst_cost_center',
        ['cost_center_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # txn_purchase_bill_line
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_bill_line_cost_center_id ON txn_purchase_bill_line (cost_center_id)")
    op.create_foreign_key(
        'fk_purchase_bill_line_cost_center',
        'txn_purchase_bill_line',
        'mst_cost_center',
        ['cost_center_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove FK constraints only (columns are from earlier migrations)
    op.drop_constraint('fk_purchase_bill_line_cost_center', 'txn_purchase_bill_line', type_='foreignkey')
    op.drop_constraint('fk_sales_invoice_line_cost_center', 'txn_sales_invoice_line', type_='foreignkey')
    op.drop_constraint('fk_voucher_line_cost_center', 'txn_voucher_line', type_='foreignkey')

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_purchase_bill_line_cost_center_id")
    op.execute("DROP INDEX IF EXISTS ix_sales_invoice_line_cost_center_id")
    op.execute("DROP INDEX IF EXISTS ix_voucher_line_cost_center_id")
