"""Add report runtime tables for MIS generation history and schedules.

Revision ID: zzc29_add_report_runtime_tables
Revises: zzc28_reconcile_payroll_runtime_columns
Create Date: 2026-05-18
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc29_add_report_runtime_tables"
down_revision = "zzc28_reconcile_payroll_runtime_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rpt_report_run",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_code", sa.String(length=80), nullable=False),
        sa.Column("report_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("export_format", sa.String(length=20), nullable=False),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["generated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rpt_report_run_organization_id", "rpt_report_run", ["organization_id"])
    op.create_index(
        "ix_rpt_run_org_generated", "rpt_report_run", ["organization_id", "generated_at"]
    )
    op.create_index("ix_rpt_run_org_report", "rpt_report_run", ["organization_id", "report_code"])
    op.create_index("ix_rpt_run_org_status", "rpt_report_run", ["organization_id", "status"])

    op.create_table(
        "rpt_report_schedule",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_code", sa.String(length=80), nullable=False),
        sa.Column("report_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=30), nullable=False),
        sa.Column("schedule_time", sa.String(length=10), nullable=False),
        sa.Column("output_format", sa.String(length=20), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recipients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=30), nullable=True),
        sa.Column("delivery_mode", sa.String(length=30), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rpt_report_schedule_organization_id", "rpt_report_schedule", ["organization_id"]
    )
    op.create_index(
        "ix_rpt_schedule_org_active", "rpt_report_schedule", ["organization_id", "is_active"]
    )
    op.create_index(
        "ix_rpt_schedule_org_report", "rpt_report_schedule", ["organization_id", "report_code"]
    )


def downgrade() -> None:
    op.drop_index("ix_rpt_schedule_org_report", table_name="rpt_report_schedule")
    op.drop_index("ix_rpt_schedule_org_active", table_name="rpt_report_schedule")
    op.drop_index("ix_rpt_report_schedule_organization_id", table_name="rpt_report_schedule")
    op.drop_table("rpt_report_schedule")
    op.drop_index("ix_rpt_run_org_status", table_name="rpt_report_run")
    op.drop_index("ix_rpt_run_org_report", table_name="rpt_report_run")
    op.drop_index("ix_rpt_run_org_generated", table_name="rpt_report_run")
    op.drop_index("ix_rpt_report_run_organization_id", table_name="rpt_report_run")
    op.drop_table("rpt_report_run")
