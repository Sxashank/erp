"""Reconcile approval workflow tables with current ORM models.

Revision ID: zzc15_reconcile_approval_workflow_tables
Revises: zzc14_add_voucher_template_recurring_tables
Create Date: 2026-05-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc15_reconcile_approval_workflow_tables"
down_revision: str | None = "zzc14_add_voucher_template_recurring_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


APPROVAL_WORKFLOW_TYPES = (
    "FA_ASSET_CREATION",
    "FA_ASSET_CAPITALIZATION",
    "FA_ASSET_DISPOSAL",
    "FA_ASSET_REVALUATION",
    "FA_ASSET_IMPAIRMENT",
    "FA_ASSET_TRANSFER",
    "FA_DEPRECIATION_RUN",
    "FA_INSURANCE_CLAIM",
    "FA_LEASE_ACTIVATION",
    "FA_LEASE_MODIFICATION",
    "FA_LEASE_TERMINATION",
    "FIN_VOUCHER",
    "FIN_JOURNAL",
    "LOAN_SANCTION",
    "LOAN_DISBURSEMENT",
    "LOAN_WRITE_OFF",
    "LOAN_OTS",
    "PAYMENT_RELEASE",
    "PAYROLL_POSTING",
)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    ]


def _create_enum_types() -> None:
    workflow_values = ", ".join(f"'{value}'" for value in APPROVAL_WORKFLOW_TYPES)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalworkflowtype') THEN
                CREATE TYPE approvalworkflowtype AS ENUM ({workflow_values});
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalrequeststatus') THEN
                CREATE TYPE approvalrequeststatus AS ENUM (
                    'PENDING', 'APPROVED', 'REJECTED', 'RETURNED', 'CANCELLED', 'EXPIRED'
                );
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalaction') THEN
                CREATE TYPE approvalaction AS ENUM ('APPROVE', 'REJECT', 'RETURN', 'ESCALATE');
            END IF;
        END $$;
        """)


def _enable_rls(table_name: str, org_column: str = "organization_id") -> None:
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS org_isolation_{table_name} ON {table_name}")
    op.execute(f"""CREATE POLICY org_isolation_{table_name} ON {table_name}
            FOR ALL
            USING (
                {org_column}::text = current_setting('app.current_org_id', true)
                OR current_setting('app.current_org_id', true) = ''
            )
        """)


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())

    _create_enum_types()

    workflow_type_enum = postgresql.ENUM(
        *APPROVAL_WORKFLOW_TYPES,
        name="approvalworkflowtype",
        create_type=False,
    )
    request_status_enum = postgresql.ENUM(
        "PENDING",
        "APPROVED",
        "REJECTED",
        "RETURNED",
        "CANCELLED",
        "EXPIRED",
        name="approvalrequeststatus",
        create_type=False,
    )
    approval_action_enum = postgresql.ENUM(
        "APPROVE",
        "REJECT",
        "RETURN",
        "ESCALATE",
        name="approvalaction",
        create_type=False,
    )

    if "mst_approval_workflow" not in existing_tables:
        op.create_table(
            "mst_approval_workflow",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("workflow_type", workflow_type_enum, nullable=False),
            sa.Column("workflow_name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "threshold_amount",
                sa.Numeric(18, 2),
                server_default="0.00",
                nullable=False,
            ),
            sa.Column("threshold_currency", sa.String(3), server_default="INR", nullable=False),
            sa.Column("approval_levels", sa.Integer(), server_default="1", nullable=False),
            sa.Column(
                "is_sequential", sa.Boolean(), server_default=sa.text("true"), nullable=False
            ),
            sa.Column(
                "auto_approve_on_timeout",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column("timeout_hours", sa.Integer(), nullable=True),
            sa.Column(
                "allow_self_approval",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column(
                "notify_on_submit", sa.Boolean(), server_default=sa.text("true"), nullable=False
            ),
            sa.Column(
                "notify_on_approval", sa.Boolean(), server_default=sa.text("true"), nullable=False
            ),
            sa.Column(
                "notify_on_rejection", sa.Boolean(), server_default=sa.text("true"), nullable=False
            ),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["organization_id"], ["mst_organization.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.UniqueConstraint(
                "organization_id", "workflow_type", name="uq_approval_workflow_org_type"
            ),
        )
        op.create_index(
            "ix_mst_approval_workflow_organization_id", "mst_approval_workflow", ["organization_id"]
        )
        op.create_index(
            "ix_mst_approval_workflow_workflow_type", "mst_approval_workflow", ["workflow_type"]
        )
        _enable_rls("mst_approval_workflow")

    if "mst_approval_workflow_level" not in existing_tables:
        op.create_table(
            "mst_approval_workflow_level",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("level_number", sa.Integer(), nullable=False),
            sa.Column("level_name", sa.String(50), nullable=False),
            sa.Column("approver_roles", postgresql.JSONB(), nullable=True),
            sa.Column("approver_users", postgresql.JSONB(), nullable=True),
            sa.Column("min_approvers", sa.Integer(), server_default="1", nullable=False),
            sa.Column("threshold_amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("escalation_hours", sa.Integer(), nullable=True),
            sa.Column("escalation_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["workflow_id"], ["mst_approval_workflow.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["escalation_user_id"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("workflow_id", "level_number", name="uq_workflow_level"),
        )
        op.create_index(
            "ix_mst_approval_workflow_level_workflow_id",
            "mst_approval_workflow_level",
            ["workflow_id"],
        )

    if "txn_approval_request" not in existing_tables:
        op.create_table(
            "txn_approval_request",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("workflow_type", workflow_type_enum, nullable=False),
            sa.Column("entity_type", sa.String(50), nullable=False),
            sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("request_number", sa.String(30), nullable=False),
            sa.Column("request_amount", sa.Numeric(18, 2), server_default="0.00", nullable=False),
            sa.Column("request_summary", sa.String(500), nullable=False),
            sa.Column("request_details", postgresql.JSONB(), nullable=True),
            sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", request_status_enum, server_default="PENDING", nullable=False),
            sa.Column("current_level", sa.Integer(), server_default="1", nullable=False),
            sa.Column("total_levels", sa.Integer(), nullable=False),
            sa.Column("approval_chain", postgresql.JSONB(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("final_comments", sa.Text(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["organization_id"], ["mst_organization.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["workflow_id"], ["mst_approval_workflow.id"], ondelete="RESTRICT"
            ),
            sa.ForeignKeyConstraint(["requested_by"], ["mst_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["resolved_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("request_number", name="uq_approval_request_number"),
        )
        op.create_index(
            "ix_txn_approval_request_organization_id", "txn_approval_request", ["organization_id"]
        )
        op.create_index(
            "ix_txn_approval_request_workflow_id", "txn_approval_request", ["workflow_id"]
        )
        op.create_index(
            "idx_approval_request_entity", "txn_approval_request", ["entity_type", "entity_id"]
        )
        op.create_index("idx_approval_request_status", "txn_approval_request", ["status"])
        op.create_index(
            "idx_approval_request_current_level", "txn_approval_request", ["current_level"]
        )
        _enable_rls("txn_approval_request")

    if "txn_approval_request_action" not in existing_tables:
        op.create_table(
            "txn_approval_request_action",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("level_number", sa.Integer(), nullable=False),
            sa.Column("action", approval_action_enum, nullable=False),
            sa.Column("action_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("action_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("comments", sa.Text(), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["request_id"], ["txn_approval_request.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["action_by"], ["mst_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        )
        op.create_index(
            "idx_approval_action_request", "txn_approval_request_action", ["request_id"]
        )
        op.create_index("idx_approval_action_user", "txn_approval_request_action", ["action_by"])


def downgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())

    if "txn_approval_request_action" in existing_tables:
        op.drop_index("idx_approval_action_user", table_name="txn_approval_request_action")
        op.drop_index("idx_approval_action_request", table_name="txn_approval_request_action")
        op.drop_table("txn_approval_request_action")
    if "txn_approval_request" in existing_tables:
        op.drop_index("idx_approval_request_current_level", table_name="txn_approval_request")
        op.drop_index("idx_approval_request_status", table_name="txn_approval_request")
        op.drop_index("idx_approval_request_entity", table_name="txn_approval_request")
        op.drop_index("ix_txn_approval_request_workflow_id", table_name="txn_approval_request")
        op.drop_index("ix_txn_approval_request_organization_id", table_name="txn_approval_request")
        op.drop_table("txn_approval_request")
    if "mst_approval_workflow_level" in existing_tables:
        op.drop_index(
            "ix_mst_approval_workflow_level_workflow_id", table_name="mst_approval_workflow_level"
        )
        op.drop_table("mst_approval_workflow_level")
    if "mst_approval_workflow" in existing_tables:
        op.drop_index("ix_mst_approval_workflow_workflow_type", table_name="mst_approval_workflow")
        op.drop_index(
            "ix_mst_approval_workflow_organization_id", table_name="mst_approval_workflow"
        )
        op.drop_table("mst_approval_workflow")
