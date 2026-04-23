"""Add separation and FnF settlement tables.

Revision ID: z20_add_separation_fnf_tables
Revises: z19_add_fa_phase3_phase4_tables
Create Date: 2026-01-15

Tables created:
- hris_separation: Employee separation tracking (resignation, termination, etc.)
- hris_clearance_checklist: Master list of clearance items
- hris_separation_clearance: Clearance status per separation
- hris_fnf_settlement: Full & Final settlement calculation and payment
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "z20_add_separation_fnf_tables"
down_revision: str = "z19_fa_phase3_phase4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create hris_clearance_checklist table
    op.create_table(
        "hris_clearance_checklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checklist_code", sa.String(20), nullable=False),
        sa.Column("checklist_item", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsible_role", sa.String(100), nullable=True),
        sa.Column("display_order", sa.Integer(), default=0, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), default=True, nullable=False),
        sa.Column("can_have_recovery", sa.Boolean(), default=False, nullable=False),
        sa.Column("default_recovery_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["mst_department.id"]),
        sa.UniqueConstraint("organization_id", "checklist_code", name="uq_clearance_checklist_code"),
    )

    # Create hris_separation table
    op.create_table(
        "hris_separation",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Separation Details
        sa.Column("separation_type", sa.String(30), nullable=False),  # RESIGNATION, TERMINATION, etc.
        sa.Column("status", sa.String(30), default="INITIATED", nullable=False),
        # Dates
        sa.Column("initiation_date", sa.Date(), nullable=False),
        sa.Column("requested_last_working_date", sa.Date(), nullable=True),
        sa.Column("approved_last_working_date", sa.Date(), nullable=True),
        sa.Column("actual_last_working_date", sa.Date(), nullable=True),
        # Notice Period
        sa.Column("notice_period_days", sa.Integer(), default=30, nullable=False),
        sa.Column("notice_period_served", sa.Integer(), default=0, nullable=False),
        sa.Column("notice_period_shortfall", sa.Integer(), default=0, nullable=False),
        sa.Column("is_notice_buyout", sa.Boolean(), default=False, nullable=False),
        sa.Column("shortfall_recovery_amount", sa.Numeric(15, 2), nullable=True),
        # Reason
        sa.Column("reason_category", sa.String(50), nullable=True),
        sa.Column("reason_detail", sa.Text(), nullable=True),
        # Exit Interview
        sa.Column("exit_interview_done", sa.Boolean(), default=False, nullable=False),
        sa.Column("exit_interview_date", sa.Date(), nullable=True),
        sa.Column("exit_interview_notes", sa.Text(), nullable=True),
        sa.Column("exit_interview_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Approval
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        # Documentation
        sa.Column("resignation_letter_path", sa.String(500), nullable=True),
        sa.Column("relieving_letter_issued", sa.Boolean(), default=False, nullable=False),
        sa.Column("relieving_letter_path", sa.String(500), nullable=True),
        sa.Column("relieving_letter_date", sa.Date(), nullable=True),
        sa.Column("experience_letter_issued", sa.Boolean(), default=False, nullable=False),
        sa.Column("experience_letter_path", sa.String(500), nullable=True),
        # Workflow
        sa.Column("workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Metadata
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["hris_employee.id"]),
        sa.ForeignKeyConstraint(["exit_interview_by"], ["mst_user.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["mst_user.id"]),
    )
    op.create_index("ix_hris_separation_org_status", "hris_separation", ["organization_id", "status"])
    op.create_index("ix_hris_separation_employee", "hris_separation", ["employee_id"])

    # Create hris_separation_clearance table
    op.create_table(
        "hris_separation_clearance",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("separation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checklist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), default="PENDING", nullable=False),
        # Recovery details
        sa.Column("has_recovery", sa.Boolean(), default=False, nullable=False),
        sa.Column("recovery_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("recovery_description", sa.Text(), nullable=True),
        # Clearance details
        sa.Column("cleared_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["separation_id"], ["hris_separation.id"]),
        sa.ForeignKeyConstraint(["checklist_id"], ["hris_clearance_checklist.id"]),
        sa.ForeignKeyConstraint(["cleared_by"], ["mst_user.id"]),
        sa.UniqueConstraint("separation_id", "checklist_id", name="uq_separation_clearance_item"),
    )

    # Create hris_fnf_settlement table
    op.create_table(
        "hris_fnf_settlement",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("separation_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("last_working_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), default="DRAFT", nullable=False),
        # Earnings
        sa.Column("pending_salary", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("leave_encashment", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("leave_encashment_days", sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column("gratuity_amount", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("gratuity_years", sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column("bonus_amount", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("pending_reimbursements", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("other_earnings", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("other_earnings_detail", postgresql.JSONB(), nullable=True),
        sa.Column("total_earnings", sa.Numeric(15, 2), default=0, nullable=False),
        # Deductions
        sa.Column("notice_recovery", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("notice_shortfall_days", sa.Integer(), default=0, nullable=False),
        sa.Column("advance_recovery", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("loan_recovery", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("asset_recovery", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("clearance_recovery", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("other_deductions", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("other_deductions_detail", postgresql.JSONB(), nullable=True),
        sa.Column("tds_amount", sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column("total_deductions", sa.Numeric(15, 2), default=0, nullable=False),
        # Net Payable
        sa.Column("net_payable", sa.Numeric(15, 2), default=0, nullable=False),
        # Calculation Details
        sa.Column("calculation_details", postgresql.JSONB(), nullable=True),
        # Gratuity Details
        sa.Column("gratuity_basic_salary", sa.Numeric(15, 2), nullable=True),
        sa.Column("gratuity_eligible", sa.Boolean(), default=False, nullable=False),
        sa.Column("gratuity_calculation_method", sa.String(50), nullable=True),
        # Approval
        sa.Column("calculated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("calculated_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        # Payment
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("payment_mode", sa.String(20), nullable=True),
        sa.Column("payment_reference", sa.String(50), nullable=True),
        sa.Column("bank_account_number", sa.String(30), nullable=True),
        sa.Column("bank_ifsc", sa.String(11), nullable=True),
        # GL Posting
        sa.Column("voucher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gl_posted", sa.Boolean(), default=False, nullable=False),
        # Metadata
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["separation_id"], ["hris_separation.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["hris_employee.id"]),
        sa.ForeignKeyConstraint(["calculated_by"], ["mst_user.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["mst_user.id"]),
        sa.ForeignKeyConstraint(["voucher_id"], ["txn_voucher.id"]),
    )
    op.create_index("ix_hris_fnf_settlement_employee", "hris_fnf_settlement", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_hris_fnf_settlement_employee", table_name="hris_fnf_settlement")
    op.drop_table("hris_fnf_settlement")
    op.drop_table("hris_separation_clearance")
    op.drop_index("ix_hris_separation_employee", table_name="hris_separation")
    op.drop_index("ix_hris_separation_org_status", table_name="hris_separation")
    op.drop_table("hris_separation")
    op.drop_table("hris_clearance_checklist")
