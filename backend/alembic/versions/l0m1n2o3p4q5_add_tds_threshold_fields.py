"""add_tds_threshold_fields

Revision ID: l0m1n2o3p4q5
Revises: k9i0j1k2l3m4
Create Date: 2026-01-12 14:00:00.000000

Add vendor and financial year tracking to TDS entries for aggregate threshold validation.
Add surcharge slabs configuration to TDS sections.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'l0m1n2o3p4q5'
down_revision: Union[str, None] = 'k9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vendor_id to TDS entry for aggregate tracking
    op.add_column(
        'txn_tds_entry',
        sa.Column(
            'vendor_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('mst_vendor.id', ondelete='SET NULL'),
            nullable=True,
            comment='Vendor for aggregate TDS threshold tracking'
        )
    )
    op.create_index('ix_tds_entry_vendor', 'txn_tds_entry', ['vendor_id'])

    # Add financial_year_id for aggregate tracking
    op.add_column(
        'txn_tds_entry',
        sa.Column(
            'financial_year_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('mst_financial_year.id', ondelete='SET NULL'),
            nullable=True,
            comment='Financial year for aggregate threshold tracking'
        )
    )
    op.create_index('ix_tds_entry_fy', 'txn_tds_entry', ['financial_year_id'])

    # Add threshold tracking fields
    op.add_column(
        'txn_tds_entry',
        sa.Column(
            'is_threshold_crossed',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='True if this entry crossed single/aggregate threshold'
        )
    )
    op.add_column(
        'txn_tds_entry',
        sa.Column(
            'aggregate_amount_ytd',
            sa.Numeric(18, 2),
            nullable=False,
            server_default='0',
            comment='Running aggregate amount for vendor in this FY at time of entry'
        )
    )
    op.add_column(
        'txn_tds_entry',
        sa.Column(
            'threshold_reason',
            sa.String(50),
            nullable=True,
            comment='Reason for TDS: SINGLE_THRESHOLD, AGGREGATE_THRESHOLD, MANUAL'
        )
    )

    # Add composite index for vendor aggregate queries
    op.create_index(
        'ix_tds_entry_vendor_fy_section',
        'txn_tds_entry',
        ['vendor_id', 'financial_year_id', 'tds_section_id']
    )

    # Add surcharge_slabs JSONB column to TDS section
    op.add_column(
        'mst_tds_section',
        sa.Column(
            'surcharge_slabs',
            postgresql.JSONB,
            nullable=True,
            comment='Surcharge rate slabs by amount and deductee type'
        )
    )


def downgrade() -> None:
    # Remove surcharge_slabs from TDS section
    op.drop_column('mst_tds_section', 'surcharge_slabs')

    # Remove indexes
    op.drop_index('ix_tds_entry_vendor_fy_section', 'txn_tds_entry')
    op.drop_index('ix_tds_entry_fy', 'txn_tds_entry')
    op.drop_index('ix_tds_entry_vendor', 'txn_tds_entry')

    # Remove columns from TDS entry
    op.drop_column('txn_tds_entry', 'threshold_reason')
    op.drop_column('txn_tds_entry', 'aggregate_amount_ytd')
    op.drop_column('txn_tds_entry', 'is_threshold_crossed')
    op.drop_column('txn_tds_entry', 'financial_year_id')
    op.drop_column('txn_tds_entry', 'vendor_id')
