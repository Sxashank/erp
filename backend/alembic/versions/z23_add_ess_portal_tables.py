"""Add ESS Portal tables.

Revision ID: z23_add_ess_portal_tables
Revises: z22_add_legal_and_portal_tables
Create Date: 2026-01-16

This migration creates:
- ESS User Management (users, sessions, devices, OTPs)
- Reimbursement Claims (categories, claims, line items, approvals)
- Helpdesk Tickets (categories, tickets, comments, history)
- IT Declaration (sections, declarations, items, HRA receipts)
- Attendance Regularization
- Profile Update Requests
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "z23_add_ess_portal_tables"
down_revision: Union[str, None] = "z22_add_legal_and_portal_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ESS Portal tables."""

    # ==========================================================================
    # ESS USER MANAGEMENT
    # ==========================================================================

    # ESS User
    op.create_table(
        "ess_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mobile", sa.String(20), nullable=False, index=True),
        sa.Column("email", sa.String(255)),
        sa.Column("is_mobile_verified", sa.Boolean, default=False),
        sa.Column("is_email_verified", sa.Boolean, default=False),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        sa.Column("must_change_password", sa.Boolean, default=False),
        sa.Column("mfa_enabled", sa.Boolean, default=False),
        sa.Column("mfa_secret", sa.String(100)),
        sa.Column("login_attempts", sa.Integer, default=0),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("last_login_ip", sa.String(50)),
        sa.Column("preferred_language", sa.String(10), default="en"),
        sa.Column("notification_preferences", postgresql.JSONB),
        sa.Column("status", sa.String(20), default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_ess_user_org", "ess_user", ["organization_id"])
    op.create_index("ix_ess_user_employee", "ess_user", ["employee_id"])
    op.create_unique_constraint("uq_ess_user_org_employee", "ess_user", ["organization_id", "employee_id"])

    # ESS Session
    op.create_table(
        "ess_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_token", sa.String(500), nullable=False, unique=True),
        sa.Column("refresh_token", sa.String(500)),
        sa.Column("device_id", postgresql.UUID(as_uuid=True)),
        sa.Column("device_type", sa.String(50)),
        sa.Column("device_name", sa.String(200)),
        sa.Column("os_name", sa.String(50)),
        sa.Column("os_version", sa.String(50)),
        sa.Column("browser", sa.String(100)),
        sa.Column("app_version", sa.String(20)),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("location", sa.String(200)),
        sa.Column("login_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ESS Device
    op.create_table(
        "ess_device",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_uuid", sa.String(100), nullable=False),
        sa.Column("device_name", sa.String(200), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("manufacturer", sa.String(100)),
        sa.Column("model", sa.String(100)),
        sa.Column("os_name", sa.String(50)),
        sa.Column("os_version", sa.String(50)),
        sa.Column("fcm_token", sa.String(500)),
        sa.Column("apns_token", sa.String(500)),
        sa.Column("is_trusted", sa.Boolean, default=False),
        sa.Column("trusted_at", sa.DateTime(timezone=True)),
        sa.Column("last_used", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Add foreign key for device_id in session
    op.create_foreign_key(
        "fk_ess_session_device",
        "ess_session", "ess_device",
        ["device_id"], ["id"],
        ondelete="SET NULL"
    )

    # ESS OTP
    op.create_table(
        "ess_otp",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), index=True),
        sa.Column("mobile", sa.String(20), index=True),
        sa.Column("email", sa.String(255)),
        sa.Column("otp_code", sa.String(10), nullable=False),
        sa.Column("otp_type", sa.String(20), nullable=False),
        sa.Column("purpose", sa.String(100)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean, default=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("max_attempts", sa.Integer, default=3),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Profile Update Request
    op.create_table(
        "ess_profile_update_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_number", sa.String(30), nullable=False, unique=True),
        sa.Column("update_type", sa.String(30), nullable=False),
        sa.Column("current_values", postgresql.JSONB, nullable=False),
        sa.Column("requested_values", postgresql.JSONB, nullable=False),
        sa.Column("change_reason", sa.Text),
        sa.Column("attachments", postgresql.JSONB),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewer_remarks", sa.Text),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ==========================================================================
    # REIMBURSEMENT CLAIMS
    # ==========================================================================

    # Reimbursement Category Master
    op.create_table(
        "mst_reimbursement_category",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("claim_type", sa.String(30), nullable=False),
        sa.Column("max_amount_per_claim", sa.Numeric(12, 2)),
        sa.Column("max_claims_per_month", sa.Integer),
        sa.Column("max_amount_per_month", sa.Numeric(12, 2)),
        sa.Column("max_amount_per_year", sa.Numeric(12, 2)),
        sa.Column("requires_approval", sa.Boolean, default=True),
        sa.Column("approval_limit", sa.Numeric(12, 2)),
        sa.Column("requires_bills", sa.Boolean, default=True),
        sa.Column("min_bill_amount", sa.Numeric(12, 2)),
        sa.Column("gl_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_taxable", sa.Boolean, default=False),
        sa.Column("tax_section", sa.String(20)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_reimbursement_category_org_code", "mst_reimbursement_category", ["organization_id", "code"])

    # Reimbursement Claim
    op.create_table(
        "ess_reimbursement_claim",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claim_number", sa.String(30), nullable=False),
        sa.Column("claim_date", sa.Date, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_reimbursement_category.id", ondelete="SET NULL")),
        sa.Column("claim_type", sa.String(30), nullable=False),
        sa.Column("expense_from", sa.Date, nullable=False),
        sa.Column("expense_to", sa.Date, nullable=False),
        sa.Column("claimed_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("purpose", sa.String(500)),
        sa.Column("travel_from", sa.String(200)),
        sa.Column("travel_to", sa.String(200)),
        sa.Column("travel_mode", sa.String(50)),
        sa.Column("kilometers", sa.Numeric(10, 2)),
        sa.Column("bills_attached", sa.Integer, default=0),
        sa.Column("attachments", postgresql.JSONB),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("approved_date", sa.Date),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("payment_date", sa.Date),
        sa.Column("payment_reference", sa.String(100)),
        sa.Column("payment_mode", sa.String(50)),
        sa.Column("payroll_month", sa.String(7)),
        sa.Column("included_in_payslip", sa.Boolean, default=False),
        sa.Column("status", sa.String(30), default="DRAFT"),
        sa.Column("workflow_instance_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_reimbursement_claim_org_number", "ess_reimbursement_claim", ["organization_id", "claim_number"])

    # Reimbursement Line Item
    op.create_table(
        "ess_reimbursement_line_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_reimbursement_claim.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2)),
        sa.Column("bill_number", sa.String(100)),
        sa.Column("bill_date", sa.Date),
        sa.Column("vendor_name", sa.String(200)),
        sa.Column("vendor_gstin", sa.String(15)),
        sa.Column("gst_amount", sa.Numeric(10, 2)),
        sa.Column("gst_rate", sa.Numeric(5, 2)),
        sa.Column("attachment_url", sa.String(500)),
        sa.Column("attachment_name", sa.String(200)),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_remarks", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Reimbursement Approval
    op.create_table(
        "ess_reimbursement_approval",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_reimbursement_claim.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("approval_level", sa.Integer, nullable=False),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("action_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remarks", sa.Text),
        sa.Column("approved_amount", sa.Numeric(12, 2)),
        sa.Column("forwarded_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ==========================================================================
    # HELPDESK TICKETS
    # ==========================================================================

    # Helpdesk Category Master
    op.create_table(
        "mst_helpdesk_category",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category_type", sa.String(30), nullable=False),
        sa.Column("department", sa.String(20), nullable=False),
        sa.Column("response_sla_hours", sa.Integer, default=4),
        sa.Column("resolution_sla_hours", sa.Integer, default=48),
        sa.Column("sla_by_priority", postgresql.JSONB),
        sa.Column("auto_assign", sa.Boolean, default=False),
        sa.Column("default_assignee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("assignment_queue", postgresql.JSONB),
        sa.Column("enable_escalation", sa.Boolean, default=True),
        sa.Column("escalation_after_hours", sa.Integer, default=24),
        sa.Column("escalate_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("notification_template", sa.String(100)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_helpdesk_category_org_code", "mst_helpdesk_category", ["organization_id", "code"])

    # Helpdesk Ticket
    op.create_table(
        "ess_helpdesk_ticket",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ticket_number", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_helpdesk_category.id", ondelete="SET NULL")),
        sa.Column("category_type", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), default="NORMAL"),
        sa.Column("attachments", postgresql.JSONB),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("assigned_date", sa.DateTime(timezone=True)),
        sa.Column("assigned_department", sa.String(50)),
        sa.Column("sla_response_hours", sa.Integer, default=4),
        sa.Column("sla_resolution_hours", sa.Integer, default=48),
        sa.Column("response_due_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True)),
        sa.Column("first_response_at", sa.DateTime(timezone=True)),
        sa.Column("response_sla_breached", sa.Boolean, default=False),
        sa.Column("resolution_sla_breached", sa.Boolean, default=False),
        sa.Column("resolution", sa.Text),
        sa.Column("resolution_date", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("closed_date", sa.DateTime(timezone=True)),
        sa.Column("closure_remarks", sa.Text),
        sa.Column("rating", sa.Integer),
        sa.Column("feedback", sa.Text),
        sa.Column("feedback_date", sa.DateTime(timezone=True)),
        sa.Column("is_escalated", sa.Boolean, default=False),
        sa.Column("escalated_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("escalated_at", sa.DateTime(timezone=True)),
        sa.Column("escalation_reason", sa.String(500)),
        sa.Column("reopen_count", sa.Integer, default=0),
        sa.Column("status", sa.String(20), default="OPEN"),
        sa.Column("parent_ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_helpdesk_ticket.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_helpdesk_ticket_org_number", "ess_helpdesk_ticket", ["organization_id", "ticket_number"])

    # Ticket Comment
    op.create_table(
        "ess_ticket_comment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_helpdesk_ticket.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_type", sa.String(20), nullable=False),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="SET NULL")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("comment", sa.Text, nullable=False),
        sa.Column("is_internal", sa.Boolean, default=False),
        sa.Column("attachments", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Ticket History
    op.create_table(
        "ess_ticket_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_helpdesk_ticket.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("field_changed", sa.String(50)),
        sa.Column("old_value", sa.String(500)),
        sa.Column("new_value", sa.String(500)),
        sa.Column("remarks", sa.Text),
        sa.Column("changed_by_type", sa.String(20), nullable=False),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="SET NULL")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ==========================================================================
    # IT DECLARATION
    # ==========================================================================

    # IT Declaration Section Master
    op.create_table(
        "mst_it_declaration_section",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("section_code", sa.String(20), nullable=False),
        sa.Column("section_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("max_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_combined_limit", sa.Boolean, default=False),
        sa.Column("combined_with_sections", postgresql.JSONB),
        sa.Column("applicable_from_fy", sa.String(10), nullable=False),
        sa.Column("applicable_to_fy", sa.String(10)),
        sa.Column("requires_proof", sa.Boolean, default=True),
        sa.Column("proof_types", postgresql.JSONB),
        sa.Column("proof_mandatory_for_amount", sa.Numeric(12, 2)),
        sa.Column("display_order", sa.Integer, default=0),
        sa.Column("help_text", sa.Text),
        sa.Column("applicable_in_old_regime", sa.Boolean, default=True),
        sa.Column("applicable_in_new_regime", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_it_declaration_section_org_code", "mst_it_declaration_section", ["organization_id", "section_code"])

    # IT Declaration
    op.create_table(
        "ess_it_declaration",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ess_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("financial_year", sa.String(10), nullable=False),
        sa.Column("tax_regime", sa.String(10), nullable=False),
        sa.Column("declaration_start_date", sa.Date),
        sa.Column("declaration_end_date", sa.Date),
        sa.Column("proof_submission_deadline", sa.Date),
        sa.Column("total_declared_amount", sa.Numeric(14, 2), default=0),
        sa.Column("total_verified_amount", sa.Numeric(14, 2), default=0),
        sa.Column("total_approved_amount", sa.Numeric(14, 2), default=0),
        sa.Column("hra_declared", sa.Numeric(12, 2)),
        sa.Column("rent_paid_monthly", sa.Numeric(10, 2)),
        sa.Column("landlord_name", sa.String(200)),
        sa.Column("landlord_pan", sa.String(10)),
        sa.Column("landlord_address", sa.Text),
        sa.Column("metro_city", sa.Boolean, default=False),
        sa.Column("home_loan_interest", sa.Numeric(12, 2)),
        sa.Column("home_loan_principal", sa.Numeric(12, 2)),
        sa.Column("loan_sanctioned_date", sa.Date),
        sa.Column("lender_name", sa.String(200)),
        sa.Column("lender_pan", sa.String(10)),
        sa.Column("property_type", sa.String(20)),
        sa.Column("estimated_taxable_income", sa.Numeric(14, 2)),
        sa.Column("estimated_tax_liability", sa.Numeric(12, 2)),
        sa.Column("monthly_tds", sa.Numeric(10, 2)),
        sa.Column("submitted_date", sa.DateTime(timezone=True)),
        sa.Column("proof_submitted_date", sa.DateTime(timezone=True)),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("verified_date", sa.DateTime(timezone=True)),
        sa.Column("verification_remarks", sa.Text),
        sa.Column("status", sa.String(20), default="DRAFT"),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("is_latest", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_it_declaration_org_emp_fy", "ess_it_declaration", ["organization_id", "employee_id", "financial_year"])

    # IT Declaration Item
    op.create_table(
        "ess_it_declaration_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("declaration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_it_declaration.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_it_declaration_section.id", ondelete="SET NULL")),
        sa.Column("section_code", sa.String(20), nullable=False),
        sa.Column("particular", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("declared_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("verified_amount", sa.Numeric(12, 2)),
        sa.Column("approved_amount", sa.Numeric(12, 2)),
        sa.Column("investment_date", sa.Date),
        sa.Column("policy_number", sa.String(100)),
        sa.Column("institution_name", sa.String(200)),
        sa.Column("proof_submitted", sa.Boolean, default=False),
        sa.Column("proof_url", sa.String(500)),
        sa.Column("proof_type", sa.String(50)),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_remarks", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # HRA Receipt
    op.create_table(
        "ess_hra_receipt",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("declaration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ess_it_declaration.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("receipt_number", sa.String(50)),
        sa.Column("rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("receipt_url", sa.String(500)),
        sa.Column("receipt_uploaded", sa.Boolean, default=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ==========================================================================
    # ATTENDANCE REGULARIZATION
    # ==========================================================================

    op.create_table(
        "ess_attendance_regularization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_organization.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hris_employee.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("request_number", sa.String(30), nullable=False),
        sa.Column("attendance_date", sa.Date, nullable=False, index=True),
        sa.Column("regularization_type", sa.String(30), nullable=False),
        sa.Column("requested_in_time", sa.String(10)),
        sa.Column("requested_out_time", sa.String(10)),
        sa.Column("actual_in_time", sa.String(10)),
        sa.Column("actual_out_time", sa.String(10)),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("supporting_document", sa.String(500)),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("mst_user.id", ondelete="SET NULL")),
        sa.Column("approved_date", sa.DateTime(timezone=True)),
        sa.Column("approver_remarks", sa.Text),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint("uq_attendance_reg_org_number", "ess_attendance_regularization", ["organization_id", "request_number"])


def downgrade() -> None:
    """Drop ESS Portal tables."""
    # Drop tables in reverse order
    op.drop_table("ess_attendance_regularization")
    op.drop_table("ess_hra_receipt")
    op.drop_table("ess_it_declaration_item")
    op.drop_table("ess_it_declaration")
    op.drop_table("mst_it_declaration_section")
    op.drop_table("ess_ticket_history")
    op.drop_table("ess_ticket_comment")
    op.drop_table("ess_helpdesk_ticket")
    op.drop_table("mst_helpdesk_category")
    op.drop_table("ess_reimbursement_approval")
    op.drop_table("ess_reimbursement_line_item")
    op.drop_table("ess_reimbursement_claim")
    op.drop_table("mst_reimbursement_category")
    op.drop_table("ess_profile_update_request")
    op.drop_table("ess_otp")
    op.drop_constraint("fk_ess_session_device", "ess_session", type_="foreignkey")
    op.drop_table("ess_device")
    op.drop_table("ess_session")
    op.drop_table("ess_user")
