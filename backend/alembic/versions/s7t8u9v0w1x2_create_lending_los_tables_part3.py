"""create_lending_los_tables_part3

Revision ID: s7t8u9v0w1x2
Revises: r6s7t8u9v0w1
Create Date: 2026-01-12 20:00:00.000000

Create Loan Origination System (LOS) tables - Part 3.
Application and Sanction models.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 's7t8u9v0w1x2'
down_revision: Union[str, None] = 'r6s7t8u9v0w1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # LOAN APPLICATION TABLES
    # ============================================================================

    # los_loan_application - Loan application master
    op.create_table(
        'los_loan_application',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_number', sa.String(50), nullable=False),
        sa.Column('lead_reference', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_product.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('requested_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('requested_tenure_months', sa.Integer, nullable=False),
        sa.Column('purpose', sa.String(500), nullable=False),
        sa.Column('detailed_purpose', sa.Text, nullable=True),
        sa.Column('is_project_finance', sa.Boolean, default=False, nullable=False),
        sa.Column('project_name', sa.String(500), nullable=True),
        sa.Column('project_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('promoter_contribution', sa.Numeric(20, 2), nullable=True),
        sa.Column('promoter_contribution_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('bank_finance', sa.Numeric(20, 2), nullable=True),
        sa.Column('other_finance', sa.Numeric(20, 2), nullable=True),
        sa.Column('project_location', sa.String(500), nullable=True),
        sa.Column('project_start_date', sa.Date, nullable=True),
        sa.Column('project_completion_date', sa.Date, nullable=True),
        sa.Column('preferred_interest_type', postgresql.ENUM(name='interesttype', create_type=False), default='FLOATING', nullable=False),
        sa.Column('preferred_repayment_frequency', postgresql.ENUM(name='repaymentfrequency', create_type=False), default='MONTHLY', nullable=False),
        sa.Column('preferred_repayment_mode', postgresql.ENUM(name='repaymentmode', create_type=False), default='EMI', nullable=False),
        sa.Column('requested_moratorium_months', sa.Integer, default=0, nullable=False),
        sa.Column('stage', postgresql.ENUM(name='applicationstage', create_type=False), default='APPLICATION', nullable=False),
        sa.Column('status', postgresql.ENUM(name='applicationstatus', create_type=False), default='DRAFT', nullable=False),
        sa.Column('sub_status', sa.String(50), nullable=True),
        sa.Column('application_date', sa.Date, nullable=False),
        sa.Column('submission_date', sa.Date, nullable=True),
        sa.Column('expected_decision_date', sa.Date, nullable=True),
        sa.Column('decision_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('relationship_manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('credit_officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_instance.id', ondelete='SET NULL'), nullable=True),
        sa.Column('entity_rating_at_application', sa.String(10), nullable=True),
        sa.Column('cibil_score_at_application', sa.Integer, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('rejection_code', sa.String(50), nullable=True),
        sa.Column('withdrawal_reason', sa.Text, nullable=True),
        sa.Column('source_channel', sa.String(50), default='DIRECT', nullable=False),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('extra_data', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'application_number', name='uq_loan_app_org_number'),
    )
    op.create_index('ix_los_loan_app_org', 'los_loan_application', ['organization_id'])
    op.create_index('ix_los_loan_app_number', 'los_loan_application', ['application_number'])
    op.create_index('ix_los_loan_app_org_stage', 'los_loan_application', ['organization_id', 'stage'])
    op.create_index('ix_los_loan_app_org_status', 'los_loan_application', ['organization_id', 'status'])
    op.create_index('ix_los_loan_app_entity', 'los_loan_application', ['entity_id'])
    op.create_index('ix_los_loan_app_product', 'los_loan_application', ['product_id'])
    op.create_index('ix_los_loan_app_date', 'los_loan_application', ['application_date'])
    op.create_index('ix_los_loan_app_branch', 'los_loan_application', ['branch_id'])

    # los_application_document - Application documents
    op.create_table(
        'los_application_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='CASCADE'), nullable=False),
        sa.Column('checklist_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_document_checklist.id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_code', sa.String(50), nullable=False),
        sa.Column('document_name', sa.String(200), nullable=False),
        sa.Column('document_description', sa.Text, nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('file_mime_type', sa.String(100), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('document_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), default='PENDING', nullable=False),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('is_waived', sa.Boolean, default=False, nullable=False),
        sa.Column('waiver_reason', sa.Text, nullable=True),
        sa.Column('waiver_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verification_remarks', sa.Text, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_app_doc_app', 'los_application_document', ['application_id'])
    op.create_index('ix_los_app_doc_app_code', 'los_application_document', ['application_id', 'document_code'])
    op.create_index('ix_los_app_doc_status', 'los_application_document', ['application_id', 'status'])

    # los_application_fee - Application fees
    op.create_table(
        'los_application_fee',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fee_master_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_fee_master.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('fee_code', sa.String(50), nullable=False),
        sa.Column('fee_name', sa.String(200), nullable=False),
        sa.Column('calculated_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('approved_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('waiver_amount', sa.Numeric(18, 2), default=0, nullable=False),
        sa.Column('waiver_percentage', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('cgst_amount', sa.Numeric(18, 2), default=0, nullable=False),
        sa.Column('sgst_amount', sa.Numeric(18, 2), default=0, nullable=False),
        sa.Column('igst_amount', sa.Numeric(18, 2), default=0, nullable=False),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('status', sa.String(50), default='PENDING', nullable=False),
        sa.Column('collection_mode', sa.String(50), nullable=True),
        sa.Column('collection_date', sa.Date, nullable=True),
        sa.Column('collection_reference', sa.String(100), nullable=True),
        sa.Column('waiver_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('waiver_reason', sa.Text, nullable=True),
        sa.Column('deducted_from_disbursement', sa.Boolean, default=False, nullable=False),
        sa.Column('disbursement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=True),
        sa.Column('invoice_date', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('application_id', 'fee_master_id', name='uq_app_fee'),
    )
    op.create_index('ix_los_app_fee_app', 'los_application_fee', ['application_id'])
    op.create_index('ix_los_app_fee_status', 'los_application_fee', ['application_id', 'status'])

    # los_technical_appraisal - Technical appraisal
    op.create_table(
        'los_technical_appraisal',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='CASCADE'), nullable=False),
        sa.Column('appraisal_reference', sa.String(50), nullable=False),
        sa.Column('appraisal_type', postgresql.ENUM(name='appraisaltype', create_type=False), default='TECHNICAL', nullable=False),
        sa.Column('appraisal_date', sa.Date, nullable=False),
        sa.Column('site_visit_date', sa.Date, nullable=True),
        sa.Column('appraiser_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('external_appraiser', sa.String(200), nullable=True),
        sa.Column('external_appraiser_firm', sa.String(200), nullable=True),
        sa.Column('project_description', sa.Text, nullable=True),
        sa.Column('location_details', sa.Text, nullable=True),
        sa.Column('land_area_sqft', sa.Numeric(15, 2), nullable=True),
        sa.Column('built_up_area_sqft', sa.Numeric(15, 2), nullable=True),
        sa.Column('estimated_project_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('land_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('construction_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('machinery_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('other_costs', sa.Numeric(20, 2), nullable=True),
        sa.Column('contingency', sa.Numeric(20, 2), nullable=True),
        sa.Column('feasibility', postgresql.ENUM(name='technicalfeasibility', create_type=False), default='FEASIBLE', nullable=False),
        sa.Column('feasibility_remarks', sa.Text, nullable=True),
        sa.Column('estimated_completion_months', sa.Integer, nullable=True),
        sa.Column('construction_stage', sa.String(100), nullable=True),
        sa.Column('completion_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('statutory_approvals', postgresql.JSONB, nullable=True),
        sa.Column('environmental_clearance', sa.String(50), nullable=True),
        sa.Column('recommendation', postgresql.ENUM(name='appraisalrecommendation', create_type=False), default='PROCEED', nullable=False),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('concerns', postgresql.JSONB, nullable=True),
        sa.Column('report_summary', sa.Text, nullable=True),
        sa.Column('report_file_path', sa.String(500), nullable=True),
        sa.Column('photos', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('application_id', 'appraisal_reference', name='uq_tech_appraisal_ref'),
    )
    op.create_index('ix_los_tech_appraisal_app', 'los_technical_appraisal', ['application_id'])
    op.create_index('ix_los_tech_appraisal_app_type', 'los_technical_appraisal', ['application_id', 'appraisal_type'])

    # los_financial_analysis - Financial analysis
    op.create_table(
        'los_financial_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_reference', sa.String(50), nullable=False),
        sa.Column('analysis_date', sa.Date, nullable=False),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('financial_years_analyzed', postgresql.JSONB, nullable=False),
        sa.Column('base_year', sa.String(10), nullable=False),
        sa.Column('historical_ratios', postgresql.JSONB, nullable=False),
        sa.Column('projection_years', sa.Integer, default=5, nullable=False),
        sa.Column('projected_revenue', postgresql.JSONB, nullable=False),
        sa.Column('projected_ebitda', postgresql.JSONB, nullable=False),
        sa.Column('projected_net_profit', postgresql.JSONB, nullable=False),
        sa.Column('projected_cash_flows', postgresql.JSONB, nullable=False),
        sa.Column('current_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('debt_equity_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('interest_coverage_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('average_dscr', sa.Numeric(10, 2), nullable=True),
        sa.Column('minimum_dscr', sa.Numeric(10, 2), nullable=True),
        sa.Column('dscr_by_year', postgresql.JSONB, nullable=True),
        sa.Column('break_even_capacity_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('break_even_sales', sa.Numeric(20, 2), nullable=True),
        sa.Column('sensitivity_analysis', postgresql.JSONB, nullable=True),
        sa.Column('recommendation', postgresql.ENUM(name='appraisalrecommendation', create_type=False), default='PROCEED', nullable=False),
        sa.Column('recommended_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('recommended_tenure', sa.Integer, nullable=True),
        sa.Column('recommended_moratorium', sa.Integer, nullable=True),
        sa.Column('strengths', sa.Text, nullable=True),
        sa.Column('weaknesses', sa.Text, nullable=True),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('report_file_path', sa.String(500), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('application_id', 'analysis_reference', name='uq_fin_analysis_ref'),
    )
    op.create_index('ix_los_fin_analysis_app', 'los_financial_analysis', ['application_id'])

    # los_project_milestone - Project milestones
    op.create_table(
        'los_project_milestone',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_number', sa.Integer, nullable=False),
        sa.Column('milestone_name', sa.String(200), nullable=False),
        sa.Column('milestone_description', sa.Text, nullable=True),
        sa.Column('expected_date', sa.Date, nullable=False),
        sa.Column('actual_date', sa.Date, nullable=True),
        sa.Column('delay_days', sa.Integer, nullable=True),
        sa.Column('disbursement_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('disbursement_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('cumulative_disbursement_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('equity_contribution_required', sa.Numeric(20, 2), nullable=True),
        sa.Column('equity_contribution_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('status', postgresql.ENUM(name='milestonestatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('verification_criteria', sa.Text, nullable=True),
        sa.Column('verification_documents', postgresql.JSONB, nullable=True),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_remarks', sa.Text, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('application_id', 'milestone_number', name='uq_milestone_app_num'),
    )
    op.create_index('ix_los_milestone_app', 'los_project_milestone', ['application_id'])
    op.create_index('ix_los_milestone_app_status', 'los_project_milestone', ['application_id', 'status'])

    print("Created loan application tables")

    # ============================================================================
    # LOAN SANCTION TABLES
    # ============================================================================

    # los_loan_sanction - Loan sanction
    op.create_table(
        'los_loan_sanction',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_application.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_product.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sanction_number', sa.String(50), nullable=False),
        sa.Column('sanction_letter_number', sa.String(50), nullable=True),
        sa.Column('sanction_date', sa.Date, nullable=False),
        sa.Column('validity_date', sa.Date, nullable=False),
        sa.Column('first_disbursement_deadline', sa.Date, nullable=True),
        sa.Column('sanctioned_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('requested_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('approved_project_cost', sa.Numeric(20, 2), nullable=True),
        sa.Column('tenure_months', sa.Integer, nullable=False),
        sa.Column('moratorium_months', sa.Integer, default=0, nullable=False),
        sa.Column('moratorium_type', sa.String(20), nullable=True),
        sa.Column('interest_type', postgresql.ENUM(name='interesttype', create_type=False), nullable=False),
        sa.Column('base_rate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_interest_rate.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('base_rate_at_sanction', sa.Numeric(5, 2), nullable=True),
        sa.Column('spread_bps', sa.Integer, default=0, nullable=False),
        sa.Column('effective_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('rate_reset_frequency', postgresql.ENUM(name='rateresetfrequency', create_type=False), nullable=True),
        sa.Column('first_rate_reset_date', sa.Date, nullable=True),
        sa.Column('penal_interest_rate', sa.Numeric(5, 2), default=2.00, nullable=False),
        sa.Column('repayment_frequency', postgresql.ENUM(name='repaymentfrequency', create_type=False), nullable=False),
        sa.Column('repayment_mode', postgresql.ENUM(name='repaymentmode', create_type=False), nullable=False),
        sa.Column('repayment_start_date', sa.Date, nullable=True),
        sa.Column('day_count_convention', postgresql.ENUM(name='daycountconvention', create_type=False), default='ACT_365', nullable=False),
        sa.Column('principal_schedule', postgresql.JSONB, nullable=True),
        sa.Column('allows_prepayment', sa.Boolean, default=True, nullable=False),
        sa.Column('prepayment_lock_in_months', sa.Integer, default=12, nullable=False),
        sa.Column('prepayment_penalty_rate', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('allows_foreclosure', sa.Boolean, default=True, nullable=False),
        sa.Column('foreclosure_penalty_rate', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('disbursement_type', sa.String(20), default='SINGLE', nullable=False),
        sa.Column('max_tranches', sa.Integer, default=1, nullable=False),
        sa.Column('status', postgresql.ENUM(name='sanctionstatus', create_type=False), default='DRAFT', nullable=False),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_instance.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_authority', sa.String(200), nullable=True),
        sa.Column('approval_reference', sa.String(100), nullable=True),
        sa.Column('acceptance_required', sa.Boolean, default=True, nullable=False),
        sa.Column('acceptance_deadline', sa.Date, nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acceptance_document_path', sa.String(500), nullable=True),
        sa.Column('is_amendment', sa.Boolean, default=False, nullable=False),
        sa.Column('original_sanction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_sanction.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amendment_reason', sa.Text, nullable=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('entity_rating', sa.String(10), nullable=True),
        sa.Column('special_terms', sa.Text, nullable=True),
        sa.Column('sanction_letter_path', sa.String(500), nullable=True),
        sa.Column('agreement_draft_path', sa.String(500), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'sanction_number', name='uq_sanction_org_number'),
    )
    op.create_index('ix_los_sanction_org', 'los_loan_sanction', ['organization_id'])
    op.create_index('ix_los_sanction_number', 'los_loan_sanction', ['sanction_number'])
    op.create_index('ix_los_sanction_org_status', 'los_loan_sanction', ['organization_id', 'status'])
    op.create_index('ix_los_sanction_app', 'los_loan_sanction', ['application_id'])
    op.create_index('ix_los_sanction_entity', 'los_loan_sanction', ['entity_id'])
    op.create_index('ix_los_sanction_date', 'los_loan_sanction', ['sanction_date'])

    # los_sanction_condition - Sanction conditions
    op.create_table(
        'los_sanction_condition',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sanction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_sanction.id', ondelete='CASCADE'), nullable=False),
        sa.Column('condition_number', sa.Integer, nullable=False),
        sa.Column('condition_code', sa.String(50), nullable=True),
        sa.Column('condition_type', postgresql.ENUM(name='conditiontype', create_type=False), nullable=False),
        sa.Column('category', postgresql.ENUM(name='conditioncategory', create_type=False), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('detailed_requirement', sa.Text, nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('is_time_bound', sa.Boolean, default=False, nullable=False),
        sa.Column('days_from_disbursement', sa.Integer, nullable=True),
        sa.Column('frequency', sa.String(50), nullable=True),
        sa.Column('next_compliance_date', sa.Date, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('blocks_disbursement', sa.Boolean, default=False, nullable=False),
        sa.Column('is_waivable', sa.Boolean, default=True, nullable=False),
        sa.Column('waiver_authority', sa.String(100), nullable=True),
        sa.Column('compliance_status', postgresql.ENUM(name='conditioncompliancestatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('compliance_date', sa.Date, nullable=True),
        sa.Column('compliance_remarks', sa.Text, nullable=True),
        sa.Column('compliance_verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('waiver_date', sa.Date, nullable=True),
        sa.Column('waiver_reason', sa.Text, nullable=True),
        sa.Column('waiver_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deferral_date', sa.Date, nullable=True),
        sa.Column('deferral_reason', sa.Text, nullable=True),
        sa.Column('deferral_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('required_documents', postgresql.JSONB, nullable=True),
        sa.Column('uploaded_documents', postgresql.JSONB, nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('sanction_id', 'condition_number', name='uq_sanction_condition_num'),
    )
    op.create_index('ix_los_sanction_cond_sanction', 'los_sanction_condition', ['sanction_id'])
    op.create_index('ix_los_sanction_cond_type', 'los_sanction_condition', ['sanction_id', 'condition_type'])
    op.create_index('ix_los_sanction_cond_status', 'los_sanction_condition', ['sanction_id', 'compliance_status'])

    # los_loan_security - Loan security/collateral
    op.create_table(
        'los_loan_security',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sanction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_sanction.id', ondelete='CASCADE'), nullable=False),
        sa.Column('security_number', sa.Integer, nullable=False),
        sa.Column('security_code', sa.String(50), nullable=True),
        sa.Column('security_category', postgresql.ENUM(name='securitycategory', create_type=False), nullable=False),
        sa.Column('security_type', postgresql.ENUM(name='securitytype', create_type=False), nullable=False),
        sa.Column('charge_type', postgresql.ENUM(name='chargetype', create_type=False), default='FIRST', nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('detailed_description', sa.Text, nullable=True),
        sa.Column('property_address', sa.Text, nullable=True),
        sa.Column('property_area_sqft', sa.Numeric(15, 2), nullable=True),
        sa.Column('survey_number', sa.String(100), nullable=True),
        sa.Column('property_type', sa.String(100), nullable=True),
        sa.Column('owner_name', sa.String(500), nullable=True),
        sa.Column('owner_relationship', sa.String(100), nullable=True),
        sa.Column('is_third_party', sa.Boolean, default=False, nullable=False),
        sa.Column('third_party_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('declared_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('market_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('forced_sale_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('acceptable_value', sa.Numeric(20, 2), nullable=False),
        sa.Column('margin_percentage', sa.Numeric(5, 2), default=25, nullable=False),
        sa.Column('net_value', sa.Numeric(20, 2), nullable=False),
        sa.Column('valuation_date', sa.Date, nullable=True),
        sa.Column('valuer_name', sa.String(200), nullable=True),
        sa.Column('valuer_firm', sa.String(200), nullable=True),
        sa.Column('valuation_report_path', sa.String(500), nullable=True),
        sa.Column('next_valuation_date', sa.Date, nullable=True),
        sa.Column('has_existing_charge', sa.Boolean, default=False, nullable=False),
        sa.Column('existing_charge_holder', sa.String(200), nullable=True),
        sa.Column('existing_charge_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('noc_obtained', sa.Boolean, default=False, nullable=False),
        sa.Column('requires_insurance', sa.Boolean, default=True, nullable=False),
        sa.Column('insured_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('insurance_policy_number', sa.String(100), nullable=True),
        sa.Column('insurance_company', sa.String(200), nullable=True),
        sa.Column('insurance_expiry', sa.Date, nullable=True),
        sa.Column('status', postgresql.ENUM(name='securitystatus', create_type=False), default='PROPOSED', nullable=False),
        sa.Column('charge_created_date', sa.Date, nullable=True),
        sa.Column('charge_id', sa.String(50), nullable=True),
        sa.Column('cersai_id', sa.String(50), nullable=True),
        sa.Column('cersai_registration_date', sa.Date, nullable=True),
        sa.Column('legal_vetted', sa.Boolean, default=False, nullable=False),
        sa.Column('legal_vetting_date', sa.Date, nullable=True),
        sa.Column('legal_opinion_path', sa.String(500), nullable=True),
        sa.Column('legal_remarks', sa.Text, nullable=True),
        sa.Column('original_documents_received', sa.Boolean, default=False, nullable=False),
        sa.Column('document_list', postgresql.JSONB, nullable=True),
        sa.Column('document_location', sa.String(200), nullable=True),
        sa.Column('guarantor_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guarantor_contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_contact.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guarantee_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('is_unlimited_guarantee', sa.Boolean, default=False, nullable=False),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('sanction_id', 'security_number', name='uq_loan_security_num'),
    )
    op.create_index('ix_los_loan_security_sanction', 'los_loan_security', ['sanction_id'])
    op.create_index('ix_los_loan_security_type', 'los_loan_security', ['sanction_id', 'security_type'])
    op.create_index('ix_los_loan_security_category', 'los_loan_security', ['sanction_id', 'security_category'])
    op.create_index('ix_los_loan_security_status', 'los_loan_security', ['sanction_id', 'status'])
    op.create_index('ix_los_loan_security_code', 'los_loan_security', ['security_code'])

    print("Created loan sanction tables")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('los_loan_security')
    op.drop_table('los_sanction_condition')
    op.drop_table('los_loan_sanction')
    op.drop_table('los_project_milestone')
    op.drop_table('los_financial_analysis')
    op.drop_table('los_technical_appraisal')
    op.drop_table('los_application_fee')
    op.drop_table('los_application_document')
    op.drop_table('los_loan_application')
