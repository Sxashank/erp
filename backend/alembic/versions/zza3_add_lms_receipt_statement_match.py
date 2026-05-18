"""Add LMS receipt to bank statement matching audit link."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zza3_add_lms_receipt_statement_match"
down_revision = "zza2_add_scheme_portal_dms_linkage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lms_receipt_bank_statement_match",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("receipt_id", sa.UUID(), nullable=False),
        sa.Column("statement_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=False),
        sa.Column("matched_amount", sa.Numeric(20, 2), nullable=False),
        sa.Column(
            "match_confidence",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="100",
        ),
        sa.Column(
            "match_basis",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "match_type",
            sa.String(length=20),
            nullable=False,
            server_default="AUTO",
        ),
        sa.Column(
            "matched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("matched_by_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint(
            "match_confidence >= 0 AND match_confidence <= 100",
            name="ck_receipt_statement_match_confidence",
        ),
        sa.CheckConstraint(
            "matched_amount > 0",
            name="ck_receipt_statement_match_amount",
        ),
        sa.ForeignKeyConstraint(
            ["bank_account_id"],
            ["mst_account.id"],
            name="fk_lms_receipt_stmt_match_bank_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["matched_by_id"],
            ["mst_user.id"],
            name="fk_lms_receipt_stmt_match_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            name="fk_lms_receipt_stmt_match_created_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            name="fk_lms_receipt_stmt_match_updated_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            name="fk_lms_receipt_stmt_match_deleted_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            name="fk_lms_receipt_stmt_match_org",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["receipt_id"],
            ["lms_loan_receipt.id"],
            name="fk_lms_receipt_stmt_match_receipt",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["txn_bank_statement.id"],
            name="fk_lms_receipt_stmt_match_statement",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "receipt_id",
            "statement_id",
            name="uq_receipt_statement_match",
        ),
    )
    op.create_index(
        "ix_lms_receipt_bank_statement_match_organization_id",
        "lms_receipt_bank_statement_match",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_lms_receipt_bank_statement_match_receipt_id",
        "lms_receipt_bank_statement_match",
        ["receipt_id"],
        unique=False,
    )
    op.create_index(
        "ix_lms_receipt_bank_statement_match_statement_id",
        "lms_receipt_bank_statement_match",
        ["statement_id"],
        unique=False,
    )
    op.create_index(
        "ix_lms_receipt_bank_statement_match_bank_account_id",
        "lms_receipt_bank_statement_match",
        ["bank_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_lms_receipt_stmt_org_date",
        "lms_receipt_bank_statement_match",
        ["organization_id", "matched_at"],
        unique=False,
    )
    op.create_index(
        "ix_lms_receipt_stmt_bank",
        "lms_receipt_bank_statement_match",
        ["bank_account_id", "matched_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lms_receipt_stmt_bank",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_index(
        "ix_lms_receipt_stmt_org_date",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_index(
        "ix_lms_receipt_bank_statement_match_bank_account_id",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_index(
        "ix_lms_receipt_bank_statement_match_statement_id",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_index(
        "ix_lms_receipt_bank_statement_match_receipt_id",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_index(
        "ix_lms_receipt_bank_statement_match_organization_id",
        table_name="lms_receipt_bank_statement_match",
    )
    op.drop_table("lms_receipt_bank_statement_match")
