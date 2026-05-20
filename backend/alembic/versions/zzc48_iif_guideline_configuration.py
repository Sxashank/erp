"""Add configurable IIF guideline rules and fund ledger.

Revision ID: zzc48_iif_guideline_configuration
Revises: zzc47_align_bi_enum_contracts
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "zzc48_iif_guideline_configuration"
down_revision = "zzc47_align_bi_enum_contracts"
branch_labels = None
depends_on = None


CALCULATION_RULES = """{
  "method": "RATE_DIFFERENTIAL_ON_PRINCIPAL_DAYS",
  "day_count": "ACT_365",
  "cap_by_actual_interest_paid": true,
  "compute_per_tranche": true
}"""

ELIGIBILITY_RULES = """{
  "require_shipyard_located_in_india": true,
  "require_lender_regulated_in_india": true,
  "require_not_wilful_defaulter": true,
  "exclude_refinance_takeover_restructure": true,
  "exclude_overdue_or_npa": true,
  "require_sanction_after_scheme_approval": true,
  "require_lender_forwarding_same_quarter": true
}"""

REQUIRED_DOCUMENTS = """[
  {"code": "LOAN_SANCTION_LETTER", "stage": "TAGGING", "label": "Loan sanction letter"},
  {"code": "APPRAISAL_NOTE", "stage": "TAGGING", "label": "Project appraisal note"},
  {"code": "DISBURSEMENT_DETAILS", "stage": "TAGGING", "label": "Disbursement details"},
  {"code": "END_USE_CERTIFICATE", "stage": "TAGGING", "label": "End-use certificate"},
  {"code": "BORROWER_COMPLIANCE_DOCUMENTS", "stage": "TAGGING", "label": "Borrower compliance documents"},
  {"code": "INTEREST_CALCULATION_SHEET", "stage": "CLAIM_SUBMISSION", "label": "Interest calculation sheet"},
  {"code": "REPAYMENT_RECORD", "stage": "CLAIM_SUBMISSION", "label": "Borrower repayment record"},
  {"code": "REGULAR_ACCOUNT_CERTIFICATE", "stage": "CLAIM_SUBMISSION", "label": "Certificate of regular account status"},
  {"code": "NON_DUPLICATION_UNDERTAKING", "stage": "CLAIM_SUBMISSION", "label": "Undertaking on non-duplication of claims"},
  {"code": "AUDITED_INTEREST_CERTIFICATE", "stage": "CLAIM_SUBMISSION", "label": "Audited interest certificate"},
  {"code": "CLAIM_SUMMARY", "stage": "CLAIM_SUBMISSION", "label": "Claim summary"}
]"""

WORKFLOW_RULES = """{
  "claim_creator_roles": ["scheme_lender", "scheme_borrower", "scheme_admin"],
  "formal_submitter_roles": ["scheme_lender", "scheme_admin"],
  "ia_decision_sla_days": 30,
  "release_sla_days": 7,
  "release_destination": "BORROWER_LOAN_ACCOUNT",
  "require_nodal_officer": true,
  "require_grievance_cell": true
}"""

FUND_RULES = """{
  "dedicated_bank_account_required": true,
  "service_charge_first_year_percent_of_corpus": "0.10",
  "service_charge_subsequent_year_percent_of_corpus": "0.072",
  "allocation_frequency": "ANNUAL",
  "manual_neft_rtgs_reference_required": true
}"""


def upgrade() -> None:
    op.add_column(
        "mst_subvention_scheme",
        sa.Column(
            "calculation_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{CALCULATION_RULES}'::jsonb"),
        ),
    )
    op.add_column(
        "mst_subvention_scheme",
        sa.Column(
            "eligibility_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{ELIGIBILITY_RULES}'::jsonb"),
        ),
    )
    op.add_column(
        "mst_subvention_scheme",
        sa.Column(
            "required_documents",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{REQUIRED_DOCUMENTS}'::jsonb"),
        ),
    )
    op.add_column(
        "mst_subvention_scheme",
        sa.Column(
            "workflow_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{WORKFLOW_RULES}'::jsonb"),
        ),
    )
    op.add_column(
        "mst_subvention_scheme",
        sa.Column(
            "fund_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(f"'{FUND_RULES}'::jsonb"),
        ),
    )

    op.create_table(
        "txn_subvention_fund_transaction",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transaction_type", sa.String(length=40), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["claim_id"], ["txn_subvention_claim.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scheme_id"], ["mst_subvention_scheme.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_txn_sft_org", "txn_subvention_fund_transaction", ["organization_id"])
    op.create_index("ix_txn_sft_scheme", "txn_subvention_fund_transaction", ["scheme_id"])
    op.create_index("ix_txn_sft_claim", "txn_subvention_fund_transaction", ["claim_id"])
    op.create_index("ix_txn_sft_date", "txn_subvention_fund_transaction", ["transaction_date"])


def downgrade() -> None:
    op.drop_index("ix_txn_sft_date", table_name="txn_subvention_fund_transaction")
    op.drop_index("ix_txn_sft_claim", table_name="txn_subvention_fund_transaction")
    op.drop_index("ix_txn_sft_scheme", table_name="txn_subvention_fund_transaction")
    op.drop_index("ix_txn_sft_org", table_name="txn_subvention_fund_transaction")
    op.drop_table("txn_subvention_fund_transaction")

    op.drop_column("mst_subvention_scheme", "fund_rules")
    op.drop_column("mst_subvention_scheme", "workflow_rules")
    op.drop_column("mst_subvention_scheme", "required_documents")
    op.drop_column("mst_subvention_scheme", "eligibility_rules")
    op.drop_column("mst_subvention_scheme", "calculation_rules")
