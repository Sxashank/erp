"""Credit Rating schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    RiskCategoryType,
    RatingGrade,
    RatingType,
    RatingStatus,
)


# =============================================================================
# Risk Category Schemas
# =============================================================================


class RiskCategoryBase(BaseSchema):
    """Base schema for risk category."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_type: RiskCategoryType
    weightage: Decimal = Field(..., ge=0, le=100, description="Weightage in total score")
    max_score: Decimal = Field(default=Decimal("100"), ge=0)
    display_order: int = Field(default=0, ge=0)


class RiskCategoryCreate(RiskCategoryBase):
    """Schema for creating risk category."""

    organization_id: UUID


class RiskCategoryUpdate(BaseSchema):
    """Schema for updating risk category."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_type: Optional[RiskCategoryType] = None
    weightage: Optional[Decimal] = Field(None, ge=0, le=100)
    max_score: Optional[Decimal] = Field(None, ge=0)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RiskCategoryResponse(RiskCategoryBase):
    """Schema for risk category response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Risk Parameter Schemas
# =============================================================================


class RiskParameterBase(BaseSchema):
    """Base schema for risk parameter."""

    risk_category_id: UUID
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    weightage: Decimal = Field(..., ge=0, le=100, description="Weightage within category")
    max_score: Decimal = Field(default=Decimal("100"), ge=0)
    score_type: str = Field(default="NUMERIC", max_length=20, description="NUMERIC/QUALITATIVE/BOOLEAN")
    scoring_criteria: Optional[Dict[str, Any]] = Field(
        None,
        description="Scoring logic: {ranges: [{min: 0, max: 1, score: 50}, ...]} or {options: [{value: 'Good', score: 80}]}"
    )
    display_order: int = Field(default=0, ge=0)


class RiskParameterCreate(RiskParameterBase):
    """Schema for creating risk parameter."""

    pass


class RiskParameterUpdate(BaseSchema):
    """Schema for updating risk parameter."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    weightage: Optional[Decimal] = Field(None, ge=0, le=100)
    max_score: Optional[Decimal] = Field(None, ge=0)
    score_type: Optional[str] = Field(None, max_length=20)
    scoring_criteria: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RiskParameterResponse(RiskParameterBase):
    """Schema for risk parameter response."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Rating Matrix Schemas
# =============================================================================


class RatingMatrixBase(BaseSchema):
    """Base schema for rating matrix."""

    grade: RatingGrade
    min_score: Decimal = Field(..., ge=0)
    max_score: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=500)
    risk_weight: Optional[Decimal] = Field(None, ge=0, le=100, description="RBI risk weight percentage")
    default_probability: Optional[Decimal] = Field(None, ge=0, le=100)
    pricing_spread_bps: Optional[int] = Field(None, ge=0, description="Additional spread in basis points")
    max_exposure_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    requires_enhanced_monitoring: bool = False


class RatingMatrixCreate(RatingMatrixBase):
    """Schema for creating rating matrix."""

    organization_id: UUID


class RatingMatrixUpdate(BaseSchema):
    """Schema for updating rating matrix."""

    min_score: Optional[Decimal] = Field(None, ge=0)
    max_score: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    risk_weight: Optional[Decimal] = Field(None, ge=0, le=100)
    default_probability: Optional[Decimal] = Field(None, ge=0, le=100)
    pricing_spread_bps: Optional[int] = Field(None, ge=0)
    max_exposure_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    requires_enhanced_monitoring: Optional[bool] = None
    is_active: Optional[bool] = None


class RatingMatrixResponse(RatingMatrixBase):
    """Schema for rating matrix response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Rating Score Detail Schemas
# =============================================================================


class RatingScoreDetailCreate(BaseSchema):
    """Schema for creating rating score detail."""

    parameter_id: UUID
    raw_value: Optional[str] = Field(None, max_length=200)
    score: Decimal = Field(..., ge=0)
    weighted_score: Decimal = Field(..., ge=0)
    remarks: Optional[str] = None


class RatingScoreDetailResponse(BaseSchema):
    """Schema for rating score detail response."""

    id: UUID
    entity_rating_id: UUID
    parameter_id: UUID
    raw_value: Optional[str] = None
    score: Decimal
    weighted_score: Decimal
    remarks: Optional[str] = None
    created_at: datetime


# =============================================================================
# Entity Rating Schemas
# =============================================================================


class EntityRatingBase(BaseSchema):
    """Base schema for entity rating."""

    rating_type: RatingType
    rating_as_of_date: date = Field(..., description="Date as of which rating is computed")
    financial_year: Optional[str] = Field(None, max_length=7)

    # Scores
    total_score: Decimal = Field(default=Decimal("0"), ge=0)
    proposed_grade: Optional[RatingGrade] = None

    # Approval
    approved_grade: Optional[RatingGrade] = None
    grade_override_reason: Optional[str] = None
    valid_from: Optional[date] = None
    valid_till: Optional[date] = None

    # Remarks
    analyst_remarks: Optional[str] = None
    approver_remarks: Optional[str] = None


class EntityRatingCreate(EntityRatingBase):
    """Schema for creating entity rating."""

    entity_id: UUID
    score_details: List[RatingScoreDetailCreate] = []


class EntityRatingUpdate(BaseSchema):
    """Schema for updating entity rating."""

    rating_type: Optional[RatingType] = None
    rating_as_of_date: Optional[date] = None
    financial_year: Optional[str] = Field(None, max_length=7)
    total_score: Optional[Decimal] = Field(None, ge=0)
    proposed_grade: Optional[RatingGrade] = None
    approved_grade: Optional[RatingGrade] = None
    grade_override_reason: Optional[str] = None
    valid_from: Optional[date] = None
    valid_till: Optional[date] = None
    status: Optional[RatingStatus] = None
    analyst_remarks: Optional[str] = None
    approver_remarks: Optional[str] = None
    is_active: Optional[bool] = None


class EntityRatingResponse(EntityRatingBase):
    """Schema for entity rating response."""

    id: UUID
    entity_id: UUID
    rating_reference_number: Optional[str] = None
    status: RatingStatus
    workflow_instance_id: Optional[UUID] = None
    initiated_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class EntityRatingDetailResponse(EntityRatingResponse):
    """Schema for detailed entity rating response with score details."""

    score_details: List[RatingScoreDetailResponse] = []
