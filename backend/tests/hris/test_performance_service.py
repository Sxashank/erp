"""Service tests for HRIS performance management."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.constants import EmploymentStatus, EmploymentType, Gender
from app.models.hris.employee import Employee
from app.schemas.hris.performance import (
    AppraisalCycleCreate,
    PerformanceCalibrationSubmit,
    PerformanceGoalCreate,
    PerformanceManagerGoalReview,
    PerformanceManagerReviewSubmit,
    PerformanceGoalSelfAssessment,
    PerformanceSelfAppraisalSubmit,
)
from app.services.hris.performance_service import PerformanceService


@pytest_asyncio.fixture
async def performance_employee(session, test_organization):
    employee = Employee(
        id=uuid4(),
        organization_id=test_organization.id,
        employee_code="EMP-PERF-001",
        first_name="Performance",
        last_name="Employee",
        gender=Gender.MALE,
        date_of_birth=date(1992, 1, 15),
        personal_mobile="9876543210",
        official_email="performance.employee@example.com",
        date_of_joining=date(2024, 4, 1),
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        notice_period_days=30,
        is_active=True,
        week_off_days=["SUNDAY"],
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee


@pytest_asyncio.fixture
async def performance_service(session):
    return PerformanceService(session)


@pytest_asyncio.fixture
async def appraisal_cycle(
    performance_service,
    performance_employee,
    test_organization,
    test_user,
):
    return await performance_service.create_cycle(
        organization_id=test_organization.id,
        data=AppraisalCycleCreate(
            name="FY26 Performance Cycle",
            description="Performance lifecycle validation",
            cycle_type="ANNUAL",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            goal_setting_start=date(2026, 4, 1),
            goal_setting_end=date(2026, 4, 15),
            self_appraisal_start=date(2026, 4, 16),
            self_appraisal_end=date(2026, 4, 25),
            manager_review_start=date(2026, 4, 26),
            manager_review_end=date(2026, 5, 5),
            calibration_start=date(2026, 5, 6),
            calibration_end=date(2026, 5, 10),
            rating_scale=5,
            weightage_goals=Decimal("70"),
            weightage_competencies=Decimal("30"),
            allow_self_rating=True,
            allow_peer_feedback=False,
            include_all_active_employees=False,
            employee_ids=[performance_employee.id],
        ),
        created_by=test_user.id,
    )


@pytest.mark.asyncio
async def test_performance_service_completes_full_cycle(
    performance_service,
    performance_employee,
    appraisal_cycle,
    test_user,
):
    cycle_id = appraisal_cycle.id

    started_cycle = await performance_service.start_cycle(cycle_id, test_user.id)
    assert started_cycle.status == "GOAL_SETTING"

    detail = await performance_service.create_goal(
        cycle_id=cycle_id,
        employee_id=performance_employee.id,
        data=PerformanceGoalCreate(
            title="Complete manual HR cycle",
            description="Validate the manual-first performance cycle.",
            category="HR",
            weightage=Decimal("100"),
            target_value="Cycle completed",
            measurement_criteria="Employee and manager submit their evaluations.",
            start_date=date(2026, 4, 1),
            due_date=date(2026, 5, 5),
        ),
        created_by=test_user.id,
    )
    assert detail.appraisal.status == "GOAL_SETTING"
    assert len(detail.goals) == 1

    detail = await performance_service.submit_goals(
        cycle_id=cycle_id,
        employee_id=performance_employee.id,
        updated_by=test_user.id,
    )
    assert detail.appraisal.status == "SELF_APPRAISAL"

    goal = detail.goals[0]
    detail = await performance_service.submit_self_appraisal(
        cycle_id=cycle_id,
        employee_id=performance_employee.id,
        data=PerformanceSelfAppraisalSubmit(
            goals=[
                PerformanceGoalSelfAssessment(
                    goal_id=goal.id,
                    self_rating=4,
                    self_progress=95,
                    self_comments="Completed the assigned HR cycle actions and validated the ESS flow.",
                    achievement_value="HR cycle closed",
                )
            ],
            competency_rating=4,
            self_summary="Delivered the required HR cycle tasks and completed the live employee packet.",
            self_achievements="Validated employee goal flow, self-appraisal, and persistence.",
            self_challenges="No material blockers remained after setup.",
            self_development_areas="Improve calibration commentary.",
            employee_comments="Ready for manager review.",
        ),
        updated_by=test_user.id,
    )
    assert detail.appraisal.status == "MANAGER_REVIEW"
    assert detail.appraisal.overall_rating is not None

    goal = detail.goals[0]
    detail = await performance_service.submit_manager_review(
        cycle_id=cycle_id,
        employee_id=performance_employee.id,
        data=PerformanceManagerReviewSubmit(
            goals=[
                PerformanceManagerGoalReview(
                    goal_id=goal.id,
                    manager_rating=4,
                    manager_comments="Strong execution across the manual-first performance workflow.",
                    final_rating=4,
                )
            ],
            competency_rating=4,
            manager_summary="Employee completed the workflow to the expected standard.",
            manager_achievements="Delivered the required cycle actions and evidence.",
            manager_improvements="Sharpen written calibration rationale.",
            manager_recommendations="Close after calibration.",
        ),
        updated_by=test_user.id,
    )
    assert detail.appraisal.status == "CALIBRATION"
    assert detail.appraisal.final_grade == "A"

    detail = await performance_service.calibrate_appraisal(
        cycle_id=cycle_id,
        employee_id=performance_employee.id,
        data=PerformanceCalibrationSubmit(
            calibrated_rating=4.25,
            calibration_notes="Final calibration confirmed.",
            final_grade="A",
        ),
        updated_by=test_user.id,
    )
    assert detail.appraisal.status == "COMPLETED"
    assert detail.appraisal.final_grade == "A"

    closed_cycle = await performance_service.close_cycle(cycle_id, test_user.id)
    assert closed_cycle.status == "COMPLETED"
