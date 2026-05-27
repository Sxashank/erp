"""Phase-D lifecycle modules — 8 transactional tables.

Revision ID: zzc56_lifecycle_modules
Revises: zzc55_loan_certificates
Create Date: 2026-05-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc56_lifecycle_modules"
down_revision: str | None = "zzc55_loan_certificates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "txn_loan_takeover_in",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("takeover_reference", sa.String(60), nullable=False, unique=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("los_loan_application.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "our_loan_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_account.id", ondelete="SET NULL"),
        ),
        sa.Column("source_lender_name", sa.String(300), nullable=False),
        sa.Column("source_loan_account_no", sa.String(100), nullable=False),
        sa.Column("source_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "source_noc_doc_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_document.id", ondelete="SET NULL"),
        ),
        sa.Column("transferred_amount", sa.Numeric(18, 2)),
        sa.Column("transfer_date", sa.Date),
        sa.Column("dd_or_rtgs_reference", sa.String(100)),
        sa.Column(
            "status",
            sa.Enum(
                "INITIATED",
                "NOC_RECEIVED",
                "DD_PAID",
                "BOOKED",
                "CANCELLED",
                name="loan_takeover_status",
            ),
            nullable=False,
            server_default="INITIATED",
        ),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index(
        "ix_txn_loan_takeover_in_org_status", "txn_loan_takeover_in", ["organization_id", "status"]
    )

    op.create_table(
        "txn_loan_transfer_out",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transfer_reference", sa.String(60), nullable=False, unique=True),
        sa.Column(
            "loan_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_account.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("target_lender_name", sa.String(300), nullable=False),
        sa.Column("noc_requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outstanding_letter_issued_at", sa.DateTime(timezone=True)),
        sa.Column("outstanding_amount_quoted", sa.Numeric(18, 2)),
        sa.Column("quote_valid_till", sa.Date),
        sa.Column("payment_received_at", sa.DateTime(timezone=True)),
        sa.Column("payment_amount", sa.Numeric(18, 2)),
        sa.Column("payment_reference", sa.String(100)),
        sa.Column("security_discharged_at", sa.DateTime(timezone=True)),
        sa.Column("docs_released_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "status",
            sa.Enum(
                "NOC_REQUESTED",
                "OUTSTANDING_ISSUED",
                "PAYMENT_RECEIVED",
                "SECURITY_DISCHARGED",
                "DOCS_RELEASED",
                "CLOSED",
                "CANCELLED",
                name="loan_transfer_out_status",
            ),
            nullable=False,
            server_default="NOC_REQUESTED",
        ),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index("ix_txn_loan_transfer_out_loan", "txn_loan_transfer_out", ["loan_account_id"])

    op.create_table(
        "txn_rate_reset_event",
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
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("benchmark_code", sa.String(30), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("old_rate_percent", sa.Numeric(8, 4), nullable=False),
        sa.Column("new_rate_percent", sa.Numeric(8, 4), nullable=False),
        sa.Column("communicated_on", sa.Date),
        sa.Column(
            "intimation_doc_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_document.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "borrower_choice",
            sa.Enum(
                "INCREASE_EMI", "EXTEND_TENOR", "MIX", "SWITCH_TO_FIXED", name="rate_reset_choice"
            ),
        ),
        sa.Column("choice_received_on", sa.Date),
        sa.Column("applied_on", sa.Date),
        sa.Column("new_emi_amount", sa.Numeric(18, 2)),
        sa.Column("new_tenure_months", sa.Integer),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index("ix_txn_rate_reset_event_loan", "txn_rate_reset_event", ["loan_account_id"])
    op.create_index("ix_txn_rate_reset_event_due", "txn_rate_reset_event", ["due_date"])

    op.create_table(
        "txn_nach_presentation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mandate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_mandate.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "loan_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("presentation_date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("instalment_number", sa.Integer),
        sa.Column(
            "status",
            sa.Enum("PRESENTED", "SUCCESS", "BOUNCED", "PENDING", name="nach_presentation_status"),
            nullable=False,
            server_default="PRESENTED",
        ),
        sa.Column("cleared_on", sa.Date),
        sa.Column("return_reason_code", sa.String(10)),
        sa.Column("return_reason_description", sa.String(300)),
        sa.Column("bank_reference", sa.String(100)),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lms_loan_receipt.id", ondelete="SET NULL"),
        ),
        *_audit_columns(),
    )
    op.create_index("ix_txn_nach_presentation_mandate", "txn_nach_presentation", ["mandate_id"])
    op.create_index(
        "ix_txn_nach_presentation_present_date", "txn_nach_presentation", ["presentation_date"]
    )

    op.create_table(
        "txn_doc_release_tracker",
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
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("closure_date", sa.Date, nullable=False),
        sa.Column("target_release_date", sa.Date, nullable=False),
        sa.Column("actual_release_date", sa.Date),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RELEASED", "BREACHED", name="doc_release_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("breach_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("compensation_payable", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column(
            "documents_released",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "released_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
        ),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index("ix_txn_doc_release_loan", "txn_doc_release_tracker", ["loan_account_id"])
    op.create_index(
        "ix_txn_doc_release_target_date", "txn_doc_release_tracker", ["target_release_date"]
    )

    op.create_table(
        "txn_wilful_defaulter_proceeding",
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
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("proceeding_reference", sa.String(60), nullable=False, unique=True),
        sa.Column("npa_date", sa.Date, nullable=False),
        sa.Column("initiated_date", sa.Date, nullable=False),
        sa.Column("sla_due_date", sa.Date, nullable=False),
        sa.Column("outstanding_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("grounds_of_wilful_default", sa.Text, nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "IDENTIFICATION",
                "SHOW_CAUSE_ISSUED",
                "PERSONAL_HEARING",
                "REVIEW",
                "CONFIRMED",
                "DISMISSED",
                "SETTLED",
                name="wilful_defaulter_stage",
            ),
            nullable=False,
            server_default="IDENTIFICATION",
        ),
        sa.Column(
            "show_cause_notice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_document.id", ondelete="SET NULL"),
        ),
        sa.Column("show_cause_issued_at", sa.DateTime(timezone=True)),
        sa.Column("borrower_response_received_at", sa.DateTime(timezone=True)),
        sa.Column("borrower_response_text", sa.Text),
        sa.Column("personal_hearing_date", sa.Date),
        sa.Column("personal_hearing_notes", sa.Text),
        sa.Column("id_committee_decision", sa.Text),
        sa.Column("id_committee_decided_at", sa.DateTime(timezone=True)),
        sa.Column("review_committee_decision", sa.Text),
        sa.Column("review_committee_decided_at", sa.DateTime(timezone=True)),
        sa.Column("bureau_reported", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("bureau_reported_at", sa.DateTime(timezone=True)),
        *_audit_columns(),
    )
    op.create_index("ix_txn_wdp_org", "txn_wilful_defaulter_proceeding", ["organization_id"])
    op.create_index("ix_txn_wdp_loan", "txn_wilful_defaulter_proceeding", ["loan_account_id"])
    op.create_index("ix_txn_wdp_stage", "txn_wilful_defaulter_proceeding", ["stage"])

    op.create_table(
        "txn_loan_write_off",
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
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("write_off_reference", sa.String(60), nullable=False, unique=True),
        sa.Column(
            "write_off_type",
            sa.Enum("TECHNICAL", "FINAL", name="loan_write_off_type"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PROPOSED",
                "APPROVED",
                "REJECTED",
                "EFFECTED",
                "REVERSED",
                name="loan_write_off_status",
            ),
            nullable=False,
            server_default="PROPOSED",
        ),
        sa.Column("proposed_date", sa.Date, nullable=False),
        sa.Column(
            "proposed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("proposed_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("proposed_reason", sa.Text, nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
        ),
        sa.Column("approval_authority", sa.String(80)),
        sa.Column("effected_date", sa.Date),
        sa.Column(
            "gl_voucher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        ),
        sa.Column("principal_written_off", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("interest_written_off", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("charges_written_off", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column(
            "total_recovered_post_write_off", sa.Numeric(18, 2), nullable=False, server_default="0"
        ),
        sa.Column("bureau_reported_at", sa.DateTime(timezone=True)),
        sa.Column("board_reported_quarter", sa.String(8)),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index("ix_txn_loan_write_off_loan", "txn_loan_write_off", ["loan_account_id"])
    op.create_index("ix_txn_loan_write_off_status", "txn_loan_write_off", ["status"])

    op.create_table(
        "txn_loan_interest_revival",
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
            sa.ForeignKey("lms_loan_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revival_reference", sa.String(60), nullable=False, unique=True),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "proposed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("revivable_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("proposed_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum("PROPOSED", "APPROVED", "REJECTED", "EFFECTED", name="interest_revival_status"),
            nullable=False,
            server_default="PROPOSED",
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
        ),
        sa.Column("effected_at", sa.DateTime(timezone=True)),
        sa.Column(
            "gl_voucher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        ),
        sa.Column("remarks", sa.Text),
        *_audit_columns(),
    )
    op.create_index(
        "ix_txn_loan_interest_revival_loan", "txn_loan_interest_revival", ["loan_account_id"]
    )


def downgrade() -> None:
    for table in (
        "txn_loan_interest_revival",
        "txn_loan_write_off",
        "txn_wilful_defaulter_proceeding",
        "txn_doc_release_tracker",
        "txn_nach_presentation",
        "txn_rate_reset_event",
        "txn_loan_transfer_out",
        "txn_loan_takeover_in",
    ):
        op.drop_table(table)
