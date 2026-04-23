"""Fix voucher_line party_type column.

Revision ID: j8h9i0j1k2l3
Revises: i7g8h9i0j1k2
Create Date: 2024-01-15 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j8h9i0j1k2l3'
down_revision: Union[str, None] = 'i7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if party_type column exists before adding
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'txn_voucher_line' AND column_name = 'party_type'
    """))
    if result.fetchone() is None:
        op.add_column(
            'txn_voucher_line',
            sa.Column(
                'party_type',
                postgresql.ENUM('CUSTOMER', 'VENDOR', 'EMPLOYEE', name='partytype', create_type=False),
                nullable=True,
                comment='Type of party - CUSTOMER, VENDOR, EMPLOYEE'
            )
        )


def downgrade() -> None:
    op.drop_column('txn_voucher_line', 'party_type')
