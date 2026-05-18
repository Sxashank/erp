"""Add LMS accounting bridge account references.

Revision ID: zzc23_lms_accounting_bridge_fields
Revises: zzc22_create_fixed_asset_configuration_table
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "zzc23_lms_accounting_bridge_fields"
down_revision = "zzc22_create_fixed_asset_configuration_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lms_loan_account",
        sa.Column(
            "penal_interest_income_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lms_loan_account",
        sa.Column(
            "charges_income_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lms_loan_account",
        sa.Column(
            "receipt_suspense_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_lms_loan_account_penal_interest_income_account",
        "lms_loan_account",
        "mst_account",
        ["penal_interest_income_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lms_loan_account_charges_income_account",
        "lms_loan_account",
        "mst_account",
        ["charges_income_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lms_loan_account_receipt_suspense_account",
        "lms_loan_account",
        "mst_account",
        ["receipt_suspense_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "lms_disbursement",
        sa.Column("source_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_lms_disbursement_source_account",
        "lms_disbursement",
        "mst_account",
        ["source_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column(
        "lms_loan_receipt",
        sa.Column("receipt_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "receipt_suspense_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column("allocation_voucher_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "gl_allocated_amount",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "gl_principal_allocated",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "gl_interest_allocated",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "gl_penal_interest_allocated",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "lms_loan_receipt",
        sa.Column(
            "gl_charges_allocated",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_foreign_key(
        "fk_lms_loan_receipt_receipt_account",
        "lms_loan_receipt",
        "mst_account",
        ["receipt_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_lms_loan_receipt_suspense_account",
        "lms_loan_receipt",
        "mst_account",
        ["receipt_suspense_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_lms_loan_receipt_allocation_voucher",
        "lms_loan_receipt",
        "txn_voucher",
        ["allocation_voucher_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_lms_loan_receipt_allocation_voucher",
        "lms_loan_receipt",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lms_loan_receipt_suspense_account",
        "lms_loan_receipt",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lms_loan_receipt_receipt_account",
        "lms_loan_receipt",
        type_="foreignkey",
    )
    op.drop_column("lms_loan_receipt", "gl_charges_allocated")
    op.drop_column("lms_loan_receipt", "gl_penal_interest_allocated")
    op.drop_column("lms_loan_receipt", "gl_interest_allocated")
    op.drop_column("lms_loan_receipt", "gl_principal_allocated")
    op.drop_column("lms_loan_receipt", "gl_allocated_amount")
    op.drop_column("lms_loan_receipt", "allocation_voucher_id")
    op.drop_column("lms_loan_receipt", "receipt_suspense_account_id")
    op.drop_column("lms_loan_receipt", "receipt_account_id")

    op.drop_constraint(
        "fk_lms_disbursement_source_account",
        "lms_disbursement",
        type_="foreignkey",
    )
    op.drop_column("lms_disbursement", "source_account_id")

    op.drop_constraint(
        "fk_lms_loan_account_receipt_suspense_account",
        "lms_loan_account",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lms_loan_account_charges_income_account",
        "lms_loan_account",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lms_loan_account_penal_interest_income_account",
        "lms_loan_account",
        type_="foreignkey",
    )
    op.drop_column("lms_loan_account", "receipt_suspense_account_id")
    op.drop_column("lms_loan_account", "charges_income_account_id")
    op.drop_column("lms_loan_account", "penal_interest_income_account_id")
