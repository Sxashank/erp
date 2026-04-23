"""Loan Application schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    ApplicationStage,
    ApplicationStatus,
    AppraisalType,
    TechnicalFeasibility,
    AppraisalRecommendation,
    MilestoneStatus,
    InterestType,
    RepaymentMode,
    RepaymentFrequency,
)


# =============================================================================
# Application Document Schemas
# =============================================================================


class ApplicationDocumentBase(BaseSchema):
    """Base schema for application document."""

    checklist_id: Optional[UUID] = None
    document_name: str = Field(..., min_length=1, max_length=200)
    document_category: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=200)
    file_size_kb: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    is_verified: bool = False
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    expiry_date: Optional[date] = None


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Schema for creating application document."""

    application_id: UUID


class ApplicationDocumentUpdate(BaseSchema):
    """Schema for updating application document."""

    document_name: Optional[str] = Field(None, min_length=1, max_length=200)
    document_category: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=200)
    file_size_kb: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    is_verified: Optional[bool] = None
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    expiry_date: Optional[date] = None
    is_active: Optional[bool] = None


class ApplicationDocumentResponse(ApplicationDocumentBase):
    """Schema for application document response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Application Fee Schemas
# =============================================================================


class ApplicationFeeBase(BaseSchema):
    """Base schema for application fee."""

    fee_master_id: UUID
    fee_name: str = Field(..., min_length=1, max_length=200)
    calculated_amount: Decimal = Field(..., ge=0)
    waiver_amount: Decimal = Field(default=Decimal("0"), ge=0)
    final_amount: Decimal = Field(..., ge=0)
    gst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    collection_stage: Optional[str] = Field(None, max_length=30)
    collected_amount: Decimal = Field(default=Decimal("0"), ge=0)
    is_collected: bool = False
    collected_date: Optional[date] = None
    waiver_approved_by_id: Optional[UUID] = None
    waiver_remarks: Optional[str] = None


class ApplicationFeeCreate(ApplicationFeeBase):
    """Schema for creating application fee."""

    application_id: UUID


class ApplicationFeeUpdate(BaseSchema):
    """Schema for updating application fee."""

    waiver_amount: Optional[Decimal] = Field(None, ge=0)
    final_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    collected_amount: Optional[Decimal] = Field(None, ge=0)
    is_collected: Optional[bool] = None
    collected_date: Optional[date] = None
    waiver_approved_by_id: Optional[UUID] = None
    waiver_remarks: Optional[str] = None
    is_active: Optional[bool] = None


class ApplicationFeeResponse(ApplicationFeeBase):
    """Schema for application fee response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Technical Appraisal Schemas
# =============================================================================


class TechnicalAppraisalBase(BaseSchema):
    """Base schema for technical appraisal."""

    appraisal_type: AppraisalType = AppraisalType.TECHNICAL
    appraisal_date: date
    appraiser_name: Optional[str] = Field(None, max_length=200)
    appraiser_agency: Optional[str] = Field(None, max_length=200)

    # Project Details
    project_description: Optional[str] = None
    project_location: Optional[str] = Field(None, max_length=500)
    project_area_sqft: Optional[Decimal] = Field(None, ge=0)
    construction_type: Optional[str] = Field(None, max_length=100)

    # Cost Details
    land_cost: Optional[Decimal] = Field(None, ge=0)
    construction_cost: Optional[Decimal] = Field(None, ge=0)
    plant_machinery_cost: Optional[Decimal] = Field(None, ge=0)
    other_costs: Optional[Decimal] = Field(None, ge=0)
    total_project_cost: Optional[Decimal] = Field(None, ge=0)
    contingency: Optional[Decimal] = Field(None, ge=0)

    # Progress
    current_completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_completion_date: Optional[date] = None

    # Assessment
    feasibility: TechnicalFeasibility = TechnicalFeasibility.FEASIBLE
    recommendation: AppraisalRecommendation = AppraisalRecommendation.PROCEED
    observations: Optional[str] = None
    conditions: Optional[str] = None

    # Valuation
    valuation_amount: Optional[Decimal] = Field(None, ge=0)
    forced_sale_value: Optional[Decimal] = Field(None, ge=0)


class TechnicalAppraisalCreate(TechnicalAppraisalBase):
    """Schema for creating technical appraisal."""

    application_id: UUID
    appraised_by_id: Optional[UUID] = None


class TechnicalAppraisalUpdate(BaseSchema):
    """Schema for updating technical appraisal."""

    appraisal_type: Optional[AppraisalType] = None
    appraisal_date: Optional[date] = None
    appraiser_name: Optional[str] = Field(None, max_length=200)
    appraiser_agency: Optional[str] = Field(None, max_length=200)

    project_description: Optional[str] = None
    project_location: Optional[str] = Field(None, max_length=500)
    project_area_sqft: Optional[Decimal] = Field(None, ge=0)
    construction_type: Optional[str] = Field(None, max_length=100)

    land_cost: Optional[Decimal] = Field(None, ge=0)
    construction_cost: Optional[Decimal] = Field(None, ge=0)
    plant_machinery_cost: Optional[Decimal] = Field(None, ge=0)
    other_costs: Optional[Decimal] = Field(None, ge=0)
    total_project_cost: Optional[Decimal] = Field(None, ge=0)
    contingency: Optional[Decimal] = Field(None, ge=0)

    current_completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_completion_date: Optional[date] = None

    feasibility: Optional[TechnicalFeasibility] = None
    recommendation: Optional[AppraisalRecommendation] = None
    observations: Optional[str] = None
    conditions: Optional[str] = None

    valuation_amount: Optional[Decimal] = Field(None, ge=0)
    forced_sale_value: Optional[Decimal] = Field(None, ge=0)

    is_active: Optional[bool] = None


class TechnicalAppraisalResponse(TechnicalAppraisalBase):
    """Schema for technical appraisal response."""

    id: UUID
    application_id: UUID
    appraised_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Financial Analysis Schemas
# =============================================================================


class FinancialAnalysisBase(BaseSchema):
    """Base schema for financial analysis."""

    analysis_date: date
    financial_year_analyzed: str = Field(..., max_length=7)

    # Project Financials
    total_project_cost: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    debt_required: Optional[Decimal] = Field(None, ge=0)
    proposed_loan_amount: Optional[Decimal] = Field(None, ge=0)

    # Projected Financials
    projected_revenue_y1: Optional[Decimal] = None
    projected_revenue_y2: Optional[Decimal] = None
    projected_revenue_y3: Optional[Decimal] = None
    projected_ebitda_y1: Optional[Decimal] = None
    projected_ebitda_y2: Optional[Decimal] = None
    projected_ebitda_y3: Optional[Decimal] = None
    projected_pat_y1: Optional[Decimal] = None
    projected_pat_y2: Optional[Decimal] = None
    projected_pat_y3: Optional[Decimal] = None

    # Key Ratios
    current_ratio: Optional[Decimal] = None
    debt_equity_ratio: Optional[Decimal] = None
    interest_coverage_ratio: Optional[Decimal] = None
    dscr_average: Optional[Decimal] = None
    dscr_minimum: Optional[Decimal] = None
    roce: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    break_even_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    # Assessment
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    recommendation: AppraisalRecommendation = AppraisalRecommendation.PROCEED
    observations: Optional[str] = None
    conditions: Optional[str] = None


class FinancialAnalysisCreate(FinancialAnalysisBase):
    """Schema for creating financial analysis."""

    application_id: UUID
    analyzed_by_id: Optional[UUID] = None


class FinancialAnalysisUpdate(BaseSchema):
    """Schema for updating financial analysis."""

    analysis_date: Optional[date] = None
    financial_year_analyzed: Optional[str] = Field(None, max_length=7)

    total_project_cost: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    debt_required: Optional[Decimal] = Field(None, ge=0)
    proposed_loan_amount: Optional[Decimal] = Field(None, ge=0)

    projected_revenue_y1: Optional[Decimal] = None
    projected_revenue_y2: Optional[Decimal] = None
    projected_revenue_y3: Optional[Decimal] = None
    projected_ebitda_y1: Optional[Decimal] = None
    projected_ebitda_y2: Optional[Decimal] = None
    projected_ebitda_y3: Optional[Decimal] = None
    projected_pat_y1: Optional[Decimal] = None
    projected_pat_y2: Optional[Decimal] = None
    projected_pat_y3: Optional[Decimal] = None

    current_ratio: Optional[Decimal] = None
    debt_equity_ratio: Optional[Decimal] = None
    interest_coverage_ratio: Optional[Decimal] = None
    dscr_average: Optional[Decimal] = None
    dscr_minimum: Optional[Decimal] = None
    roce: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    break_even_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    sensitivity_analysis: Optional[Dict[str, Any]] = None
    recommendation: Optional[AppraisalRecommendation] = None
    observations: Optional[str] = None
    conditions: Optional[str] = None

    is_active: Optional[bool] = None


class FinancialAnalysisResponse(FinancialAnalysisBase):
    """Schema for financial analysis response."""

    id: UUID
    application_id: UUID
    analyzed_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Project Milestone Schemas
# =============================================================================


class ProjectMilestoneBase(BaseSchema):
    """Base schema for project milestone."""

    milestone_number: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    expected_completion_date: date
    actual_completion_date: Optional[date] = None
    completion_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    disbursement_percentage: Decimal = Field(..., ge=0, le=100)
    disbursement_amount: Optional[Decimal] = Field(None, ge=0)
    status: MilestoneStatus = MilestoneStatus.PENDING
    verification_required: bool = True
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None


class ProjectMilestoneCreate(ProjectMilestoneBase):
    """Schema for creating project milestone."""

    application_id: UUID


class ProjectMilestoneUpdate(BaseSchema):
    """Schema for updating project milestone."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    disbursement_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    disbursement_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[MilestoneStatus] = None
    verification_required: Optional[bool] = None
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectMilestoneResponse(ProjectMilestoneBase):
    """Schema for project milestone response."""

    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Loan Application Schemas
# =============================================================================


class LoanApplicationBase(BaseSchema):
    """Base schema for loan application."""

    entity_id: UUID
    product_id: UUID

    # Loan Request
    requested_amount: Decimal = Field(..., ge=0)
    requested_tenure_months: int = Field(..., ge=1)
    purpose: str = Field(..., min_length=1, max_length=500)
    detailed_purpose: Optional[str] = None

    # Project Details (for project finance)
    is_project_finance: bool = False
    project_name: Optional[str] = Field(None, max_length=200)
    project_cost: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    bank_finance: Optional[Decimal] = Field(None, ge=0)
    other_finance: Optional[Decimal] = Field(None, ge=0)
    project_location: Optional[str] = Field(None, max_length=500)
    project_start_date: Optional[date] = None
    project_completion_date: Optional[date] = None

    # Preferred Terms
    preferred_interest_type: InterestType = InterestType.FLOATING
    preferred_repayment_frequency: RepaymentFrequency = RepaymentFrequency.MONTHLY
    preferred_repayment_mode: RepaymentMode = RepaymentMode.EMI
    requested_moratorium_months: int = Field(default=0, ge=0)

    # Source
    source_channel: str = Field(default="DIRECT", max_length=50)
    source_reference: Optional[str] = Field(None, max_length=100)

    # Metadata
    remarks: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class LoanApplicationCreate(LoanApplicationBase):
    """Schema for creating loan application."""

    organization_id: UUID


class LoanApplicationUpdate(BaseSchema):
    """Schema for updating loan application."""

    requested_amount: Optional[Decimal] = Field(None, ge=0)
    requested_tenure_months: Optional[int] = Field(None, ge=1)
    purpose: Optional[str] = Field(None, min_length=1, max_length=500)
    detailed_purpose: Optional[str] = None

    # Project Details
    is_project_finance: Optional[bool] = None
    project_name: Optional[str] = Field(None, max_length=200)
    project_cost: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution: Optional[Decimal] = Field(None, ge=0)
    promoter_contribution_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    bank_finance: Optional[Decimal] = Field(None, ge=0)
    other_finance: Optional[Decimal] = Field(None, ge=0)
    project_location: Optional[str] = Field(None, max_length=500)
    project_start_date: Optional[date] = None
    project_completion_date: Optional[date] = None

    # Preferred Terms
    preferred_interest_type: Optional[InterestType] = None
    preferred_repayment_frequency: Optional[RepaymentFrequency] = None
    preferred_repayment_mode: Optional[RepaymentMode] = None
    requested_moratorium_months: Optional[int] = Field(None, ge=0)

    # Source
    source_channel: Optional[str] = Field(None, max_length=50)
    source_reference: Optional[str] = Field(None, max_length=100)

    # Status
    stage: Optional[ApplicationStage] = None
    status: Optional[ApplicationStatus] = None
    sub_status: Optional[str] = Field(None, max_length=50)

    remarks: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LoanApplicationResponse(LoanApplicationBase):
    """Schema for loan application response."""

    id: UUID
    application_number: str
    organization_id: UUID
    stage: ApplicationStage
    status: ApplicationStatus
    workflow_instance_id: Optional[UUID] = None
    relationship_manager_id: Optional[UUID] = None
    credit_officer_id: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class LoanApplicationListResponse(BaseSchema):
    """Schema for loan application list response (lightweight)."""

    id: UUID
    application_number: str
    entity_id: UUID
    product_id: UUID
    requested_amount: Decimal
    requested_tenure_months: int
    stage: ApplicationStage
    status: ApplicationStatus
    priority: str
    submitted_at: Optional[datetime] = None
    created_at: datetime


class LoanApplicationDetailResponse(LoanApplicationResponse):
    """Schema for detailed loan application response with related data."""

    documents: List[ApplicationDocumentResponse] = []
    fees: List[ApplicationFeeResponse] = []
    technical_appraisals: List[TechnicalAppraisalResponse] = []
    financial_analyses: List[FinancialAnalysisResponse] = []
    milestones: List[ProjectMilestoneResponse] = []
