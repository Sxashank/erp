"""Attendance service for HRIS module."""

from datetime import date, time, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hris.attendance import (
    AttendancePunch,
    Attendance,
    AttendanceRegularization,
    MonthlyAttendanceSummary,
)
from app.models.hris.employee import Employee
from app.models.hris.shift import Shift
from app.models.hris.leave import LeaveApplication
from app.schemas.hris.attendance import (
    AttendancePunchCreate,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceFilters,
    AttendanceRegularizationCreate,
    AttendanceRegularizationFilters,
    ProcessDailyAttendanceRequest,
    ProcessMonthlyAttendanceRequest,
    AttendanceProcessingResult,
)
from app.core.constants import (
    AttendanceStatus,
    AttendanceSource,
    RegularizationStatus,
    LeaveApplicationStatus,
    EmploymentStatus,
)
from app.services.hris.shift_service import HolidayService


class AttendanceService:
    """Service for attendance operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Punch Operations
    # ============================================
    async def record_punch(
        self, data: AttendancePunchCreate, created_by: Optional[UUID] = None
    ) -> AttendancePunch:
        """Record an attendance punch."""
        punch = AttendancePunch(**data.model_dump())
        if created_by:
            punch.created_by = created_by
        self.db.add(punch)
        await self.db.commit()
        await self.db.refresh(punch)
        return punch

    async def get_punches(
        self, employee_id: UUID, punch_date: date
    ) -> List[AttendancePunch]:
        """Get all punches for an employee on a date."""
        start_dt = datetime.combine(punch_date, time.min)
        end_dt = datetime.combine(punch_date, time.max)

        result = await self.db.execute(
            select(AttendancePunch)
            .where(
                AttendancePunch.employee_id == employee_id,
                AttendancePunch.punch_datetime >= start_dt,
                AttendancePunch.punch_datetime <= end_dt,
            )
            .order_by(AttendancePunch.punch_datetime)
        )
        return list(result.scalars().all())

    # ============================================
    # Attendance Operations
    # ============================================
    async def get_attendance(
        self, employee_id: UUID, attendance_date: date
    ) -> Optional[Attendance]:
        """Get attendance for an employee on a date."""
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, attendance_id: UUID) -> Optional[Attendance]:
        """Get attendance by ID."""
        result = await self.db.execute(
            select(Attendance)
            .where(Attendance.id == attendance_id)
            .options(
                selectinload(Attendance.employee),
                selectinload(Attendance.shift),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: AttendanceFilters,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Attendance], int]:
        """List attendance records with filters."""
        query = select(Attendance).options(
            selectinload(Attendance.employee),
            selectinload(Attendance.shift),
        )

        conditions = []
        if filters.organization_id:
            query = query.join(Employee)
            conditions.append(Employee.organization_id == filters.organization_id)
        if filters.employee_id:
            conditions.append(Attendance.employee_id == filters.employee_id)
        if filters.department_id:
            if Employee not in [m.entity for m in query.froms]:
                query = query.join(Employee)
            conditions.append(Employee.department_id == filters.department_id)
        if filters.shift_id:
            conditions.append(Attendance.shift_id == filters.shift_id)
        if filters.status:
            conditions.append(Attendance.status == filters.status)
        if filters.from_date:
            conditions.append(Attendance.attendance_date >= filters.from_date)
        if filters.to_date:
            conditions.append(Attendance.attendance_date <= filters.to_date)
        if filters.is_processed is not None:
            conditions.append(Attendance.is_processed == filters.is_processed)
        if filters.is_locked is not None:
            conditions.append(Attendance.is_locked == filters.is_locked)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(Attendance.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            if filters.organization_id or filters.department_id:
                count_query = count_query.join(Employee)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(
            Attendance.attendance_date.desc(),
            Attendance.employee_id,
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def create_or_update(
        self, data: AttendanceCreate, user_id: UUID
    ) -> Attendance:
        """Create or update attendance."""
        existing = await self.get_attendance(data.employee_id, data.attendance_date)
        if existing:
            update_data = data.model_dump(exclude={"employee_id", "attendance_date"})
            for field, value in update_data.items():
                setattr(existing, field, value)
            existing.updated_by = user_id
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            attendance = Attendance(**data.model_dump(), created_by=user_id)
            self.db.add(attendance)
            await self.db.commit()
            await self.db.refresh(attendance)
            return attendance

    async def update(
        self, attendance_id: UUID, data: AttendanceUpdate, updated_by: UUID
    ) -> Optional[Attendance]:
        """Update attendance."""
        attendance = await self.get_by_id(attendance_id)
        if not attendance:
            return None

        if attendance.is_locked:
            raise ValueError("Cannot update locked attendance")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attendance, field, value)

        attendance.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    # ============================================
    # Daily Processing
    # ============================================
    async def process_daily_attendance(
        self, request: ProcessDailyAttendanceRequest, user_id: UUID
    ) -> AttendanceProcessingResult:
        """Process daily attendance for employees."""
        result = AttendanceProcessingResult(
            total_employees=0,
            processed=0,
            skipped=0,
            errors=[],
        )

        # Get employees
        query = select(Employee).where(
            Employee.organization_id == request.organization_id,
            Employee.employment_status == EmploymentStatus.ACTIVE,
        )
        if request.employee_ids:
            query = query.where(Employee.id.in_(request.employee_ids))

        emp_result = await self.db.execute(query)
        employees = emp_result.scalars().all()
        result.total_employees = len(employees)

        holiday_service = HolidayService(self.db)

        for employee in employees:
            try:
                await self._process_employee_attendance(
                    employee, request.attendance_date, holiday_service, user_id
                )
                result.processed += 1
            except Exception as e:
                result.errors.append({
                    "employee_id": str(employee.id),
                    "employee_code": employee.employee_code,
                    "error": str(e),
                })
                result.skipped += 1

        await self.db.commit()
        return result

    async def _process_employee_attendance(
        self,
        employee: Employee,
        attendance_date: date,
        holiday_service: HolidayService,
        user_id: UUID,
    ) -> Attendance:
        """Process attendance for a single employee."""
        # Check if already processed
        existing = await self.get_attendance(employee.id, attendance_date)
        if existing and existing.is_processed:
            return existing

        # Get punches
        punches = await self.get_punches(employee.id, attendance_date)

        # Get shift
        shift = None
        if employee.shift_id:
            result = await self.db.execute(
                select(Shift).where(Shift.id == employee.shift_id)
            )
            shift = result.scalar_one_or_none()

        # Check for holiday
        holiday = await holiday_service.is_holiday(
            employee.organization_id, attendance_date, employee.unit_id
        )

        # Check for week off
        week_off_days = employee.week_off_days or ["SUNDAY"]
        is_week_off = attendance_date.strftime("%A").upper() in week_off_days

        # Check for approved leave
        leave_result = await self.db.execute(
            select(LeaveApplication).where(
                LeaveApplication.employee_id == employee.id,
                LeaveApplication.status == LeaveApplicationStatus.APPROVED,
                LeaveApplication.from_date <= attendance_date,
                LeaveApplication.to_date >= attendance_date,
            )
        )
        leave_application = leave_result.scalar_one_or_none()

        # Determine status and calculate times
        status = AttendanceStatus.ABSENT
        first_in = None
        last_out = None
        total_work_minutes = 0
        late_minutes = 0
        early_leave_minutes = 0
        overtime_minutes = 0

        if holiday:
            status = AttendanceStatus.HOLIDAY
        elif is_week_off:
            status = AttendanceStatus.WEEK_OFF
        elif leave_application:
            status = AttendanceStatus.ON_LEAVE
        elif punches:
            # Calculate from punches
            in_punches = [p for p in punches if p.punch_type == "IN"]
            out_punches = [p for p in punches if p.punch_type == "OUT"]

            if in_punches:
                first_in = in_punches[0].punch_datetime.time()
            if out_punches:
                last_out = out_punches[-1].punch_datetime.time()

            if first_in and last_out:
                # Calculate work minutes
                first_in_minutes = first_in.hour * 60 + first_in.minute
                last_out_minutes = last_out.hour * 60 + last_out.minute
                total_work_minutes = last_out_minutes - first_in_minutes

                if shift:
                    # Calculate late minutes
                    scheduled_in_minutes = shift.start_time.hour * 60 + shift.start_time.minute
                    if first_in_minutes > scheduled_in_minutes + shift.grace_period_late_minutes:
                        late_minutes = first_in_minutes - scheduled_in_minutes

                    # Calculate early leave
                    scheduled_out_minutes = shift.end_time.hour * 60 + shift.end_time.minute
                    if last_out_minutes < scheduled_out_minutes - shift.grace_period_early_minutes:
                        early_leave_minutes = scheduled_out_minutes - last_out_minutes

                    # Calculate overtime
                    if shift.overtime_applicable and total_work_minutes > shift.working_hours:
                        overtime_minutes = total_work_minutes - shift.working_hours

                # Determine status
                if total_work_minutes >= (shift.working_hours if shift else 480):
                    status = AttendanceStatus.PRESENT
                    if late_minutes > 0:
                        status = AttendanceStatus.LATE
                elif total_work_minutes >= (shift.half_day_hours if shift else 240):
                    status = AttendanceStatus.HALF_DAY
                else:
                    status = AttendanceStatus.ABSENT
            elif first_in:
                status = AttendanceStatus.HALF_DAY  # Only punch in, no out

        # Create/update attendance
        attendance_data = AttendanceCreate(
            employee_id=employee.id,
            attendance_date=attendance_date,
            shift_id=employee.shift_id,
            scheduled_in=shift.start_time if shift else None,
            scheduled_out=shift.end_time if shift else None,
            first_in=first_in,
            last_out=last_out,
            all_punches=[
                {"time": p.punch_datetime.isoformat(), "type": p.punch_type}
                for p in punches
            ],
            status=status,
            total_work_minutes=total_work_minutes,
            effective_work_minutes=total_work_minutes,
            late_minutes=late_minutes,
            early_leave_minutes=early_leave_minutes,
            overtime_minutes=overtime_minutes,
            leave_application_id=leave_application.id if leave_application else None,
            leave_type_id=leave_application.leave_type_id if leave_application else None,
            is_holiday=holiday is not None,
            holiday_name=holiday.holiday_name if holiday else None,
            is_week_off=is_week_off,
            is_processed=True,
        )

        return await self.create_or_update(attendance_data, user_id)

    # ============================================
    # Regularization Operations
    # ============================================
    async def create_regularization(
        self, data: AttendanceRegularizationCreate, created_by: UUID
    ) -> AttendanceRegularization:
        """Create attendance regularization request."""
        regularization = AttendanceRegularization(
            **data.model_dump(),
            status=RegularizationStatus.PENDING,
            created_by=created_by,
        )
        self.db.add(regularization)
        await self.db.commit()
        await self.db.refresh(regularization)
        return regularization

    async def get_regularization(
        self, regularization_id: UUID
    ) -> Optional[AttendanceRegularization]:
        """Get regularization by ID."""
        result = await self.db.execute(
            select(AttendanceRegularization)
            .where(AttendanceRegularization.id == regularization_id)
            .options(selectinload(AttendanceRegularization.employee))
        )
        return result.scalar_one_or_none()

    async def list_regularizations(
        self,
        filters: AttendanceRegularizationFilters,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AttendanceRegularization], int]:
        """List regularization requests."""
        query = select(AttendanceRegularization).options(
            selectinload(AttendanceRegularization.employee)
        )

        conditions = []
        if filters.organization_id:
            query = query.join(Employee)
            conditions.append(Employee.organization_id == filters.organization_id)
        if filters.employee_id:
            conditions.append(AttendanceRegularization.employee_id == filters.employee_id)
        if filters.department_id:
            if Employee not in [m.entity for m in query.froms]:
                query = query.join(Employee)
            conditions.append(Employee.department_id == filters.department_id)
        if filters.status:
            conditions.append(AttendanceRegularization.status == filters.status)
        if filters.request_type:
            conditions.append(AttendanceRegularization.request_type == filters.request_type)
        if filters.from_date:
            conditions.append(AttendanceRegularization.attendance_date >= filters.from_date)
        if filters.to_date:
            conditions.append(AttendanceRegularization.attendance_date <= filters.to_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Count
        count_query = select(func.count(AttendanceRegularization.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            if filters.organization_id or filters.department_id:
                count_query = count_query.join(Employee)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AttendanceRegularization.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def approve_regularization(
        self, regularization_id: UUID, remarks: Optional[str], approved_by: UUID
    ) -> Optional[AttendanceRegularization]:
        """Approve regularization and update attendance."""
        regularization = await self.get_regularization(regularization_id)
        if not regularization:
            return None

        if regularization.status != RegularizationStatus.PENDING:
            raise ValueError("Can only approve pending regularizations")

        # Update attendance
        attendance = await self.get_attendance(
            regularization.employee_id, regularization.attendance_date
        )
        if attendance:
            if regularization.requested_first_in:
                attendance.first_in = regularization.requested_first_in
            if regularization.requested_last_out:
                attendance.last_out = regularization.requested_last_out
            if regularization.requested_status:
                attendance.status = AttendanceStatus(regularization.requested_status)
            attendance.is_regularized = True
            attendance.regularization_id = regularization.id
            attendance.updated_by = approved_by

        regularization.status = RegularizationStatus.APPROVED
        regularization.approved_by = approved_by
        regularization.approved_at = date.today()
        regularization.approver_remarks = remarks
        regularization.updated_by = approved_by
        await self.db.commit()
        await self.db.refresh(regularization)
        return regularization

    async def reject_regularization(
        self, regularization_id: UUID, reason: str, rejected_by: UUID
    ) -> Optional[AttendanceRegularization]:
        """Reject regularization."""
        regularization = await self.get_regularization(regularization_id)
        if not regularization:
            return None

        if regularization.status != RegularizationStatus.PENDING:
            raise ValueError("Can only reject pending regularizations")

        regularization.status = RegularizationStatus.REJECTED
        regularization.rejected_by = rejected_by
        regularization.rejected_at = date.today()
        regularization.rejection_reason = reason
        regularization.updated_by = rejected_by
        await self.db.commit()
        await self.db.refresh(regularization)
        return regularization

    # ============================================
    # Monthly Summary
    # ============================================
    async def process_monthly_summary(
        self, request: ProcessMonthlyAttendanceRequest, user_id: UUID
    ) -> AttendanceProcessingResult:
        """Process monthly attendance summary for payroll."""
        result = AttendanceProcessingResult(
            total_employees=0,
            processed=0,
            skipped=0,
            errors=[],
        )

        # Get employees
        query = select(Employee).where(
            Employee.organization_id == request.organization_id,
            Employee.employment_status == EmploymentStatus.ACTIVE,
        )
        if request.employee_ids:
            query = query.where(Employee.id.in_(request.employee_ids))

        emp_result = await self.db.execute(query)
        employees = emp_result.scalars().all()
        result.total_employees = len(employees)

        for employee in employees:
            try:
                await self._calculate_monthly_summary(
                    employee, request.year, request.month, user_id
                )
                result.processed += 1
            except Exception as e:
                result.errors.append({
                    "employee_id": str(employee.id),
                    "employee_code": employee.employee_code,
                    "error": str(e),
                })
                result.skipped += 1

        await self.db.commit()
        return result

    async def _calculate_monthly_summary(
        self, employee: Employee, year: int, month: int, user_id: UUID
    ) -> MonthlyAttendanceSummary:
        """Calculate monthly summary for an employee."""
        # Get all attendance for the month
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        first_day = date(year, month, 1)
        last_day = date(year, month, days_in_month)

        result = await self.db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee.id,
                Attendance.attendance_date >= first_day,
                Attendance.attendance_date <= last_day,
            )
        )
        attendances = result.scalars().all()

        # Calculate counts
        present_days = Decimal("0")
        absent_days = Decimal("0")
        half_days = Decimal("0")
        late_days = 0
        early_leave_days = 0
        holidays = 0
        week_offs = 0
        on_leave = Decimal("0")
        total_late_minutes = 0
        total_overtime_hours = Decimal("0")

        leave_breakdown: Dict[str, Decimal] = {}

        for att in attendances:
            if att.status == AttendanceStatus.PRESENT:
                present_days += Decimal("1")
            elif att.status == AttendanceStatus.HALF_DAY:
                half_days += Decimal("1")
            elif att.status == AttendanceStatus.ABSENT:
                absent_days += Decimal("1")
            elif att.status == AttendanceStatus.HOLIDAY:
                holidays += 1
            elif att.status == AttendanceStatus.WEEK_OFF:
                week_offs += 1
            elif att.status == AttendanceStatus.ON_LEAVE:
                on_leave += Decimal("1")
                if att.leave_type_id:
                    leave_id = str(att.leave_type_id)
                    leave_breakdown[leave_id] = leave_breakdown.get(leave_id, Decimal("0")) + Decimal("1")
            elif att.status == AttendanceStatus.LATE:
                present_days += Decimal("1")
                late_days += 1
                total_late_minutes += att.late_minutes

            if att.early_leave_minutes > 0:
                early_leave_days += 1

            total_overtime_hours += Decimal(str(att.overtime_minutes)) / 60

        # Calculate working days and payable days
        working_days = days_in_month - holidays - week_offs
        payable_days = present_days + half_days * Decimal("0.5") + on_leave

        # Calculate LOP
        lop_days = Decimal(str(working_days)) - payable_days
        if lop_days < 0:
            lop_days = Decimal("0")

        # Create or update summary
        existing = await self.db.execute(
            select(MonthlyAttendanceSummary).where(
                MonthlyAttendanceSummary.employee_id == employee.id,
                MonthlyAttendanceSummary.year == year,
                MonthlyAttendanceSummary.month == month,
            )
        )
        summary = existing.scalar_one_or_none()

        if summary:
            summary.total_days = days_in_month
            summary.working_days = working_days
            summary.holidays = holidays
            summary.week_offs = week_offs
            summary.present_days = present_days
            summary.absent_days = absent_days
            summary.half_days = half_days
            summary.late_days = late_days
            summary.early_leave_days = early_leave_days
            summary.paid_leave_days = on_leave  # Assuming all leaves are paid
            summary.leave_breakdown = leave_breakdown
            summary.total_overtime_hours = total_overtime_hours
            summary.total_late_minutes = total_late_minutes
            summary.payable_days = payable_days
            summary.lop_days = lop_days
            summary.is_processed = True
            summary.processed_at = datetime.now()
            summary.updated_by = user_id
        else:
            summary = MonthlyAttendanceSummary(
                employee_id=employee.id,
                year=year,
                month=month,
                total_days=days_in_month,
                working_days=working_days,
                holidays=holidays,
                week_offs=week_offs,
                present_days=present_days,
                absent_days=absent_days,
                half_days=half_days,
                late_days=late_days,
                early_leave_days=early_leave_days,
                paid_leave_days=on_leave,
                leave_breakdown=leave_breakdown,
                total_overtime_hours=total_overtime_hours,
                total_late_minutes=total_late_minutes,
                payable_days=payable_days,
                lop_days=lop_days,
                is_processed=True,
                processed_at=datetime.now(),
                created_by=user_id,
            )
            self.db.add(summary)

        return summary

    async def lock_monthly_attendance(
        self, organization_id: UUID, year: int, month: int, user_id: UUID
    ) -> int:
        """Lock monthly attendance for payroll."""
        result = await self.db.execute(
            select(MonthlyAttendanceSummary)
            .join(Employee)
            .where(
                Employee.organization_id == organization_id,
                MonthlyAttendanceSummary.year == year,
                MonthlyAttendanceSummary.month == month,
                MonthlyAttendanceSummary.is_locked == False,
            )
        )
        summaries = result.scalars().all()

        for summary in summaries:
            summary.is_locked = True
            summary.locked_at = datetime.now()
            summary.updated_by = user_id

        await self.db.commit()
        return len(summaries)
