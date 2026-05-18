"""Leave service for HRIS module."""

import builtins
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import LeaveApplicationStatus
from app.models.hris.employee import Employee
from app.models.hris.leave import (
    LeaveApplication,
    LeaveBalance,
    LeaveType,
)
from app.schemas.hris.leave import (
    LeaveApplicationCreate,
    LeaveApplicationFilters,
    LeaveApplicationUpdate,
    LeaveBalanceCreate,
    LeaveTypeCreate,
    LeaveTypeUpdate,
)
from app.services.hris.shift_service import HolidayService


class LeaveTypeService:
    """Service for leave type operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: LeaveTypeCreate, created_by: UUID) -> LeaveType:
        """Create a new leave type."""
        leave_type = LeaveType(**data.model_dump(), created_by=created_by)
        self.db.add(leave_type)
        await self.db.flush()
        await self.db.refresh(leave_type)
        return leave_type

    async def get(self, leave_type_id: UUID) -> LeaveType | None:
        """Get leave type by ID."""
        result = await self.db.execute(select(LeaveType).where(LeaveType.id == leave_type_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, organization_id: UUID, leave_code: str) -> LeaveType | None:
        """Get leave type by code."""
        result = await self.db.execute(
            select(LeaveType).where(
                LeaveType.organization_id == organization_id,
                LeaveType.leave_code == leave_code,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        active_only: bool = True,
    ) -> list[LeaveType]:
        """List leave types for organization."""
        query = select(LeaveType).where(LeaveType.organization_id == organization_id)
        if active_only:
            query = query.where(LeaveType.is_active == True)
        query = query.order_by(LeaveType.display_order, LeaveType.leave_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, leave_type_id: UUID, data: LeaveTypeUpdate, updated_by: UUID
    ) -> LeaveType | None:
        """Update leave type."""
        leave_type = await self.get(leave_type_id)
        if not leave_type:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(leave_type, field, value)

        leave_type.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(leave_type)
        return leave_type

    async def delete(self, leave_type_id: UUID) -> bool:
        """Soft delete leave type."""
        leave_type = await self.get(leave_type_id)
        if not leave_type:
            return False

        leave_type.is_active = False
        await self.db.flush()
        return True


class LeaveBalanceService:
    """Service for leave balance operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(
        self, employee_id: UUID, leave_type_id: UUID, year: int
    ) -> LeaveBalance | None:
        """Get leave balance for employee/type/year."""
        result = await self.db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_balances(self, employee_id: UUID, year: int) -> list[LeaveBalance]:
        """Get all leave balances for employee in a year."""
        result = await self.db.execute(
            select(LeaveBalance)
            .where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year,
            )
            .options(selectinload(LeaveBalance.leave_type))
        )
        return list(result.scalars().all())

    async def create_or_update(self, data: LeaveBalanceCreate, user_id: UUID) -> LeaveBalance:
        """Create or update leave balance."""
        existing = await self.get_balance(data.employee_id, data.leave_type_id, data.year)
        if existing:
            update_data = data.model_dump(exclude={"employee_id", "leave_type_id", "year"})
            for field, value in update_data.items():
                setattr(existing, field, value)
            existing.updated_by = user_id
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            balance = LeaveBalance(**data.model_dump(), created_by=user_id)
            self.db.add(balance)
            await self.db.flush()
            await self.db.refresh(balance)
            return balance

    async def update_used(
        self, employee_id: UUID, leave_type_id: UUID, year: int, days: Decimal
    ) -> None:
        """Update used days in balance."""
        balance = await self.get_balance(employee_id, leave_type_id, year)
        if balance:
            balance.used = balance.used + days
            await self.db.flush()

    async def initialize_balances(
        self, employee_id: UUID, organization_id: UUID, year: int, user_id: UUID
    ) -> list[LeaveBalance]:
        """Initialize leave balances for a new year."""
        # Get all active leave types for organization
        result = await self.db.execute(
            select(LeaveType).where(
                LeaveType.organization_id == organization_id,
                LeaveType.is_active == True,
            )
        )
        leave_types = result.scalars().all()

        balances = []
        for leave_type in leave_types:
            existing = await self.get_balance(employee_id, leave_type.id, year)
            if not existing:
                balance = LeaveBalance(
                    employee_id=employee_id,
                    leave_type_id=leave_type.id,
                    year=year,
                    opening_balance=Decimal("0"),
                    accrued=leave_type.annual_quota,
                    created_by=user_id,
                )
                self.db.add(balance)
                balances.append(balance)

        await self.db.flush()
        return balances


class LeaveApplicationService:
    """Service for leave application operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_application_number(self, organization_id: UUID) -> str:
        """Generate leave application number."""
        today = date.today()
        prefix = f"LV{today.strftime('%y%m')}"

        # Count applications this month
        result = await self.db.execute(
            select(func.count(LeaveApplication.id))
            .join(Employee)
            .where(
                Employee.organization_id == organization_id,
                LeaveApplication.application_number.like(f"{prefix}%"),
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(4)}"

    async def calculate_working_days(
        self,
        organization_id: UUID,
        employee_id: UUID,
        from_date: date,
        to_date: date,
        leave_type: LeaveType,
    ) -> tuple[Decimal, Decimal]:
        """Calculate total days and working days for leave period."""
        total_days = (to_date - from_date).days + 1

        # Get employee for week off
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        week_off_days = employee.week_off_days if employee else ["SUNDAY"]

        # Get holidays
        holiday_service = HolidayService(self.db)
        holidays = await holiday_service.get_holidays_between(organization_id, from_date, to_date)
        holiday_dates = {h.holiday_date for h in holidays}

        # Calculate working days
        working_days = Decimal("0")
        current = from_date
        while current <= to_date:
            is_week_off = current.strftime("%A").upper() in week_off_days
            is_holiday = current in holiday_dates

            if leave_type.can_club_with_weekoff and is_week_off:
                pass  # Don't count
            elif leave_type.can_club_with_holidays and is_holiday:
                pass  # Don't count
            else:
                working_days += Decimal("1")

            current += timedelta(days=1)

        return Decimal(str(total_days)), working_days

    async def create(self, data: LeaveApplicationCreate, created_by: UUID) -> LeaveApplication:
        """Create leave application."""
        # Get employee's organization
        result = await self.db.execute(select(Employee).where(Employee.id == data.employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            raise ValueError("Employee not found")

        # Get leave type
        result = await self.db.execute(select(LeaveType).where(LeaveType.id == data.leave_type_id))
        leave_type = result.scalar_one_or_none()
        if not leave_type:
            raise ValueError("Leave type not found")

        # Generate application number
        application_number = await self.generate_application_number(employee.organization_id)

        # Calculate days
        total_days, working_days = await self.calculate_working_days(
            employee.organization_id,
            data.employee_id,
            data.from_date,
            data.to_date,
            leave_type,
        )

        # Adjust for half day
        if data.is_half_day:
            total_days = Decimal("0.5")
            working_days = Decimal("0.5")

        # Create application
        application = LeaveApplication(
            **data.model_dump(),
            application_number=application_number,
            total_days=total_days,
            working_days=working_days,
            status=LeaveApplicationStatus.PENDING,
            created_by=created_by,
        )
        self.db.add(application)
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def get(self, application_id: UUID) -> LeaveApplication | None:
        """Get leave application by ID."""
        result = await self.db.execute(
            select(LeaveApplication)
            .where(LeaveApplication.id == application_id)
            .options(
                selectinload(LeaveApplication.employee),
                selectinload(LeaveApplication.leave_type),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: LeaveApplicationFilters,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[LeaveApplication], int]:
        """List leave applications with filters."""
        query = select(LeaveApplication).options(
            selectinload(LeaveApplication.employee),
            selectinload(LeaveApplication.leave_type),
        )

        conditions = []
        if filters.organization_id:
            query = query.join(Employee)
            conditions.append(Employee.organization_id == filters.organization_id)
        if filters.employee_id:
            conditions.append(LeaveApplication.employee_id == filters.employee_id)
        if filters.leave_type_id:
            conditions.append(LeaveApplication.leave_type_id == filters.leave_type_id)
        if filters.status:
            conditions.append(LeaveApplication.status == filters.status)
        if filters.from_date:
            conditions.append(LeaveApplication.from_date >= filters.from_date)
        if filters.to_date:
            conditions.append(LeaveApplication.to_date <= filters.to_date)
        if filters.department_id:
            if Employee not in [m.entity for m in query.froms]:
                query = query.join(Employee)
            conditions.append(Employee.department_id == filters.department_id)
        if filters.reporting_manager_id:
            if Employee not in [m.entity for m in query.froms]:
                query = query.join(Employee)
            conditions.append(Employee.reporting_manager_id == filters.reporting_manager_id)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(LeaveApplication.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            if filters.organization_id or filters.department_id or filters.reporting_manager_id:
                count_query = count_query.join(Employee)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(LeaveApplication.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        applications = list(result.scalars().all())

        return applications, total

    async def update(
        self, application_id: UUID, data: LeaveApplicationUpdate, updated_by: UUID
    ) -> LeaveApplication | None:
        """Update leave application (only if PENDING)."""
        application = await self.get(application_id)
        if not application:
            return None

        if application.status != LeaveApplicationStatus.PENDING:
            raise ValueError("Can only update pending applications")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)

        # Recalculate days if dates changed
        if data.from_date or data.to_date:
            result = await self.db.execute(
                select(Employee).where(Employee.id == application.employee_id)
            )
            employee = result.scalar_one_or_none()
            total_days, working_days = await self.calculate_working_days(
                employee.organization_id,
                application.employee_id,
                application.from_date,
                application.to_date,
                application.leave_type,
            )
            application.total_days = total_days
            application.working_days = working_days

        application.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def approve(
        self, application_id: UUID, remarks: str | None, approved_by: UUID
    ) -> LeaveApplication | None:
        """Approve leave application.

        §8.4 maker-checker: an employee cannot approve their own leave.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        application = await self.get(application_id)
        if not application:
            return None

        if application.status != LeaveApplicationStatus.PENDING:
            raise ValueError("Can only approve pending applications")

        ensure_maker_is_not_checker(
            maker_user_id=application.created_by,
            checker_user_id=approved_by,
        )

        # Update balance
        balance_service = LeaveBalanceService(self.db)
        year = application.from_date.year
        await balance_service.update_used(
            application.employee_id,
            application.leave_type_id,
            year,
            application.working_days,
        )

        application.status = LeaveApplicationStatus.APPROVED
        application.approved_by = approved_by
        application.approved_at = date.today()
        application.approver_remarks = remarks
        application.updated_by = approved_by
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def reject(
        self, application_id: UUID, reason: str, rejected_by: UUID
    ) -> LeaveApplication | None:
        """Reject leave application."""
        application = await self.get(application_id)
        if not application:
            return None

        if application.status != LeaveApplicationStatus.PENDING:
            raise ValueError("Can only reject pending applications")

        application.status = LeaveApplicationStatus.REJECTED
        application.rejected_by = rejected_by
        application.rejected_at = date.today()
        application.rejection_reason = reason
        application.updated_by = rejected_by
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def cancel(
        self, application_id: UUID, reason: str, cancelled_by: UUID
    ) -> LeaveApplication | None:
        """Cancel leave application."""
        application = await self.get(application_id)
        if not application:
            return None

        if application.status not in [
            LeaveApplicationStatus.PENDING,
            LeaveApplicationStatus.APPROVED,
        ]:
            raise ValueError("Can only cancel pending or approved applications")

        # If approved, restore balance
        if application.status == LeaveApplicationStatus.APPROVED:
            balance_service = LeaveBalanceService(self.db)
            year = application.from_date.year
            await balance_service.update_used(
                application.employee_id,
                application.leave_type_id,
                year,
                -application.working_days,  # Negative to restore
            )

        application.status = LeaveApplicationStatus.CANCELLED
        application.cancelled_at = date.today()
        application.cancellation_reason = reason
        application.updated_by = cancelled_by
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def get_pending_for_approval(
        self, manager_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[builtins.list[LeaveApplication], int]:
        """Get pending leave applications for manager approval."""
        filters = LeaveApplicationFilters(
            reporting_manager_id=manager_id,
            status=LeaveApplicationStatus.PENDING,
        )
        return await self.list(filters, skip, limit)
