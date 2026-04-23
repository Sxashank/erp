"""Create Phase 3 NPA & Collections tables

Revision ID: u9v0w1x2y3z4
Revises: t8u9v0w1x2y3
Create Date: 2025-01-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "u9v0w1x2y3z4"
down_revision = "t8u9v0w1x2y3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums for Phase 3
    collection_stage_enum = postgresql.ENUM(
        "NORMAL", "SOFT_COLLECTION", "HARD_COLLECTION", "RECOVERY", "LEGAL", "WRITE_OFF",
        name="collectionstage",
        create_type=False)
    collection_stage_enum.create(op.get_bind(), checkfirst=True)

    follow_up_type_enum = postgresql.ENUM(
        "SMS", "EMAIL", "PHONE_CALL", "FIELD_VISIT", "DEMAND_NOTICE", "LEGAL_NOTICE", "RECALL_NOTICE",
        name="followuptype",
        create_type=False)
    follow_up_type_enum.create(op.get_bind(), checkfirst=True)

    follow_up_status_enum = postgresql.ENUM(
        "SCHEDULED", "COMPLETED", "CANCELLED", "RESCHEDULED", "NO_RESPONSE", "PTP_RECEIVED",
        name="followupstatus",
        create_type=False)
    follow_up_status_enum.create(op.get_bind(), checkfirst=True)

    follow_up_outcome_enum = postgresql.ENUM(
        "CONTACTED", "NOT_CONTACTABLE", "PROMISE_TO_PAY", "PARTIAL_PAYMENT",
        "DISPUTE", "REFUSED", "BROKEN_PTP", "SETTLEMENT_REQUESTED",
        name="followupoutcome",
        create_type=False)
    follow_up_outcome_enum.create(op.get_bind(), checkfirst=True)

    demand_notice_type_enum = postgresql.ENUM(
        "REMINDER", "DEMAND", "FINAL_DEMAND", "RECALL", "SARFAESI_13_2", "SARFAESI_13_4",
        name="demandnoticetype",
        create_type=False)
    demand_notice_type_enum.create(op.get_bind(), checkfirst=True)

    npa_status_enum = postgresql.ENUM(
        "SMA", "NPA", "UPGRADED", "RECOVERED", "WRITTEN_OFF", "SETTLED",
        name="npastatus",
        create_type=False)
    npa_status_enum.create(op.get_bind(), checkfirst=True)

    ots_status_enum = postgresql.ENUM(
        "DRAFT", "PROPOSED", "NEGOTIATION", "PENDING_APPROVAL", "APPROVED", "REJECTED",
        "ACCEPTED", "PAYMENT_PENDING", "PARTIALLY_PAID", "COMPLETED", "CANCELLED", "EXPIRED",
        name="otsstatus",
        create_type=False)
    ots_status_enum.create(op.get_bind(), checkfirst=True)

    ots_payment_mode_enum = postgresql.ENUM(
        "LUMP_SUM", "INSTALLMENTS", "HYBRID",
        name="otspaymentmode",
        create_type=False)
    ots_payment_mode_enum.create(op.get_bind(), checkfirst=True)

    restructure_type_enum = postgresql.ENUM(
        "TENURE_EXTENSION", "EMI_REDUCTION", "MORATORIUM", "RATE_REDUCTION",
        "PRINCIPAL_HAIRCUT", "INTEREST_WAIVER", "COMPREHENSIVE", "COVID_RESTRUCTURE",
        name="restructuretype",
        create_type=False)
    restructure_type_enum.create(op.get_bind(), checkfirst=True)

    restructure_status_enum = postgresql.ENUM(
        "DRAFT", "PROPOSED", "PENDING_APPROVAL", "APPROVED", "REJECTED", "IMPLEMENTED", "CANCELLED",
        name="restructurestatus",
        create_type=False)
    restructure_status_enum.create(op.get_bind(), checkfirst=True)

    legal_forum_type_enum = postgresql.ENUM(
        "DRT", "NCLT", "CIVIL_COURT", "HIGH_COURT", "ARBITRATION", "LOK_ADALAT",
        name="legalforumtype",
        create_type=False)
    legal_forum_type_enum.create(op.get_bind(), checkfirst=True)

    legal_case_type_enum = postgresql.ENUM(
        "SARFAESI", "DRT_APPLICATION", "RECOVERY_SUIT", "WINDING_UP", "IBC", "ARBITRATION", "EXECUTION", "APPEAL",
        name="legalcasetype",
        create_type=False)
    legal_case_type_enum.create(op.get_bind(), checkfirst=True)

    legal_case_status_enum = postgresql.ENUM(
        "DRAFT", "NOTICE_ISSUED", "FILED", "PENDING", "INTERIM_ORDER", "DECREE_OBTAINED",
        "EXECUTION", "SETTLED", "DISMISSED", "WITHDRAWN", "APPEALED", "CLOSED",
        name="legalcasestatus",
        create_type=False)
    legal_case_status_enum.create(op.get_bind(), checkfirst=True)

    sarfaesi_stage_enum = postgresql.ENUM(
        "DEMAND_13_2", "OBJECTION_PERIOD", "POSSESSION_13_4", "PHYSICAL_POSSESSION",
        "SYMBOLIC_POSSESSION", "SALE_NOTICE", "AUCTION", "SALE_COMPLETED",
        name="sarfaesistage",
        create_type=False)
    sarfaesi_stage_enum.create(op.get_bind(), checkfirst=True)

    auction_status_enum = postgresql.ENUM(
        "SCHEDULED", "PUBLISHED", "BID_RECEIVED", "COMPLETED", "CANCELLED", "RESCHEDULED", "NO_BIDDERS",
        name="auctionstatus",
        create_type=False)
    auction_status_enum.create(op.get_bind(), checkfirst=True)

    write_off_type_enum = postgresql.ENUM(
        "TECHNICAL", "PRUDENTIAL", "PARTIAL",
        name="writeofftype",
        create_type=False)
    write_off_type_enum.create(op.get_bind(), checkfirst=True)

    write_off_status_enum = postgresql.ENUM(
        "PROPOSED", "PENDING_APPROVAL", "APPROVED", "REJECTED", "EFFECTED", "WRITTEN_BACK",
        name="writeoffstatus",
        create_type=False)
    write_off_status_enum.create(op.get_bind(), checkfirst=True)

    # Create Collection Follow-Up table
    op.create_table(
        "col_collection_follow_up",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("follow_up_type", sa.String(50), nullable=False),
        sa.Column("collection_stage", sa.String(50), nullable=False),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("scheduled_time", sa.String(20)),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_to_name", sa.String(200)),
        sa.Column("status", sa.String(50), nullable=False, default="SCHEDULED"),
        sa.Column("executed_date", sa.DateTime),
        sa.Column("outcome", sa.String(50)),
        sa.Column("ptp_date", sa.Date),
        sa.Column("ptp_amount", sa.Numeric(18, 2)),
        sa.Column("ptp_broken", sa.Boolean, default=False),
        sa.Column("contact_person", sa.String(200)),
        sa.Column("contact_number", sa.String(50)),
        sa.Column("remarks", sa.Text),
        sa.Column("follow_up_notes", sa.Text),
        sa.Column("next_follow_up_date", sa.Date),
        sa.Column("next_action", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_follow_up_loan_account", "col_collection_follow_up", ["loan_account_id"])
    op.create_index("ix_col_follow_up_scheduled_date", "col_collection_follow_up", ["scheduled_date"])
    op.create_index("ix_col_follow_up_status", "col_collection_follow_up", ["status"])

    # Create Demand Notice table
    op.create_table(
        "col_demand_notice",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("notice_number", sa.String(50), unique=True, nullable=False),
        sa.Column("notice_type", sa.String(50), nullable=False),
        sa.Column("notice_date", sa.Date, nullable=False),
        sa.Column("principal_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("penal_outstanding", sa.Numeric(18, 2), default=0),
        sa.Column("other_charges", sa.Numeric(18, 2), default=0),
        sa.Column("total_due", sa.Numeric(18, 2), nullable=False),
        sa.Column("response_due_date", sa.Date),
        sa.Column("delivery_mode", sa.String(50)),
        sa.Column("delivery_address", sa.Text),
        sa.Column("dispatch_date", sa.Date),
        sa.Column("delivery_date", sa.Date),
        sa.Column("tracking_number", sa.String(100)),
        sa.Column("delivery_status", sa.String(50)),
        sa.Column("document_path", sa.String(500)),
        sa.Column("response_received", sa.Boolean, default=False),
        sa.Column("response_date", sa.Date),
        sa.Column("response_summary", sa.Text),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_demand_notice_loan_account", "col_demand_notice", ["loan_account_id"])
    op.create_index("ix_col_demand_notice_type", "col_demand_notice", ["notice_type"])
    op.create_index("ix_col_demand_notice_date", "col_demand_notice", ["notice_date"])

    # Create NPA Record table
    op.create_table(
        "col_npa_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("npa_status", sa.String(50), nullable=False),
        sa.Column("classification_at_npa", sa.String(50), nullable=False),
        sa.Column("current_classification", sa.String(50), nullable=False),
        sa.Column("npa_date", sa.Date, nullable=False),
        sa.Column("first_overdue_date", sa.Date),
        sa.Column("upgrade_date", sa.Date),
        sa.Column("closure_date", sa.Date),
        sa.Column("principal_at_npa", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_at_npa", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_at_npa", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_interest", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_penal", sa.Numeric(18, 2), default=0),
        sa.Column("current_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("provision_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("provision_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("realizable_security_value", sa.Numeric(18, 2)),
        sa.Column("erosion_in_security", sa.Numeric(18, 2)),
        sa.Column("total_recovery", sa.Numeric(18, 2), default=0),
        sa.Column("recovery_principal", sa.Numeric(18, 2), default=0),
        sa.Column("recovery_interest", sa.Numeric(18, 2), default=0),
        sa.Column("resolution_strategy", sa.String(100)),
        sa.Column("expected_resolution_date", sa.Date),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_npa_record_loan_account", "col_npa_record", ["loan_account_id"])
    op.create_index("ix_col_npa_record_status", "col_npa_record", ["npa_status"])
    op.create_index("ix_col_npa_record_npa_date", "col_npa_record", ["npa_date"])

    # Create Penal Interest table
    op.create_table(
        "col_penal_interest",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("overdue_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("overdue_interest", sa.Numeric(18, 2), nullable=False),
        sa.Column("overdue_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("penal_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("days_overdue", sa.Integer, nullable=False),
        sa.Column("calculated_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("applied_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("waived_amount", sa.Numeric(18, 2), default=0),
        sa.Column("is_accrued", sa.Boolean, default=True),
        sa.Column("is_suspended", sa.Boolean, default=False),
        sa.Column("gl_entry_reference", sa.String(100)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_penal_interest_loan_account", "col_penal_interest", ["loan_account_id"])
    op.create_index("ix_col_penal_interest_period", "col_penal_interest", ["period_start", "period_end"])

    # Create Penal Waiver table
    op.create_table(
        "col_penal_waiver",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("waiver_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("waiver_date", sa.Date, nullable=False),
        sa.Column("total_penal_accrued", sa.Numeric(18, 2), nullable=False),
        sa.Column("waiver_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("balance_after_waiver", sa.Numeric(18, 2), nullable=False),
        sa.Column("waiver_reason", sa.Text, nullable=False),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.Date),
        sa.Column("approval_reference", sa.String(100)),
        sa.Column("is_approved", sa.Boolean, default=False),
        sa.Column("is_effected", sa.Boolean, default=False),
        sa.Column("gl_entry_reference", sa.String(100)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_penal_waiver_loan_account", "col_penal_waiver", ["loan_account_id"])

    # Create OTS Proposal table
    op.create_table(
        "col_ots_proposal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("ots_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("proposal_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="DRAFT"),
        sa.Column("principal_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("penal_outstanding", sa.Numeric(18, 2), default=0),
        sa.Column("other_charges", sa.Numeric(18, 2), default=0),
        sa.Column("total_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("ots_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("haircut_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("haircut_percent", sa.Numeric(8, 4), nullable=False),
        sa.Column("principal_waiver", sa.Numeric(18, 2), default=0),
        sa.Column("interest_waiver", sa.Numeric(18, 2), default=0),
        sa.Column("penal_waiver", sa.Numeric(18, 2), default=0),
        sa.Column("charges_waiver", sa.Numeric(18, 2), default=0),
        sa.Column("payment_mode", sa.String(50), nullable=False),
        sa.Column("upfront_amount", sa.Numeric(18, 2), default=0),
        sa.Column("upfront_due_date", sa.Date),
        sa.Column("number_of_installments", sa.Integer, default=1),
        sa.Column("valid_till", sa.Date, nullable=False),
        sa.Column("security_release_terms", sa.Text),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.Date),
        sa.Column("approval_authority", sa.String(100)),
        sa.Column("borrower_acceptance_date", sa.Date),
        sa.Column("borrower_acceptance_document", sa.String(500)),
        sa.Column("total_received", sa.Numeric(18, 2), default=0),
        sa.Column("balance_pending", sa.Numeric(18, 2), nullable=False),
        sa.Column("completion_date", sa.Date),
        sa.Column("remarks", sa.Text),
        sa.Column("terms_and_conditions", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_ots_proposal_loan_account", "col_ots_proposal", ["loan_account_id"])
    op.create_index("ix_col_ots_proposal_status", "col_ots_proposal", ["status"])

    # Create OTS Payment Schedule table
    op.create_table(
        "col_ots_payment_schedule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ots_proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("col_ots_proposal.id"), nullable=False),
        sa.Column("installment_number", sa.Integer, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("due_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(18, 2), default=0),
        sa.Column("paid_date", sa.Date),
        sa.Column("receipt_reference", sa.String(100)),
        sa.Column("is_paid", sa.Boolean, default=False),
        sa.Column("is_overdue", sa.Boolean, default=False),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_ots_payment_schedule_ots", "col_ots_payment_schedule", ["ots_proposal_id"])
    op.create_index("ix_col_ots_payment_schedule_due_date", "col_ots_payment_schedule", ["due_date"])

    # Create Loan Restructure table
    op.create_table(
        "col_loan_restructure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("restructure_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("restructure_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="DRAFT"),
        sa.Column("proposal_date", sa.Date, nullable=False),
        sa.Column("pre_outstanding_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("pre_outstanding_interest", sa.Numeric(18, 2), nullable=False),
        sa.Column("pre_interest_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("pre_tenure_months", sa.Integer, nullable=False),
        sa.Column("pre_emi_amount", sa.Numeric(18, 2)),
        sa.Column("pre_maturity_date", sa.Date, nullable=False),
        sa.Column("post_outstanding_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("post_interest_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("post_tenure_months", sa.Integer, nullable=False),
        sa.Column("post_emi_amount", sa.Numeric(18, 2)),
        sa.Column("post_maturity_date", sa.Date, nullable=False),
        sa.Column("moratorium_months", sa.Integer, default=0),
        sa.Column("moratorium_start_date", sa.Date),
        sa.Column("moratorium_end_date", sa.Date),
        sa.Column("moratorium_interest_treatment", sa.String(50)),
        sa.Column("interest_waived", sa.Numeric(18, 2), default=0),
        sa.Column("penal_waived", sa.Numeric(18, 2), default=0),
        sa.Column("principal_converted_to_fitl", sa.Numeric(18, 2), default=0),
        sa.Column("is_standard_restructure", sa.Boolean, default=True),
        sa.Column("downgrade_required", sa.Boolean, default=False),
        sa.Column("pre_conditions", sa.Text),
        sa.Column("post_conditions", sa.Text),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.Date),
        sa.Column("approval_authority", sa.String(100)),
        sa.Column("implementation_date", sa.Date),
        sa.Column("new_schedule_generated", sa.Boolean, default=False),
        sa.Column("justification", sa.Text, nullable=False),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_restructure_loan_account", "col_loan_restructure", ["loan_account_id"])
    op.create_index("ix_col_restructure_status", "col_loan_restructure", ["status"])

    # Create Legal Case table
    op.create_table(
        "col_legal_case",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("case_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("case_type", sa.String(50), nullable=False),
        sa.Column("forum_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="DRAFT"),
        sa.Column("court_name", sa.String(200), nullable=False),
        sa.Column("court_location", sa.String(200), nullable=False),
        sa.Column("case_number", sa.String(100)),
        sa.Column("filing_date", sa.Date),
        sa.Column("claim_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("claim_interest", sa.Numeric(18, 2), nullable=False),
        sa.Column("claim_costs", sa.Numeric(18, 2), default=0),
        sa.Column("total_claim", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_rate_claimed", sa.Numeric(8, 4)),
        sa.Column("sarfaesi_stage", sa.String(50)),
        sa.Column("demand_notice_date", sa.Date),
        sa.Column("possession_date", sa.Date),
        sa.Column("possession_type", sa.String(50)),
        sa.Column("decree_date", sa.Date),
        sa.Column("decree_amount", sa.Numeric(18, 2)),
        sa.Column("decree_interest_rate", sa.Numeric(8, 4)),
        sa.Column("advocate_name", sa.String(200)),
        sa.Column("advocate_contact", sa.String(100)),
        sa.Column("law_firm", sa.String(200)),
        sa.Column("next_hearing_date", sa.Date),
        sa.Column("legal_costs_incurred", sa.Numeric(18, 2), default=0),
        sa.Column("court_fees_paid", sa.Numeric(18, 2), default=0),
        sa.Column("recovery_through_case", sa.Numeric(18, 2), default=0),
        sa.Column("closure_date", sa.Date),
        sa.Column("closure_reason", sa.String(200)),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_legal_case_loan_account", "col_legal_case", ["loan_account_id"])
    op.create_index("ix_col_legal_case_status", "col_legal_case", ["status"])
    op.create_index("ix_col_legal_case_forum", "col_legal_case", ["forum_type"])

    # Create Legal Hearing table
    op.create_table(
        "col_legal_hearing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("legal_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("col_legal_case.id"), nullable=False),
        sa.Column("hearing_number", sa.Integer, nullable=False),
        sa.Column("hearing_date", sa.Date, nullable=False),
        sa.Column("hearing_type", sa.String(100), nullable=False),
        sa.Column("bench", sa.String(200)),
        sa.Column("presiding_officer", sa.String(200)),
        sa.Column("proceedings_summary", sa.Text, nullable=False),
        sa.Column("order_passed", sa.Text),
        sa.Column("our_advocate_present", sa.Boolean, default=True),
        sa.Column("opposite_party_present", sa.Boolean, default=False),
        sa.Column("documents_filed", sa.Text),
        sa.Column("documents_received", sa.Text),
        sa.Column("next_hearing_date", sa.Date),
        sa.Column("next_hearing_purpose", sa.String(200)),
        sa.Column("action_required", sa.Text),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_legal_hearing_case", "col_legal_hearing", ["legal_case_id"])
    op.create_index("ix_col_legal_hearing_date", "col_legal_hearing", ["hearing_date"])

    # Create Property Auction table
    op.create_table(
        "col_property_auction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("legal_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("col_legal_case.id"), nullable=False),
        sa.Column("loan_security_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("los_loan_security.id")),
        sa.Column("auction_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("auction_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="SCHEDULED"),
        sa.Column("property_description", sa.Text, nullable=False),
        sa.Column("property_address", sa.Text, nullable=False),
        sa.Column("property_area", sa.String(100)),
        sa.Column("valuation_date", sa.Date),
        sa.Column("market_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("forced_sale_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("reserve_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("emd_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("emd_percent", sa.Numeric(8, 4), nullable=False),
        sa.Column("publication_date", sa.Date),
        sa.Column("publication_details", sa.Text),
        sa.Column("newspapers", sa.Text),
        sa.Column("auction_date", sa.Date, nullable=False),
        sa.Column("auction_time", sa.String(20), nullable=False),
        sa.Column("auction_venue", sa.String(500), nullable=False),
        sa.Column("is_e_auction", sa.Boolean, default=False),
        sa.Column("e_auction_portal", sa.String(200)),
        sa.Column("number_of_bidders", sa.Integer, default=0),
        sa.Column("highest_bid", sa.Numeric(18, 2)),
        sa.Column("successful_bidder_name", sa.String(200)),
        sa.Column("successful_bidder_address", sa.Text),
        sa.Column("sale_confirmed", sa.Boolean, default=False),
        sa.Column("sale_confirmation_date", sa.Date),
        sa.Column("sale_certificate_date", sa.Date),
        sa.Column("sale_amount", sa.Numeric(18, 2)),
        sa.Column("total_received", sa.Numeric(18, 2), default=0),
        sa.Column("balance_due", sa.Numeric(18, 2)),
        sa.Column("payment_due_date", sa.Date),
        sa.Column("cancellation_reason", sa.Text),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_auction_legal_case", "col_property_auction", ["legal_case_id"])
    op.create_index("ix_col_auction_status", "col_property_auction", ["status"])

    # Create Write-Off Record table
    op.create_table(
        "col_write_off",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms_loan_account.id"), nullable=False),
        sa.Column("write_off_reference", sa.String(50), unique=True, nullable=False),
        sa.Column("write_off_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="PROPOSED"),
        sa.Column("proposal_date", sa.Date, nullable=False),
        sa.Column("principal_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("penal_outstanding", sa.Numeric(18, 2), default=0),
        sa.Column("other_charges", sa.Numeric(18, 2), default=0),
        sa.Column("total_outstanding", sa.Numeric(18, 2), nullable=False),
        sa.Column("principal_written_off", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_written_off", sa.Numeric(18, 2), nullable=False),
        sa.Column("penal_written_off", sa.Numeric(18, 2), default=0),
        sa.Column("total_written_off", sa.Numeric(18, 2), nullable=False),
        sa.Column("provision_available", sa.Numeric(18, 2), nullable=False),
        sa.Column("provision_utilized", sa.Numeric(18, 2), nullable=False),
        sa.Column("security_value", sa.Numeric(18, 2)),
        sa.Column("security_realized", sa.Numeric(18, 2)),
        sa.Column("shortfall", sa.Numeric(18, 2)),
        sa.Column("justification", sa.Text, nullable=False),
        sa.Column("recovery_efforts", sa.Text),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.Date),
        sa.Column("approval_authority", sa.String(100)),
        sa.Column("board_resolution_date", sa.Date),
        sa.Column("board_resolution_number", sa.String(100)),
        sa.Column("effective_date", sa.Date),
        sa.Column("gl_entry_reference", sa.String(100)),
        sa.Column("recovery_after_write_off", sa.Numeric(18, 2), default=0),
        sa.Column("write_back_date", sa.Date),
        sa.Column("write_back_amount", sa.Numeric(18, 2)),
        sa.Column("write_back_reason", sa.Text),
        sa.Column("remarks", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean, default=False))
    op.create_index("ix_col_write_off_loan_account", "col_write_off", ["loan_account_id"])
    op.create_index("ix_col_write_off_status", "col_write_off", ["status"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("col_write_off")
    op.drop_table("col_property_auction")
    op.drop_table("col_legal_hearing")
    op.drop_table("col_legal_case")
    op.drop_table("col_loan_restructure")
    op.drop_table("col_ots_payment_schedule")
    op.drop_table("col_ots_proposal")
    op.drop_table("col_penal_waiver")
    op.drop_table("col_penal_interest")
    op.drop_table("col_npa_record")
    op.drop_table("col_demand_notice")
    op.drop_table("col_collection_follow_up")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS writeoffstatus")
    op.execute("DROP TYPE IF EXISTS writeofftype")
    op.execute("DROP TYPE IF EXISTS auctionstatus")
    op.execute("DROP TYPE IF EXISTS sarfaesistage")
    op.execute("DROP TYPE IF EXISTS legalcasestatus")
    op.execute("DROP TYPE IF EXISTS legalcasetype")
    op.execute("DROP TYPE IF EXISTS legalforumtype")
    op.execute("DROP TYPE IF EXISTS restructurestatus")
    op.execute("DROP TYPE IF EXISTS restructuretype")
    op.execute("DROP TYPE IF EXISTS otspaymentmode")
    op.execute("DROP TYPE IF EXISTS otsstatus")
    op.execute("DROP TYPE IF EXISTS npastatus")
    op.execute("DROP TYPE IF EXISTS demandnoticetype")
    op.execute("DROP TYPE IF EXISTS followupoutcome")
    op.execute("DROP TYPE IF EXISTS followupstatus")
    op.execute("DROP TYPE IF EXISTS followuptype")
    op.execute("DROP TYPE IF EXISTS collectionstage")
