"""Add treasury fund deployment mapping."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zza4_add_fund_deployment_mapping"
down_revision = "zza3_add_lms_receipt_statement_match"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trs_fund_deployment",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("borrowing_id", sa.UUID(), nullable=False),
        sa.Column("borrowing_tranche_id", sa.UUID(), nullable=True),
        sa.Column("loan_account_id", sa.UUID(), nullable=False),
        sa.Column("disbursement_id", sa.UUID(), nullable=True),
        sa.Column("deployment_reference", sa.String(length=50), nullable=False),
        sa.Column("allocation_date", sa.Date(), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("cost_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("lending_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("spread_bps", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "allocation_basis",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("remarks", sa.Text(), nullable=True),
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
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("allocated_amount > 0", name="ck_trs_fund_deployment_amount"),
        sa.CheckConstraint("cost_rate >= 0", name="ck_trs_fund_deployment_cost_rate"),
        sa.CheckConstraint(
            "lending_rate >= 0",
            name="ck_trs_fund_deployment_lending_rate",
        ),
        sa.ForeignKeyConstraint(
            ["borrowing_id"],
            ["trs_borrowing.id"],
            name="fk_trs_fund_deployment_borrowing",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["borrowing_tranche_id"],
            ["trs_borrowing_tranche.id"],
            name="fk_trs_fund_deployment_tranche",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            name="fk_trs_fund_deployment_created_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            name="fk_trs_fund_deployment_deleted_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["disbursement_id"],
            ["lms_disbursement.id"],
            name="fk_trs_fund_deployment_disbursement",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["loan_account_id"],
            ["lms_loan_account.id"],
            name="fk_trs_fund_deployment_loan_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            name="fk_trs_fund_deployment_org",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            name="fk_trs_fund_deployment_updated_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "deployment_reference",
            name="uq_trs_fund_deployment_reference",
        ),
    )
    op.create_index(
        "ix_trs_fund_deployment_org_date",
        "trs_fund_deployment",
        ["organization_id", "allocation_date"],
    )
    op.create_index(
        "ix_trs_fund_deployment_borrowing",
        "trs_fund_deployment",
        ["borrowing_id", "status"],
    )
    op.create_index(
        "ix_trs_fund_deployment_loan",
        "trs_fund_deployment",
        ["loan_account_id", "status"],
    )
    op.create_index(
        "ix_trs_fund_deployment_disbursement",
        "trs_fund_deployment",
        ["disbursement_id"],
    )
    op.create_index(
        "ix_trs_fund_deployment_organization_id",
        "trs_fund_deployment",
        ["organization_id"],
    )
    op.create_index(
        "ix_trs_fund_deployment_allocation_date",
        "trs_fund_deployment",
        ["allocation_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trs_fund_deployment_allocation_date",
        table_name="trs_fund_deployment",
    )
    op.drop_index(
        "ix_trs_fund_deployment_organization_id",
        table_name="trs_fund_deployment",
    )
    op.drop_index(
        "ix_trs_fund_deployment_disbursement",
        table_name="trs_fund_deployment",
    )
    op.drop_index("ix_trs_fund_deployment_loan", table_name="trs_fund_deployment")
    op.drop_index("ix_trs_fund_deployment_borrowing", table_name="trs_fund_deployment")
    op.drop_index("ix_trs_fund_deployment_org_date", table_name="trs_fund_deployment")
    op.drop_table("trs_fund_deployment")
