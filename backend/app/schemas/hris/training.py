"""Schemas for HRIS training programs, nominations, and feedback."""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema

TrainingProgramStatus = Literal[
    "DRAFT",
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
]
TrainingProgramMode = Literal[
    "CLASSROOM",
    "VIRTUAL",
    "E_LEARNING",
    "WORKSHOP",
    "ON_THE_JOB",
]
TrainingTrainerType = Literal["INTERNAL", "EXTERNAL"]
TrainingNominationStatus = Literal[
    "NOMINATED",
    "CONFIRMED",
    "ATTENDED",
    "NO_SHOW",
    "CANCELLED",
]


class TrainingProgramBase(CamelSchema):
    """Base schema for training program input."""

    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20)
    category: str = Field(..., min_length=1, max_length=100)
    mode: TrainingProgramMode
    trainer_type: TrainingTrainerType
    trainer_name: str = Field(..., min_length=2, max_length=200)
    trainer_contact: Optional[str] = Field(None, max_length=200)
    start_date: date
    end_date: date
    duration_hours: float = Field(..., ge=1)
    location: str = Field(..., min_length=1, max_length=255)
    max_participants: int = Field(..., ge=1)
    cost_per_participant: float = Field(0, ge=0)
    pre_requisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    is_mandatory: bool = False
    certificate_provided: bool = True
    status: Optional[TrainingProgramStatus] = None


class TrainingProgramCreate(TrainingProgramBase):
    """Schema for creating a training program."""

    organization_id: Optional[UUID] = None


class TrainingProgramUpdate(CamelSchema):
    """Schema for updating a training program."""

    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    mode: Optional[TrainingProgramMode] = None
    trainer_type: Optional[TrainingTrainerType] = None
    trainer_name: Optional[str] = Field(None, min_length=2, max_length=200)
    trainer_contact: Optional[str] = Field(None, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_hours: Optional[float] = Field(None, ge=1)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    max_participants: Optional[int] = Field(None, ge=1)
    cost_per_participant: Optional[float] = Field(None, ge=0)
    pre_requisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    is_mandatory: Optional[bool] = None
    certificate_provided: Optional[bool] = None
    status: Optional[TrainingProgramStatus] = None


class TrainingProgramFilters(CamelSchema):
    """Filters for listing training programs."""

    organization_id: Optional[UUID] = None
    category: Optional[str] = None
    mode: Optional[TrainingProgramMode] = None
    status: Optional[TrainingProgramStatus] = None
    search: Optional[str] = None


class TrainingProgramResponse(TrainingProgramBase):
    """Training program payload."""

    id: UUID
    organization_id: UUID
    program_code: str
    status: TrainingProgramStatus
    enrolled_count: int = 0


class TrainingProgramSummaryResponse(CamelSchema):
    """Summary counts for the training list view."""

    total_programs: int
    scheduled: int
    in_progress: int
    completed: int
    total_participants: int


class TrainingProgramListBundleResponse(CamelSchema):
    """Program list with summary metadata."""

    items: List[TrainingProgramResponse]
    total: int
    skip: int
    limit: int
    summary: TrainingProgramSummaryResponse


class TrainingNominationBulkCreate(CamelSchema):
    """Bulk nomination request."""

    employee_ids: List[UUID] = Field(..., min_length=1)


class TrainingNominationStatusUpdate(CamelSchema):
    """Update nomination status."""

    status: TrainingNominationStatus
    attendance_marked: Optional[bool] = None


class TrainingAvailableEmployeeResponse(CamelSchema):
    """Employee available for nomination."""

    id: UUID
    employee_code: str
    full_name: str
    department: str
    designation: str
    email: Optional[str] = None


class TrainingNominationResponse(CamelSchema):
    """Nomination row."""

    id: UUID
    employee_id: UUID
    employee_code: str
    employee_name: str
    department: str
    designation: str
    nominated_by: Optional[str] = None
    nominated_on: date
    status: TrainingNominationStatus
    attendance_marked: bool


class TrainingFeedbackBase(CamelSchema):
    """Base training feedback payload."""

    employee_id: UUID
    overall_rating: float = Field(..., ge=1, le=5)
    content_rating: float = Field(..., ge=1, le=5)
    trainer_rating: float = Field(..., ge=1, le=5)
    facilities_rating: float = Field(..., ge=1, le=5)
    relevance_rating: float = Field(..., ge=1, le=5)
    would_recommend: bool = True
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    comments: Optional[str] = None
    submitted_on: date


class TrainingFeedbackCreate(TrainingFeedbackBase):
    """Create or update manual feedback."""


class TrainingFeedbackResponse(TrainingFeedbackBase):
    """Individual feedback row."""

    id: UUID
    nomination_id: Optional[UUID] = None
    employee_name: str
    employee_code: str
    department: str


class TrainingFeedbackRatingSummary(CamelSchema):
    """Average rating for a category."""

    category: str
    rating: float
    max_rating: float = 5


class TrainingFeedbackDistributionItem(CamelSchema):
    """Rating distribution bucket."""

    stars: int
    count: int


class TrainingFeedbackSummaryResponse(CamelSchema):
    """Aggregated feedback summary."""

    total_participants: int
    feedback_received: int
    response_rate: float
    overall_rating: float
    ratings: List[TrainingFeedbackRatingSummary]
    rating_distribution: List[TrainingFeedbackDistributionItem]
    recommend_percentage: float


class TrainingFeedbackBundleResponse(CamelSchema):
    """Feedback page payload."""

    program: TrainingProgramResponse
    summary: TrainingFeedbackSummaryResponse
    individual_feedbacks: List[TrainingFeedbackResponse]
