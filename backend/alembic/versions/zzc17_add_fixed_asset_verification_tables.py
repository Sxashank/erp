"""Add fixed-assets physical verification tables for the live operational core.

Revision ID: zzc17_add_fixed_asset_verification_tables
Revises: zzc16_add_bi_fixed_assets_base_model_columns
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "zzc17_add_fixed_asset_verification_tables"
down_revision = "zzc16_add_bi_fixed_assets_base_model_columns"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("txn_pv_schedule"):
        op.create_table(
            "txn_pv_schedule",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("schedule_reference", sa.String(length=30), nullable=False),
            sa.Column("schedule_name", sa.String(length=200), nullable=False),
            sa.Column("financial_year", sa.String(length=10), nullable=False),
            sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("category_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("scheduled_start_date", sa.Date(), nullable=False),
            sa.Column("scheduled_end_date", sa.Date(), nullable=False),
            sa.Column("actual_start_date", sa.Date(), nullable=True),
            sa.Column("actual_end_date", sa.Date(), nullable=True),
            sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("team_members", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("total_assets", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("verified_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("found_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("discrepancy_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_value_verified", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("total_value_missing", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["location_id"], ["mst_unit.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["assigned_to"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["approved_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("organization_id", "schedule_reference", name="uq_pv_schedule_org_ref"),
        )
        op.create_index("ix_txn_pv_schedule_organization_id", "txn_pv_schedule", ["organization_id"])
        op.create_index("ix_txn_pv_schedule_financial_year", "txn_pv_schedule", ["financial_year"])
        op.create_index("ix_txn_pv_schedule_location_id", "txn_pv_schedule", ["location_id"])
        op.create_index("ix_txn_pv_schedule_status", "txn_pv_schedule", ["status"])

    if not _table_exists("txn_pv_entry"):
        op.create_table(
            "txn_pv_entry",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("schedule_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("expected_location_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("expected_department_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("verification_date", sa.Date(), nullable=True),
            sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("verification_result", sa.String(length=20), nullable=True),
            sa.Column("asset_condition", sa.String(length=20), nullable=True),
            sa.Column("actual_location_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("actual_department_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("book_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("photo_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("barcode_scan", sa.String(length=100), nullable=True),
            sa.Column("condition_notes", sa.Text(), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["schedule_id"], ["txn_pv_schedule.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["asset_id"], ["mst_fixed_asset.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["verified_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("schedule_id", "asset_id", name="uq_pv_entry_schedule_asset"),
        )
        op.create_index("ix_txn_pv_entry_schedule_id", "txn_pv_entry", ["schedule_id"])
        op.create_index("ix_txn_pv_entry_asset_id", "txn_pv_entry", ["asset_id"])
        op.create_index("ix_txn_pv_entry_verification_result", "txn_pv_entry", ["verification_result"])

    if not _table_exists("txn_pv_discrepancy"):
        op.create_table(
            "txn_pv_discrepancy",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discrepancy_type", sa.String(length=30), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("value_impact", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
            sa.Column("investigated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("investigation_notes", sa.Text(), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
            sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["entry_id"], ["txn_pv_entry.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["investigated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["resolved_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_txn_pv_discrepancy_entry_id", "txn_pv_discrepancy", ["entry_id"])
        op.create_index("ix_txn_pv_discrepancy_status", "txn_pv_discrepancy", ["status"])


def downgrade() -> None:
    if _table_exists("txn_pv_discrepancy"):
        op.drop_index("ix_txn_pv_discrepancy_status", table_name="txn_pv_discrepancy")
        op.drop_index("ix_txn_pv_discrepancy_entry_id", table_name="txn_pv_discrepancy")
        op.drop_table("txn_pv_discrepancy")

    if _table_exists("txn_pv_entry"):
        op.drop_index("ix_txn_pv_entry_verification_result", table_name="txn_pv_entry")
        op.drop_index("ix_txn_pv_entry_asset_id", table_name="txn_pv_entry")
        op.drop_index("ix_txn_pv_entry_schedule_id", table_name="txn_pv_entry")
        op.drop_table("txn_pv_entry")

    if _table_exists("txn_pv_schedule"):
        op.drop_index("ix_txn_pv_schedule_status", table_name="txn_pv_schedule")
        op.drop_index("ix_txn_pv_schedule_location_id", table_name="txn_pv_schedule")
        op.drop_index("ix_txn_pv_schedule_financial_year", table_name="txn_pv_schedule")
        op.drop_index("ix_txn_pv_schedule_organization_id", table_name="txn_pv_schedule")
        op.drop_table("txn_pv_schedule")
