"""Repair legacy approval tables to match current ORM shape.

Revision ID: zzc62_repair_legacy_approval_table_shape
Revises: zzc61_entity_policy_terms_text
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc62_repair_legacy_approval_table_shape"
down_revision: str | None = "zzc61_entity_policy_terms_text"
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

REQUEST_STATUS_VALUES = (
    "PENDING",
    "APPROVED",
    "REJECTED",
    "RETURNED",
    "CANCELLED",
    "EXPIRED",
)

APPROVAL_ACTION_VALUES = (
    "APPROVE",
    "REJECT",
    "RETURN",
    "ESCALATE",
)

REQUIRED_COLUMNS = {
    "mst_approval_workflow": {
        "id",
        "organization_id",
        "workflow_type",
        "workflow_name",
        "description",
        "threshold_amount",
        "threshold_currency",
        "approval_levels",
        "is_sequential",
        "auto_approve_on_timeout",
        "timeout_hours",
        "allow_self_approval",
        "notify_on_submit",
        "notify_on_approval",
        "notify_on_rejection",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "is_active",
        "version",
    },
    "mst_approval_workflow_level": {
        "id",
        "workflow_id",
        "level_number",
        "level_name",
        "approver_roles",
        "approver_users",
        "min_approvers",
        "threshold_amount",
        "escalation_hours",
        "escalation_user_id",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "is_active",
        "version",
    },
    "txn_approval_request": {
        "id",
        "organization_id",
        "workflow_id",
        "workflow_type",
        "entity_type",
        "entity_id",
        "request_number",
        "request_amount",
        "request_summary",
        "request_details",
        "requested_by",
        "requested_at",
        "status",
        "current_level",
        "total_levels",
        "approval_chain",
        "resolved_at",
        "resolved_by",
        "final_comments",
        "expires_at",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "is_active",
        "version",
    },
    "txn_approval_request_action": {
        "id",
        "request_id",
        "level_number",
        "action",
        "action_by",
        "action_at",
        "comments",
        "action_context",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "is_active",
        "version",
    },
}


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
    request_status_values = ", ".join(f"'{value}'" for value in REQUEST_STATUS_VALUES)
    action_values = ", ".join(f"'{value}'" for value in APPROVAL_ACTION_VALUES)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalworkflowtype') THEN
                CREATE TYPE approvalworkflowtype AS ENUM ({workflow_values});
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalrequeststatus') THEN
                CREATE TYPE approvalrequeststatus AS ENUM ({request_status_values});
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalaction') THEN
                CREATE TYPE approvalaction AS ENUM ({action_values});
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


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_count(bind, table_name: str) -> int:
    return int(bind.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0)


def _all_approval_tables_empty(bind, existing_tables: set[str]) -> bool:
    table_names = [
        "mst_approval_workflow",
        "mst_approval_workflow_level",
        "txn_approval_request",
        "txn_approval_request_action",
    ]
    return all(
        table_name not in existing_tables or _table_count(bind, table_name) == 0
        for table_name in table_names
    )


def _needs_repair(inspector, existing_tables: set[str]) -> bool:
    for table_name, required_columns in REQUIRED_COLUMNS.items():
        if table_name not in existing_tables:
            return True
        if not required_columns.issubset(_column_names(inspector, table_name)):
            return True
    return False


def _create_canonical_tables() -> None:
    workflow_type_enum = postgresql.ENUM(
        *APPROVAL_WORKFLOW_TYPES,
        name="approvalworkflowtype",
        create_type=False,
    )
    request_status_enum = postgresql.ENUM(
        *REQUEST_STATUS_VALUES,
        name="approvalrequeststatus",
        create_type=False,
    )
    approval_action_enum = postgresql.ENUM(
        *APPROVAL_ACTION_VALUES,
        name="approvalaction",
        create_type=False,
    )

    op.create_table(
        "mst_approval_workflow",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_type", workflow_type_enum, nullable=False),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("threshold_amount", sa.Numeric(18, 2), server_default="0.00", nullable=False),
        sa.Column("threshold_currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("approval_levels", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_sequential", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.Column("notify_on_submit", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "notify_on_approval",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "notify_on_rejection",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "organization_id", "workflow_type", name="uq_approval_workflow_org_type"
        ),
    )
    op.create_index(
        "ix_mst_approval_workflow_organization_id",
        "mst_approval_workflow",
        ["organization_id"],
    )
    op.create_index(
        "ix_mst_approval_workflow_workflow_type",
        "mst_approval_workflow",
        ["workflow_type"],
    )
    _enable_rls("mst_approval_workflow")

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
        sa.ForeignKeyConstraint(["workflow_id"], ["mst_approval_workflow.id"], ondelete="CASCADE"),
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
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["mst_approval_workflow.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by"], ["mst_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["resolved_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("request_number", name="uq_approval_request_number"),
    )
    op.create_index(
        "ix_txn_approval_request_organization_id",
        "txn_approval_request",
        ["organization_id"],
    )
    op.create_index(
        "ix_txn_approval_request_workflow_id",
        "txn_approval_request",
        ["workflow_id"],
    )
    op.create_index(
        "idx_approval_request_entity", "txn_approval_request", ["entity_type", "entity_id"]
    )
    op.create_index("idx_approval_request_status", "txn_approval_request", ["status"])
    op.create_index("idx_approval_request_current_level", "txn_approval_request", ["current_level"])
    _enable_rls("txn_approval_request")

    op.create_table(
        "txn_approval_request_action",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level_number", sa.Integer(), nullable=False),
        sa.Column("action", approval_action_enum, nullable=False),
        sa.Column("action_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("action_context", postgresql.JSONB(), nullable=True),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["request_id"], ["txn_approval_request.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["action_by"], ["mst_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_approval_action_request", "txn_approval_request_action", ["request_id"])
    op.create_index("idx_approval_action_user", "txn_approval_request_action", ["action_by"])


def _repair_existing_tables(bind, inspector) -> None:
    workflow_columns = _column_names(inspector, "mst_approval_workflow")
    workflow_level_columns = _column_names(inspector, "mst_approval_workflow_level")
    request_columns = _column_names(inspector, "txn_approval_request")
    action_columns = _column_names(inspector, "txn_approval_request_action")

    workflow_type_enum = postgresql.ENUM(
        *APPROVAL_WORKFLOW_TYPES,
        name="approvalworkflowtype",
        create_type=False,
    )

    with op.batch_alter_table("mst_approval_workflow") as batch_op:
        if "threshold_currency" not in workflow_columns:
            batch_op.add_column(
                sa.Column("threshold_currency", sa.String(3), server_default="INR", nullable=False)
            )
        if "is_sequential" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "is_sequential", sa.Boolean(), server_default=sa.text("true"), nullable=False
                )
            )
        if "auto_approve_on_timeout" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "auto_approve_on_timeout",
                    sa.Boolean(),
                    server_default=sa.text("false"),
                    nullable=False,
                )
            )
        if "allow_self_approval" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "allow_self_approval",
                    sa.Boolean(),
                    server_default=sa.text("false"),
                    nullable=False,
                )
            )
        if "notify_on_submit" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "notify_on_submit", sa.Boolean(), server_default=sa.text("true"), nullable=False
                )
            )
        if "notify_on_approval" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "notify_on_approval",
                    sa.Boolean(),
                    server_default=sa.text("true"),
                    nullable=False,
                )
            )
        if "notify_on_rejection" not in workflow_columns:
            batch_op.add_column(
                sa.Column(
                    "notify_on_rejection",
                    sa.Boolean(),
                    server_default=sa.text("true"),
                    nullable=False,
                )
            )

    op.execute(
        "UPDATE mst_approval_workflow SET threshold_amount = COALESCE(threshold_amount, 0.00)"
    )
    if "send_email_notifications" in workflow_columns:
        op.execute("""
            UPDATE mst_approval_workflow
            SET notify_on_submit = COALESCE(notify_on_submit, send_email_notifications),
                notify_on_approval = COALESCE(notify_on_approval, send_email_notifications),
                notify_on_rejection = COALESCE(notify_on_rejection, send_email_notifications)
            """)

    with op.batch_alter_table("mst_approval_workflow_level") as batch_op:
        if "level_number" not in workflow_level_columns:
            batch_op.add_column(sa.Column("level_number", sa.Integer(), nullable=True))
        if "level_name" not in workflow_level_columns:
            batch_op.add_column(sa.Column("level_name", sa.String(50), nullable=True))
        if "approver_roles" not in workflow_level_columns:
            batch_op.add_column(sa.Column("approver_roles", postgresql.JSONB(), nullable=True))
        if "approver_users" not in workflow_level_columns:
            batch_op.add_column(sa.Column("approver_users", postgresql.JSONB(), nullable=True))
        if "min_approvers" not in workflow_level_columns:
            batch_op.add_column(
                sa.Column("min_approvers", sa.Integer(), server_default="1", nullable=False)
            )
        if "threshold_amount" not in workflow_level_columns:
            batch_op.add_column(sa.Column("threshold_amount", sa.Numeric(18, 2), nullable=True))
        if "escalation_hours" not in workflow_level_columns:
            batch_op.add_column(sa.Column("escalation_hours", sa.Integer(), nullable=True))
        if "escalation_user_id" not in workflow_level_columns:
            batch_op.add_column(
                sa.Column("escalation_user_id", postgresql.UUID(as_uuid=True), nullable=True)
            )

    if "level" in workflow_level_columns:
        op.execute(
            "UPDATE mst_approval_workflow_level SET level_number = COALESCE(level_number, level)"
        )
    op.execute("""
        UPDATE mst_approval_workflow_level
        SET level_name = COALESCE(level_name, 'Level ' || COALESCE(level_number, 1)::text)
        """)
    if "approver_role_id" in workflow_level_columns:
        op.execute("""
            UPDATE mst_approval_workflow_level
            SET approver_roles = COALESCE(approver_roles, jsonb_build_array(approver_role_id))
            WHERE approver_role_id IS NOT NULL
            """)
    if "approver_user_id" in workflow_level_columns:
        op.execute("""
            UPDATE mst_approval_workflow_level
            SET approver_users = COALESCE(approver_users, jsonb_build_array(approver_user_id))
            WHERE approver_user_id IS NOT NULL
            """)

    with op.batch_alter_table("txn_approval_request") as batch_op:
        if "workflow_type" not in request_columns:
            batch_op.add_column(sa.Column("workflow_type", workflow_type_enum, nullable=True))
        if "request_amount" not in request_columns:
            batch_op.add_column(
                sa.Column(
                    "request_amount", sa.Numeric(18, 2), server_default="0.00", nullable=False
                )
            )
        if "request_summary" not in request_columns:
            batch_op.add_column(sa.Column("request_summary", sa.String(500), nullable=True))
        if "request_details" not in request_columns:
            batch_op.add_column(sa.Column("request_details", postgresql.JSONB(), nullable=True))
        if "resolved_at" not in request_columns:
            batch_op.add_column(sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
        if "resolved_by" not in request_columns:
            batch_op.add_column(
                sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True)
            )
        if "final_comments" not in request_columns:
            batch_op.add_column(sa.Column("final_comments", sa.Text(), nullable=True))

    if "entity_amount" in request_columns:
        op.execute(
            "UPDATE txn_approval_request SET request_amount = COALESCE(request_amount, entity_amount, 0.00)"
        )
    op.execute(
        """
        UPDATE txn_approval_request
        SET request_summary = COALESCE(
            request_summary,
            entity_reference,
            entity_type || ' ' || entity_id::text
        )
        """
        if "entity_reference" in request_columns
        else """
        UPDATE txn_approval_request
        SET request_summary = COALESCE(request_summary, entity_type || ' ' || entity_id::text)
        """
    )
    if "request_data" in request_columns:
        op.execute("""
            UPDATE txn_approval_request
            SET request_details = COALESCE(request_details, request_data)
            """)
    if "final_approved_at" in request_columns:
        op.execute("""
            UPDATE txn_approval_request
            SET resolved_at = COALESCE(resolved_at, final_approved_at)
            """)
    if "final_approved_by" in request_columns:
        op.execute("""
            UPDATE txn_approval_request
            SET resolved_by = COALESCE(resolved_by, final_approved_by)
            """)
    if "remarks" in request_columns or "rejection_reason" in request_columns:
        op.execute("""
            UPDATE txn_approval_request
            SET final_comments = COALESCE(final_comments, rejection_reason, remarks)
            """)
    op.execute("""
        UPDATE txn_approval_request req
        SET workflow_type = wf.workflow_type
        FROM mst_approval_workflow wf
        WHERE req.workflow_id = wf.id
          AND req.workflow_type IS NULL
        """)

    missing_workflow_type_count = int(bind.execute(text("""
                SELECT COUNT(*)
                FROM txn_approval_request
                WHERE workflow_type IS NULL
                """)).scalar() or 0)
    if missing_workflow_type_count:
        raise RuntimeError(
            "Cannot reconcile txn_approval_request.workflow_type automatically; "
            "manual repair is required before continuing."
        )

    with op.batch_alter_table("txn_approval_request_action") as batch_op:
        if "level_number" not in action_columns:
            batch_op.add_column(sa.Column("level_number", sa.Integer(), nullable=True))
        if "action_context" not in action_columns:
            batch_op.add_column(sa.Column("action_context", postgresql.JSONB(), nullable=True))

    if "level" in action_columns:
        op.execute("""
            UPDATE txn_approval_request_action
            SET level_number = COALESCE(level_number, level)
            """)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    _create_enum_types()

    if not _needs_repair(inspector, existing_tables):
        return

    if _all_approval_tables_empty(bind, existing_tables):
        op.execute("DROP TABLE IF EXISTS txn_approval_request_action CASCADE")
        op.execute("DROP TABLE IF EXISTS txn_approval_request CASCADE")
        op.execute("DROP TABLE IF EXISTS mst_approval_workflow_level CASCADE")
        op.execute("DROP TABLE IF EXISTS mst_approval_workflow CASCADE")
        _create_canonical_tables()
        return

    if "mst_approval_workflow" not in existing_tables:
        _create_canonical_tables()
        return

    _repair_existing_tables(bind, inspector)


def downgrade() -> None:
    """No-op downgrade.

    This migration repairs drifted approval tables that may already contain tenant data.
    Reversing it safely would require table-shape heuristics that are not reliable enough
    for an automatic downgrade.
    """
