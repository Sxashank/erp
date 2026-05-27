"""Realign legacy fixed-asset physical-verification tables with the live contract.

Revision ID: zzc63_realign_fixed_asset_verification_tables
Revises: zzc62_repair_legacy_approval_table_shape
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "zzc63_realign_fixed_asset_verification_tables"
down_revision = "zzc62_repair_legacy_approval_table_shape"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _ensure_schedule_shape() -> None:
    if not _table_exists("txn_pv_schedule"):
        return

    cols = _column_names("txn_pv_schedule")
    with op.batch_alter_table("txn_pv_schedule") as batch_op:
        if "planned_start_date" in cols and "scheduled_start_date" not in cols:
            batch_op.alter_column(
                "planned_start_date",
                new_column_name="scheduled_start_date",
                existing_type=sa.Date(),
                existing_nullable=False,
            )
        if "planned_end_date" in cols and "scheduled_end_date" not in cols:
            batch_op.alter_column(
                "planned_end_date",
                new_column_name="scheduled_end_date",
                existing_type=sa.Date(),
                existing_nullable=False,
            )
        if "not_found_count" in cols and "missing_count" not in cols:
            batch_op.alter_column(
                "not_found_count",
                new_column_name="missing_count",
                existing_type=sa.Integer(),
                existing_nullable=False,
            )

    cols = _column_names("txn_pv_schedule")
    with op.batch_alter_table("txn_pv_schedule") as batch_op:
        if "financial_year" not in cols:
            batch_op.add_column(sa.Column("financial_year", sa.String(length=10), nullable=True))
        if "category_ids" not in cols:
            batch_op.add_column(
                sa.Column("category_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
            )
        if "team_members" not in cols:
            batch_op.add_column(
                sa.Column("team_members", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
            )
        if "found_count" not in cols:
            batch_op.add_column(
                sa.Column(
                    "found_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )
        if "total_value_verified" not in cols:
            batch_op.add_column(
                sa.Column(
                    "total_value_verified",
                    sa.Numeric(18, 2),
                    nullable=False,
                    server_default="0",
                )
            )
        if "total_value_missing" not in cols:
            batch_op.add_column(
                sa.Column(
                    "total_value_missing",
                    sa.Numeric(18, 2),
                    nullable=False,
                    server_default="0",
                )
            )
        if "approved_by" not in cols:
            batch_op.add_column(
                sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "approved_at" not in cols:
            batch_op.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("ALTER TABLE txn_pv_schedule ALTER COLUMN status SET DEFAULT 'DRAFT'")

    op.execute("""
        UPDATE txn_pv_schedule
        SET financial_year = CASE
            WHEN financial_year IS NOT NULL THEN financial_year
            WHEN scheduled_start_date IS NULL THEN NULL
            WHEN EXTRACT(MONTH FROM scheduled_start_date) >= 4 THEN
                TO_CHAR(scheduled_start_date, 'YYYY') || '-' ||
                RIGHT(TO_CHAR(scheduled_start_date + INTERVAL '1 year', 'YYYY'), 2)
            ELSE
                TO_CHAR(scheduled_start_date - INTERVAL '1 year', 'YYYY') || '-' ||
                RIGHT(TO_CHAR(scheduled_start_date, 'YYYY'), 2)
        END
        """)
    op.execute("""
        UPDATE txn_pv_schedule
        SET category_ids = CASE
            WHEN category_ids IS NOT NULL THEN category_ids
            WHEN category_id IS NULL THEN NULL
            ELSE jsonb_build_array(category_id)
        END
        """)
    op.execute("""
        UPDATE txn_pv_schedule
        SET found_count = GREATEST(COALESCE(verified_count, 0) - COALESCE(missing_count, 0), 0)
        WHERE COALESCE(found_count, 0) = 0
        """)

    indexes = _index_names("txn_pv_schedule")
    if "ix_txn_pv_schedule_financial_year" not in indexes:
        op.create_index(
            "ix_txn_pv_schedule_financial_year",
            "txn_pv_schedule",
            ["financial_year"],
        )
    if "ix_txn_pv_schedule_location_id" not in indexes:
        op.create_index(
            "ix_txn_pv_schedule_location_id",
            "txn_pv_schedule",
            ["location_id"],
        )

    with op.batch_alter_table("txn_pv_schedule") as batch_op:
        batch_op.alter_column("financial_year", existing_type=sa.String(length=10), nullable=False)


def _ensure_entry_shape() -> None:
    if not _table_exists("txn_pv_entry"):
        return

    cols = _column_names("txn_pv_entry")
    with op.batch_alter_table("txn_pv_entry") as batch_op:
        if "expected_location_id" not in cols:
            batch_op.add_column(
                sa.Column("expected_location_id", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "expected_department_id" not in cols:
            batch_op.add_column(
                sa.Column("expected_department_id", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "verification_result" not in cols:
            batch_op.add_column(
                sa.Column("verification_result", sa.String(length=20), nullable=True)
            )
        if "asset_condition" not in cols:
            batch_op.add_column(sa.Column("asset_condition", sa.String(length=20), nullable=True))
        if "actual_location_id" not in cols:
            batch_op.add_column(
                sa.Column("actual_location_id", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "actual_department_id" not in cols:
            batch_op.add_column(
                sa.Column("actual_department_id", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "book_value" not in cols:
            batch_op.add_column(
                sa.Column(
                    "book_value",
                    sa.Numeric(18, 2),
                    nullable=False,
                    server_default="0",
                )
            )
        if "barcode_scan" not in cols:
            batch_op.add_column(sa.Column("barcode_scan", sa.String(length=100), nullable=True))

    op.execute("ALTER TABLE txn_pv_entry ALTER COLUMN status SET DEFAULT 'PENDING'")
    op.execute("""
        UPDATE txn_pv_entry entry
        SET expected_location_id = asset.location_id,
            expected_department_id = asset.department_id,
            book_value = COALESCE(asset.wdv_value, 0)
        FROM mst_fixed_asset asset
        WHERE asset.id = entry.asset_id
          AND (
            entry.expected_location_id IS NULL
            OR entry.expected_department_id IS NULL
            OR COALESCE(entry.book_value, 0) = 0
          )
        """)
    op.execute("""
        UPDATE txn_pv_entry
        SET verification_result = CASE status::text
            WHEN 'VERIFIED' THEN 'FOUND'
            WHEN 'NOT_FOUND' THEN 'MISSING'
            WHEN 'DISCREPANCY' THEN 'MISPLACED'
            ELSE verification_result
        END
        WHERE verification_result IS NULL
        """)
    op.execute("""
        UPDATE txn_pv_entry
        SET asset_condition = COALESCE(asset_condition, physical_condition)
        WHERE asset_condition IS NULL
        """)

    indexes = _index_names("txn_pv_entry")
    if "ix_txn_pv_entry_verification_result" not in indexes:
        op.create_index(
            "ix_txn_pv_entry_verification_result",
            "txn_pv_entry",
            ["verification_result"],
        )


def _ensure_discrepancy_shape() -> None:
    if not _table_exists("txn_pv_discrepancy"):
        return

    cols = _column_names("txn_pv_discrepancy")
    with op.batch_alter_table("txn_pv_discrepancy") as batch_op:
        if "description" not in cols:
            batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        if "value_impact" not in cols:
            batch_op.add_column(
                sa.Column(
                    "value_impact",
                    sa.Numeric(18, 2),
                    nullable=False,
                    server_default="0",
                )
            )
        if "investigated_by" not in cols:
            batch_op.add_column(
                sa.Column("investigated_by", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "investigation_notes" not in cols:
            batch_op.add_column(sa.Column("investigation_notes", sa.Text(), nullable=True))

    op.execute("""
        UPDATE txn_pv_discrepancy
        SET value_impact = COALESCE(variance_amount, 0)
        WHERE COALESCE(value_impact, 0) = 0
        """)
    op.execute("""
        UPDATE txn_pv_discrepancy
        SET description = COALESCE(
            description,
            NULLIF(
                CONCAT_WS(
                    ' | ',
                    NULLIF(expected_value, ''),
                    NULLIF(actual_value, '')
                ),
                ''
            ),
            discrepancy_type
        )
        WHERE description IS NULL
        """)
    with op.batch_alter_table("txn_pv_discrepancy") as batch_op:
        batch_op.alter_column("description", existing_type=sa.Text(), nullable=False)


def upgrade() -> None:
    _ensure_schedule_shape()
    _ensure_entry_shape()
    _ensure_discrepancy_shape()


def downgrade() -> None:
    # Irreversible compatibility repair.
    pass
