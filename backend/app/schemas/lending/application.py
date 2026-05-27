"""Loan Application schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.models.lending.enums import (
    ApplicationStage,
    ApplicationStatus,
    AppraisalRecommendation,
    AppraisalType,
    MilestoneStatus,
    TechnicalFeasibility,
)
from app.schemas.base import CamelSchema

# =============================================================================
# Application Document Schemas
# =============================================================================


class ApplicationDocumentBase(CamelSchema):
    """Base schema for application document."""

    checklist_item_id: UUID | None = None
    document_code: str = Field(..., min_length=1, max_length=50)
    document_name: str = Field(..., min_length=1, max_length=200)
    document_description: str | None = None
    file_name: str = Field(..., min_length=1, max_length=255)
    dms_document_id: UUID | None = None
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size_bytes: int | None = Field(None, ge=0)
    file_mime_type: str | None = Field(None, max_length=100)
    file_hash: str | None = Field(None, max_length=64)
    document_date: date | None = None
    expiry_date: date | None = None
    upload_date: datetime | None = None
    status: str = Field(default="PENDING", max_length=50)
    is_mandatory: bool = True
    is_waived: bool = False
    waiver_reason: str | None = None
    waiver_approved_by: UUID | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    verification_remarks: str | None = None
    rejection_reason: str | None = None


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Schema for creating application document."""

    application_id: UUID


class ApplicationDocumentUpdate(CamelSchema):
    """Schema for updating application document."""

    checklist_item_id: UUID | None = None
    document_code: str | None = Field(None, min_length=1, max_length=50)
    document_name: str | None = Field(None, min_length=1, max_length=200)
    document_description: str | None = None
    file_path: str | None = Field(None, max_length=500)
    file_name: str | None = Field(None, max_length=255)
    dms_document_id: UUID | None = None
    file_size_bytes: int | None = Field(None, ge=0)
    file_mime_type: str | None = Field(None, max_length=100)
    file_hash: str | None = Field(None, max_length=64)
    document_date: date | None = None
    status: str | None = Field(None, max_length=50)
    is_mandatory: bool | None = None
    is_waived: bool | None = None
    waiver_reason: str | None = None
    waiver_approved_by: UUID | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    verification_remarks: str | None = None
    rejection_reason: str | None = None
    expiry_date: date | None = None
    is_active: bool | None = None


class ApplicationDocumentResponse(ApplicationDocumentBase):
    """Schema for application document response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Application Fee Schemas
# =============================================================================


class ApplicationFeeBase(CamelSchema):
    """Base schema for application fee."""

    fee_master_id: UUID
    fee_code: str = Field(..., min_length=1, max_length=50)
    fee_name: str = Field(..., min_length=1, max_length=200)
    calculated_amount: Decimal = Field(..., ge=0)
    approved_amount: Decimal = Field(..., ge=0)
    waiver_amount: Decimal = Field(default=Decimal("0"), ge=0)
    waiver_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    cgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    igst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    status: str = Field(default="PENDING", max_length=50)
    collection_mode: str | None = Field(None, max_length=50)
    collection_date: date | None = None
    collection_reference: str | None = Field(None, max_length=100)
    waiver_approved_by: UUID | None = None
    waiver_reason: str | None = None
    deducted_from_disbursement: bool = False
    disbursement_id: UUID | None = None
    invoice_number: str | None = Field(None, max_length=50)
    invoice_date: date | None = None


class ApplicationFeeCreate(ApplicationFeeBase):
    """Schema for creating application fee."""

    application_id: UUID


class ApplicationFeeUpdate(CamelSchema):
    """Schema for updating application fee."""

    approved_amount: Decimal | None = Field(None, ge=0)
    waiver_amount: Decimal | None = Field(None, ge=0)
    waiver_percentage: Decimal | None = Field(None, ge=0, le=100)
    cgst_amount: Decimal | None = Field(None, ge=0)
    sgst_amount: Decimal | None = Field(None, ge=0)
    igst_amount: Decimal | None = Field(None, ge=0)
    total_amount: Decimal | None = Field(None, ge=0)
    status: str | None = Field(None, max_length=50)
    collection_mode: str | None = Field(None, max_length=50)
    collection_date: date | None = None
    collection_reference: str | None = Field(None, max_length=100)
    waiver_approved_by: UUID | None = None
    waiver_reason: str | None = None
    deducted_from_disbursement: bool | None = None
    disbursement_id: UUID | None = None
    invoice_number: str | None = Field(None, max_length=50)
    invoice_date: date | None = None
    is_active: bool | None = None


class ApplicationFeeResponse(ApplicationFeeBase):
    """Schema for application fee response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Technical Appraisal Schemas
# =============================================================================


class TechnicalAppraisalBase(CamelSchema):
    """Base schema for technical appraisal."""

    appraisal_reference: str | None = Field(None, max_length=50)
    appraisal_type: AppraisalType = AppraisalType.TECHNICAL
    appraisal_date: date
    site_visit_date: date | None = None
    appraiser_id: UUID | None = None
    external_appraiser: str | None = Field(None, max_length=200)
    external_appraiser_firm: str | None = Field(None, max_length=200)

    # Project Details
    project_description: str | None = None
    location_details: str | None = None
    land_area_sqft: Decimal | None = Field(None, ge=0)
    built_up_area_sqft: Decimal | None = Field(None, ge=0)

    # Cost Details
    estimated_project_cost: Decimal | None = Field(None, ge=0)
    land_cost: Decimal | None = Field(None, ge=0)
    construction_cost: Decimal | None = Field(None, ge=0)
    machinery_cost: Decimal | None = Field(None, ge=0)
    other_costs: Decimal | None = Field(None, ge=0)
    contingency: Decimal | None = Field(None, ge=0)

    # Progress
    feasibility: TechnicalFeasibility = TechnicalFeasibility.FEASIBLE
    feasibility_remarks: str | None = None
    estimated_completion_months: int | None = Field(None, ge=0)
    construction_stage: str | None = Field(None, max_length=100)
    completion_percentage: Decimal | None = Field(None, ge=0, le=100)
    statutory_approvals: dict[str, Any] | None = None
    environmental_clearance: str | None = Field(None, max_length=50)

    # Assessment
    recommendation: AppraisalRecommendation = AppraisalRecommendation.PROCEED
    conditions: list[dict[str, Any]] | None = None
    concerns: list[dict[str, Any]] | None = None
    report_summary: str | None = None
    report_file_path: str | None = Field(None, max_length=500)
    photos: list[dict[str, Any]] | None = None


class TechnicalAppraisalCreate(TechnicalAppraisalBase):
    """Schema for creating technical appraisal."""

    application_id: UUID


class TechnicalAppraisalUpdate(CamelSchema):
    """Schema for updating technical appraisal."""

    appraisal_reference: str | None = Field(None, max_length=50)
    appraisal_type: AppraisalType | None = None
    appraisal_date: date | None = None
    site_visit_date: date | None = None
    appraiser_id: UUID | None = None
    external_appraiser: str | None = Field(None, max_length=200)
    external_appraiser_firm: str | None = Field(None, max_length=200)

    project_description: str | None = None
    location_details: str | None = None
    land_area_sqft: Decimal | None = Field(None, ge=0)
    built_up_area_sqft: Decimal | None = Field(None, ge=0)

    estimated_project_cost: Decimal | None = Field(None, ge=0)
    land_cost: Decimal | None = Field(None, ge=0)
    construction_cost: Decimal | None = Field(None, ge=0)
    machinery_cost: Decimal | None = Field(None, ge=0)
    other_costs: Decimal | None = Field(None, ge=0)
    contingency: Decimal | None = Field(None, ge=0)

    feasibility: TechnicalFeasibility | None = None
    feasibility_remarks: str | None = None
    estimated_completion_months: int | None = Field(None, ge=0)
    construction_stage: str | None = Field(None, max_length=100)
    completion_percentage: Decimal | None = Field(None, ge=0, le=100)
    statutory_approvals: dict[str, Any] | None = None
    environmental_clearance: str | None = Field(None, max_length=50)
    recommendation: AppraisalRecommendation | None = None
    conditions: list[dict[str, Any]] | None = None
    concerns: list[dict[str, Any]] | None = None
    report_summary: str | None = None
    report_file_path: str | None = Field(None, max_length=500)
    photos: list[dict[str, Any]] | None = None

    is_active: bool | None = None


class TechnicalAppraisalResponse(TechnicalAppraisalBase):
    """Schema for technical appraisal response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Financial Analysis Schemas
# =============================================================================


class FinancialAnalysisBase(CamelSchema):
    """Base schema for financial analysis."""

    analysis_reference: str | None = Field(None, max_length=50)
    analysis_date: date
    analyst_id: UUID | None = None
    financial_years_analyzed: list[str] = Field(default_factory=list)
    base_year: str = Field(..., max_length=10)
    historical_ratios: dict[str, Any] = Field(default_factory=dict)

    # Project Financials
    projection_years: int = Field(default=5, ge=1)
    projected_revenue: dict[str, Any] = Field(default_factory=dict)
    projected_ebitda: dict[str, Any] = Field(default_factory=dict)
    projected_net_profit: dict[str, Any] = Field(default_factory=dict)
    projected_cash_flows: dict[str, Any] = Field(default_factory=dict)

    current_ratio: Decimal | None = None
    debt_equity_ratio: Decimal | None = None
    interest_coverage_ratio: Decimal | None = None
    average_dscr: Decimal | None = None
    minimum_dscr: Decimal | None = None
    dscr_by_year: dict[str, Any] | None = None
    break_even_capacity_pct: Decimal | None = Field(None, ge=0, le=100)
    break_even_sales: Decimal | None = Field(None, ge=0)

    # Assessment
    sensitivity_analysis: dict[str, Any] | None = None
    recommendation: AppraisalRecommendation = AppraisalRecommendation.PROCEED
    recommended_amount: Decimal | None = Field(None, ge=0)
    recommended_tenure: int | None = Field(None, ge=1)
    recommended_moratorium: int | None = Field(None, ge=0)
    strengths: str | None = None
    weaknesses: str | None = None
    comments: str | None = None
    conditions: list[dict[str, Any]] | None = None
    report_file_path: str | None = Field(None, max_length=500)


class FinancialAnalysisCreate(FinancialAnalysisBase):
    """Schema for creating financial analysis."""

    application_id: UUID


class FinancialAnalysisUpdate(CamelSchema):
    """Schema for updating financial analysis."""

    analysis_reference: str | None = Field(None, max_length=50)
    analysis_date: date | None = None
    analyst_id: UUID | None = None
    financial_years_analyzed: list[str] | None = None
    base_year: str | None = Field(None, max_length=10)
    historical_ratios: dict[str, Any] | None = None

    projection_years: int | None = Field(None, ge=1)
    projected_revenue: dict[str, Any] | None = None
    projected_ebitda: dict[str, Any] | None = None
    projected_net_profit: dict[str, Any] | None = None
    projected_cash_flows: dict[str, Any] | None = None

    current_ratio: Decimal | None = None
    debt_equity_ratio: Decimal | None = None
    interest_coverage_ratio: Decimal | None = None
    average_dscr: Decimal | None = None
    minimum_dscr: Decimal | None = None
    dscr_by_year: dict[str, Any] | None = None
    break_even_capacity_pct: Decimal | None = Field(None, ge=0, le=100)
    break_even_sales: Decimal | None = Field(None, ge=0)

    sensitivity_analysis: dict[str, Any] | None = None
    recommendation: AppraisalRecommendation | None = None
    recommended_amount: Decimal | None = Field(None, ge=0)
    recommended_tenure: int | None = Field(None, ge=1)
    recommended_moratorium: int | None = Field(None, ge=0)
    strengths: str | None = None
    weaknesses: str | None = None
    comments: str | None = None
    conditions: list[dict[str, Any]] | None = None
    report_file_path: str | None = Field(None, max_length=500)

    is_active: bool | None = None


class FinancialAnalysisResponse(FinancialAnalysisBase):
    """Schema for financial analysis response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Project Milestone Schemas
# =============================================================================


class ProjectMilestoneBase(CamelSchema):
    """Base schema for project milestone."""

    milestone_number: int = Field(..., ge=1)
    milestone_name: str = Field(..., min_length=1, max_length=200)
    milestone_description: str | None = None
    expected_date: date
    actual_date: date | None = None
    delay_days: int | None = None
    disbursement_percentage: Decimal = Field(..., ge=0, le=100)
    disbursement_amount: Decimal | None = Field(None, ge=0)
    cumulative_disbursement_pct: Decimal | None = Field(None, ge=0, le=100)
    equity_contribution_required: Decimal | None = Field(None, ge=0)
    equity_contribution_verified: bool = False
    status: MilestoneStatus = MilestoneStatus.PENDING
    verification_criteria: str | None = None
    verification_documents: list[dict[str, Any]] | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    verification_remarks: str | None = None
    remarks: str | None = None


class ProjectMilestoneCreate(ProjectMilestoneBase):
    """Schema for creating project milestone."""

    application_id: UUID


class ProjectMilestoneUpdate(CamelSchema):
    """Schema for updating project milestone."""

    milestone_name: str | None = Field(None, min_length=1, max_length=200)
    milestone_description: str | None = None
    expected_date: date | None = None
    actual_date: date | None = None
    delay_days: int | None = None
    disbursement_percentage: Decimal | None = Field(None, ge=0, le=100)
    disbursement_amount: Decimal | None = Field(None, ge=0)
    cumulative_disbursement_pct: Decimal | None = Field(None, ge=0, le=100)
    equity_contribution_required: Decimal | None = Field(None, ge=0)
    equity_contribution_verified: bool | None = None
    status: MilestoneStatus | None = None
    verification_criteria: str | None = None
    verification_documents: list[dict[str, Any]] | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    verification_remarks: str | None = None
    remarks: str | None = None
    is_active: bool | None = None


class ProjectMilestoneResponse(ProjectMilestoneBase):
    """Schema for project milestone response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Loan Application Schemas
# =============================================================================


class LoanApplicationBase(CamelSchema):
    """Base schema for loan application."""

    entity_id: UUID
    product_id: UUID

    # Loan Request
    requested_amount: Decimal = Field(..., ge=0)
    requested_tenure_months: int = Field(..., ge=1)
    purpose: str = Field(..., min_length=1, max_length=500)
    detailed_purpose: str | None = None

    # Project Details (for project finance)
    is_project_finance: bool = False
    project_name: str | None = Field(None, max_length=200)
    project_cost: Decimal | None = Field(None, ge=0)
    promoter_contribution: Decimal | None = Field(None, ge=0)
    promoter_contribution_pct: Decimal | None = Field(None, ge=0, le=100)
    bank_finance: Decimal | None = Field(None, ge=0)
    other_finance: Decimal | None = Field(None, ge=0)
    project_location: str | None = Field(None, max_length=500)
    project_start_date: date | None = None
    project_completion_date: date | None = None

    # Preferred Terms
    preferred_interest_type: str = Field(default="FLOATING", min_length=1, max_length=80)
    preferred_repayment_frequency: str = Field(default="MONTHLY", min_length=1, max_length=80)
    preferred_repayment_mode: str = Field(default="EMI", min_length=1, max_length=80)
    requested_moratorium_months: int = Field(default=0, ge=0)

    # Source
    source_channel: str = Field(default="DIRECT", max_length=50)
    source_reference: str | None = Field(None, max_length=100)

    # Metadata
    remarks: str | None = None
    extra_data: dict[str, Any] | None = None


class LoanApplicationCreate(LoanApplicationBase):
    """Schema for creating loan application."""

    organization_id: UUID | None = None


class LoanApplicationUpdate(CamelSchema):
    """Schema for updating loan application."""

    requested_amount: Decimal | None = Field(None, ge=0)
    requested_tenure_months: int | None = Field(None, ge=1)
    purpose: str | None = Field(None, min_length=1, max_length=500)
    detailed_purpose: str | None = None

    # Project Details
    is_project_finance: bool | None = None
    project_name: str | None = Field(None, max_length=200)
    project_cost: Decimal | None = Field(None, ge=0)
    promoter_contribution: Decimal | None = Field(None, ge=0)
    promoter_contribution_pct: Decimal | None = Field(None, ge=0, le=100)
    bank_finance: Decimal | None = Field(None, ge=0)
    other_finance: Decimal | None = Field(None, ge=0)
    project_location: str | None = Field(None, max_length=500)
    project_start_date: date | None = None
    project_completion_date: date | None = None

    # Preferred Terms
    preferred_interest_type: str | None = Field(None, min_length=1, max_length=80)
    preferred_repayment_frequency: str | None = Field(None, min_length=1, max_length=80)
    preferred_repayment_mode: str | None = Field(None, min_length=1, max_length=80)
    requested_moratorium_months: int | None = Field(None, ge=0)

    # Source
    source_channel: str | None = Field(None, max_length=50)
    source_reference: str | None = Field(None, max_length=100)

    # Status
    stage: ApplicationStage | None = None
    status: ApplicationStatus | None = None
    sub_status: str | None = Field(None, max_length=50)

    remarks: str | None = None
    extra_data: dict[str, Any] | None = None
    is_active: bool | None = None


class LoanApplicationResponse(LoanApplicationBase):
    """Schema for loan application response."""

    id: UUID
    application_number: str
    organization_id: UUID
    stage: ApplicationStage
    status: ApplicationStatus
    workflow_instance_id: UUID | None = None
    relationship_manager_id: UUID | None = None
    credit_officer_id: UUID | None = None
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


class LoanApplicationListResponse(CamelSchema):
    """Slim list response for loan applications (camelCase wire format).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    application_number: str
    entity_id: UUID
    entity_name: str | None = None
    product_id: UUID
    product_name: str | None = None
    requested_amount: Decimal
    requested_tenure_months: int
    stage: ApplicationStage
    status: ApplicationStatus
    priority: str
    submitted_at: datetime | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        entity = getattr(obj, "entity", None)
        product = getattr(obj, "product", None)
        return {
            "id": obj.id,
            "application_number": obj.application_number,
            "entity_id": obj.entity_id,
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "product_id": obj.product_id,
            "product_name": getattr(product, "name", None),
            "requested_amount": obj.requested_amount,
            "requested_tenure_months": obj.requested_tenure_months,
            "stage": obj.stage,
            "status": obj.status,
            "priority": getattr(obj, "priority", None) or "NORMAL",
            "submitted_at": getattr(obj, "submitted_at", None)
            or getattr(obj, "submission_date", None),
            "created_at": obj.created_at,
        }


class LoanApplicationDetailResponse(LoanApplicationResponse):
    """Schema for detailed loan application response with related data."""

    documents: list[ApplicationDocumentResponse] = []
    fees: list[ApplicationFeeResponse] = []
    technical_appraisals: list[TechnicalAppraisalResponse] = []
    financial_analyses: list[FinancialAnalysisResponse] = []
    milestones: list[ProjectMilestoneResponse] = []


class LoanApplicationViewResponse(CamelSchema):
    """Slim detail response for the application view page (camelCase wire).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    application_number: str
    stage: ApplicationStage
    status: ApplicationStatus
    priority: str = "NORMAL"
    requested_amount: Decimal
    requested_tenure_months: int
    purpose: str | None = None
    project_name: str | None = None
    project_cost: Decimal | None = None
    promoter_contribution: Decimal | None = None
    entity_id: UUID
    entity_name: str | None = None
    entity_legal_name: str | None = None
    entity_code: str | None = None
    entity_pan: str | None = None
    entity_type: str | None = None
    product_id: UUID
    product_name: str | None = None
    product_code: str | None = None
    product_category: str | None = None
    relationship_manager_id: UUID | None = None
    credit_officer_id: UUID | None = None
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        entity = getattr(obj, "entity", None)
        product = getattr(obj, "product", None)
        return {
            "id": obj.id,
            "application_number": obj.application_number,
            "stage": obj.stage,
            "status": obj.status,
            "priority": getattr(obj, "priority", None) or "NORMAL",
            "requested_amount": obj.requested_amount,
            "requested_tenure_months": obj.requested_tenure_months,
            "purpose": getattr(obj, "purpose", None),
            "project_name": getattr(obj, "project_name", None),
            "project_cost": getattr(obj, "project_cost", None),
            "promoter_contribution": getattr(obj, "promoter_contribution", None),
            "entity_id": obj.entity_id,
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "entity_legal_name": getattr(entity, "legal_name", None),
            "entity_code": getattr(entity, "entity_code", None),
            "entity_pan": getattr(entity, "pan", None),
            "entity_type": (
                getattr(entity, "entity_type", None).value
                if getattr(entity, "entity_type", None) is not None
                and hasattr(entity.entity_type, "value")
                else getattr(entity, "entity_type", None)
            ),
            "product_id": obj.product_id,
            "product_name": getattr(product, "name", None),
            "product_code": getattr(product, "code", None),
            "product_category": (
                getattr(product, "category", None).value
                if getattr(product, "category", None) is not None
                and hasattr(product.category, "value")
                else getattr(product, "category", None)
            ),
            "relationship_manager_id": getattr(obj, "relationship_manager_id", None),
            "credit_officer_id": getattr(obj, "credit_officer_id", None),
            "submitted_at": getattr(obj, "submitted_at", None)
            or getattr(obj, "submission_date", None),
            "created_at": obj.created_at,
            "updated_at": getattr(obj, "updated_at", None),
        }
