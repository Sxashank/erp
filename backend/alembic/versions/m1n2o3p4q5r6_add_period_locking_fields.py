"""add_period_locking_fields

Revision ID: m1n2o3p4q5r6
Revises: l0m1n2o3p4q5
Create Date: 2026-01-12 14:30:00.000000

Add period locking fields for GST compliance - prevents back-dated entries.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'm1n2o3p4q5r6'
down_revision: Union[str, None] = 'l0m1n2o3p4q5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_locked field (soft lock)
    op.add_column(
        'mst_financial_period',
        sa.Column(
            'is_locked',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Soft lock - prevents new entries but allows viewing'
        )
    )

    # Add locked_at timestamp
    op.add_column(
        'mst_financial_period',
        sa.Column(
            'locked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the period was locked'
        )
    )

    # Add locked_by user reference
    op.add_column(
        'mst_financial_period',
        sa.Column(
            'locked_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('mst_user.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who locked the period'
        )
    )

    # Add lock_reason
    op.add_column(
        'mst_financial_period',
        sa.Column(
            'lock_reason',
            sa.String(50),
            nullable=True,
            comment='GST_RETURN_FILED, PERIOD_CLOSE, AUDIT, etc.'
        )
    )

    # Add gst_return_filed_date
    op.add_column(
        'mst_financial_period',
        sa.Column(
            'gst_return_filed_date',
            sa.Date,
            nullable=True,
            comment='Date until which GST return has been filed (entries on/before this date locked)'
        )
    )


def downgrade() -> None:
    op.drop_column('mst_financial_period', 'gst_return_filed_date')
    op.drop_column('mst_financial_period', 'lock_reason')
    op.drop_column('mst_financial_period', 'locked_by')
    op.drop_column('mst_financial_period', 'locked_at')
    op.drop_column('mst_financial_period', 'is_locked')
