"""Create fixed-asset configuration table.

Revision ID: zzc22_create_fixed_asset_configuration_table
Revises: zzc21_extend_gl_entry_source_type_for_fixed_assets
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "zzc22_create_fixed_asset_configuration_table"
down_revision = "zzc21_extend_gl_entry_source_type_for_fixed_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mst_fa_configuration",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_code_prefix", sa.String(length=10), nullable=False, server_default="FA"),
        sa.Column(
            "asset_code_format",
            sa.String(length=100),
            nullable=False,
            server_default="{prefix}/{category}/{year}/{sequence:05d}",
        ),
        sa.Column("asset_code_separator", sa.String(length=1), nullable=False, server_default="/"),
        sa.Column("auto_generate_code", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fy_start_month", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("fy_start_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "creation_approval_threshold",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="1000000.00",
        ),
        sa.Column(
            "disposal_approval_threshold",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "revaluation_approval_threshold",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "transfer_requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("days_in_year", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("pro_rata_method", sa.String(length=20), nullable=False, server_default="DAILY"),
        sa.Column(
            "min_asset_value_for_depreciation",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="5000.00",
        ),
        sa.Column(
            "depreciation_posting_auto_approve",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("amc_expiry_reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("insurance_expiry_reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("warranty_expiry_reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("lease_expiry_reminder_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("lease_payment_reminder_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("pv_frequency_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column(
            "pv_tolerance_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="5.00",
        ),
        sa.Column("auto_post_capitalization", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auto_post_disposal", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auto_post_depreciation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("default_page_size", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_page_size", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("custom_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notification_emails", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_fa_config_org"),
    )
    op.create_index(
        op.f("ix_mst_fa_configuration_organization_id"),
        "mst_fa_configuration",
        ["organization_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mst_fa_configuration_organization_id"), table_name="mst_fa_configuration")
    op.drop_table("mst_fa_configuration")
