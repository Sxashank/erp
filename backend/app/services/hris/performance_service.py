"""Service layer for HRIS performance management."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import EmploymentStatus
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.hris.employee import Employee
from app.models.hris.performance import AppraisalCycle, EmployeeAppraisal, PerformanceGoal
from app.schemas.hris.performance import (
    AppraisalCycleCreate,
    AppraisalCycleListBundleResponse,
    AppraisalCycleListResponse,
    AppraisalCycleResponse,
    AppraisalCycleSummaryResponse,
    AppraisalCycleUpdate,
    EmployeeAppraisalResponse,
    EmployeePerformanceDetailResponse,
    PerformanceCalibrationSubmit,
    PerformanceEmployeeSummaryResponse,
    PerformanceGoalCreate,
    PerformanceGoalResponse,
    PerformanceGoalUpdate,
    PerformanceManagerReviewSubmit,
    PerformanceSelfAppraisalSubmit,
)

ACTIVE_EMPLOYEE_STATUSES = [
    EmploymentStatus.ACTIVE,
    EmploymentStatus.PROBATION,
    EmploymentStatus.NOTICE_PERIOD,
]


class PerformanceService:
    """Business logic for appraisal cycles, goals, and reviews."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_cycles(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> AppraisalCycleListBundleResponse:
        query = (
            select(AppraisalCycle)
            .where(
                AppraisalCycle.organization_id == organization_id,
                AppraisalCycle.deleted_at.is_(None),
            )
            .options(
                selectinload(AppraisalCycle.financial_year),
                selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.department),
                selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.designation),
            )
        )
        if status:
            query = query.where(func.upper(AppraisalCycle.status) == status.upper())
        if search:
            like = f"%{search.strip()}%"
            query = query.where(
                or_(AppraisalCycle.name.ilike(like), AppraisalCycle.code.ilike(like))
            )

        total = await self._count(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(
            query.order_by(AppraisalCycle.start_date.desc()).offset(skip).limit(limit)
        )
        cycles = list(result.scalars().all())
        all_cycles_result = await self.db.execute(
            select(AppraisalCycle)
            .where(
                AppraisalCycle.organization_id == organization_id,
                AppraisalCycle.deleted_at.is_(None),
            )
            .options(selectinload(AppraisalCycle.appraisals))
        )
        all_cycles = list(all_cycles_result.scalars().all())
        return AppraisalCycleListBundleResponse(
            items=[self._cycle_list_response(cycle) for cycle in cycles],
            total=total,
            skip=skip,
            limit=limit,
            summary=self._cycle_summary(all_cycles),
        )

    async def create_cycle(
        self,
        organization_id: UUID,
        data: AppraisalCycleCreate,
        created_by: UUID,
    ) -> AppraisalCycleResponse:
        self._validate_weightages(data.weightage_goals, data.weightage_competencies)
        cycle = AppraisalCycle(
            organization_id=organization_id,
            code=await self._generate_cycle_code(organization_id),
            name=data.name,
            description=data.description,
            financial_year_id=data.financial_year_id,
            cycle_type=data.cycle_type,
            start_date=data.start_date,
            end_date=data.end_date,
            goal_setting_start=data.goal_setting_start,
            goal_setting_end=data.goal_setting_end,
            self_appraisal_start=data.self_appraisal_start,
            self_appraisal_end=data.self_appraisal_end,
            manager_review_start=data.manager_review_start,
            manager_review_end=data.manager_review_end,
            calibration_start=data.calibration_start,
            calibration_end=data.calibration_end,
            rating_scale=data.rating_scale,
            weightage_goals=data.weightage_goals,
            weightage_competencies=data.weightage_competencies,
            allow_self_rating=data.allow_self_rating,
            allow_peer_feedback=data.allow_peer_feedback,
            status="DRAFT",
            created_by=created_by,
        )
        self.db.add(cycle)
        await self.db.flush()

        employees = await self._resolve_cycle_employees(
            organization_id=organization_id,
            include_all_active_employees=data.include_all_active_employees,
            employee_ids=data.employee_ids,
        )
        for employee in employees:
            self.db.add(
                EmployeeAppraisal(
                    appraisal_cycle_id=cycle.id,
                    employee_id=employee.id,
                    reviewer_id=(
                        employee.reporting_manager.user_id
                        if employee.reporting_manager and employee.reporting_manager.user_id
                        else None
                    ),
                    status="NOT_STARTED",
                    created_by=created_by,
                )
            )
        await self.db.flush()
        return await self.get_cycle(cycle.id)

    async def get_cycle(self, cycle_id: UUID) -> AppraisalCycleResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        return self._cycle_response(cycle)

    async def update_cycle(
        self,
        cycle_id: UUID,
        data: AppraisalCycleUpdate,
        updated_by: UUID,
    ) -> AppraisalCycleResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        if data.weightage_goals is not None or data.weightage_competencies is not None:
            self._validate_weightages(
                data.weightage_goals or cycle.weightage_goals,
                data.weightage_competencies or cycle.weightage_competencies,
            )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cycle, field, value)
        cycle.updated_by = updated_by
        await self.db.flush()
        return self._cycle_response(cycle)

    async def start_cycle(self, cycle_id: UUID, updated_by: UUID) -> AppraisalCycleResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        cycle.status = "GOAL_SETTING"
        cycle.updated_by = updated_by
        for appraisal in cycle.appraisals:
            if appraisal.status == "NOT_STARTED":
                appraisal.status = "GOAL_SETTING"
                appraisal.updated_by = updated_by
        await self.db.flush()
        return self._cycle_response(cycle)

    async def close_cycle(self, cycle_id: UUID, updated_by: UUID) -> AppraisalCycleResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        incomplete = [
            appraisal for appraisal in cycle.appraisals if appraisal.status != "COMPLETED"
        ]
        if incomplete:
            raise BadRequestException(
                detail="All employee appraisals must be completed before closing the cycle",
                error_code="APPRAISAL_CYCLE_INCOMPLETE",
            )
        cycle.status = "COMPLETED"
        cycle.updated_by = updated_by
        await self.db.flush()
        return self._cycle_response(cycle)

    async def list_cycle_employees(
        self,
        cycle_id: UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[PerformanceEmployeeSummaryResponse]:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        goal_counts = self._goal_count_map(cycle.goals)
        rows: list[PerformanceEmployeeSummaryResponse] = []
        for appraisal in cycle.appraisals:
            employee = appraisal.employee
            if search:
                haystack = " ".join(
                    filter(None, [employee.full_name, employee.employee_code, cycle.name])
                ).lower()
                if search.strip().lower() not in haystack:
                    continue
            normalized_status = self._upper(appraisal.status)
            if status and normalized_status != status.upper():
                continue
            counts = goal_counts.get(employee.id, {"total": 0, "submitted": 0, "completed": 0})
            rows.append(self._employee_summary_from_appraisal(appraisal, counts))
        return rows

    async def get_employee_performance_detail(
        self, cycle_id: UUID, employee_id: UUID
    ) -> EmployeePerformanceDetailResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        appraisal = next(
            (item for item in cycle.appraisals if item.employee_id == employee_id), None
        )
        if not appraisal:
            raise NotFoundException(
                detail="Employee appraisal not found",
                error_code="EMPLOYEE_APPRAISAL_NOT_FOUND",
            )
        goal_list = [goal for goal in cycle.goals if goal.employee_id == employee_id]
        counts = self._goal_count_map(goal_list).get(
            employee_id, {"total": len(goal_list), "submitted": 0, "completed": 0}
        )
        return EmployeePerformanceDetailResponse(
            cycle=self._cycle_response(cycle),
            employee=self._employee_summary_from_appraisal(appraisal, counts),
            appraisal=self._appraisal_response(appraisal),
            goals=[
                self._goal_response(goal)
                for goal in sorted(goal_list, key=lambda item: item.goal_number)
            ],
        )

    async def create_goal(
        self,
        cycle_id: UUID,
        employee_id: UUID,
        data: PerformanceGoalCreate,
        created_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        appraisal = next(
            (item for item in cycle.appraisals if item.employee_id == employee_id), None
        )
        if not appraisal:
            raise NotFoundException(
                detail="Employee appraisal not found",
                error_code="EMPLOYEE_APPRAISAL_NOT_FOUND",
            )
        employee_goals = [goal for goal in cycle.goals if goal.employee_id == employee_id]
        existing_weight = sum(goal.weightage for goal in employee_goals)
        if existing_weight + data.weightage > Decimal("100"):
            raise BadRequestException(
                detail="Goal weightage cannot exceed 100%",
                error_code="GOAL_WEIGHTAGE_EXCEEDED",
            )
        goal = PerformanceGoal(
            appraisal_cycle_id=cycle_id,
            employee_id=employee_id,
            goal_number=len(employee_goals) + 1,
            title=data.title,
            description=data.description,
            category=data.category,
            weightage=data.weightage,
            target_value=data.target_value,
            measurement_criteria=data.measurement_criteria,
            start_date=data.start_date,
            due_date=data.due_date,
            status="DRAFT",
            created_by=created_by,
        )
        appraisal.status = "GOAL_SETTING"
        appraisal.updated_by = created_by
        self.db.add(goal)
        await self.db.flush()
        return await self.get_employee_performance_detail(cycle_id, employee_id)

    async def update_goal(
        self,
        goal_id: UUID,
        data: PerformanceGoalUpdate,
        updated_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        goal = await self._get_goal(goal_id)
        if not goal:
            raise NotFoundException(detail="Goal not found", error_code="GOAL_NOT_FOUND")
        current_goals_result = await self.db.execute(
            select(PerformanceGoal).where(
                PerformanceGoal.appraisal_cycle_id == goal.appraisal_cycle_id,
                PerformanceGoal.employee_id == goal.employee_id,
                PerformanceGoal.id != goal.id,
                PerformanceGoal.deleted_at.is_(None),
            )
        )
        sibling_goals = list(current_goals_result.scalars().all())
        if data.weightage is not None:
            other_weight = sum(item.weightage for item in sibling_goals)
            if other_weight + data.weightage > Decimal("100"):
                raise BadRequestException(
                    detail="Goal weightage cannot exceed 100%",
                    error_code="GOAL_WEIGHTAGE_EXCEEDED",
                )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        goal.updated_by = updated_by
        await self.db.flush()
        return await self.get_employee_performance_detail(goal.appraisal_cycle_id, goal.employee_id)

    async def delete_goal(
        self,
        goal_id: UUID,
        deleted_by: UUID,
    ) -> tuple[UUID, UUID]:
        goal = await self._get_goal(goal_id)
        if not goal:
            raise NotFoundException(detail="Goal not found", error_code="GOAL_NOT_FOUND")
        cycle_id = goal.appraisal_cycle_id
        employee_id = goal.employee_id
        goal.soft_delete(deleted_by)
        await self.db.flush()
        return cycle_id, employee_id

    async def submit_goals(
        self,
        cycle_id: UUID,
        employee_id: UUID,
        updated_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        detail = await self.get_employee_performance_detail(cycle_id, employee_id)
        total_weight = sum(Decimal(str(goal.weightage)) for goal in detail.goals)
        if total_weight != Decimal("100"):
            raise BadRequestException(
                detail="Goal weightage must total 100% before submission",
                error_code="GOAL_WEIGHTAGE_INCOMPLETE",
            )
        cycle = await self._get_cycle(cycle_id)
        assert cycle is not None
        appraisal = next(item for item in cycle.appraisals if item.employee_id == employee_id)
        for goal in cycle.goals:
            if goal.employee_id == employee_id and goal.deleted_at is None:
                goal.status = "SUBMITTED"
                goal.updated_by = updated_by
        appraisal.status = "SELF_APPRAISAL"
        appraisal.updated_by = updated_by
        cycle.status = "IN_PROGRESS"
        cycle.updated_by = updated_by
        await self.db.flush()
        return await self.get_employee_performance_detail(cycle_id, employee_id)

    async def submit_self_appraisal(
        self,
        cycle_id: UUID,
        employee_id: UUID,
        data: PerformanceSelfAppraisalSubmit,
        updated_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        appraisal = next(
            (item for item in cycle.appraisals if item.employee_id == employee_id), None
        )
        if not appraisal:
            raise NotFoundException(
                detail="Employee appraisal not found",
                error_code="EMPLOYEE_APPRAISAL_NOT_FOUND",
            )
        goals_by_id = {
            goal.id: goal
            for goal in cycle.goals
            if goal.employee_id == employee_id and goal.deleted_at is None
        }
        if set(goals_by_id) != {item.goal_id for item in data.goals}:
            raise BadRequestException(
                detail="All employee goals must be self-appraised before submission",
                error_code="GOAL_SELF_APPRAISAL_INCOMPLETE",
            )
        for item in data.goals:
            goal = goals_by_id[item.goal_id]
            goal.self_rating = Decimal(str(item.self_rating))
            goal.self_comments = item.self_comments
            goal.progress_percent = Decimal(str(item.self_progress))
            goal.achievement_value = item.achievement_value
            goal.status = "IN_PROGRESS"
            goal.updated_by = updated_by

        goal_rating = self._weighted_rating(goals_by_id.values(), attr="self_rating")
        overall_rating = self._blend_ratings(
            goal_rating=goal_rating,
            competency_rating=Decimal(str(data.competency_rating)),
            goal_weight=cycle.weightage_goals,
            competency_weight=cycle.weightage_competencies,
        )
        appraisal.goal_rating = goal_rating
        appraisal.competency_rating = Decimal(str(data.competency_rating))
        appraisal.overall_rating = overall_rating
        appraisal.self_appraisal_date = datetime.now(timezone.utc)
        appraisal.self_summary = data.self_summary
        appraisal.self_achievements = data.self_achievements
        appraisal.self_challenges = data.self_challenges
        appraisal.self_development_areas = data.self_development_areas
        appraisal.employee_comments = data.employee_comments
        appraisal.status = "MANAGER_REVIEW"
        appraisal.updated_by = updated_by
        cycle.status = "REVIEW"
        cycle.updated_by = updated_by
        await self.db.flush()
        return await self.get_employee_performance_detail(cycle_id, employee_id)

    async def submit_manager_review(
        self,
        cycle_id: UUID,
        employee_id: UUID,
        data: PerformanceManagerReviewSubmit,
        updated_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        appraisal = next(
            (item for item in cycle.appraisals if item.employee_id == employee_id), None
        )
        if not appraisal:
            raise NotFoundException(
                detail="Employee appraisal not found",
                error_code="EMPLOYEE_APPRAISAL_NOT_FOUND",
            )
        goals_by_id = {
            goal.id: goal
            for goal in cycle.goals
            if goal.employee_id == employee_id and goal.deleted_at is None
        }
        if set(goals_by_id) != {item.goal_id for item in data.goals}:
            raise BadRequestException(
                detail="All employee goals must be manager-reviewed before submission",
                error_code="MANAGER_REVIEW_INCOMPLETE",
            )
        for item in data.goals:
            goal = goals_by_id[item.goal_id]
            goal.manager_rating = Decimal(str(item.manager_rating))
            goal.manager_comments = item.manager_comments
            goal.final_rating = (
                Decimal(str(item.final_rating))
                if item.final_rating is not None
                else Decimal(str(item.manager_rating))
            )
            goal.status = "COMPLETED"
            goal.updated_by = updated_by
        goal_rating = self._weighted_rating(goals_by_id.values(), attr="final_rating")
        overall_rating = self._blend_ratings(
            goal_rating=goal_rating,
            competency_rating=Decimal(str(data.competency_rating)),
            goal_weight=cycle.weightage_goals,
            competency_weight=cycle.weightage_competencies,
        )
        appraisal.goal_rating = goal_rating
        appraisal.competency_rating = Decimal(str(data.competency_rating))
        appraisal.overall_rating = overall_rating
        appraisal.final_grade = self._grade_for_rating(overall_rating)
        appraisal.manager_review_date = datetime.now(timezone.utc)
        appraisal.manager_summary = data.manager_summary
        appraisal.manager_achievements = data.manager_achievements
        appraisal.manager_improvements = data.manager_improvements
        appraisal.manager_recommendations = data.manager_recommendations
        appraisal.status = "CALIBRATION"
        appraisal.updated_by = updated_by
        cycle.status = "CALIBRATION"
        cycle.updated_by = updated_by
        await self.db.flush()
        return await self.get_employee_performance_detail(cycle_id, employee_id)

    async def calibrate_appraisal(
        self,
        cycle_id: UUID,
        employee_id: UUID,
        data: PerformanceCalibrationSubmit,
        updated_by: UUID,
    ) -> EmployeePerformanceDetailResponse:
        cycle = await self._get_cycle(cycle_id)
        if not cycle:
            raise NotFoundException(
                detail="Appraisal cycle not found",
                error_code="APPRAISAL_CYCLE_NOT_FOUND",
            )
        appraisal = next(
            (item for item in cycle.appraisals if item.employee_id == employee_id), None
        )
        if not appraisal:
            raise NotFoundException(
                detail="Employee appraisal not found",
                error_code="EMPLOYEE_APPRAISAL_NOT_FOUND",
            )
        appraisal.calibrated_rating = Decimal(str(data.calibrated_rating))
        appraisal.calibration_notes = data.calibration_notes
        appraisal.calibrated_grade = data.final_grade or self._grade_for_rating(
            appraisal.calibrated_rating
        )
        appraisal.overall_rating = appraisal.calibrated_rating
        appraisal.final_grade = appraisal.calibrated_grade
        appraisal.calibrated_by = updated_by
        appraisal.calibrated_at = datetime.now(timezone.utc)
        appraisal.status = "COMPLETED"
        appraisal.updated_by = updated_by
        await self.db.flush()
        return await self.get_employee_performance_detail(cycle_id, employee_id)

    async def get_current_employee_appraisal(
        self, employee_id: UUID
    ) -> Optional[EmployeePerformanceDetailResponse]:
        result = await self.db.execute(
            select(EmployeeAppraisal)
            .where(
                EmployeeAppraisal.employee_id == employee_id,
                EmployeeAppraisal.deleted_at.is_(None),
                EmployeeAppraisal.status.in_(
                    ["GOAL_SETTING", "SELF_APPRAISAL", "MANAGER_REVIEW", "CALIBRATION"]
                ),
            )
            .options(
                selectinload(EmployeeAppraisal.employee).selectinload(Employee.department),
                selectinload(EmployeeAppraisal.employee).selectinload(Employee.designation),
                selectinload(EmployeeAppraisal.reviewer),
                selectinload(EmployeeAppraisal.appraisal_cycle).selectinload(AppraisalCycle.goals),
                selectinload(EmployeeAppraisal.appraisal_cycle)
                .selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.department),
                selectinload(EmployeeAppraisal.appraisal_cycle)
                .selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.designation),
                selectinload(EmployeeAppraisal.appraisal_cycle)
                .selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.reviewer),
            )
            .order_by(EmployeeAppraisal.created_at.desc())
            .limit(1)
        )
        appraisal = result.scalar_one_or_none()
        if not appraisal:
            return None
        return await self.get_employee_performance_detail(
            appraisal.appraisal_cycle_id, appraisal.employee_id
        )

    async def _resolve_cycle_employees(
        self,
        organization_id: UUID,
        include_all_active_employees: bool,
        employee_ids: Sequence[UUID],
    ) -> list[Employee]:
        query = (
            select(Employee)
            .options(selectinload(Employee.reporting_manager))
            .where(
                Employee.organization_id == organization_id,
                Employee.employment_status.in_(ACTIVE_EMPLOYEE_STATUSES),
            )
        )
        if not include_all_active_employees:
            if not employee_ids:
                raise BadRequestException(
                    detail="Select at least one employee for the appraisal cycle",
                    error_code="APPRAISAL_CYCLE_EMPLOYEES_REQUIRED",
                )
            query = query.where(Employee.id.in_(employee_ids))
        result = await self.db.execute(query.order_by(Employee.employee_code.asc()))
        return list(result.scalars().all())

    async def _generate_cycle_code(self, organization_id: UUID) -> str:
        result = await self.db.execute(
            select(func.count(AppraisalCycle.id)).where(
                AppraisalCycle.organization_id == organization_id
            )
        )
        count = int(result.scalar() or 0) + 1
        return f"APR{date.today().strftime('%Y')}{count:04d}"

    async def _get_cycle(self, cycle_id: UUID) -> Optional[AppraisalCycle]:
        result = await self.db.execute(
            select(AppraisalCycle)
            .execution_options(populate_existing=True)
            .where(AppraisalCycle.id == cycle_id, AppraisalCycle.deleted_at.is_(None))
            .options(
                selectinload(AppraisalCycle.financial_year),
                selectinload(AppraisalCycle.goals),
                selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.department),
                selectinload(AppraisalCycle.appraisals)
                .selectinload(EmployeeAppraisal.employee)
                .selectinload(Employee.designation),
                selectinload(AppraisalCycle.appraisals).selectinload(EmployeeAppraisal.reviewer),
            )
        )
        return result.scalar_one_or_none()

    async def _get_goal(self, goal_id: UUID) -> Optional[PerformanceGoal]:
        result = await self.db.execute(
            select(PerformanceGoal).where(
                PerformanceGoal.id == goal_id,
                PerformanceGoal.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    def _cycle_list_response(self, cycle: AppraisalCycle) -> AppraisalCycleListResponse:
        metrics = self._cycle_metrics(cycle)
        return AppraisalCycleListResponse(
            id=cycle.id,
            code=cycle.code,
            name=cycle.name,
            financial_year=(
                getattr(cycle.financial_year, "fy_code", None)
                if getattr(cycle, "financial_year", None)
                else None
            ),
            cycle_type=self._upper(cycle.cycle_type),
            start_date=cycle.start_date,
            end_date=cycle.end_date,
            goal_setting_end=cycle.goal_setting_end,
            self_appraisal_end=cycle.self_appraisal_end,
            manager_review_end=cycle.manager_review_end,
            status=self._upper(cycle.status),
            eligible_employees=metrics["eligible_employees"],
            completed_appraisals=metrics["completed_appraisals"],
            pending_self_appraisal=metrics["pending_self_appraisal"],
            pending_manager_review=metrics["pending_manager_review"],
        )

    def _cycle_response(self, cycle: AppraisalCycle) -> AppraisalCycleResponse:
        metrics = self._cycle_metrics(cycle)
        return AppraisalCycleResponse(
            id=cycle.id,
            organization_id=cycle.organization_id,
            code=cycle.code,
            name=cycle.name,
            description=cycle.description,
            financial_year_id=cycle.financial_year_id,
            cycle_type=self._upper(cycle.cycle_type),
            start_date=cycle.start_date,
            end_date=cycle.end_date,
            goal_setting_start=cycle.goal_setting_start,
            goal_setting_end=cycle.goal_setting_end,
            self_appraisal_start=cycle.self_appraisal_start,
            self_appraisal_end=cycle.self_appraisal_end,
            manager_review_start=cycle.manager_review_start,
            manager_review_end=cycle.manager_review_end,
            calibration_start=cycle.calibration_start,
            calibration_end=cycle.calibration_end,
            rating_scale=cycle.rating_scale,
            weightage_goals=cycle.weightage_goals,
            weightage_competencies=cycle.weightage_competencies,
            allow_self_rating=cycle.allow_self_rating,
            allow_peer_feedback=cycle.allow_peer_feedback,
            status=self._upper(cycle.status),
            eligible_employees=metrics["eligible_employees"],
            completed_appraisals=metrics["completed_appraisals"],
            pending_self_appraisal=metrics["pending_self_appraisal"],
            pending_manager_review=metrics["pending_manager_review"],
        )

    def _appraisal_response(self, appraisal: EmployeeAppraisal) -> EmployeeAppraisalResponse:
        return EmployeeAppraisalResponse(
            id=appraisal.id,
            appraisal_cycle_id=appraisal.appraisal_cycle_id,
            employee_id=appraisal.employee_id,
            reviewer_id=appraisal.reviewer_id,
            status=self._upper(appraisal.status),
            goal_rating=float(appraisal.goal_rating) if appraisal.goal_rating is not None else None,
            competency_rating=(
                float(appraisal.competency_rating)
                if appraisal.competency_rating is not None
                else None
            ),
            overall_rating=(
                float(appraisal.overall_rating) if appraisal.overall_rating is not None else None
            ),
            final_grade=appraisal.final_grade,
            self_appraisal_date=appraisal.self_appraisal_date,
            self_summary=appraisal.self_summary,
            self_achievements=appraisal.self_achievements,
            self_challenges=appraisal.self_challenges,
            self_development_areas=appraisal.self_development_areas,
            manager_review_date=appraisal.manager_review_date,
            manager_summary=appraisal.manager_summary,
            manager_achievements=appraisal.manager_achievements,
            manager_improvements=appraisal.manager_improvements,
            manager_recommendations=appraisal.manager_recommendations,
            calibration_notes=appraisal.calibration_notes,
            calibrated_rating=(
                float(appraisal.calibrated_rating)
                if appraisal.calibrated_rating is not None
                else None
            ),
            calibrated_grade=appraisal.calibrated_grade,
            calibrated_by=appraisal.calibrated_by,
            calibrated_at=appraisal.calibrated_at,
            employee_acknowledgment=appraisal.employee_acknowledgment,
            acknowledgment_date=appraisal.acknowledgment_date,
            employee_comments=appraisal.employee_comments,
        )

    def _goal_response(self, goal: PerformanceGoal) -> PerformanceGoalResponse:
        return PerformanceGoalResponse(
            id=goal.id,
            employee_id=goal.employee_id,
            goal_number=goal.goal_number,
            title=goal.title,
            description=goal.description,
            category=goal.category,
            weightage=goal.weightage,
            target_value=goal.target_value,
            measurement_criteria=goal.measurement_criteria,
            start_date=goal.start_date,
            due_date=goal.due_date,
            status=self._upper(goal.status),
            progress_percent=float(goal.progress_percent),
            achievement_value=goal.achievement_value,
            self_rating=float(goal.self_rating) if goal.self_rating is not None else None,
            self_comments=goal.self_comments,
            manager_rating=float(goal.manager_rating) if goal.manager_rating is not None else None,
            manager_comments=goal.manager_comments,
            final_rating=float(goal.final_rating) if goal.final_rating is not None else None,
            approved_at=goal.approved_at,
        )

    def _employee_summary_from_appraisal(
        self,
        appraisal: EmployeeAppraisal,
        counts: dict[str, int],
    ) -> PerformanceEmployeeSummaryResponse:
        employee = appraisal.employee
        reviewer_name = appraisal.reviewer.full_name if appraisal.reviewer else None
        return PerformanceEmployeeSummaryResponse(
            appraisal_id=appraisal.id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.full_name,
            department=employee.department.name if employee.department else None,
            designation=employee.designation.name if employee.designation else None,
            reviewer_name=reviewer_name,
            status=self._upper(appraisal.status),
            goal_count=counts["total"],
            submitted_goals=counts["submitted"],
            completed_goals=counts["completed"],
            overall_rating=(
                float(appraisal.overall_rating) if appraisal.overall_rating is not None else None
            ),
            final_grade=appraisal.final_grade,
            self_appraisal_date=appraisal.self_appraisal_date,
            manager_review_date=appraisal.manager_review_date,
            calibrated_at=appraisal.calibrated_at,
        )

    def _cycle_metrics(self, cycle: AppraisalCycle) -> dict[str, int]:
        completed = 0
        pending_self = 0
        pending_manager = 0
        for appraisal in cycle.appraisals:
            status = self._upper(appraisal.status)
            if status == "COMPLETED":
                completed += 1
            elif status == "SELF_APPRAISAL":
                pending_self += 1
            elif status in {"MANAGER_REVIEW", "CALIBRATION"}:
                pending_manager += 1
        return {
            "eligible_employees": len(cycle.appraisals),
            "completed_appraisals": completed,
            "pending_self_appraisal": pending_self,
            "pending_manager_review": pending_manager,
        }

    def _cycle_summary(self, cycles: Sequence[AppraisalCycle]) -> AppraisalCycleSummaryResponse:
        return AppraisalCycleSummaryResponse(
            total_cycles=len(cycles),
            active=sum(
                1
                for cycle in cycles
                if self._upper(cycle.status)
                in {"GOAL_SETTING", "IN_PROGRESS", "REVIEW", "CALIBRATION"}
            ),
            completed=sum(1 for cycle in cycles if self._upper(cycle.status) == "COMPLETED"),
            draft=sum(1 for cycle in cycles if self._upper(cycle.status) == "DRAFT"),
            employees_appraised=sum(
                self._cycle_metrics(cycle)["completed_appraisals"] for cycle in cycles
            ),
        )

    def _goal_count_map(self, goals: Iterable[PerformanceGoal]) -> dict[UUID, dict[str, int]]:
        counts: dict[UUID, dict[str, int]] = {}
        for goal in goals:
            if goal.deleted_at is not None:
                continue
            bucket = counts.setdefault(
                goal.employee_id, {"total": 0, "submitted": 0, "completed": 0}
            )
            bucket["total"] += 1
            status = self._upper(goal.status)
            if status in {"SUBMITTED", "IN_PROGRESS", "COMPLETED"}:
                bucket["submitted"] += 1
            if status == "COMPLETED":
                bucket["completed"] += 1
        return counts

    def _weighted_rating(
        self,
        goals: Iterable[PerformanceGoal],
        attr: str,
    ) -> Decimal:
        total_weight = Decimal("0")
        weighted_sum = Decimal("0")
        for goal in goals:
            rating = getattr(goal, attr)
            if rating is None:
                continue
            weighted_sum += Decimal(str(rating)) * Decimal(str(goal.weightage))
            total_weight += Decimal(str(goal.weightage))
        if total_weight == 0:
            return Decimal("0")
        return (weighted_sum / total_weight).quantize(Decimal("0.01"))

    def _blend_ratings(
        self,
        goal_rating: Decimal,
        competency_rating: Decimal,
        goal_weight: Decimal,
        competency_weight: Decimal,
    ) -> Decimal:
        total_weight = Decimal(str(goal_weight)) + Decimal(str(competency_weight))
        if total_weight == 0:
            return Decimal("0")
        value = (
            goal_rating * Decimal(str(goal_weight))
            + competency_rating * Decimal(str(competency_weight))
        ) / total_weight
        return value.quantize(Decimal("0.01"))

    def _grade_for_rating(self, rating: Decimal) -> str:
        value = float(rating)
        if value >= 4.5:
            return "A+"
        if value >= 4.0:
            return "A"
        if value >= 3.5:
            return "B+"
        if value >= 3.0:
            return "B"
        if value >= 2.0:
            return "C"
        return "D"

    def _validate_weightages(self, goals_weight: Decimal, competency_weight: Decimal) -> None:
        total = Decimal(str(goals_weight)) + Decimal(str(competency_weight))
        if total != Decimal("100"):
            raise BadRequestException(
                detail="Goal and competency weightages must total 100%",
                error_code="APPRAISAL_WEIGHTAGE_INVALID",
            )

    def _upper(self, value: Optional[str]) -> str:
        return (value or "").upper()

    async def _count(self, query) -> int:
        result = await self.db.execute(query)
        return int(result.scalar() or 0)
