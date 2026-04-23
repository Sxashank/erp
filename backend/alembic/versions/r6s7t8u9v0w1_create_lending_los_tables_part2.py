"""create_lending_los_tables_part2

Revision ID: r6s7t8u9v0w1
Revises: q5r6s7t8u9v0
Create Date: 2026-01-12 19:30:00.000000

Create Loan Origination System (LOS) tables - Part 2.
Rating, Product, Application, and Sanction models.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'r6s7t8u9v0w1'
down_revision: Union[str, None] = 'q5r6s7t8u9v0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # CREDIT RATING TABLES
    # ============================================================================

    # los_risk_category - Risk categories for scoring
    op.create_table(
        'los_risk_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category_type', postgresql.ENUM(name='riskcategorytype', create_type=False), nullable=False),
        sa.Column('weight_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('max_score', sa.Integer, default=100, nullable=False),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        sa.Column('applicable_entity_types', postgresql.JSONB, nullable=True),
        sa.Column('applicable_product_categories', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_risk_category_org_code'),
    )
    op.create_index('ix_los_risk_category_org', 'los_risk_category', ['organization_id'])
    op.create_index('ix_los_risk_category_org_type', 'los_risk_category', ['organization_id', 'category_type'])

    # los_risk_parameter - Risk parameters within categories
    op.create_table(
        'los_risk_parameter',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_risk_category.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('max_score', sa.Integer, default=10, nullable=False),
        sa.Column('weight_in_category', sa.Numeric(5, 2), default=100, nullable=False),
        sa.Column('value_type', sa.String(20), default='NUMERIC', nullable=False),
        sa.Column('min_value', sa.Numeric(20, 4), nullable=True),
        sa.Column('max_value', sa.Numeric(20, 4), nullable=True),
        sa.Column('scoring_slabs', postgresql.JSONB, nullable=True),
        sa.Column('categorical_options', postgresql.JSONB, nullable=True),
        sa.Column('is_auto_calculated', sa.Boolean, default=False, nullable=False),
        sa.Column('calculation_formula', sa.Text, nullable=True),
        sa.Column('data_source_field', sa.String(100), nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('default_remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('category_id', 'code', name='uq_risk_param_category_code'),
    )
    op.create_index('ix_los_risk_parameter_category', 'los_risk_parameter', ['category_id'])
    op.create_index('ix_los_risk_parameter_code', 'los_risk_parameter', ['code'])

    # los_rating_matrix - Score to grade mapping
    op.create_table(
        'los_rating_matrix',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade', postgresql.ENUM(name='ratinggrade', create_type=False), nullable=False),
        sa.Column('grade_description', sa.String(200), nullable=False),
        sa.Column('min_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('max_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('risk_weight', sa.Numeric(5, 2), default=100, nullable=False),
        sa.Column('provisioning_rate', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('pricing_spread_bps', sa.Integer, default=0, nullable=False),
        sa.Column('max_exposure_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('requires_collateral', sa.Boolean, default=False, nullable=False),
        sa.Column('min_collateral_coverage', sa.Numeric(5, 2), nullable=True),
        sa.Column('approval_authority', sa.String(100), nullable=True),
        sa.Column('max_sanction_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        sa.Column('color_code', sa.String(10), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'grade', name='uq_rating_matrix_org_grade'),
    )
    op.create_index('ix_los_rating_matrix_org', 'los_rating_matrix', ['organization_id'])
    op.create_index('ix_los_rating_matrix_org_score', 'los_rating_matrix', ['organization_id', 'min_score', 'max_score'])

    # los_entity_rating - Entity credit ratings
    op.create_table(
        'los_entity_rating',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating_reference', sa.String(50), nullable=False),
        sa.Column('rating_type', postgresql.ENUM(name='ratingtype', create_type=False), nullable=False),
        sa.Column('rating_date', sa.Date, nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=False),
        sa.Column('previous_rating_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_rating.id', ondelete='SET NULL'), nullable=True),
        sa.Column('previous_grade', postgresql.ENUM(name='ratinggrade', create_type=False), nullable=True),
        sa.Column('total_score', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_possible_score', sa.Numeric(10, 2), default=100, nullable=False),
        sa.Column('score_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('calculated_grade', postgresql.ENUM(name='ratinggrade', create_type=False), nullable=False),
        sa.Column('final_grade', postgresql.ENUM(name='ratinggrade', create_type=False), nullable=False),
        sa.Column('grade_overridden', sa.Boolean, default=False, nullable=False),
        sa.Column('override_reason', sa.Text, nullable=True),
        sa.Column('category_scores', postgresql.JSONB, nullable=False),
        sa.Column('parameter_scores', postgresql.JSONB, nullable=False),
        sa.Column('financial_year_used', sa.String(10), nullable=True),
        sa.Column('status', postgresql.ENUM(name='ratingstatus', create_type=False), default='DRAFT', nullable=False),
        sa.Column('workflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wf_workflow_instance.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.Date, nullable=True),
        sa.Column('approval_remarks', sa.Text, nullable=True),
        sa.Column('rated_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('rating_summary', sa.Text, nullable=True),
        sa.Column('strengths', sa.Text, nullable=True),
        sa.Column('weaknesses', sa.Text, nullable=True),
        sa.Column('recommendations', sa.Text, nullable=True),
        sa.Column('supporting_documents', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'rating_reference', name='uq_entity_rating_ref'),
    )
    op.create_index('ix_los_entity_rating_org', 'los_entity_rating', ['organization_id'])
    op.create_index('ix_los_entity_rating_entity', 'los_entity_rating', ['entity_id'])
    op.create_index('ix_los_entity_rating_entity_date', 'los_entity_rating', ['entity_id', 'rating_date'])
    op.create_index('ix_los_entity_rating_org_status', 'los_entity_rating', ['organization_id', 'status'])
    op.create_index('ix_los_entity_rating_org_grade', 'los_entity_rating', ['organization_id', 'final_grade'])

    # los_rating_score_detail - Individual parameter scores
    op.create_table(
        'los_rating_score_detail',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rating_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_rating.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_risk_category.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('parameter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_risk_parameter.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('input_value', sa.String(200), nullable=True),
        sa.Column('numeric_value', sa.Numeric(20, 4), nullable=True),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('max_score', sa.Integer, nullable=False),
        sa.Column('weighted_score', sa.Numeric(10, 4), nullable=False),
        sa.Column('is_auto_calculated', sa.Boolean, default=False, nullable=False),
        sa.Column('data_source', sa.String(100), nullable=True),
        sa.Column('is_overridden', sa.Boolean, default=False, nullable=False),
        sa.Column('original_score', sa.Integer, nullable=True),
        sa.Column('override_reason', sa.Text, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('rating_id', 'parameter_id', name='uq_rating_score_param'),
    )
    op.create_index('ix_los_rating_score_rating', 'los_rating_score_detail', ['rating_id'])
    op.create_index('ix_los_rating_score_rating_cat', 'los_rating_score_detail', ['rating_id', 'category_id'])

    print("Created credit rating tables")

    # ============================================================================
    # LOAN PRODUCT TABLES
    # ============================================================================

    # los_interest_rate - Base rate master
    op.create_table(
        'los_interest_rate',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rate_type', sa.String(50), default='BASE_RATE', nullable=False),
        sa.Column('benchmark_name', sa.String(100), nullable=True),
        sa.Column('current_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('previous_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('previous_effective_from', sa.Date, nullable=True),
        sa.Column('reset_frequency', postgresql.ENUM(name='rateresetfrequency', create_type=False), nullable=True),
        sa.Column('next_review_date', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_interest_rate_org_code'),
    )
    op.create_index('ix_los_interest_rate_org', 'los_interest_rate', ['organization_id'])
    op.create_index('ix_los_interest_rate_org_date', 'los_interest_rate', ['organization_id', 'effective_from'])

    # los_interest_rate_history - Rate change history
    op.create_table(
        'los_interest_rate_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('interest_rate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_interest_rate.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_until', sa.Date, nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('approved_by', sa.String(200), nullable=True),
        sa.Column('approval_reference', sa.String(100), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_rate_history_rate', 'los_interest_rate_history', ['interest_rate_id'])
    op.create_index('ix_los_rate_history_rate_date', 'los_interest_rate_history', ['interest_rate_id', 'effective_from'])

    # los_loan_product - Loan product configuration
    op.create_table(
        'los_loan_product',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', postgresql.ENUM(name='productcategory', create_type=False), nullable=False),
        sa.Column('min_amount', sa.Numeric(20, 2), default=100000, nullable=False),
        sa.Column('max_amount', sa.Numeric(20, 2), default=100000000, nullable=False),
        sa.Column('default_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('min_tenure_months', sa.Integer, default=12, nullable=False),
        sa.Column('max_tenure_months', sa.Integer, default=120, nullable=False),
        sa.Column('default_tenure_months', sa.Integer, nullable=True),
        sa.Column('allows_moratorium', sa.Boolean, default=True, nullable=False),
        sa.Column('max_moratorium_months', sa.Integer, default=12, nullable=False),
        sa.Column('moratorium_type', sa.String(20), default='INTEREST_ONLY', nullable=False),
        sa.Column('interest_type', postgresql.ENUM(name='interesttype', create_type=False), default='FLOATING', nullable=False),
        sa.Column('base_rate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_interest_rate.id', ondelete='SET NULL'), nullable=True),
        sa.Column('min_spread_bps', sa.Integer, default=0, nullable=False),
        sa.Column('max_spread_bps', sa.Integer, default=500, nullable=False),
        sa.Column('default_spread_bps', sa.Integer, default=200, nullable=False),
        sa.Column('min_effective_rate', sa.Numeric(5, 2), default=8.00, nullable=False),
        sa.Column('max_effective_rate', sa.Numeric(5, 2), default=24.00, nullable=False),
        sa.Column('rate_reset_frequency', postgresql.ENUM(name='rateresetfrequency', create_type=False), nullable=True),
        sa.Column('day_count_convention', postgresql.ENUM(name='daycountconvention', create_type=False), default='ACT_365', nullable=False),
        sa.Column('interest_calculation_method', sa.String(50), default='REDUCING_BALANCE', nullable=False),
        sa.Column('interest_compounding', sa.String(20), default='MONTHLY', nullable=False),
        sa.Column('allowed_repayment_frequencies', postgresql.JSONB, default=['MONTHLY', 'QUARTERLY'], nullable=False),
        sa.Column('default_repayment_frequency', postgresql.ENUM(name='repaymentfrequency', create_type=False), default='MONTHLY', nullable=False),
        sa.Column('allowed_repayment_modes', postgresql.JSONB, default=['EMI', 'STRUCTURED'], nullable=False),
        sa.Column('default_repayment_mode', postgresql.ENUM(name='repaymentmode', create_type=False), default='EMI', nullable=False),
        sa.Column('allows_prepayment', sa.Boolean, default=True, nullable=False),
        sa.Column('prepayment_lock_in_months', sa.Integer, default=12, nullable=False),
        sa.Column('allows_foreclosure', sa.Boolean, default=True, nullable=False),
        sa.Column('foreclosure_lock_in_months', sa.Integer, default=12, nullable=False),
        sa.Column('requires_collateral', sa.Boolean, default=True, nullable=False),
        sa.Column('min_collateral_coverage', sa.Numeric(5, 2), default=100, nullable=False),
        sa.Column('allowed_security_types', postgresql.JSONB, nullable=True),
        sa.Column('requires_guarantee', sa.Boolean, default=False, nullable=False),
        sa.Column('eligible_entity_types', postgresql.JSONB, default=['CORPORATE', 'LLP', 'PARTNERSHIP'], nullable=False),
        sa.Column('min_vintage_months', sa.Integer, default=24, nullable=False),
        sa.Column('min_turnover', sa.Numeric(20, 2), nullable=True),
        sa.Column('min_rating_grade', sa.String(10), nullable=True),
        sa.Column('min_cibil_score', sa.Integer, nullable=True),
        sa.Column('max_debt_equity_ratio', sa.Numeric(5, 2), nullable=True),
        sa.Column('min_current_ratio', sa.Numeric(5, 2), nullable=True),
        sa.Column('min_dscr', sa.Numeric(5, 2), nullable=True),
        sa.Column('disbursement_type', sa.String(20), default='SINGLE', nullable=False),
        sa.Column('max_tranches', sa.Integer, default=1, nullable=False),
        sa.Column('allows_partial_disbursement', sa.Boolean, default=True, nullable=False),
        sa.Column('disbursement_validity_days', sa.Integer, default=180, nullable=False),
        sa.Column('approval_workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gl_mapping', postgresql.JSONB, nullable=True),
        sa.Column('is_active_for_new_loans', sa.Boolean, default=True, nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_until', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_loan_product_org_code'),
    )
    op.create_index('ix_los_loan_product_org', 'los_loan_product', ['organization_id'])
    op.create_index('ix_los_loan_product_org_cat', 'los_loan_product', ['organization_id', 'category'])
    op.create_index('ix_los_loan_product_org_active', 'los_loan_product', ['organization_id', 'is_active_for_new_loans'])

    # los_fee_master - Fee type master
    op.create_table(
        'los_fee_master',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('fee_type', postgresql.ENUM(name='feetype', create_type=False), nullable=False),
        sa.Column('calculation_type', postgresql.ENUM(name='feecalculationtype', create_type=False), default='PERCENTAGE', nullable=False),
        sa.Column('default_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('default_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('min_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('slabs', postgresql.JSONB, nullable=True),
        sa.Column('collection_stage', postgresql.ENUM(name='feecollectionstage', create_type=False), default='DISBURSEMENT', nullable=False),
        sa.Column('is_refundable', sa.Boolean, default=False, nullable=False),
        sa.Column('deduct_from_disbursement', sa.Boolean, default=True, nullable=False),
        sa.Column('is_taxable', sa.Boolean, default=True, nullable=False),
        sa.Column('gst_rate', sa.Numeric(5, 2), default=18.00, nullable=False),
        sa.Column('hsn_sac_code', sa.String(20), nullable=True),
        sa.Column('income_gl_account', sa.String(50), nullable=True),
        sa.Column('receivable_gl_account', sa.String(50), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_fee_master_org_code'),
    )
    op.create_index('ix_los_fee_master_org', 'los_fee_master', ['organization_id'])
    op.create_index('ix_los_fee_master_org_type', 'los_fee_master', ['organization_id', 'fee_type'])

    # los_product_fee - Product fee configuration
    op.create_table(
        'los_product_fee',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_product.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fee_master_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_fee_master.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('is_waivable', sa.Boolean, default=True, nullable=False),
        sa.Column('max_waiver_percentage', sa.Numeric(5, 2), default=100, nullable=False),
        sa.Column('override_calculation_type', postgresql.ENUM(name='feecalculationtype', create_type=False), nullable=True),
        sa.Column('override_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('override_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('override_min_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('override_max_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('product_id', 'fee_master_id', name='uq_product_fee'),
    )
    op.create_index('ix_los_product_fee_product', 'los_product_fee', ['product_id'])

    # los_document_checklist - Product document checklist
    op.create_table(
        'los_document_checklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_product.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', postgresql.ENUM(name='documentcategory', create_type=False), nullable=False),
        sa.Column('required_at_stage', postgresql.ENUM(name='documentstage', create_type=False), nullable=False),
        sa.Column('is_mandatory', sa.Boolean, default=True, nullable=False),
        sa.Column('is_mandatory_for_disbursement', sa.Boolean, default=False, nullable=False),
        sa.Column('applicable_entity_types', postgresql.JSONB, nullable=True),
        sa.Column('applicable_conditions', postgresql.JSONB, nullable=True),
        sa.Column('has_expiry', sa.Boolean, default=False, nullable=False),
        sa.Column('validity_months', sa.Integer, nullable=True),
        sa.Column('renewal_alert_days', sa.Integer, nullable=True),
        sa.Column('allowed_file_types', postgresql.JSONB, default=['pdf', 'jpg', 'jpeg', 'png'], nullable=False),
        sa.Column('max_file_size_mb', sa.Integer, default=10, nullable=False),
        sa.Column('min_file_count', sa.Integer, default=1, nullable=False),
        sa.Column('max_file_count', sa.Integer, default=10, nullable=False),
        sa.Column('requires_verification', sa.Boolean, default=False, nullable=False),
        sa.Column('verification_instructions', sa.Text, nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        sa.Column('help_text', sa.Text, nullable=True),
        sa.Column('sample_document_path', sa.String(500), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('product_id', 'code', name='uq_doc_checklist_product_code'),
    )
    op.create_index('ix_los_doc_checklist_product', 'los_document_checklist', ['product_id'])
    op.create_index('ix_los_doc_checklist_product_stage', 'los_document_checklist', ['product_id', 'required_at_stage'])
    op.create_index('ix_los_doc_checklist_product_cat', 'los_document_checklist', ['product_id', 'category'])

    print("Created loan product tables")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('los_document_checklist')
    op.drop_table('los_product_fee')
    op.drop_table('los_fee_master')
    op.drop_table('los_loan_product')
    op.drop_table('los_interest_rate_history')
    op.drop_table('los_interest_rate')
    op.drop_table('los_rating_score_detail')
    op.drop_table('los_entity_rating')
    op.drop_table('los_rating_matrix')
    op.drop_table('los_risk_parameter')
    op.drop_table('los_risk_category')
