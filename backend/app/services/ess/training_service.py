"""Employee self-service training queries."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.hris.training import TrainingFeedback, TrainingNomination, TrainingProgram
from app.schemas.ess.operations import (
    ESSTrainingDetailResponse,
    ESSTrainingFeedbackDetail,
    ESSTrainingListResponse,
    ESSTrainingProgramSummary,
    ESSTrainingSummaryResponse,
)


class ESSTrainingService:
    """Read-only employee training views."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_employee_training(self, employee_id: UUID) -> ESSTrainingListResponse:
        result = await self.db.execute(
            select(TrainingNomination)
            .where(
                TrainingNomination.employee_id == employee_id,
                TrainingNomination.deleted_at.is_(None),
            )
            .options(
                selectinload(TrainingNomination.program),
                selectinload(TrainingNomination.employee),
            )
            .order_by(TrainingNomination.created_at.desc())
        )
        nominations = list(result.scalars().all())

        feedback_result = await self.db.execute(
            select(TrainingFeedback).where(
                TrainingFeedback.employee_id == employee_id,
                TrainingFeedback.deleted_at.is_(None),
            )
        )
        feedback_by_program = {
            feedback.program_id: feedback for feedback in feedback_result.scalars().all()
        }
        items = [
            ESSTrainingProgramSummary(
                program_id=nomination.program.id,
                program_code=nomination.program.program_code,
                title=nomination.program.title,
                category=nomination.program.category,
                mode=nomination.program.mode,
                trainer_name=nomination.program.trainer_name,
                start_date=nomination.program.start_date,
                end_date=nomination.program.end_date,
                duration_hours=float(nomination.program.duration_hours),
                location=nomination.program.location,
                status=nomination.program.status,
                nomination_status=nomination.status,
                attendance_marked=nomination.attendance_marked,
                feedback_submitted=nomination.program_id in feedback_by_program,
                certificate_provided=nomination.program.certificate_provided,
            )
            for nomination in nominations
        ]
        total_hours = float(
            sum(
                (
                    nomination.program.duration_hours
                    for nomination in nominations
                    if nomination.status in {"ATTENDED", "CONFIRMED"}
                ),
                Decimal("0"),
            )
        )
        summary = ESSTrainingSummaryResponse(
            completed_programs=sum(1 for item in items if item.nomination_status == "ATTENDED"),
            upcoming_programs=sum(
                1 for item in items if item.nomination_status in {"NOMINATED", "CONFIRMED"}
            ),
            mandatory_programs=sum(1 for item in items if item.certificate_provided),
            feedback_pending=sum(
                1
                for item in items
                if item.nomination_status == "ATTENDED" and not item.feedback_submitted
            ),
            total_hours_completed=total_hours,
        )
        return ESSTrainingListResponse(summary=summary, items=items)

    async def get_training_detail(
        self, employee_id: UUID, program_id: UUID
    ) -> ESSTrainingDetailResponse:
        result = await self.db.execute(
            select(TrainingNomination)
            .where(
                TrainingNomination.employee_id == employee_id,
                TrainingNomination.program_id == program_id,
                TrainingNomination.deleted_at.is_(None),
            )
            .options(selectinload(TrainingNomination.program))
        )
        nomination = result.scalar_one_or_none()
        if not nomination:
            raise NotFoundException(
                detail="Training nomination not found",
                error_code="TRAINING_NOMINATION_NOT_FOUND",
            )
        feedback_result = await self.db.execute(
            select(TrainingFeedback).where(
                TrainingFeedback.employee_id == employee_id,
                TrainingFeedback.program_id == program_id,
                TrainingFeedback.deleted_at.is_(None),
            )
        )
        feedback = feedback_result.scalar_one_or_none()
        return ESSTrainingDetailResponse(
            program_id=nomination.program.id,
            program_code=nomination.program.program_code,
            title=nomination.program.title,
            description=nomination.program.description,
            category=nomination.program.category,
            mode=nomination.program.mode,
            trainer_type=nomination.program.trainer_type,
            trainer_name=nomination.program.trainer_name,
            trainer_contact=nomination.program.trainer_contact,
            start_date=nomination.program.start_date,
            end_date=nomination.program.end_date,
            duration_hours=float(nomination.program.duration_hours),
            location=nomination.program.location,
            is_mandatory=nomination.program.is_mandatory,
            certificate_provided=nomination.program.certificate_provided,
            nomination_status=nomination.status,
            attendance_marked=nomination.attendance_marked,
            feedback=(
                ESSTrainingFeedbackDetail(
                    id=feedback.id,
                    overall_rating=float(feedback.overall_rating),
                    content_rating=float(feedback.content_rating),
                    trainer_rating=float(feedback.trainer_rating),
                    facilities_rating=float(feedback.facilities_rating),
                    relevance_rating=float(feedback.relevance_rating),
                    would_recommend=feedback.would_recommend,
                    strengths=feedback.strengths,
                    improvements=feedback.improvements,
                    comments=feedback.comments,
                    submitted_on=feedback.submitted_on,
                )
                if feedback
                else None
            ),
        )
