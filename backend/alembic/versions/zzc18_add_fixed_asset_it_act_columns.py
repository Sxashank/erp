"""Add missing IT Act columns to fixed asset table.

Revision ID: zzc18_add_fixed_asset_it_act_columns
Revises: zzc17_add_fixed_asset_verification_tables
Create Date: 2026-05-17 19:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "zzc18_add_fixed_asset_it_act_columns"
down_revision = "zzc17_add_fixed_asset_verification_tables"
branch_labels = None
depends_on = None


IT_ACT_ASSET_BLOCK_VALUES = (
    "BLOCK_1",
    "BLOCK_2",
    "BLOCK_3",
    "BLOCK_4",
    "BLOCK_5",
    "BLOCK_6",
    "BLOCK_7",
    "BLOCK_8",
    "BLOCK_9",
    "BLOCK_10",
    "BLOCK_11",
    "BLOCK_12",
)


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'itactassetblock'
            ) THEN
                CREATE TYPE itactassetblock AS ENUM (
                    'BLOCK_1',
                    'BLOCK_2',
                    'BLOCK_3',
                    'BLOCK_4',
                    'BLOCK_5',
                    'BLOCK_6',
                    'BLOCK_7',
                    'BLOCK_8',
                    'BLOCK_9',
                    'BLOCK_10',
                    'BLOCK_11',
                    'BLOCK_12'
                );
            END IF;
        END
        $$;
        """
    )

    columns = _existing_columns("mst_fixed_asset")
    enum_type = postgresql.ENUM(
        *IT_ACT_ASSET_BLOCK_VALUES,
        name="itactassetblock",
        create_type=False,
    )

    if "it_act_block" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column("it_act_block", enum_type, nullable=True),
        )
    if "it_act_rate" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column(
                "it_act_rate",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
    if "it_accumulated_depreciation" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column(
                "it_accumulated_depreciation",
                sa.Numeric(18, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
    if "it_wdv_value" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column(
                "it_wdv_value",
                sa.Numeric(18, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
    if "it_last_depreciation_date" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column("it_last_depreciation_date", sa.Date(), nullable=True),
        )
    if "it_last_depreciation_fy" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column("it_last_depreciation_fy", sa.String(length=10), nullable=True),
        )
    if "is_additional_depreciation_eligible" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column(
                "is_additional_depreciation_eligible",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )
    if "additional_depreciation_claimed" not in columns:
        op.add_column(
            "mst_fixed_asset",
            sa.Column(
                "additional_depreciation_claimed",
                sa.Numeric(18, 2),
                nullable=False,
                server_default="0.00",
            ),
        )


def downgrade() -> None:
    columns = _existing_columns("mst_fixed_asset")

    if "additional_depreciation_claimed" in columns:
        op.drop_column("mst_fixed_asset", "additional_depreciation_claimed")
    if "is_additional_depreciation_eligible" in columns:
        op.drop_column("mst_fixed_asset", "is_additional_depreciation_eligible")
    if "it_last_depreciation_fy" in columns:
        op.drop_column("mst_fixed_asset", "it_last_depreciation_fy")
    if "it_last_depreciation_date" in columns:
        op.drop_column("mst_fixed_asset", "it_last_depreciation_date")
    if "it_wdv_value" in columns:
        op.drop_column("mst_fixed_asset", "it_wdv_value")
    if "it_accumulated_depreciation" in columns:
        op.drop_column("mst_fixed_asset", "it_accumulated_depreciation")
    if "it_act_rate" in columns:
        op.drop_column("mst_fixed_asset", "it_act_rate")
    if "it_act_block" in columns:
        op.drop_column("mst_fixed_asset", "it_act_block")

    op.execute("DROP TYPE IF EXISTS itactassetblock")
