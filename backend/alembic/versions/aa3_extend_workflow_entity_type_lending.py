"""Extend `workflowentitytype` enum with lending entity kinds.

Revision ID: aa3_workflowentitytype_lending
Revises: aa2_audit_day_anchor
Create Date: 2026-04-24

Closes STAGE-4-PENDING-010. Lending services (application/sanction/rating)
were building a typed `WorkflowInitRequest` but couldn't dispatch it because
the enum only covered finance types. We extend with:
  LOAN_APPLICATION
  LOAN_SANCTION
  LOAN_RATING

PostgreSQL enums cannot be altered inside a transaction if the new value is
used in the same transaction. We use ``ALTER TYPE ... ADD VALUE IF NOT EXISTS``
(Postgres 9.6+) which is idempotent and runs outside a transaction via
``op.get_context().autocommit_block()``.

Down-migration drops and recreates the enum with the original five values —
but that only works if no rows reference the new lending values. If lending
workflows are already live at down-migration time, this will fail (intended).
"""

from alembic import op

revision = "aa3_workflowentitytype_lending"
down_revision = "aa2_audit_day_anchor"
branch_labels = None
depends_on = None


NEW_VALUES = ("LOAN_APPLICATION", "LOAN_SANCTION", "LOAN_RATING")
ORIGINAL_VALUES = ("VOUCHER", "PURCHASE_BILL", "SALES_INVOICE", "PAYMENT", "JOURNAL_ENTRY")


def upgrade() -> None:
    # ALTER TYPE ADD VALUE must run outside a transaction.
    with op.get_context().autocommit_block():
        for value in NEW_VALUES:
            op.execute(f"ALTER TYPE workflowentitytype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # There's no DROP VALUE in Postgres; recreate the type.
    # This fails if any row in workflow_instances.entity_type references a new value,
    # which is correct: it would be data-destructive to allow it.
    op.execute("ALTER TYPE workflowentitytype RENAME TO workflowentitytype_old")
    new_values_sql = ", ".join(f"'{v}'" for v in ORIGINAL_VALUES)
    op.execute(f"CREATE TYPE workflowentitytype AS ENUM ({new_values_sql})")
    op.execute(
        "ALTER TABLE workflow_instances "
        "ALTER COLUMN entity_type TYPE workflowentitytype "
        "USING entity_type::text::workflowentitytype"
    )
    op.execute("DROP TYPE workflowentitytype_old")
