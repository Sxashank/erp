"""Service layer for HRIS training programs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import EmploymentStatus
from app.core.exceptions import BadRequestException
from app.models.hris.employee import Employee
from app.models.hris.training import TrainingFeedback, TrainingNomination, TrainingProgram
from app.schemas.hris.training import (
    TrainingAvailableEmployeeResponse,
    TrainingFeedbackBundleResponse,
    TrainingFeedbackCreate,
    TrainingFeedbackDistributionItem,
    TrainingFeedbackRatingSummary,
    TrainingFeedbackResponse,
    TrainingFeedbackSummaryResponse,
    TrainingNominationResponse,
    TrainingProgramCreate,
    TrainingProgramFilters,
    TrainingProgramResponse,
    TrainingProgramSummaryResponse,
    TrainingProgramUpdate,
)


class TrainingService:
    """Business logic for HRIS training flows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_program_code(self, organization_id: UUID) -> str:
        result = await self.db.execute(
            select(func.count(TrainingProgram.id)).where(
                TrainingProgram.organization_id == organization_id
            )
        )
        count = result.scalar() or 0
        return f"TRN{count + 1:05d}"

    def _derive_status(
        self,
        start_date: date,
        end_date: date,
        explicit_status: Optional[str] = None,
    ) -> str:
        if explicit_status == "CANCELLED":
            return "CANCELLED"
        today = date.today()
        if explicit_status == "DRAFT":
            return "DRAFT"
        if end_date < today:
            return "COMPLETED"
        if start_date > today:
            return "SCHEDULED"
        return "IN_PROGRESS"

    def _program_response(self, program: TrainingProgram) -> TrainingProgramResponse:
        enrolled_count = sum(
            1 for nomination in program.nominations if nomination.status != "CANCELLED"
        )
        return TrainingProgramResponse(
            id=program.id,
            organization_id=program.organization_id,
            program_code=program.program_code,
            title=program.title,
            description=program.description,
            category=program.category,
            mode=program.mode,
            trainer_type=program.trainer_type,
            trainer_name=program.trainer_name,
            trainer_contact=program.trainer_contact,
            start_date=program.start_date,
            end_date=program.end_date,
            duration_hours=float(program.duration_hours),
            location=program.location,
            max_participants=program.max_participants,
            cost_per_participant=float(program.cost_per_participant),
            pre_requisites=program.pre_requisites,
            learning_objectives=program.learning_objectives,
            is_mandatory=program.is_mandatory,
            certificate_provided=program.certificate_provided,
            status=program.status,
            enrolled_count=enrolled_count,
        )

    def _nomination_response(self, nomination: TrainingNomination) -> TrainingNominationResponse:
        employee = nomination.employee
        return TrainingNominationResponse(
            id=nomination.id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.full_name,
            department=employee.department.department_name if employee.department else "-",
            designation=employee.designation.designation_name if employee.designation else "-",
            nominated_by=(
                nomination.nominated_by_user.full_name if nomination.nominated_by_user else None
            ),
            nominated_on=nomination.created_at.date(),
            status=nomination.status,
            attendance_marked=nomination.attendance_marked,
        )

    def _feedback_response(self, feedback: TrainingFeedback) -> TrainingFeedbackResponse:
        employee = feedback.employee
        return TrainingFeedbackResponse(
            id=feedback.id,
            nomination_id=feedback.nomination_id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.full_name,
            department=employee.department.department_name if employee.department else "-",
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

    def _feedback_summary(
        self,
        total_participants: int,
        feedback_rows: Sequence[TrainingFeedbackResponse],
    ) -> TrainingFeedbackSummaryResponse:
        feedback_received = len(feedback_rows)
        if feedback_received == 0:
            return TrainingFeedbackSummaryResponse(
                total_participants=total_participants,
                feedback_received=0,
                response_rate=0,
                overall_rating=0,
                ratings=[
                    TrainingFeedbackRatingSummary(category="Content", rating=0),
                    TrainingFeedbackRatingSummary(category="Trainer", rating=0),
                    TrainingFeedbackRatingSummary(category="Facilities", rating=0),
                    TrainingFeedbackRatingSummary(category="Relevance", rating=0),
                ],
                rating_distribution=[
                    TrainingFeedbackDistributionItem(stars=5, count=0),
                    TrainingFeedbackDistributionItem(stars=4, count=0),
                    TrainingFeedbackDistributionItem(stars=3, count=0),
                    TrainingFeedbackDistributionItem(stars=2, count=0),
                    TrainingFeedbackDistributionItem(stars=1, count=0),
                ],
                recommend_percentage=0,
            )

        overall_rating = sum(item.overall_rating for item in feedback_rows) / feedback_received
        rating_distribution_map = {stars: 0 for stars in range(1, 6)}
        for item in feedback_rows:
            stars = min(5, max(1, int(round(item.overall_rating))))
            rating_distribution_map[stars] += 1

        recommend_count = sum(1 for item in feedback_rows if item.would_recommend)
        response_rate = (
            round((feedback_received / total_participants) * 100, 2) if total_participants else 0
        )
        recommend_percentage = round((recommend_count / feedback_received) * 100, 2)

        return TrainingFeedbackSummaryResponse(
            total_participants=total_participants,
            feedback_received=feedback_received,
            response_rate=response_rate,
            overall_rating=round(overall_rating, 2),
            ratings=[
                TrainingFeedbackRatingSummary(
                    category="Content",
                    rating=round(
                        sum(item.content_rating for item in feedback_rows) / feedback_received,
                        2,
                    ),
                ),
                TrainingFeedbackRatingSummary(
                    category="Trainer",
                    rating=round(
                        sum(item.trainer_rating for item in feedback_rows) / feedback_received,
                        2,
                    ),
                ),
                TrainingFeedbackRatingSummary(
                    category="Facilities",
                    rating=round(
                        sum(item.facilities_rating for item in feedback_rows) / feedback_received,
                        2,
                    ),
                ),
                TrainingFeedbackRatingSummary(
                    category="Relevance",
                    rating=round(
                        sum(item.relevance_rating for item in feedback_rows) / feedback_received,
                        2,
                    ),
                ),
            ],
            rating_distribution=[
                TrainingFeedbackDistributionItem(stars=stars, count=rating_distribution_map[stars])
                for stars in range(5, 0, -1)
            ],
            recommend_percentage=recommend_percentage,
        )

    async def create_program(
        self, data: TrainingProgramCreate, created_by: UUID
    ) -> TrainingProgram:
        program_code = await self.generate_program_code(data.organization_id)
        program = TrainingProgram(
            organization_id=data.organization_id,
            program_code=program_code,
            title=data.title,
            description=data.description,
            category=data.category,
            mode=data.mode,
            trainer_type=data.trainer_type,
            trainer_name=data.trainer_name,
            trainer_contact=data.trainer_contact,
            start_date=data.start_date,
            end_date=data.end_date,
            duration_hours=Decimal(str(data.duration_hours)),
            location=data.location,
            max_participants=data.max_participants,
            status=self._derive_status(data.start_date, data.end_date, data.status),
            cost_per_participant=Decimal(str(data.cost_per_participant)),
            pre_requisites=data.pre_requisites,
            learning_objectives=data.learning_objectives,
            is_mandatory=data.is_mandatory,
            certificate_provided=data.certificate_provided,
            created_by=created_by,
        )
        self.db.add(program)
        await self.db.flush()
        await self.db.refresh(program)
        return program

    async def get_program(self, program_id: UUID) -> Optional[TrainingProgram]:
        result = await self.db.execute(
            select(TrainingProgram)
            .options(
                selectinload(TrainingProgram.nominations)
                .selectinload(TrainingNomination.employee)
                .selectinload(Employee.department),
                selectinload(TrainingProgram.nominations)
                .selectinload(TrainingNomination.employee)
                .selectinload(Employee.designation),
                selectinload(TrainingProgram.feedback_entries)
                .selectinload(TrainingFeedback.employee)
                .selectinload(Employee.department),
                selectinload(TrainingProgram.feedback_entries).selectinload(
                    TrainingFeedback.nomination
                ),
            )
            .where(TrainingProgram.id == program_id)
        )
        return result.scalar_one_or_none()

    async def list_programs(
        self,
        filters: TrainingProgramFilters,
        skip: int,
        limit: int,
    ) -> Tuple[List[TrainingProgramResponse], int, TrainingProgramSummaryResponse]:
        query = select(TrainingProgram).options(selectinload(TrainingProgram.nominations))
        conditions = []
        if filters.organization_id:
            conditions.append(TrainingProgram.organization_id == filters.organization_id)
        if filters.category:
            conditions.append(TrainingProgram.category == filters.category)
        if filters.mode:
            conditions.append(TrainingProgram.mode == filters.mode)
        if filters.status:
            conditions.append(TrainingProgram.status == filters.status)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    TrainingProgram.title.ilike(search_term),
                    TrainingProgram.program_code.ilike(search_term),
                    TrainingProgram.trainer_name.ilike(search_term),
                )
            )
        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count(TrainingProgram.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query.order_by(TrainingProgram.start_date.desc()).offset(skip).limit(limit)
        )
        programs = list(result.scalars().all())
        items = [self._program_response(program) for program in programs]

        summary_query = select(TrainingProgram).options(selectinload(TrainingProgram.nominations))
        if filters.organization_id:
            summary_query = summary_query.where(
                TrainingProgram.organization_id == filters.organization_id
            )
        summary_result = await self.db.execute(summary_query)
        summary_programs = list(summary_result.scalars().all())
        summary = TrainingProgramSummaryResponse(
            total_programs=len(summary_programs),
            scheduled=sum(1 for program in summary_programs if program.status == "SCHEDULED"),
            in_progress=sum(1 for program in summary_programs if program.status == "IN_PROGRESS"),
            completed=sum(1 for program in summary_programs if program.status == "COMPLETED"),
            total_participants=sum(
                sum(
                    1
                    for nomination in program.nominations
                    if nomination.status in {"NOMINATED", "CONFIRMED", "ATTENDED"}
                )
                for program in summary_programs
            ),
        )
        return items, total, summary

    async def update_program(
        self,
        program_id: UUID,
        data: TrainingProgramUpdate,
        updated_by: UUID,
    ) -> Optional[TrainingProgram]:
        program = await self.get_program(program_id)
        if not program:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in {"duration_hours", "cost_per_participant"} and value is not None:
                setattr(program, field, Decimal(str(value)))
            else:
                setattr(program, field, value)

        if program.start_date and program.end_date:
            program.status = self._derive_status(
                program.start_date,
                program.end_date,
                update_data.get("status", program.status),
            )
        program.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(program)
        return program

    async def list_available_employees(
        self,
        organization_id: UUID,
        program_id: UUID,
        search: Optional[str] = None,
    ) -> List[TrainingAvailableEmployeeResponse]:
        nominated_subquery = select(TrainingNomination.employee_id).where(
            TrainingNomination.program_id == program_id
        )
        query = (
            select(Employee)
            .options(selectinload(Employee.department), selectinload(Employee.designation))
            .where(
                Employee.organization_id == organization_id,
                Employee.employment_status == EmploymentStatus.ACTIVE,
                Employee.id.not_in(nominated_subquery),
            )
            .order_by(Employee.employee_code)
        )
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Employee.employee_code.ilike(search_term),
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.official_email.ilike(search_term),
                )
            )
        result = await self.db.execute(query.limit(100))
        employees = list(result.scalars().all())
        return [
            TrainingAvailableEmployeeResponse(
                id=employee.id,
                employee_code=employee.employee_code,
                full_name=employee.full_name,
                department=employee.department.department_name if employee.department else "-",
                designation=employee.designation.designation_name if employee.designation else "-",
                email=employee.official_email or employee.personal_email,
            )
            for employee in employees
        ]

    async def list_nominations(
        self,
        program_id: UUID,
    ) -> List[TrainingNominationResponse]:
        result = await self.db.execute(
            select(TrainingNomination)
            .options(
                selectinload(TrainingNomination.employee).selectinload(Employee.department),
                selectinload(TrainingNomination.employee).selectinload(Employee.designation),
                selectinload(TrainingNomination.nominated_by_user),
            )
            .where(TrainingNomination.program_id == program_id)
            .order_by(TrainingNomination.created_at.desc())
        )
        nominations = list(result.scalars().all())
        return [self._nomination_response(nomination) for nomination in nominations]

    async def add_nominations(
        self,
        program_id: UUID,
        employee_ids: Sequence[UUID],
        created_by: UUID,
    ) -> List[TrainingNominationResponse]:
        program = await self.get_program(program_id)
        if not program:
            return []

        existing_employee_ids = {nomination.employee_id for nomination in program.nominations}
        new_employee_ids = [
            employee_id for employee_id in employee_ids if employee_id not in existing_employee_ids
        ]
        current_enrolled = sum(
            1
            for nomination in program.nominations
            if nomination.status in {"NOMINATED", "CONFIRMED", "ATTENDED"}
        )
        if current_enrolled + len(new_employee_ids) > program.max_participants:
            raise BadRequestException(
                detail="Nominations exceed the configured participant capacity",
                error_code="TRAINING_CAPACITY_EXCEEDED",
            )

        employees_result = await self.db.execute(
            select(Employee).where(
                Employee.organization_id == program.organization_id,
                Employee.id.in_(new_employee_ids),
            )
        )
        employees = list(employees_result.scalars().all())
        found_ids = {employee.id for employee in employees}
        missing_ids = [
            employee_id for employee_id in new_employee_ids if employee_id not in found_ids
        ]
        if missing_ids:
            raise BadRequestException(
                detail="One or more selected employees are invalid for this organization",
                error_code="TRAINING_EMPLOYEE_NOT_FOUND",
            )

        for employee in employees:
            self.db.add(
                TrainingNomination(
                    program_id=program.id,
                    employee_id=employee.id,
                    status="NOMINATED",
                    attendance_marked=False,
                    created_by=created_by,
                )
            )

        await self.db.flush()
        return await self.list_nominations(program_id)

    async def update_nomination_status(
        self,
        program_id: UUID,
        nomination_id: UUID,
        status: str,
        updated_by: UUID,
        attendance_marked: Optional[bool] = None,
    ) -> Optional[TrainingNominationResponse]:
        result = await self.db.execute(
            select(TrainingNomination)
            .options(
                selectinload(TrainingNomination.employee).selectinload(Employee.department),
                selectinload(TrainingNomination.employee).selectinload(Employee.designation),
                selectinload(TrainingNomination.nominated_by_user),
            )
            .where(
                TrainingNomination.id == nomination_id,
                TrainingNomination.program_id == program_id,
            )
        )
        nomination = result.scalar_one_or_none()
        if not nomination:
            return None

        nomination.status = status
        if attendance_marked is not None:
            nomination.attendance_marked = attendance_marked
        elif status == "ATTENDED":
            nomination.attendance_marked = True
        nomination.updated_by = updated_by
        await self.db.flush()
        refreshed_result = await self.db.execute(
            select(TrainingNomination)
            .options(
                selectinload(TrainingNomination.employee).selectinload(Employee.department),
                selectinload(TrainingNomination.employee).selectinload(Employee.designation),
                selectinload(TrainingNomination.nominated_by_user),
            )
            .where(TrainingNomination.id == nomination_id)
        )
        refreshed_nomination = refreshed_result.scalar_one_or_none()
        if not refreshed_nomination:
            return None
        return self._nomination_response(refreshed_nomination)

    async def get_feedback_bundle(
        self, program_id: UUID
    ) -> Optional[TrainingFeedbackBundleResponse]:
        program = await self.get_program(program_id)
        if not program:
            return None

        feedback_result = await self.db.execute(
            select(TrainingFeedback)
            .options(
                selectinload(TrainingFeedback.employee).selectinload(Employee.department),
                selectinload(TrainingFeedback.nomination),
            )
            .where(TrainingFeedback.program_id == program_id)
            .order_by(TrainingFeedback.submitted_on.desc())
        )
        feedback_rows = [self._feedback_response(item) for item in feedback_result.scalars().all()]
        total_participants = sum(
            1 for nomination in program.nominations if nomination.status != "CANCELLED"
        )
        summary = self._feedback_summary(total_participants, feedback_rows)
        return TrainingFeedbackBundleResponse(
            program=self._program_response(program),
            summary=summary,
            individual_feedbacks=feedback_rows,
        )

    async def upsert_feedback(
        self,
        program_id: UUID,
        data: TrainingFeedbackCreate,
        created_by: UUID,
    ) -> TrainingFeedbackBundleResponse:
        program = await self.get_program(program_id)
        if not program:
            raise BadRequestException(
                detail="Training program not found",
                error_code="TRAINING_PROGRAM_NOT_FOUND",
            )

        nomination = next(
            (item for item in program.nominations if item.employee_id == data.employee_id),
            None,
        )
        if not nomination:
            raise BadRequestException(
                detail="Feedback can only be recorded for nominated employees",
                error_code="TRAINING_FEEDBACK_EMPLOYEE_NOT_NOMINATED",
            )

        existing_result = await self.db.execute(
            select(TrainingFeedback).where(
                TrainingFeedback.program_id == program_id,
                TrainingFeedback.employee_id == data.employee_id,
            )
        )
        feedback = existing_result.scalar_one_or_none()
        if feedback:
            feedback.overall_rating = Decimal(str(data.overall_rating))
            feedback.content_rating = Decimal(str(data.content_rating))
            feedback.trainer_rating = Decimal(str(data.trainer_rating))
            feedback.facilities_rating = Decimal(str(data.facilities_rating))
            feedback.relevance_rating = Decimal(str(data.relevance_rating))
            feedback.would_recommend = data.would_recommend
            feedback.strengths = data.strengths
            feedback.improvements = data.improvements
            feedback.comments = data.comments
            feedback.submitted_on = data.submitted_on
            feedback.updated_by = created_by
        else:
            feedback = TrainingFeedback(
                program_id=program_id,
                nomination_id=nomination.id,
                employee_id=data.employee_id,
                overall_rating=Decimal(str(data.overall_rating)),
                content_rating=Decimal(str(data.content_rating)),
                trainer_rating=Decimal(str(data.trainer_rating)),
                facilities_rating=Decimal(str(data.facilities_rating)),
                relevance_rating=Decimal(str(data.relevance_rating)),
                would_recommend=data.would_recommend,
                strengths=data.strengths,
                improvements=data.improvements,
                comments=data.comments,
                submitted_on=data.submitted_on,
                created_by=created_by,
            )
            self.db.add(feedback)

        if nomination.status == "NOMINATED":
            nomination.status = "ATTENDED"
            nomination.attendance_marked = True
            nomination.updated_by = created_by

        await self.db.flush()
        bundle = await self.get_feedback_bundle(program_id)
        if bundle is None:
            raise BadRequestException(
                detail="Feedback bundle could not be loaded",
                error_code="TRAINING_FEEDBACK_LOAD_FAILED",
            )
        return bundle
