"""Add portal IIF loan tagging detail tables.

Revision ID: zzc50_iif_portal_loan_tagging_tables
Revises: zzc49_align_lms_receipt_status_enum
Create Date: 2026-05-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "zzc50_iif_portal_loan_tagging_tables"
down_revision: str | None = "zzc49_align_lms_receipt_status_enum"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    ]


def _audit_fks(table: str) -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_created_by",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_updated_by",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_deleted_by",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "los_application_funding_source",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_code", sa.String(length=50), nullable=False),
        sa.Column("source_label", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("remarks", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_los_app_funding_org",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["los_loan_application.id"],
            ondelete="CASCADE",
            name="fk_los_app_funding_application",
        ),
        *_audit_fks("los_application_funding_source"),
        sa.UniqueConstraint(
            "application_id",
            "source_code",
            name="uq_los_application_funding_source_app_code",
        ),
    )
    op.create_index(
        "ix_los_application_funding_source_org",
        "los_application_funding_source",
        ["organization_id"],
    )
    op.create_index(
        "ix_los_application_funding_source_app",
        "los_application_funding_source",
        ["application_id"],
    )

    op.create_table(
        "los_application_lender_loan",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("loan_type", sa.String(length=80), nullable=False),
        sa.Column("loan_amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("lender_name", sa.String(length=200), nullable=False),
        sa.Column("lender_category", sa.String(length=80), nullable=True),
        sa.Column("lender_contact", sa.String(length=50), nullable=True),
        sa.Column("lender_email", sa.String(length=255), nullable=True),
        sa.Column("lender_address", sa.String(length=500), nullable=True),
        sa.Column("lender_state", sa.String(length=100), nullable=True),
        sa.Column("lender_district", sa.String(length=100), nullable=True),
        sa.Column("lender_pincode", sa.String(length=20), nullable=True),
        sa.Column("sanction_reference", sa.String(length=100), nullable=True),
        sa.Column("sanction_date", sa.Date(), nullable=True),
        sa.Column("interest_rate_percent", sa.Numeric(9, 4), nullable=True),
        sa.Column("emi_periodicity", sa.String(length=30), nullable=True),
        sa.Column("interest_debiting_periodicity", sa.String(length=30), nullable=True),
        sa.Column("loan_account_number", sa.String(length=80), nullable=True),
        sa.Column("ifsc_code", sa.String(length=20), nullable=True),
        sa.Column("security_type", sa.String(length=100), nullable=True),
        sa.Column("disbursement_call_type", sa.String(length=40), nullable=True),
        sa.Column("emi_amount", sa.Numeric(20, 2), nullable=True),
        sa.Column("emi_due_date", sa.Date(), nullable=True),
        sa.Column(
            "lender_validation_status",
            sa.String(length=30),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("lender_validation_remarks", sa.String(length=1000), nullable=True),
        sa.Column("lender_validated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lender_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_los_app_lender_loan_org",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["los_loan_application.id"],
            ondelete="CASCADE",
            name="fk_los_app_lender_loan_application",
        ),
        sa.ForeignKeyConstraint(
            ["lender_validated_by"],
            ["portal_user.id"],
            ondelete="SET NULL",
            name="fk_los_app_lender_loan_validated_by",
        ),
        *_audit_fks("los_application_lender_loan"),
    )
    op.create_index(
        "ix_los_application_lender_loan_org",
        "los_application_lender_loan",
        ["organization_id"],
    )
    op.create_index(
        "ix_los_application_lender_loan_app",
        "los_application_lender_loan",
        ["application_id"],
    )
    op.create_index(
        "ix_los_application_lender_loan_status",
        "los_application_lender_loan",
        ["lender_validation_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_los_application_lender_loan_status", table_name="los_application_lender_loan")
    op.drop_index("ix_los_application_lender_loan_app", table_name="los_application_lender_loan")
    op.drop_index("ix_los_application_lender_loan_org", table_name="los_application_lender_loan")
    op.drop_table("los_application_lender_loan")
    op.drop_index(
        "ix_los_application_funding_source_app",
        table_name="los_application_funding_source",
    )
    op.drop_index(
        "ix_los_application_funding_source_org",
        table_name="los_application_funding_source",
    )
    op.drop_table("los_application_funding_source")
