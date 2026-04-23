"""Add legal and portal tables.

Revision ID: z22_add_legal_and_portal_tables
Revises: z21_add_einvoice_ewaybill_tables
Create Date: 2026-01-15

This migration creates:
- Legal Module tables (law firms, advocates, notices, documents, expenses, courts)
- Portal Module tables (users, sessions, notifications, payments, documents, service requests)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "z22_add_legal_and_portal_tables"
down_revision: Union[str, None] = "z21_add_einvoice_ewaybill_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Legal and Portal module tables."""

    # ==========================================================================
    # LEGAL MODULE TABLES
    # ==========================================================================

    # Law Firm Master
    op.create_table(
        "mst_law_firm",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("registration_number", sa.String(100)),
        sa.Column("bar_council_id", sa.String(100)),
        sa.Column("pan", sa.String(10)),
        sa.Column("gstin", sa.String(15)),
        sa.Column("address_line1", sa.String(255)),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state_code", sa.String(2)),
        sa.Column("pincode", sa.String(10)),
        sa.Column("country", sa.String(50), default="India"),
        sa.Column("phone", sa.String(20)),
        sa.Column("mobile", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(255)),
        sa.Column("bank_account_name", sa.String(255)),
        sa.Column("bank_account_number", sa.String(50)),
        sa.Column("bank_ifsc", sa.String(11)),
        sa.Column("empanelment_date", sa.Date),
        sa.Column("contract_expiry_date", sa.Date),
        sa.Column("fee_structure_type", sa.String(50)),
        sa.Column("retainer_amount", sa.Numeric(15, 2)),
        sa.Column("rating", sa.Numeric(3, 2)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_mst_law_firm_org", "mst_law_firm", ["organization_id"])

    # Advocate Master
    op.create_table(
        "mst_advocate",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("law_firm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_law_firm.id")),
        sa.Column("enrollment_number", sa.String(100), nullable=False),
        sa.Column("bar_council_state", sa.String(50)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("designation", sa.String(100)),
        sa.Column("pan", sa.String(10)),
        sa.Column("aadhaar_hash", sa.String(64)),
        sa.Column("address_line1", sa.String(255)),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state_code", sa.String(2)),
        sa.Column("pincode", sa.String(10)),
        sa.Column("country", sa.String(50), default="India"),
        sa.Column("phone", sa.String(20)),
        sa.Column("mobile", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("fee_structure_type", sa.String(50)),
        sa.Column("base_fee", sa.Numeric(15, 2)),
        sa.Column("appearance_fee", sa.Numeric(15, 2)),
        sa.Column("success_fee_percent", sa.Numeric(5, 2)),
        sa.Column("bank_account_name", sa.String(255)),
        sa.Column("bank_account_number", sa.String(50)),
        sa.Column("bank_ifsc", sa.String(11)),
        sa.Column("rating", sa.Numeric(3, 2)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_mst_advocate_org", "mst_advocate", ["organization_id"])
    op.create_index("ix_mst_advocate_enrollment", "mst_advocate", ["enrollment_number"], unique=True)

    # Advocate Specialization
    op.create_table(
        "mst_advocate_specialization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("advocate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_advocate.id"), nullable=False),
        sa.Column("specialization_type", sa.String(50), nullable=False),
        sa.Column("years_experience", sa.Integer),
        sa.Column("certification", sa.String(255)),
        sa.Column("is_primary", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Advocate Assignment
    op.create_table(
        "txn_advocate_assignment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("advocate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_advocate.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("role", sa.String(50), default="LEAD"),
        sa.Column("assigned_date", sa.Date, nullable=False),
        sa.Column("relieved_date", sa.Date),
        sa.Column("agreed_fee", sa.Numeric(15, 2)),
        sa.Column("fee_type", sa.String(50)),
        sa.Column("remarks", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Advocate Performance
    op.create_table(
        "txn_advocate_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("advocate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_advocate.id"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("cases_assigned", sa.Integer, default=0),
        sa.Column("cases_won", sa.Integer, default=0),
        sa.Column("cases_lost", sa.Integer, default=0),
        sa.Column("cases_settled", sa.Integer, default=0),
        sa.Column("hearings_attended", sa.Integer, default=0),
        sa.Column("hearings_missed", sa.Integer, default=0),
        sa.Column("total_recovery", sa.Numeric(15, 2)),
        sa.Column("total_fees_paid", sa.Numeric(15, 2)),
        sa.Column("success_rate", sa.Numeric(5, 2)),
        sa.Column("rating", sa.Numeric(3, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Court Master
    op.create_table(
        "mst_court",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("court_type", sa.String(50), nullable=False),
        sa.Column("jurisdiction", sa.String(255)),
        sa.Column("address_line1", sa.String(255)),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state_code", sa.String(2)),
        sa.Column("pincode", sa.String(10)),
        sa.Column("country", sa.String(50), default="India"),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(255)),
        sa.Column("filing_portal_url", sa.String(500)),
        sa.Column("pecuniary_limit_min", sa.Numeric(15, 2)),
        sa.Column("pecuniary_limit_max", sa.Numeric(15, 2)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_mst_court_org_code", "mst_court", ["organization_id", "code"], unique=True)

    # Court Bench
    op.create_table(
        "mst_court_bench",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("court_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_court.id"), nullable=False),
        sa.Column("bench_number", sa.String(50)),
        sa.Column("presiding_officer", sa.String(255)),
        sa.Column("designation", sa.String(100)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Court Fee Slab
    op.create_table(
        "mst_court_fee_slab",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("court_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_court.id"), nullable=False),
        sa.Column("case_type", sa.String(50)),
        sa.Column("claim_min", sa.Numeric(15, 2), nullable=False),
        sa.Column("claim_max", sa.Numeric(15, 2)),
        sa.Column("fee_type", sa.String(20)),
        sa.Column("fee_value", sa.Numeric(15, 4), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Notice Template
    op.create_table(
        "mst_notice_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("notice_type", sa.String(50), nullable=False),
        sa.Column("template_body", sa.Text, nullable=False),
        sa.Column("statutory_period_days", sa.Integer),
        sa.Column("act_reference", sa.String(255)),
        sa.Column("section_reference", sa.String(100)),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_mst_notice_template_org_code", "mst_notice_template", ["organization_id", "code"], unique=True)

    # Legal Notice
    op.create_table(
        "txn_legal_notice",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("notice_number", sa.String(100), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_notice_template.id")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("notice_type", sa.String(50), nullable=False),
        sa.Column("notice_date", sa.Date, nullable=False),
        sa.Column("notice_body", sa.Text, nullable=False),
        sa.Column("amount_demanded", sa.Numeric(15, 2)),
        sa.Column("statutory_period_days", sa.Integer),
        sa.Column("response_due_date", sa.Date),
        sa.Column("status", sa.String(50), default="DRAFT"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_txn_legal_notice_org_number", "txn_legal_notice", ["organization_id", "notice_number"], unique=True)

    # Notice Delivery
    op.create_table(
        "txn_notice_delivery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("notice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_notice.id"), nullable=False),
        sa.Column("recipient_type", sa.String(50)),
        sa.Column("recipient_name", sa.String(255)),
        sa.Column("delivery_mode", sa.String(50), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("dispatch_date", sa.Date),
        sa.Column("tracking_number", sa.String(100)),
        sa.Column("delivery_date", sa.Date),
        sa.Column("delivery_status", sa.String(50), default="PENDING"),
        sa.Column("pod_document_path", sa.String(500)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Notice Response
    op.create_table(
        "txn_notice_response",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("notice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_notice.id"), nullable=False),
        sa.Column("response_date", sa.Date, nullable=False),
        sa.Column("response_type", sa.String(50)),
        sa.Column("response_summary", sa.Text),
        sa.Column("document_path", sa.String(500)),
        sa.Column("is_valid_objection", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Legal Document Type
    op.create_table(
        "mst_legal_document_type",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("is_mandatory", sa.Boolean, default=False),
        sa.Column("requires_original", sa.Boolean, default=False),
        sa.Column("requires_notarization", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Legal Document
    op.create_table(
        "txn_legal_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_legal_document_type.id")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_number", sa.String(100)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("file_size", sa.Integer),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("is_original", sa.Boolean, default=False),
        sa.Column("is_certified_copy", sa.Boolean, default=False),
        sa.Column("execution_date", sa.Date),
        sa.Column("expiry_date", sa.Date),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Document Version
    op.create_table(
        "txn_document_version",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_document.id"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("change_remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Document Checklist
    op.create_table(
        "txn_document_checklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_legal_document_type.id")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_document.id")),
        sa.Column("is_collected", sa.Boolean, default=False),
        sa.Column("collected_date", sa.Date),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Expense Category
    op.create_table(
        "mst_expense_category",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_type", sa.String(50)),
        sa.Column("gl_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_recoverable", sa.Boolean, default=True),
        sa.Column("requires_approval", sa.Boolean, default=True),
        sa.Column("approval_limit", sa.Numeric(15, 2)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Legal Expense
    op.create_table(
        "txn_legal_expense",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("expense_number", sa.String(100), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_expense_category.id")),
        sa.Column("advocate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_advocate.id")),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("base_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2)),
        sa.Column("gst_amount", sa.Numeric(15, 2)),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("tds_applicable", sa.Boolean, default=False),
        sa.Column("tds_section", sa.String(20)),
        sa.Column("tds_rate", sa.Numeric(5, 2)),
        sa.Column("tds_amount", sa.Numeric(15, 2)),
        sa.Column("net_payable", sa.Numeric(15, 2)),
        sa.Column("voucher_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(50), default="PENDING"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("paid_date", sa.Date),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Expense Recovery
    op.create_table(
        "txn_expense_recovery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_expense.id"), nullable=False),
        sa.Column("recovery_type", sa.String(50)),
        sa.Column("recovery_date", sa.Date),
        sa.Column("recovery_amount", sa.Numeric(15, 2)),
        sa.Column("auction_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ots_id", postgresql.UUID(as_uuid=True)),
        sa.Column("voucher_id", postgresql.UUID(as_uuid=True)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Advocate Fee
    op.create_table(
        "txn_advocate_fee",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("advocate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_advocate.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("fee_type", sa.String(50)),
        sa.Column("hearing_date", sa.Date),
        sa.Column("description", sa.Text),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_legal_expense.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Statutory Period Master
    op.create_table(
        "mst_statutory_period",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("act_name", sa.String(255)),
        sa.Column("section", sa.String(100)),
        sa.Column("period_days", sa.Integer, nullable=False),
        sa.Column("period_type", sa.String(20), default="CALENDAR"),
        sa.Column("trigger_event", sa.String(255)),
        sa.Column("consequence", sa.Text),
        sa.Column("alert_days_before", sa.Integer, default=7),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Period Tracking
    op.create_table(
        "txn_period_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("statutory_period_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_statutory_period.id")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("trigger_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("completed_date", sa.Date),
        sa.Column("status", sa.String(50), default="ACTIVE"),
        sa.Column("remarks", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Limitation Alert
    op.create_table(
        "txn_limitation_alert",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("period_tracking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("txn_period_tracking.id")),
        sa.Column("alert_date", sa.Date, nullable=False),
        sa.Column("days_remaining", sa.Integer),
        sa.Column("priority", sa.String(20)),
        sa.Column("message", sa.Text),
        sa.Column("is_acknowledged", sa.Boolean, default=False),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ==========================================================================
    # PORTAL MODULE TABLES
    # ==========================================================================

    # Portal User
    op.create_table(
        "portal_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("mobile", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("full_name", sa.String(255)),
        sa.Column("status", sa.String(50), default="PENDING_VERIFICATION"),
        sa.Column("preferred_language", sa.String(10), default="en"),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("failed_login_attempts", sa.Integer, default=0),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_user_org_mobile", "portal_user", ["organization_id", "mobile"], unique=True)

    # Portal Session
    op.create_table(
        "portal_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True)),
        sa.Column("session_token", sa.String(255), nullable=False),
        sa.Column("refresh_token", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_portal_session_token", "portal_session", ["session_token"], unique=True)

    # Portal Device
    op.create_table(
        "portal_device",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("device_type", sa.String(50)),
        sa.Column("device_name", sa.String(255)),
        sa.Column("os_name", sa.String(100)),
        sa.Column("os_version", sa.String(50)),
        sa.Column("app_version", sa.String(50)),
        sa.Column("push_token", sa.String(500)),
        sa.Column("is_trusted", sa.Boolean, default=False),
        sa.Column("trusted_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Portal OTP
    op.create_table(
        "portal_otp",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id")),
        sa.Column("mobile", sa.String(20), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("max_attempts", sa.Integer, default=3),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_portal_otp_mobile_purpose", "portal_otp", ["mobile", "purpose"])

    # Portal Consent
    op.create_table(
        "portal_consent",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("consent_version", sa.String(20)),
        sa.Column("is_accepted", sa.Boolean, default=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("device_info", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Portal Notification
    op.create_table(
        "portal_notification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("notification_type", sa.String(50)),
        sa.Column("channel", sa.String(50)),
        sa.Column("priority", sa.String(20), default="NORMAL"),
        sa.Column("action_url", sa.String(500)),
        sa.Column("action_data", postgresql.JSONB),
        sa.Column("is_read", sa.Boolean, default=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("delivery_status", sa.String(50)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_notification_user_read", "portal_notification", ["user_id", "is_read"])

    # Portal Message
    op.create_table(
        "portal_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True)),
        sa.Column("subject", sa.String(255)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_from_customer", sa.Boolean, default=True),
        sa.Column("sender_name", sa.String(255)),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_read", sa.Boolean, default=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("has_attachments", sa.Boolean, default=False),
        sa.Column("attachment_paths", postgresql.JSONB),
        sa.Column("reference_type", sa.String(50)),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal Ticket
    op.create_table(
        "portal_ticket",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("ticket_number", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(50)),
        sa.Column("sub_category", sa.String(100)),
        sa.Column("priority", sa.String(20), default="MEDIUM"),
        sa.Column("status", sa.String(50), default="OPEN"),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("sla_due_at", sa.DateTime(timezone=True)),
        sa.Column("is_sla_breached", sa.Boolean, default=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("resolution_summary", sa.Text),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("customer_rating", sa.Integer),
        sa.Column("customer_feedback", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_ticket_org_number", "portal_ticket", ["organization_id", "ticket_number"], unique=True)

    # Portal Announcement
    op.create_table(
        "portal_announcement",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("announcement_type", sa.String(50)),
        sa.Column("display_position", sa.String(50)),
        sa.Column("target_audience", sa.String(50)),
        sa.Column("action_url", sa.String(500)),
        sa.Column("action_text", sa.String(100)),
        sa.Column("start_date", sa.DateTime(timezone=True)),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("is_dismissible", sa.Boolean, default=True),
        sa.Column("view_count", sa.Integer, default=0),
        sa.Column("dismiss_count", sa.Integer, default=0),
        sa.Column("click_count", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal Payment Request
    op.create_table(
        "portal_payment_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("request_number", sa.String(100), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payment_type", sa.String(50)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), default="INR"),
        sa.Column("description", sa.Text),
        sa.Column("due_date", sa.Date),
        sa.Column("installment_number", sa.Integer),
        sa.Column("gateway_name", sa.String(50)),
        sa.Column("gateway_order_id", sa.String(255)),
        sa.Column("checkout_url", sa.String(500)),
        sa.Column("status", sa.String(50), default="INITIATED"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_payment_request_org_number", "portal_payment_request", ["organization_id", "request_number"], unique=True)

    # Portal Payment Transaction
    op.create_table(
        "portal_payment_transaction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_payment_request.id"), nullable=False),
        sa.Column("transaction_reference", sa.String(255), nullable=False),
        sa.Column("gateway_payment_id", sa.String(255)),
        sa.Column("gateway_signature", sa.String(500)),
        sa.Column("payment_mode", sa.String(50)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), default="INR"),
        sa.Column("status", sa.String(50)),
        sa.Column("bank_reference", sa.String(255)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("card_last4", sa.String(4)),
        sa.Column("card_network", sa.String(50)),
        sa.Column("upi_vpa", sa.String(255)),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text),
        sa.Column("gateway_response", postgresql.JSONB),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_portal_payment_txn_ref", "portal_payment_transaction", ["transaction_reference"], unique=True)

    # Portal Saved Payment Method
    op.create_table(
        "portal_saved_payment_method",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("payment_mode", sa.String(50), nullable=False),
        sa.Column("token_id", sa.String(255)),
        sa.Column("display_name", sa.String(255)),
        sa.Column("card_last4", sa.String(4)),
        sa.Column("card_network", sa.String(50)),
        sa.Column("card_expiry", sa.String(7)),
        sa.Column("upi_vpa", sa.String(255)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("is_default", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal Auto Debit Mandate
    op.create_table(
        "portal_auto_debit_mandate",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("mandate_type", sa.String(50)),
        sa.Column("umrn", sa.String(100)),
        sa.Column("bank_account_number", sa.String(50)),
        sa.Column("bank_ifsc", sa.String(11)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("account_holder_name", sa.String(255)),
        sa.Column("max_amount", sa.Numeric(15, 2)),
        sa.Column("frequency", sa.String(50)),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("status", sa.String(50), default="PENDING"),
        sa.Column("registered_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("cancellation_reason", sa.Text),
        sa.Column("gateway_mandate_id", sa.String(255)),
        sa.Column("gateway_response", postgresql.JSONB),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal Document
    op.create_table(
        "portal_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_size", sa.Integer),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("document_date", sa.Date),
        sa.Column("financial_year", sa.String(10)),
        sa.Column("is_downloadable", sa.Boolean, default=True),
        sa.Column("download_count", sa.Integer, default=0),
        sa.Column("last_downloaded_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_document_user_type", "portal_document", ["user_id", "document_type"])

    # Portal Document Request
    op.create_table(
        "portal_document_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("request_reason", sa.Text),
        sa.Column("status", sa.String(50), default="PENDING"),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("due_date", sa.Date),
        sa.Column("processed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_document.id")),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal KYC Verification
    op.create_table(
        "portal_kyc_verification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("kyc_type", sa.String(50), nullable=False),
        sa.Column("reference_number", sa.String(100)),
        sa.Column("name_as_per_kyc", sa.String(255)),
        sa.Column("dob", sa.Date),
        sa.Column("address", sa.Text),
        sa.Column("photo_path", sa.String(500)),
        sa.Column("status", sa.String(50), default="PENDING"),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("verification_data", postgresql.JSONB),
        sa.Column("api_response", postgresql.JSONB),
        sa.Column("failure_reason", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )

    # Portal Service Request
    op.create_table(
        "portal_service_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_user.id"), nullable=False),
        sa.Column("request_number", sa.String(100), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("request_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="SUBMITTED"),
        sa.Column("request_data", postgresql.JSONB),
        sa.Column("amount", sa.Numeric(15, 2)),
        sa.Column("effective_date", sa.Date),
        sa.Column("remarks", sa.Text),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_remarks", sa.Text),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approval_remarks", sa.Text),
        sa.Column("processed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("processing_remarks", sa.Text),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
    )
    op.create_index("ix_portal_service_request_org_number", "portal_service_request", ["organization_id", "request_number"], unique=True)

    # Portal Service Request Document
    op.create_table(
        "portal_service_request_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_service_request.id"), nullable=False),
        sa.Column("document_type", sa.String(50)),
        sa.Column("title", sa.String(255)),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_size", sa.Integer),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Portal Service Request History
    op.create_table(
        "portal_service_request_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portal_service_request.id"), nullable=False),
        sa.Column("from_status", sa.String(50)),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("changed_by_name", sa.String(255)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop Legal and Portal module tables."""

    # Portal tables
    op.drop_table("portal_service_request_history")
    op.drop_table("portal_service_request_document")
    op.drop_table("portal_service_request")
    op.drop_table("portal_kyc_verification")
    op.drop_table("portal_document_request")
    op.drop_table("portal_document")
    op.drop_table("portal_auto_debit_mandate")
    op.drop_table("portal_saved_payment_method")
    op.drop_table("portal_payment_transaction")
    op.drop_table("portal_payment_request")
    op.drop_table("portal_announcement")
    op.drop_table("portal_ticket")
    op.drop_table("portal_message")
    op.drop_table("portal_notification")
    op.drop_table("portal_consent")
    op.drop_table("portal_otp")
    op.drop_table("portal_device")
    op.drop_table("portal_session")
    op.drop_table("portal_user")

    # Legal tables
    op.drop_table("txn_limitation_alert")
    op.drop_table("txn_period_tracking")
    op.drop_table("mst_statutory_period")
    op.drop_table("txn_advocate_fee")
    op.drop_table("txn_expense_recovery")
    op.drop_table("txn_legal_expense")
    op.drop_table("mst_expense_category")
    op.drop_table("txn_document_checklist")
    op.drop_table("txn_document_version")
    op.drop_table("txn_legal_document")
    op.drop_table("mst_legal_document_type")
    op.drop_table("txn_notice_response")
    op.drop_table("txn_notice_delivery")
    op.drop_table("txn_legal_notice")
    op.drop_table("mst_notice_template")
    op.drop_table("mst_court_fee_slab")
    op.drop_table("mst_court_bench")
    op.drop_table("mst_court")
    op.drop_table("txn_advocate_performance")
    op.drop_table("txn_advocate_assignment")
    op.drop_table("mst_advocate_specialization")
    op.drop_table("mst_advocate")
    op.drop_table("mst_law_firm")
