"""fix_payment_status_enum

Revision ID: f6274ffb4ba5
Revises: f2c8b5ae0598
Create Date: 2026-01-12 00:55:06.404721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6274ffb4ba5'
down_revision: Union[str, None] = 'f2c8b5ae0598'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The current 'paymentstatus' enum has UNPAID/PARTIALLY_PAID/PAID
    # which is used for bill/invoice payment status.
    # The Payment model needs DRAFT/SUBMITTED/APPROVED/POSTED/CANCELLED.

    # Create new enum for transaction payment status
    op.execute("CREATE TYPE txnpaymentstatus AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'POSTED', 'CANCELLED')")

    # Alter the column to use the new enum type
    # First drop the default
    op.execute("ALTER TABLE txn_payment ALTER COLUMN status DROP DEFAULT")

    # Then change the column type
    op.execute("""
        ALTER TABLE txn_payment
        ALTER COLUMN status TYPE txnpaymentstatus
        USING 'DRAFT'::txnpaymentstatus
    """)

    # Set new default
    op.execute("ALTER TABLE txn_payment ALTER COLUMN status SET DEFAULT 'DRAFT'")


def downgrade() -> None:
    # Revert: change column back to paymentstatus
    op.execute("ALTER TABLE txn_payment ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE txn_payment
        ALTER COLUMN status TYPE paymentstatus
        USING 'UNPAID'::paymentstatus
    """)
    op.execute("ALTER TABLE txn_payment ALTER COLUMN status SET DEFAULT 'UNPAID'")

    # Drop the new enum
    op.execute("DROP TYPE txnpaymentstatus")
