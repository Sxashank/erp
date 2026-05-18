"""Add missing depreciation book columns to fixed-assets depreciation tables.

Revision ID: zzc20_add_fixed_asset_depreciation_book_columns
Revises: zzc19_widen_fixed_asset_code_length
Create Date: 2026-05-17 20:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "zzc20_add_fixed_asset_depreciation_book_columns"
down_revision = "zzc19_widen_fixed_asset_code_length"
branch_labels = None
depends_on = None


DEPRECIATION_BOOK_VALUES = ("COMPANIES_ACT", "IT_ACT")


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _existing_indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _existing_unique_constraints(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'depreciationbook'
            ) THEN
                CREATE TYPE depreciationbook AS ENUM ('COMPANIES_ACT', 'IT_ACT');
            END IF;
        END
        $$;
        """
    )

    enum_type = postgresql.ENUM(
        *DEPRECIATION_BOOK_VALUES,
        name="depreciationbook",
        create_type=False,
    )

    run_columns = _existing_columns("txn_depreciation_run")
    run_indexes = _existing_indexes("txn_depreciation_run")
    run_constraints = _existing_unique_constraints("txn_depreciation_run")
    if "depreciation_book" not in run_columns:
        op.add_column(
            "txn_depreciation_run",
            sa.Column(
                "depreciation_book",
                enum_type,
                nullable=False,
                server_default="COMPANIES_ACT",
            ),
        )
        op.alter_column(
            "txn_depreciation_run",
            "depreciation_book",
            server_default=None,
        )
    if "ix_txn_depreciation_run_depreciation_book" not in run_indexes:
        op.create_index(
            "ix_txn_depreciation_run_depreciation_book",
            "txn_depreciation_run",
            ["depreciation_book"],
        )
    if "uq_depreciation_run_org_period" in run_constraints:
        op.drop_constraint(
            "uq_depreciation_run_org_period",
            "txn_depreciation_run",
            type_="unique",
        )
    if "uq_depreciation_run_org_period_book" not in run_constraints:
        op.create_unique_constraint(
            "uq_depreciation_run_org_period_book",
            "txn_depreciation_run",
            ["organization_id", "depreciation_period", "depreciation_book"],
        )

    dep_columns = _existing_columns("txn_depreciation")
    dep_indexes = _existing_indexes("txn_depreciation")
    dep_constraints = _existing_unique_constraints("txn_depreciation")
    if "depreciation_book" not in dep_columns:
        op.add_column(
            "txn_depreciation",
            sa.Column(
                "depreciation_book",
                enum_type,
                nullable=False,
                server_default="COMPANIES_ACT",
            ),
        )
        op.alter_column(
            "txn_depreciation",
            "depreciation_book",
            server_default=None,
        )
    if "ix_txn_depreciation_depreciation_book" not in dep_indexes:
        op.create_index(
            "ix_txn_depreciation_depreciation_book",
            "txn_depreciation",
            ["depreciation_book"],
        )
    if "uq_depreciation_asset_period_type" in dep_constraints:
        op.drop_constraint(
            "uq_depreciation_asset_period_type",
            "txn_depreciation",
            type_="unique",
        )
    if "uq_depreciation_asset_period_type_book" not in dep_constraints:
        op.create_unique_constraint(
            "uq_depreciation_asset_period_type_book",
            "txn_depreciation",
            ["asset_id", "depreciation_period", "depreciation_type", "depreciation_book"],
        )


def downgrade() -> None:
    dep_constraints = _existing_unique_constraints("txn_depreciation")
    dep_indexes = _existing_indexes("txn_depreciation")
    dep_columns = _existing_columns("txn_depreciation")
    if "uq_depreciation_asset_period_type_book" in dep_constraints:
        op.drop_constraint(
            "uq_depreciation_asset_period_type_book",
            "txn_depreciation",
            type_="unique",
        )
    if "uq_depreciation_asset_period_type" not in dep_constraints:
        op.create_unique_constraint(
            "uq_depreciation_asset_period_type",
            "txn_depreciation",
            ["asset_id", "depreciation_period", "depreciation_type"],
        )
    if "ix_txn_depreciation_depreciation_book" in dep_indexes:
        op.drop_index("ix_txn_depreciation_depreciation_book", table_name="txn_depreciation")
    if "depreciation_book" in dep_columns:
        op.drop_column("txn_depreciation", "depreciation_book")

    run_constraints = _existing_unique_constraints("txn_depreciation_run")
    run_indexes = _existing_indexes("txn_depreciation_run")
    run_columns = _existing_columns("txn_depreciation_run")
    if "uq_depreciation_run_org_period_book" in run_constraints:
        op.drop_constraint(
            "uq_depreciation_run_org_period_book",
            "txn_depreciation_run",
            type_="unique",
        )
    if "uq_depreciation_run_org_period" not in run_constraints:
        op.create_unique_constraint(
            "uq_depreciation_run_org_period",
            "txn_depreciation_run",
            ["organization_id", "depreciation_period"],
        )
    if "ix_txn_depreciation_run_depreciation_book" in run_indexes:
        op.drop_index("ix_txn_depreciation_run_depreciation_book", table_name="txn_depreciation_run")
    if "depreciation_book" in run_columns:
        op.drop_column("txn_depreciation_run", "depreciation_book")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE udt_name = 'depreciationbook'
            ) THEN
                DROP TYPE IF EXISTS depreciationbook;
            END IF;
        END
        $$;
        """
    )
