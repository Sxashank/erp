"""Operational ESS schemas."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from app.schemas.base import CamelSchema
from app.schemas.hris.performance import EmployeePerformanceDetailResponse


class ESSAssetResponse(CamelSchema):
    """Employee-scoped fixed asset view."""

    id: UUID
    asset_code: str
    asset_name: str
    category: str
    status: str
    serial_number: Optional[str] = None
    assigned_date: date
    location: Optional[str] = None
    department: Optional[str] = None
    total_cost: float
    warranty_expiry_date: Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    return_required: bool = True


class ESSAssignedAssetsResponse(CamelSchema):
    """Asset list summary for ESS."""

    items: list[ESSAssetResponse]
    total_assets: int
    total_asset_value: float


class ESSTrainingProgramSummary(CamelSchema):
    """Training row in ESS."""

    program_id: UUID
    program_code: str
    title: str
    category: str
    mode: str
    trainer_name: str
    start_date: date
    end_date: date
    duration_hours: float
    location: str
    status: str
    nomination_status: str
    attendance_marked: bool
    feedback_submitted: bool
    certificate_provided: bool


class ESSTrainingSummaryResponse(CamelSchema):
    """ESS training summary cards."""

    completed_programs: int
    upcoming_programs: int
    mandatory_programs: int
    feedback_pending: int
    total_hours_completed: float


class ESSTrainingListResponse(CamelSchema):
    """ESS training list payload."""

    summary: ESSTrainingSummaryResponse
    items: list[ESSTrainingProgramSummary]


class ESSTrainingFeedbackDetail(CamelSchema):
    """Employee feedback detail."""

    id: UUID
    overall_rating: float
    content_rating: float
    trainer_rating: float
    facilities_rating: float
    relevance_rating: float
    would_recommend: bool
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    comments: Optional[str] = None
    submitted_on: date


class ESSTrainingDetailResponse(CamelSchema):
    """ESS training program detail."""

    program_id: UUID
    program_code: str
    title: str
    description: str
    category: str
    mode: str
    trainer_type: str
    trainer_name: str
    trainer_contact: Optional[str] = None
    start_date: date
    end_date: date
    duration_hours: float
    location: str
    is_mandatory: bool
    certificate_provided: bool
    nomination_status: str
    attendance_marked: bool
    feedback: Optional[ESSTrainingFeedbackDetail] = None


class ESSPerformanceGoalListResponse(CamelSchema):
    """ESS goals list payload."""

    appraisal: Optional[EmployeePerformanceDetailResponse] = None
