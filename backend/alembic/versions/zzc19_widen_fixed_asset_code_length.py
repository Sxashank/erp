"""Widen fixed asset code length for configurable category-based codes.

Revision ID: zzc19_widen_fixed_asset_code_length
Revises: zzc18_add_fixed_asset_it_act_columns
Create Date: 2026-05-17 19:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "zzc19_widen_fixed_asset_code_length"
down_revision = "zzc18_add_fixed_asset_it_act_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "mst_fixed_asset",
        "asset_code",
        existing_type=sa.String(length=30),
        type_=sa.String(length=60),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "mst_fixed_asset",
        "asset_code",
        existing_type=sa.String(length=60),
        type_=sa.String(length=30),
        existing_nullable=False,
    )
