"""LoanCertificate table — Phase C.

Revision ID: zzc55_loan_certificates
Revises: zzc54_loan_master_data
Create Date: 2026-05-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc55_loan_certificates"
down_revision: str | None = "zzc54_loan_master_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "txn_loan_certificate",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "loan_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_account.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("los_loan_application.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "sanction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("los_loan_sanction.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "certificate_type",
            sa.Enum(
                "KFS",
                "SANCTION_LETTER",
                "WELCOME_LETTER",
                "INTEREST_CERT",
                "PROVISIONAL_INTEREST_CERT",
                "PRINCIPAL_PAID_CERT",
                "STATEMENT_OF_ACCOUNT",
                "NDC",
                "FORECLOSURE_LETTER",
                "BALANCE_CONFIRMATION",
                "CHARGE_RELEASE_LETTER",
                "ANNUAL_LOAN_STATEMENT",
                "RATE_REVISION_INTIMATION",
                "DEMAND_NOTICE",
                "SARFAESI_13_2_NOTICE",
                "OTS_LETTER",
                "RESTRUCTURE_ADDENDUM",
                "WILFUL_DEFAULTER_NOTICE",
                name="loan_certificate_type",
            ),
            nullable=False,
        ),
        sa.Column("certificate_number", sa.String(80), nullable=False),
        sa.Column(
            "dms_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_document.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("file_size", sa.BigInteger),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "issued_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "issued_to_portal_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portal_user.id", ondelete="SET NULL"),
        ),
        sa.Column("period_from", sa.Date),
        sa.Column("period_to", sa.Date),
        sa.Column("financial_year", sa.String(10)),
        sa.Column(
            "requires_acknowledgement", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column("is_acknowledged", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column(
            "acknowledged_by_portal_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portal_user.id", ondelete="SET NULL"),
        ),
        sa.Column("template_code", sa.String(60)),
        sa.Column("template_version", sa.Integer),
        sa.Column("remarks", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("ix_txn_loan_certificate_loan", "txn_loan_certificate", ["loan_account_id"])
    op.create_index(
        "ix_txn_loan_certificate_application", "txn_loan_certificate", ["application_id"]
    )
    op.create_index("ix_txn_loan_certificate_type", "txn_loan_certificate", ["certificate_type"])
    op.create_index("ix_txn_loan_certificate_issued_at", "txn_loan_certificate", ["issued_at"])


def downgrade() -> None:
    op.drop_index("ix_txn_loan_certificate_issued_at", "txn_loan_certificate")
    op.drop_index("ix_txn_loan_certificate_type", "txn_loan_certificate")
    op.drop_index("ix_txn_loan_certificate_application", "txn_loan_certificate")
    op.drop_index("ix_txn_loan_certificate_loan", "txn_loan_certificate")
    op.drop_table("txn_loan_certificate")
    sa.Enum(name="loan_certificate_type").drop(op.get_bind(), checkfirst=True)
