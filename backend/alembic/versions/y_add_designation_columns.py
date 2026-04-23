"""Add missing designation columns.

Revision ID: y_add_designation_columns
Revises: x_add_org_bank_address
Create Date: 2026-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'y_add_designation_columns'
down_revision: Union[str, None] = 'v1w2x3y4z5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing approval_limit column to mst_designation
    op.add_column('mst_designation', sa.Column('approval_limit', sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('mst_designation', 'approval_limit')
