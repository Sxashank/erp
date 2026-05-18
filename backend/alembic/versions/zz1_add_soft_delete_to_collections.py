"""Add SoftDeleteMixin + VersionedMixin columns to collection tables.

These tables were created from an older snapshot and never got the
``deleted_at``/``deleted_by``/``is_active``/``version`` columns that
``BaseModel`` (via SoftDeleteMixin + VersionedMixin) declares. Every
``select(OTSProposal)`` etc. fails with ``UndefinedColumnError`` until
this lands.

The new list endpoints (`/lending/collections/ots-proposals`,
`/restructures`, `/follow-ups`) added in Phase 4 surfaced this drift,
but it applied to every existing query against these tables too.

Revision ID: zz1_collections_softdelete
Revises: aa3_workflowentitytype_lending
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zz1_collections_softdelete"
down_revision = "aa3_workflowentitytype_lending"
branch_labels = None
depends_on = None


TABLES = [
    "col_ots_proposal",
    "col_loan_restructure",
    "col_collection_follow_up",
    "col_legal_case",
    "col_legal_hearing",
    "col_property_auction",
    "col_write_off_record",
    "col_demand_notice",
    "col_npa_record",
    "col_penal_interest",
    "col_penal_waiver",
    "col_ots_payment_schedule",
    # Treasury tables — same drift
    "trs_lender",
    "trs_borrowing",
    "trs_borrowing_tranche",
    "trs_borrowing_schedule",
    "trs_borrowing_payment",
    "trs_borrowing_covenant",
    "trs_alm_position",
    "trs_alm_asset",
    "trs_alm_liability",
    "trs_irs_analysis",
    "trs_exposure_limit",
    "trs_exposure_tracking",
]


def _has_column(table: str, column: str) -> bool:
    """Check whether ``column`` exists on ``table`` in the current DB."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    cols = {c["name"] for c in insp.get_columns(table)}
    return column in cols


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def upgrade() -> None:
    for tbl in TABLES:
        if not _table_exists(tbl):
            continue
        if not _has_column(tbl, "deleted_at"):
            op.add_column(tbl, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column(tbl, "deleted_by"):
            op.add_column(
                tbl,
                sa.Column("deleted_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            )
        if not _has_column(tbl, "is_active"):
            op.add_column(
                tbl,
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            )
        if not _has_column(tbl, "version"):
            op.add_column(
                tbl,
                sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            )

    # Aliased PK columns ------------------------------------------------------
    # The Lender / Borrowing ORM classes declare a second primary-key column
    # (`lender_id`, `borrowing_id`) on top of the inherited `id`. The actual
    # tables only have `id`, so every query SELECTs a column that doesn't
    # exist. Backfill the alias columns from `id` and keep them in sync via
    # GENERATED-style equality. We use a plain column + trigger-free populate
    # so existing FKs keep referencing `id`.
    alias_pairs = [
        ("trs_lender", "lender_id"),
        ("trs_borrowing", "borrowing_id"),
        ("trs_borrowing_tranche", "tranche_id"),
        ("trs_borrowing_schedule", "schedule_id"),
        ("trs_borrowing_payment", "payment_id"),
        ("trs_borrowing_covenant", "covenant_id"),
        ("trs_alm_position", "position_id"),
        ("trs_alm_asset", "asset_id"),
        ("trs_alm_liability", "liability_id"),
        ("trs_irs_analysis", "analysis_id"),
        ("trs_exposure_limit", "limit_id"),
        ("trs_exposure_tracking", "tracking_id"),
    ]
    for tbl, alias_col in alias_pairs:
        if not _table_exists(tbl):
            continue
        if not _has_column(tbl, alias_col):
            op.add_column(
                tbl,
                sa.Column(alias_col, sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.execute(f"UPDATE {tbl} SET {alias_col} = id WHERE {alias_col} IS NULL")
            op.alter_column(tbl, alias_col, nullable=False)
            # Keep alias in sync on inserts so the model PK assignment works
            # even when callers don't set the alias explicitly.
            op.execute(f"""
                CREATE OR REPLACE FUNCTION {tbl}_sync_{alias_col}() RETURNS trigger AS $$
                BEGIN
                    IF NEW.{alias_col} IS NULL THEN
                        NEW.{alias_col} := NEW.id;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """)
            op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_sync_{alias_col} ON {tbl}")
            op.execute(f"""
                CREATE TRIGGER trg_{tbl}_sync_{alias_col}
                BEFORE INSERT ON {tbl}
                FOR EACH ROW EXECUTE FUNCTION {tbl}_sync_{alias_col}()
                """)


def downgrade() -> None:
    for tbl in TABLES:
        if not _table_exists(tbl):
            continue
        for col in ("version", "is_active", "deleted_by", "deleted_at"):
            if _has_column(tbl, col):
                op.drop_column(tbl, col)
