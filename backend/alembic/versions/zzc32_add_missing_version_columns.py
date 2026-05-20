"""Add missing optimistic-lock columns to existing ID tables.

Revision ID: zzc32_add_missing_version_columns
Revises: zzc31_create_user_session_table
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "zzc32_add_missing_version_columns"
down_revision = "zzc31_create_user_session_table"
branch_labels = None
depends_on = None


TABLES = (
    "audit_day_anchor",
    "gst_einvoice_request",
    "gst_eway_bill",
    "gst_eway_bill_item",
    "gst_eway_bill_vehicle_update",
    "idempotency_key",
    "lending_credit_enquiry",
    "lending_credit_pull",
    "lms_aa_bank_account",
    "lms_aa_bank_transaction",
    "lms_aa_consent",
    "lms_aa_consent_log",
    "lms_aa_fetch_session",
    "lms_asset_classification_history",
    "lms_disbursement",
    "lms_loan_account",
    "lms_loan_accrual",
    "lms_loan_adjustment",
    "lms_loan_mandate",
    "lms_loan_provision",
    "lms_loan_receipt",
    "lms_nach_batch",
    "lms_nach_mandate_log",
    "lms_nach_transaction",
    "lms_receipt_allocation",
    "lms_repayment_schedule",
    "lms_schedule_installment",
    "los_application_fee",
    "los_bureau_pull",
    "los_bureau_report",
    "los_ckyc_transaction",
    "los_document_checklist",
    "los_entity",
    "los_entity_address",
    "los_entity_bank_account",
    "los_entity_contact",
    "los_entity_financial",
    "los_entity_kyc_document",
    "los_entity_rating",
    "los_entity_relation",
    "los_fee_master",
    "los_financial_analysis",
    "los_interest_rate",
    "los_interest_rate_history",
    "los_kyc_document_type",
    "los_loan_application",
    "los_loan_product",
    "los_loan_security",
    "los_product_fee",
    "los_project_milestone",
    "los_rating_matrix",
    "los_rating_score_detail",
    "los_risk_category",
    "los_risk_parameter",
    "los_sanction_condition",
    "los_technical_appraisal",
    "map_role_permission",
    "map_user_role",
    "mst_advocate_specialization",
    "mst_court_bench",
    "mst_court_fee_slab",
    "mst_expense_category",
    "mst_helpdesk_category",
    "mst_it_declaration_section",
    "mst_legal_document_type",
    "mst_reimbursement_category",
    "mst_statutory_period",
    "portal_asn_line",
    "portal_payment_transaction",
    "portal_service_request_document",
    "portal_service_request_history",
    "portal_vendor_invoice_document",
    "portal_vendor_invoice_line",
    "portal_vendor_notification",
    "portal_vendor_otp",
    "portal_vendor_reg_document",
    "portal_vendor_session",
    "sys_integration_config",
    "sys_integration_log",
    "txn_advocate_fee",
    "txn_advocate_performance",
    "txn_amc_contract_asset",
    "txn_audit_log",
    "txn_background_job",
    "txn_bank_statement_match",
    "txn_document_checklist",
    "txn_document_version",
    "txn_expense_recovery",
    "txn_insurance_policy_asset",
    "txn_limitation_alert",
    "txn_notice_delivery",
    "txn_notice_response",
    "txn_payment",
    "txn_payment_file",
    "txn_payment_file_transaction",
    "txn_purchase_bill",
    "txn_purchase_bill_line",
    "txn_sales_invoice",
    "txn_sales_invoice_line",
)


def _table_exists(conn, table_name: str) -> bool:
    return (
        conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = current_schema() AND table_name = :table_name"
            ),
            {"table_name": table_name},
        ).scalar()
        is not None
    )


def upgrade() -> None:
    conn = op.get_bind()
    for table_name in TABLES:
        if not _table_exists(conn, table_name):
            continue
        op.execute(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1')
        op.execute(f'ALTER TABLE "{table_name}" ALTER COLUMN version DROP DEFAULT')


def downgrade() -> None:
    conn = op.get_bind()
    for table_name in reversed(TABLES):
        if not _table_exists(conn, table_name):
            continue
        op.execute(f'ALTER TABLE "{table_name}" DROP COLUMN IF EXISTS version')
