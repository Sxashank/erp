"""Add DEBIT_NOTE and CREDIT_NOTE voucher classes

Revision ID: 4aeb501e0e8c
Revises: 74c88413b1e7
Create Date: 2026-01-11 21:29:46.518580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4aeb501e0e8c'
down_revision: Union[str, None] = '74c88413b1e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to voucherclass
    op.execute("ALTER TYPE voucherclass ADD VALUE IF NOT EXISTS 'DEBIT_NOTE'")
    op.execute("ALTER TYPE voucherclass ADD VALUE IF NOT EXISTS 'CREDIT_NOTE'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # The downgrade would require recreating the enum type
    pass
