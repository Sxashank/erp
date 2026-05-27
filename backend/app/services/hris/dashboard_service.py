"""Service layer for HRIS dashboard metrics."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AttendanceStatus, EmploymentStatus, LeaveApplicationStatus
from app.models.hris.attendance import Attendance, AttendanceRegularization
from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveApplication
from app.models.hris.performance import AppraisalCycle, EmployeeAppraisal
from app.models.hris.separation import Separation, SeparationStatus
from app.models.hris.shift import Holiday
from app.models.hris.training import TrainingFeedback, TrainingNomination, TrainingProgram
from app.models.masters.department import Department
from app.models.masters.unit import Unit
from app.models.payroll.payroll import PayrollBatch, PayrollBatchStatus
from app.schemas.hris.dashboard import (
    HRDashboardPendingActionResponse,
    HRDashboardPayrollStatusResponse,
    HRDashboardResponse,
    HRDashboardStatsResponse,
    HRDashboardUpcomingEventResponse,
    HRDistributionItemResponse,
)


class HRDashboardService:
    """Business logic for HR dashboard."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(self, organization_id: UUID) -> HRDashboardResponse:
        today = date.today()
        month_start = today.replace(day=1)
        next_30_days = today + timedelta(days=30)

        active_statuses = [
            EmploymentStatus.ACTIVE,
            EmploymentStatus.PROBATION,
            EmploymentStatus.NOTICE_PERIOD,
        ]

        total_employees = await self._count(
            select(func.count(Employee.id)).where(Employee.organization_id == organization_id)
        )
        active_employees = await self._count(
            select(func.count(Employee.id)).where(
                Employee.organization_id == organization_id,
                Employee.employment_status.in_(active_statuses),
            )
        )
        new_joinees_this_month = await self._count(
            select(func.count(Employee.id)).where(
                Employee.organization_id == organization_id,
                Employee.date_of_joining >= month_start,
                Employee.date_of_joining <= today,
            )
        )
        separations_this_month = await self._count(
            select(func.count(Separation.id)).where(
                Separation.organization_id == organization_id,
                Separation.actual_last_working_date.is_not(None),
                Separation.actual_last_working_date >= month_start,
                Separation.actual_last_working_date <= today,
            )
        )
        pending_leave_approvals = await self._count(
            select(func.count(LeaveApplication.id)).where(
                LeaveApplication.organization_id == organization_id,
                LeaveApplication.status == LeaveApplicationStatus.PENDING,
            )
        )
        pending_regularizations = await self._count(
            select(func.count(AttendanceRegularization.id))
            .join(Employee, Employee.id == AttendanceRegularization.employee_id)
            .where(
                Employee.organization_id == organization_id,
                AttendanceRegularization.status == "PENDING",
            )
        )

        attendance_counts = await self._attendance_mix(organization_id, today)
        today_present = (
            attendance_counts.get(AttendanceStatus.PRESENT, 0)
            + attendance_counts.get(AttendanceStatus.LATE, 0)
            + attendance_counts.get(AttendanceStatus.EARLY_LEAVE, 0)
        )
        today_on_leave = attendance_counts.get(AttendanceStatus.ON_LEAVE, 0)
        today_absent = max(active_employees - today_present - today_on_leave, 0)
        attendance_percentage = (
            round((today_present / active_employees) * 100, 2) if active_employees else 0.0
        )

        upcoming_trainings = await self._count(
            select(func.count(TrainingProgram.id)).where(
                TrainingProgram.organization_id == organization_id,
                TrainingProgram.start_date >= today,
                TrainingProgram.start_date <= next_30_days,
                TrainingProgram.status.in_(["SCHEDULED", "IN_PROGRESS"]),
            )
        )
        active_cycles = await self._count(
            select(func.count(AppraisalCycle.id)).where(
                AppraisalCycle.organization_id == organization_id,
                AppraisalCycle.status.in_(["GOAL_SETTING", "IN_PROGRESS", "REVIEW", "CALIBRATION"]),
            )
        )
        pending_goals = await self._count(
            select(func.count(EmployeeAppraisal.id))
            .join(AppraisalCycle, AppraisalCycle.id == EmployeeAppraisal.appraisal_cycle_id)
            .where(
                AppraisalCycle.organization_id == organization_id,
                EmployeeAppraisal.status == "GOAL_SETTING",
            )
        )
        pending_appraisals = await self._count(
            select(func.count(EmployeeAppraisal.id))
            .join(AppraisalCycle, AppraisalCycle.id == EmployeeAppraisal.appraisal_cycle_id)
            .where(
                AppraisalCycle.organization_id == organization_id,
                EmployeeAppraisal.status.in_(["SELF_APPRAISAL", "MANAGER_REVIEW"]),
            )
        )

        payroll_status = await self._payroll_status(organization_id)

        stats = HRDashboardStatsResponse(
            total_employees=total_employees,
            active_employees=active_employees,
            new_joinees_this_month=new_joinees_this_month,
            separations_this_month=separations_this_month,
            pending_leave_approvals=pending_leave_approvals,
            pending_regularizations=pending_regularizations,
            today_present=today_present,
            today_absent=today_absent,
            today_on_leave=today_on_leave,
            attendance_percentage=attendance_percentage,
            upcoming_trainings=upcoming_trainings,
            active_cycles=active_cycles,
            pending_goals=pending_goals,
            pending_appraisals=pending_appraisals,
            payroll_ready_batches=payroll_status.approved_batches_this_year,
            payroll_pending_batches=payroll_status.processed_batches_this_year,
        )

        return HRDashboardResponse(
            stats=stats,
            pending_actions=await self._pending_actions(organization_id),
            upcoming_events=await self._upcoming_events(organization_id, today, next_30_days),
            department_distribution=await self._department_distribution(organization_id),
            unit_distribution=await self._unit_distribution(organization_id),
            training_completion=await self._training_completion(organization_id),
            separation_pipeline=await self._separation_pipeline(organization_id),
            payroll=payroll_status,
        )

    async def _count(self, query) -> int:
        result = await self.db.execute(query)
        return int(result.scalar() or 0)

    async def _attendance_mix(self, organization_id: UUID, attendance_date: date) -> dict[str, int]:
        result = await self.db.execute(
            select(Attendance.status, func.count(Attendance.id))
            .join(Employee, Employee.id == Attendance.employee_id)
            .where(
                Employee.organization_id == organization_id,
                Attendance.attendance_date == attendance_date,
            )
            .group_by(Attendance.status)
        )
        return {str(status): int(count) for status, count in result.all()}

    async def _department_distribution(
        self, organization_id: UUID
    ) -> list[HRDistributionItemResponse]:
        result = await self.db.execute(
            select(
                Department.name,
                func.count(Employee.id),
            )
            .join(Employee, Employee.department_id == Department.id)
            .where(Employee.organization_id == organization_id)
            .group_by(Department.name)
            .order_by(func.count(Employee.id).desc(), Department.name.asc())
            .limit(8)
        )
        return [
            HRDistributionItemResponse(label=name or "Unassigned", count=int(count))
            for name, count in result.all()
        ]

    async def _unit_distribution(self, organization_id: UUID) -> list[HRDistributionItemResponse]:
        result = await self.db.execute(
            select(Unit.name, func.count(Employee.id))
            .join(Employee, Employee.unit_id == Unit.id)
            .where(Employee.organization_id == organization_id)
            .group_by(Unit.name)
            .order_by(func.count(Employee.id).desc(), Unit.name.asc())
            .limit(8)
        )
        return [
            HRDistributionItemResponse(label=name or "Unassigned", count=int(count))
            for name, count in result.all()
        ]

    async def _training_completion(self, organization_id: UUID) -> list[HRDistributionItemResponse]:
        result = await self.db.execute(
            select(TrainingProgram.category, func.count(TrainingFeedback.id))
            .join(TrainingFeedback, TrainingFeedback.program_id == TrainingProgram.id)
            .where(TrainingProgram.organization_id == organization_id)
            .group_by(TrainingProgram.category)
            .order_by(func.count(TrainingFeedback.id).desc(), TrainingProgram.category.asc())
        )
        return [
            HRDistributionItemResponse(label=category or "General", count=int(count))
            for category, count in result.all()
        ]

    async def _separation_pipeline(self, organization_id: UUID) -> list[HRDistributionItemResponse]:
        result = await self.db.execute(
            select(Separation.status, func.count(Separation.id))
            .where(Separation.organization_id == organization_id)
            .group_by(Separation.status)
            .order_by(func.count(Separation.id).desc(), Separation.status.asc())
        )
        return [
            HRDistributionItemResponse(label=str(status), count=int(count))
            for status, count in result.all()
        ]

    async def _payroll_status(self, organization_id: UUID) -> HRDashboardPayrollStatusResponse:
        latest_batch_result = await self.db.execute(
            select(PayrollBatch)
            .where(PayrollBatch.organization_id == organization_id)
            .order_by(PayrollBatch.payroll_year.desc(), PayrollBatch.payroll_month.desc())
            .limit(1)
        )
        latest_batch = latest_batch_result.scalar_one_or_none()
        current_year = date.today().year
        counts_result = await self.db.execute(
            select(PayrollBatch.status, func.count(PayrollBatch.id))
            .where(
                PayrollBatch.organization_id == organization_id,
                PayrollBatch.payroll_year.in_([current_year - 1, current_year, current_year + 1]),
            )
            .group_by(PayrollBatch.status)
        )
        counts = {str(status): int(count) for status, count in counts_result.all()}
        return HRDashboardPayrollStatusResponse(
            latest_batch_id=latest_batch.id if latest_batch else None,
            latest_batch_number=latest_batch.batch_number if latest_batch else None,
            latest_batch_status=latest_batch.status if latest_batch else None,
            processed_batches_this_year=counts.get(PayrollBatchStatus.PROCESSED, 0),
            approved_batches_this_year=counts.get(PayrollBatchStatus.APPROVED, 0),
            paid_batches_this_year=counts.get(PayrollBatchStatus.PAID, 0),
        )

    async def _pending_actions(
        self, organization_id: UUID
    ) -> list[HRDashboardPendingActionResponse]:
        actions: list[HRDashboardPendingActionResponse] = []

        leave_result = await self.db.execute(
            select(LeaveApplication, Employee)
            .join(Employee, Employee.id == LeaveApplication.employee_id)
            .where(
                LeaveApplication.organization_id == organization_id,
                LeaveApplication.status == LeaveApplicationStatus.PENDING,
            )
            .order_by(LeaveApplication.created_at.desc())
            .limit(5)
        )
        for leave, employee in leave_result.all():
            actions.append(
                HRDashboardPendingActionResponse(
                    id=leave.id,
                    type="LEAVE",
                    title="Leave request pending approval",
                    employee=employee.full_name,
                    request_date=leave.from_date,
                    status=str(leave.status),
                )
            )

        regularization_result = await self.db.execute(
            select(AttendanceRegularization, Employee)
            .join(Employee, Employee.id == AttendanceRegularization.employee_id)
            .where(
                Employee.organization_id == organization_id,
                AttendanceRegularization.status == "PENDING",
            )
            .order_by(AttendanceRegularization.created_at.desc())
            .limit(5)
        )
        for regularization, employee in regularization_result.all():
            actions.append(
                HRDashboardPendingActionResponse(
                    id=regularization.id,
                    type="REGULARIZATION",
                    title=f"Attendance regularization: {regularization.request_type}",
                    employee=employee.full_name,
                    request_date=regularization.attendance_date,
                    status=str(regularization.status),
                )
            )

        appraisal_result = await self.db.execute(
            select(EmployeeAppraisal, Employee)
            .join(Employee, Employee.id == EmployeeAppraisal.employee_id)
            .join(AppraisalCycle, AppraisalCycle.id == EmployeeAppraisal.appraisal_cycle_id)
            .where(
                AppraisalCycle.organization_id == organization_id,
                EmployeeAppraisal.status.in_(["SELF_APPRAISAL", "MANAGER_REVIEW"]),
            )
            .order_by(
                EmployeeAppraisal.updated_at.desc().nullslast(), EmployeeAppraisal.created_at.desc()
            )
            .limit(5)
        )
        for appraisal, employee in appraisal_result.all():
            actions.append(
                HRDashboardPendingActionResponse(
                    id=appraisal.id,
                    type="APPRAISAL",
                    title=f"Performance review pending: {appraisal.status}",
                    employee=employee.full_name,
                    request_date=(appraisal.updated_at or appraisal.created_at).date(),
                    status=str(appraisal.status),
                )
            )

        separation_result = await self.db.execute(
            select(Separation, Employee)
            .join(Employee, Employee.id == Separation.employee_id)
            .where(
                Separation.organization_id == organization_id,
                Separation.status.in_(
                    [
                        SeparationStatus.PENDING_APPROVAL,
                        SeparationStatus.CLEARANCE,
                        SeparationStatus.FNF_PENDING,
                    ]
                ),
            )
            .order_by(Separation.created_at.desc())
            .limit(5)
        )
        for separation, employee in separation_result.all():
            actions.append(
                HRDashboardPendingActionResponse(
                    id=separation.id,
                    type="SEPARATION",
                    title=f"Separation workflow: {separation.separation_type}",
                    employee=employee.full_name,
                    request_date=separation.initiation_date,
                    status=str(separation.status),
                )
            )

        training_result = await self.db.execute(
            select(TrainingNomination, Employee, TrainingProgram)
            .join(Employee, Employee.id == TrainingNomination.employee_id)
            .join(TrainingProgram, TrainingProgram.id == TrainingNomination.program_id)
            .where(
                TrainingProgram.organization_id == organization_id,
                TrainingNomination.status.in_(["NOMINATED", "CONFIRMED"]),
            )
            .order_by(TrainingProgram.start_date.asc())
            .limit(5)
        )
        for nomination, employee, program in training_result.all():
            actions.append(
                HRDashboardPendingActionResponse(
                    id=nomination.id,
                    type="TRAINING",
                    title=f"Training nomination: {program.title}",
                    employee=employee.full_name,
                    request_date=program.start_date,
                    status=str(nomination.status),
                )
            )

        return sorted(actions, key=lambda item: item.request_date, reverse=True)[:10]

    async def _upcoming_events(
        self,
        organization_id: UUID,
        today: date,
        next_30_days: date,
    ) -> list[HRDashboardUpcomingEventResponse]:
        events: list[HRDashboardUpcomingEventResponse] = []

        holiday_result = await self.db.execute(
            select(Holiday)
            .where(Holiday.holiday_date >= today, Holiday.holiday_date <= next_30_days)
            .order_by(Holiday.holiday_date.asc())
            .limit(5)
        )
        for holiday in holiday_result.scalars().all():
            events.append(
                HRDashboardUpcomingEventResponse(
                    id=f"holiday:{holiday.id}",
                    type="HOLIDAY",
                    title=holiday.holiday_name,
                    date=holiday.holiday_date,
                )
            )

        training_result = await self.db.execute(
            select(TrainingProgram)
            .where(
                TrainingProgram.organization_id == organization_id,
                TrainingProgram.start_date >= today,
                TrainingProgram.start_date <= next_30_days,
            )
            .order_by(TrainingProgram.start_date.asc())
            .limit(5)
        )
        for program in training_result.scalars().all():
            events.append(
                HRDashboardUpcomingEventResponse(
                    id=f"training:{program.id}",
                    type="TRAINING",
                    title=program.title,
                    date=program.start_date,
                )
            )

        appraisal_due_result = await self.db.execute(
            select(AppraisalCycle)
            .where(
                AppraisalCycle.organization_id == organization_id,
                AppraisalCycle.self_appraisal_end.is_not(None),
                AppraisalCycle.self_appraisal_end >= today,
                AppraisalCycle.self_appraisal_end <= next_30_days,
                AppraisalCycle.status.in_(["GOAL_SETTING", "IN_PROGRESS", "REVIEW"]),
            )
            .order_by(AppraisalCycle.self_appraisal_end.asc())
            .limit(5)
        )
        for cycle in appraisal_due_result.scalars().all():
            events.append(
                HRDashboardUpcomingEventResponse(
                    id=f"cycle:{cycle.id}",
                    type="APPRAISAL_DUE",
                    title=f"{cycle.name} self-appraisal closes",
                    date=cycle.self_appraisal_end or cycle.end_date,
                )
            )

        anniversary_result = await self.db.execute(
            select(Employee)
            .where(
                Employee.organization_id == organization_id,
                Employee.employment_status.in_(
                    [EmploymentStatus.ACTIVE, EmploymentStatus.PROBATION]
                ),
            )
            .limit(100)
        )
        anniversary_count = sum(
            1
            for employee in anniversary_result.scalars().all()
            if today <= employee.date_of_joining.replace(year=today.year) <= next_30_days
        )
        if anniversary_count:
            events.append(
                HRDashboardUpcomingEventResponse(
                    id="anniversary:next30",
                    type="ANNIVERSARY",
                    title="Work anniversaries due",
                    date=today,
                    count=anniversary_count,
                )
            )

        return sorted(events, key=lambda item: item.date)[:10]
