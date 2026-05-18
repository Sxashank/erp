"""ESS Profile and Payslip Service."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveBalance, LeaveApplication
from app.models.hris.attendance import Attendance
from app.models.payroll.payroll import PayrollBatch, PayrollStatutory, Payslip
from app.models.ess.ess_user import ESSUser, ProfileUpdateRequest
from app.models.ess.enums import ProfileUpdateType, ProfileUpdateStatus


class ESSProfileService:
    """Service for ESS Profile and Payslip management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def payslip_period(payslip: Payslip) -> str:
        if payslip.batch:
            return f"{payslip.batch.payroll_year}-{payslip.batch.payroll_month:02d}"
        return ""

    # ==================== Profile ====================

    async def get_employee_profile(
        self,
        employee_id: UUID,
    ) -> Optional[Employee]:
        """Get employee profile details."""
        query = select(Employee).where(
            Employee.id == employee_id
        ).options(
            selectinload(Employee.department),
            selectinload(Employee.designation),
            selectinload(Employee.unit),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_update_request_number(self, organization_id: UUID) -> str:
        """Generate unique profile update request number."""
        today = date.today()
        prefix = f"PUR{today.strftime('%Y%m')}"

        query = select(func.count()).select_from(ProfileUpdateRequest).where(
            and_(
                ProfileUpdateRequest.organization_id == organization_id,
                ProfileUpdateRequest.request_number.like(f"{prefix}%")
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return f"{prefix}{count + 1:04d}"

    async def request_profile_update(
        self,
        organization_id: UUID,
        ess_user_id: UUID,
        employee_id: UUID,
        update_type: ProfileUpdateType,
        current_values: dict,
        requested_values: dict,
        change_reason: Optional[str] = None,
        attachments: Optional[dict] = None,
    ) -> ProfileUpdateRequest:
        """Create a profile update request."""
        request_number = await self.generate_update_request_number(organization_id)

        request = ProfileUpdateRequest(
            organization_id=organization_id,
            ess_user_id=ess_user_id,
            employee_id=employee_id,
            request_number=request_number,
            update_type=update_type,
            current_values=current_values,
            requested_values=requested_values,
            change_reason=change_reason,
            attachments=attachments,
            status=ProfileUpdateStatus.PENDING,
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_profile_update_requests(
        self,
        employee_id: UUID,
        status: Optional[ProfileUpdateStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ProfileUpdateRequest], int]:
        """Get profile update requests for an employee."""
        query = select(ProfileUpdateRequest).where(
            ProfileUpdateRequest.employee_id == employee_id
        )

        if status:
            query = query.where(ProfileUpdateRequest.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(ProfileUpdateRequest.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def approve_profile_update(
        self,
        request_id: UUID,
        reviewer_id: UUID,
        remarks: Optional[str] = None,
    ) -> Optional[ProfileUpdateRequest]:
        """Approve a profile update request and apply changes."""
        query = select(ProfileUpdateRequest).where(
            ProfileUpdateRequest.id == request_id
        )
        result = await self.session.execute(query)
        request = result.scalar_one_or_none()

        if not request:
            return None

        if request.status != ProfileUpdateStatus.PENDING:
            raise ValueError("Request is not pending")

        # Apply changes to employee
        employee = await self.get_employee_profile(request.employee_id)
        if employee:
            for key, value in request.requested_values.items():
                if hasattr(employee, key):
                    setattr(employee, key, value)

        # Update request status
        request.status = ProfileUpdateStatus.APPROVED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.utcnow()
        request.reviewer_remarks = remarks

        await self.session.flush()
        return request

    async def reject_profile_update(
        self,
        request_id: UUID,
        reviewer_id: UUID,
        reason: str,
    ) -> Optional[ProfileUpdateRequest]:
        """Reject a profile update request."""
        query = select(ProfileUpdateRequest).where(
            ProfileUpdateRequest.id == request_id
        )
        result = await self.session.execute(query)
        request = result.scalar_one_or_none()

        if not request:
            return None

        if request.status != ProfileUpdateStatus.PENDING:
            raise ValueError("Request is not pending")

        request.status = ProfileUpdateStatus.REJECTED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.utcnow()
        request.reviewer_remarks = reason

        await self.session.flush()
        return request

    # ==================== Payslip ====================

    async def get_payslips(
        self,
        employee_id: UUID,
        financial_year: Optional[str] = None,
        limit: int = 12,
        offset: int = 0,
    ) -> Tuple[List[Payslip], int]:
        """Get payslips for an employee."""
        query = (
            select(Payslip)
            .join(PayrollBatch)
            .options(selectinload(Payslip.batch))
            .where(Payslip.employee_id == employee_id)
        )

        if financial_year:
            # Parse FY like "2024-25"
            start_year = int(financial_year.split("-")[0])
            query = query.where(
                (
                    (PayrollBatch.payroll_year == start_year)
                    & (PayrollBatch.payroll_month >= 4)
                )
                | (
                    (PayrollBatch.payroll_year == start_year + 1)
                    & (PayrollBatch.payroll_month <= 3)
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination (most recent first)
        query = query.order_by(PayrollBatch.payroll_year.desc(), PayrollBatch.payroll_month.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_payslip_by_id(
        self,
        payslip_id: UUID,
        employee_id: UUID,
    ) -> Optional[Payslip]:
        """Get a specific payslip."""
        query = select(Payslip).options(selectinload(Payslip.batch)).where(
            and_(
                Payslip.id == payslip_id,
                Payslip.employee_id == employee_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_payslip_by_period(
        self,
        employee_id: UUID,
        pay_period: str,
    ) -> Optional[Payslip]:
        """Get payslip for a specific period."""
        year, month = (int(part) for part in pay_period.split("-"))
        query = select(Payslip).join(PayrollBatch).where(
            and_(
                Payslip.employee_id == employee_id,
                PayrollBatch.payroll_year == year,
                PayrollBatch.payroll_month == month,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ytd_summary(
        self,
        employee_id: UUID,
        financial_year: Optional[str] = None,
    ) -> dict:
        """Get year-to-date salary summary."""
        # Determine date range for financial year
        if financial_year:
            start_year = int(financial_year.split("-")[0])
        else:
            today = date.today()
            if today.month >= 4:
                start_year = today.year
            else:
                start_year = today.year - 1

        query = select(
            func.sum(Payslip.gross_salary).label("total_gross"),
            func.sum(Payslip.total_deductions).label("total_deductions"),
            func.sum(Payslip.net_salary).label("total_net"),
            func.count().label("months_processed"),
        ).join(PayrollBatch).where(
            and_(
                Payslip.employee_id == employee_id,
                (
                    (
                        (PayrollBatch.payroll_year == start_year)
                        & (PayrollBatch.payroll_month >= 4)
                    )
                    | (
                        (PayrollBatch.payroll_year == start_year + 1)
                        & (PayrollBatch.payroll_month <= 3)
                    )
                ),
            )
        )

        result = await self.session.execute(query)
        row = result.one()

        tax_result = await self.session.execute(
            select(func.sum(PayrollStatutory.employee_amount))
            .join(Payslip, PayrollStatutory.payslip_id == Payslip.id)
            .join(PayrollBatch, Payslip.batch_id == PayrollBatch.id)
            .where(
                and_(
                    Payslip.employee_id == employee_id,
                    PayrollStatutory.statutory_type == "TDS",
                    (
                        (
                            (PayrollBatch.payroll_year == start_year)
                            & (PayrollBatch.payroll_month >= 4)
                        )
                        | (
                            (PayrollBatch.payroll_year == start_year + 1)
                            & (PayrollBatch.payroll_month <= 3)
                        )
                    ),
                )
            )
        )

        return {
            "financial_year": f"{start_year}-{str(start_year + 1)[-2:]}",
            "total_gross": float(row.total_gross or 0),
            "total_deductions": float(row.total_deductions or 0),
            "total_net": float(row.total_net or 0),
            "total_tax": float(tax_result.scalar() or 0),
            "months_processed": row.months_processed or 0,
        }

    # ==================== Leave ====================

    async def get_leave_balances(
        self,
        employee_id: UUID,
    ) -> List[LeaveBalance]:
        """Get leave balances for an employee."""
        query = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id
        ).options(
            selectinload(LeaveBalance.leave_type)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_leave_applications(
        self,
        employee_id: UUID,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[LeaveApplication], int]:
        """Get leave applications for an employee."""
        query = select(LeaveApplication).where(
            LeaveApplication.employee_id == employee_id
        )

        if status:
            query = query.where(LeaveApplication.status == status)
        if from_date:
            query = query.where(LeaveApplication.from_date >= from_date)
        if to_date:
            query = query.where(LeaveApplication.to_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(LeaveApplication.created_at.desc())
        query = query.offset(offset).limit(limit)
        query = query.options(selectinload(LeaveApplication.leave_type))

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    # ==================== Attendance ====================

    async def get_attendance(
        self,
        employee_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[Attendance]:
        """Get attendance records for an employee."""
        query = select(Attendance).where(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date >= from_date,
                Attendance.attendance_date <= to_date,
            )
        ).order_by(Attendance.attendance_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_attendance_summary(
        self,
        employee_id: UUID,
        month: str,  # YYYY-MM format
    ) -> dict:
        """Get attendance summary for a month."""
        # Parse month
        year, month_num = map(int, month.split("-"))
        from datetime import calendar
        _, last_day = calendar.monthrange(year, month_num)
        start_date = date(year, month_num, 1)
        end_date = date(year, month_num, last_day)

        query = select(
            Attendance.status,
            func.count().label("count"),
        ).where(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date,
            )
        ).group_by(Attendance.status)

        result = await self.session.execute(query)
        rows = result.all()

        summary = {
            "month": month,
            "working_days": 0,
            "present": 0,
            "absent": 0,
            "leave": 0,
            "holiday": 0,
            "half_day": 0,
            "work_from_home": 0,
            "late_arrivals": 0,
            "early_departures": 0,
            "by_status": {}
        }

        for row in rows:
            status = row.status if row.status else "UNKNOWN"
            summary["by_status"][status] = row.count

            if status == "PRESENT":
                summary["present"] += row.count
                summary["working_days"] += row.count
            elif status == "ABSENT":
                summary["absent"] += row.count
            elif status == "LEAVE":
                summary["leave"] += row.count
            elif status == "HOLIDAY":
                summary["holiday"] += row.count
            elif status == "HALF_DAY":
                summary["half_day"] += row.count
                summary["working_days"] += 0.5
            elif status == "WFH":
                summary["work_from_home"] += row.count
                summary["working_days"] += row.count

        return summary

    # ==================== Dashboard ====================

    async def get_dashboard_data(
        self,
        employee_id: UUID,
    ) -> dict:
        """Get dashboard data for ESS home page."""
        # Get employee
        employee = await self.get_employee_profile(employee_id)
        if not employee:
            return {}

        # Get leave balances
        leave_balances = await self.get_leave_balances(employee_id)

        # Get recent payslip
        payslips, _ = await self.get_payslips(employee_id, limit=1)
        latest_payslip = payslips[0] if payslips else None

        # Get this month's attendance
        today = date.today()
        month_str = today.strftime("%Y-%m")
        attendance_summary = await self.get_attendance_summary(employee_id, month_str)

        # Get pending requests count
        pending_profile_requests, _ = await self.get_profile_update_requests(
            employee_id, status=ProfileUpdateStatus.PENDING
        )

        return {
            "employee": {
                "id": str(employee.id),
                "code": employee.employee_code,
                "name": f"{employee.first_name} {employee.last_name}",
                "designation": employee.designation.name if employee.designation else None,
                "department": employee.department.name if employee.department else None,
                "date_of_joining": employee.date_of_joining.isoformat() if employee.date_of_joining else None,
            },
            "leave_balance": [
                {
                    "type": lb.leave_type.name if lb.leave_type else None,
                    "code": lb.leave_type.code if lb.leave_type else None,
                    "balance": float(lb.balance),
                    "used": float(lb.used),
                }
                for lb in leave_balances
            ],
            "latest_payslip": {
                "period": self.payslip_period(latest_payslip),
                "gross": float(latest_payslip.gross_salary),
                "net": float(latest_payslip.net_salary),
            } if latest_payslip else None,
            "attendance_this_month": attendance_summary,
            "pending_requests": len(pending_profile_requests),
        }
