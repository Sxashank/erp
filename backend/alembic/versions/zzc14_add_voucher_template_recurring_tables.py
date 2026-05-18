"""Add finance voucher template and recurring voucher tables.

Revision ID: zzc14_add_voucher_template_recurring_tables
Revises: zzc13_align_dms_folder_columns
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc14_add_voucher_template_recurring_tables"
down_revision = "zzc13_align_dms_folder_columns"
branch_labels = None
depends_on = None


recurrence_frequency = postgresql.ENUM(
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "QUARTERLY",
    "HALF_YEARLY",
    "YEARLY",
    name="recurrencefrequency",
    create_type=False,
)

recurring_voucher_status = postgresql.ENUM(
    "ACTIVE",
    "PAUSED",
    "COMPLETED",
    "CANCELLED",
    name="recurringvoucherstatus",
    create_type=False,
)


def _has_table(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE recurrencefrequency AS ENUM (
                'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE recurringvoucherstatus AS ENUM (
                'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    if not _has_table("fin_voucher_template"):
        op.create_table(
            "fin_voucher_template",
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "voucher_type_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_voucher_type.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("template_name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("default_narration", sa.Text()),
            sa.Column("total_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
            sa.Column("template_data", postgresql.JSONB(), nullable=False),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_used_at", sa.DateTime(timezone=True)),
            sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("category", sa.String(length=50)),
            *_base_columns(),
        )
        op.create_index("ix_fin_voucher_template_org", "fin_voucher_template", ["organization_id"])
        op.create_index("ix_fin_voucher_template_voucher_type", "fin_voucher_template", ["voucher_type_id"])
        op.create_index("ix_fin_voucher_template_is_active", "fin_voucher_template", ["is_active"])

    if not _has_table("fin_recurring_voucher"):
        op.create_table(
            "fin_recurring_voucher",
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "voucher_type_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_voucher_type.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("template_name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("frequency", recurrence_frequency, nullable=False),
            sa.Column("day_of_month", sa.Integer()),
            sa.Column("day_of_week", sa.Integer()),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date()),
            sa.Column("next_run_date", sa.Date()),
            sa.Column("last_run_date", sa.Date()),
            sa.Column("total_occurrences", sa.Integer()),
            sa.Column("completed_occurrences", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", recurring_voucher_status, nullable=False, server_default="ACTIVE"),
            sa.Column("auto_post", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("auto_approve", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("narration_template", sa.Text()),
            sa.Column("total_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
            sa.Column("template_data", postgresql.JSONB(), nullable=False),
            sa.Column("notify_on_generation", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notify_days_before", sa.Integer(), nullable=False, server_default="0"),
            *_base_columns(),
        )
        op.create_index("ix_fin_recurring_voucher_org", "fin_recurring_voucher", ["organization_id"])
        op.create_index("ix_fin_recurring_voucher_voucher_type", "fin_recurring_voucher", ["voucher_type_id"])
        op.create_index("ix_fin_recurring_voucher_next_run", "fin_recurring_voucher", ["next_run_date"])
        op.create_index("ix_fin_recurring_voucher_status", "fin_recurring_voucher", ["status"])

    if not _has_table("fin_recurring_voucher_log"):
        op.create_table(
            "fin_recurring_voucher_log",
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "recurring_voucher_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fin_recurring_voucher.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "voucher_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("txn_voucher.id", ondelete="SET NULL"),
            ),
            sa.Column("scheduled_date", sa.Date(), nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True)),
            sa.Column("occurrence_number", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
            sa.Column("error_message", sa.Text()),
            *_base_columns(),
        )
        op.create_index("ix_fin_recurring_voucher_log_org", "fin_recurring_voucher_log", ["organization_id"])
        op.create_index(
            "ix_fin_recurring_voucher_log_recurring",
            "fin_recurring_voucher_log",
            ["recurring_voucher_id"],
        )
        op.create_index("ix_fin_recurring_voucher_log_voucher", "fin_recurring_voucher_log", ["voucher_id"])


def downgrade() -> None:
    for table in ["fin_recurring_voucher_log", "fin_recurring_voucher", "fin_voucher_template"]:
        if _has_table(table):
            op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS recurringvoucherstatus")
    op.execute("DROP TYPE IF EXISTS recurrencefrequency")
