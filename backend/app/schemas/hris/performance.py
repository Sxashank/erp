"""Schemas for HRIS performance management."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema

AppraisalCycleStatus = Literal[
    "DRAFT",
    "GOAL_SETTING",
    "IN_PROGRESS",
    "REVIEW",
    "CALIBRATION",
    "COMPLETED",
    "CANCELLED",
]
GoalStatus = Literal[
    "DRAFT",
    "SUBMITTED",
    "APPROVED",
    "IN_PROGRESS",
    "COMPLETED",
    "DEFERRED",
]
AppraisalStatus = Literal[
    "NOT_STARTED",
    "GOAL_SETTING",
    "SELF_APPRAISAL",
    "MANAGER_REVIEW",
    "CALIBRATION",
    "COMPLETED",
    "CANCELLED",
]
AppraisalCycleType = Literal["ANNUAL", "HALF_YEARLY", "QUARTERLY"]


class AppraisalCycleBase(CamelSchema):
    """Base cycle payload."""

    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    financial_year_id: Optional[UUID] = None
    cycle_type: AppraisalCycleType = "ANNUAL"
    start_date: date
    end_date: date
    goal_setting_start: Optional[date] = None
    goal_setting_end: Optional[date] = None
    self_appraisal_start: Optional[date] = None
    self_appraisal_end: Optional[date] = None
    manager_review_start: Optional[date] = None
    manager_review_end: Optional[date] = None
    calibration_start: Optional[date] = None
    calibration_end: Optional[date] = None
    rating_scale: int = Field(5, ge=3, le=10)
    weightage_goals: Decimal = Field(Decimal("70"), ge=0, le=100)
    weightage_competencies: Decimal = Field(Decimal("30"), ge=0, le=100)
    allow_self_rating: bool = True
    allow_peer_feedback: bool = False


class AppraisalCycleCreate(AppraisalCycleBase):
    """Create cycle payload."""

    include_all_active_employees: bool = True
    employee_ids: list[UUID] = Field(default_factory=list)


class AppraisalCycleUpdate(CamelSchema):
    """Update cycle payload."""

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    cycle_type: Optional[AppraisalCycleType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    goal_setting_start: Optional[date] = None
    goal_setting_end: Optional[date] = None
    self_appraisal_start: Optional[date] = None
    self_appraisal_end: Optional[date] = None
    manager_review_start: Optional[date] = None
    manager_review_end: Optional[date] = None
    calibration_start: Optional[date] = None
    calibration_end: Optional[date] = None
    rating_scale: Optional[int] = Field(None, ge=3, le=10)
    weightage_goals: Optional[Decimal] = Field(None, ge=0, le=100)
    weightage_competencies: Optional[Decimal] = Field(None, ge=0, le=100)
    allow_self_rating: Optional[bool] = None
    allow_peer_feedback: Optional[bool] = None


class AppraisalCycleResponse(AppraisalCycleBase):
    """Cycle detail response."""

    id: UUID
    organization_id: UUID
    code: str
    status: AppraisalCycleStatus
    eligible_employees: int
    completed_appraisals: int
    pending_self_appraisal: int
    pending_manager_review: int


class AppraisalCycleListResponse(CamelSchema):
    """Cycle list row."""

    id: UUID
    code: str
    name: str
    financial_year: Optional[str] = None
    cycle_type: AppraisalCycleType
    start_date: date
    end_date: date
    goal_setting_end: Optional[date] = None
    self_appraisal_end: Optional[date] = None
    manager_review_end: Optional[date] = None
    status: AppraisalCycleStatus
    eligible_employees: int
    completed_appraisals: int
    pending_self_appraisal: int
    pending_manager_review: int


class AppraisalCycleSummaryResponse(CamelSchema):
    """Cycle summary cards."""

    total_cycles: int
    active: int
    completed: int
    draft: int
    employees_appraised: int


class AppraisalCycleListBundleResponse(CamelSchema):
    """Cycle list bundle."""

    items: list[AppraisalCycleListResponse]
    total: int
    skip: int
    limit: int
    summary: AppraisalCycleSummaryResponse


class PerformanceEmployeeSummaryResponse(CamelSchema):
    """Employee row in cycle performance queue."""

    appraisal_id: UUID
    employee_id: UUID
    employee_code: str
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    reviewer_name: Optional[str] = None
    status: AppraisalStatus
    goal_count: int
    submitted_goals: int
    completed_goals: int
    overall_rating: Optional[float] = None
    final_grade: Optional[str] = None
    self_appraisal_date: Optional[datetime] = None
    manager_review_date: Optional[datetime] = None
    calibrated_at: Optional[datetime] = None


class PerformanceGoalBase(CamelSchema):
    """Base goal payload."""

    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    weightage: Decimal = Field(..., gt=0, le=100)
    target_value: Optional[str] = Field(None, max_length=255)
    measurement_criteria: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None


class PerformanceGoalCreate(PerformanceGoalBase):
    """Create goal payload."""


class PerformanceGoalUpdate(CamelSchema):
    """Update goal payload."""

    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    weightage: Optional[Decimal] = Field(None, gt=0, le=100)
    target_value: Optional[str] = Field(None, max_length=255)
    measurement_criteria: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    progress_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    achievement_value: Optional[str] = Field(None, max_length=255)


class PerformanceGoalResponse(PerformanceGoalBase):
    """Goal detail response."""

    id: UUID
    employee_id: UUID
    goal_number: int
    status: GoalStatus
    progress_percent: float
    achievement_value: Optional[str] = None
    self_rating: Optional[float] = None
    self_comments: Optional[str] = None
    manager_rating: Optional[float] = None
    manager_comments: Optional[str] = None
    final_rating: Optional[float] = None
    approved_at: Optional[datetime] = None


class PerformanceGoalSelfAssessment(CamelSchema):
    """Employee self-assessment against a goal."""

    goal_id: UUID
    self_rating: float = Field(..., ge=1, le=5)
    self_progress: float = Field(..., ge=0, le=100)
    self_comments: str = Field(..., min_length=10)
    achievement_value: Optional[str] = Field(None, max_length=255)


class PerformanceSelfAppraisalSubmit(CamelSchema):
    """Employee self-appraisal submission payload."""

    goals: list[PerformanceGoalSelfAssessment] = Field(..., min_length=1)
    competency_rating: float = Field(..., ge=1, le=5)
    self_summary: str = Field(..., min_length=20)
    self_achievements: str = Field(..., min_length=20)
    self_challenges: Optional[str] = None
    self_development_areas: str = Field(..., min_length=10)
    employee_comments: Optional[str] = None


class PerformanceManagerGoalReview(CamelSchema):
    """Manager review against a goal."""

    goal_id: UUID
    manager_rating: float = Field(..., ge=1, le=5)
    manager_comments: str = Field(..., min_length=10)
    final_rating: Optional[float] = Field(None, ge=1, le=5)


class PerformanceManagerReviewSubmit(CamelSchema):
    """Manager review payload."""

    goals: list[PerformanceManagerGoalReview] = Field(..., min_length=1)
    competency_rating: float = Field(..., ge=1, le=5)
    manager_summary: str = Field(..., min_length=20)
    manager_achievements: Optional[str] = None
    manager_improvements: str = Field(..., min_length=10)
    manager_recommendations: Optional[str] = None


class PerformanceCalibrationSubmit(CamelSchema):
    """HR calibration payload."""

    calibrated_rating: float = Field(..., ge=1, le=5)
    calibration_notes: Optional[str] = None
    final_grade: Optional[str] = Field(None, max_length=10)


class EmployeeAppraisalResponse(CamelSchema):
    """Appraisal detail response."""

    id: UUID
    appraisal_cycle_id: UUID
    employee_id: UUID
    reviewer_id: Optional[UUID] = None
    status: AppraisalStatus
    goal_rating: Optional[float] = None
    competency_rating: Optional[float] = None
    overall_rating: Optional[float] = None
    final_grade: Optional[str] = None
    self_appraisal_date: Optional[datetime] = None
    self_summary: Optional[str] = None
    self_achievements: Optional[str] = None
    self_challenges: Optional[str] = None
    self_development_areas: Optional[str] = None
    manager_review_date: Optional[datetime] = None
    manager_summary: Optional[str] = None
    manager_achievements: Optional[str] = None
    manager_improvements: Optional[str] = None
    manager_recommendations: Optional[str] = None
    calibration_notes: Optional[str] = None
    calibrated_rating: Optional[float] = None
    calibrated_grade: Optional[str] = None
    calibrated_by: Optional[UUID] = None
    calibrated_at: Optional[datetime] = None
    employee_acknowledgment: bool
    acknowledgment_date: Optional[datetime] = None
    employee_comments: Optional[str] = None


class EmployeePerformanceDetailResponse(CamelSchema):
    """Complete cycle/employee appraisal payload."""

    cycle: AppraisalCycleResponse
    employee: PerformanceEmployeeSummaryResponse
    appraisal: EmployeeAppraisalResponse
    goals: list[PerformanceGoalResponse]
