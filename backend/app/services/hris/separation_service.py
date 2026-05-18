"""
Separation Service

Business logic for employee separation, clearance, and Full & Final settlement.
Handles:
- Resignation/termination/retirement initiation
- Clearance workflow management
- FnF calculation including gratuity, leave encashment, recoveries
"""

import builtins
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveBalance
from app.models.hris.separation import (
    ClearanceChecklist,
    ClearanceStatus,
    FnFSettlement,
    FnFStatus,
    ResignationReason,
    Separation,
    SeparationClearance,
    SeparationStatus,
    SeparationType,
)
from app.models.payroll.salary_component import EmployeeSalary, EmployeeSalaryComponent

# Constants
GRATUITY_YEARS_REQUIRED = Decimal("5")
GRATUITY_MAX_AMOUNT = Decimal("2000000")  # ₹20 Lakhs max
GRATUITY_FORMULA_DAYS = 15
GRATUITY_DIVISOR = 26
LEAVE_ENCASHMENT_DIVISOR = 26  # Days in working month


class SeparationService:
    """Service for separation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_separation(
        self,
        organization_id: UUID,
        employee_id: UUID,
        separation_type: SeparationType,
        requested_last_working_date: date,
        reason_category: ResignationReason | None = None,
        reason_detail: str | None = None,
        resignation_letter_path: str | None = None,
        created_by: UUID = None,
    ) -> Separation:
        """
        Initiate employee separation process.

        Args:
            organization_id: Organization ID
            employee_id: Employee being separated
            separation_type: Type of separation (resignation, termination, etc.)
            requested_last_working_date: Requested last working date
            reason_category: Category of resignation reason
            reason_detail: Detailed reason
            resignation_letter_path: Path to resignation letter
            created_by: User initiating the separation

        Returns:
            Created Separation object
        """
        # Get employee
        employee = await self._get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Check for existing active separation
        existing = await self.db.execute(
            select(Separation).where(
                and_(
                    Separation.employee_id == employee_id,
                    Separation.status.notin_(
                        [
                            SeparationStatus.COMPLETED,
                            SeparationStatus.WITHDRAWN,
                            SeparationStatus.REJECTED,
                        ]
                    ),
                    Separation.is_active == True,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Employee already has an active separation process")

        # Create separation
        separation = Separation(
            organization_id=organization_id,
            employee_id=employee_id,
            separation_type=separation_type,
            status=SeparationStatus.INITIATED,
            initiation_date=date.today(),
            requested_last_working_date=requested_last_working_date,
            notice_period_days=employee.notice_period_days or 30,
            reason_category=reason_category,
            reason_detail=reason_detail,
            resignation_letter_path=resignation_letter_path,
            created_by=created_by,
        )
        self.db.add(separation)
        await self.db.flush()
        await self.db.refresh(separation)

        return separation

    async def approve_separation(
        self,
        separation_id: UUID,
        approved_last_working_date: date,
        approved_by: UUID,
        remarks: str | None = None,
    ) -> Separation:
        """
        Approve separation and set final last working date.

        Args:
            separation_id: Separation ID
            approved_last_working_date: Approved last working date
            approved_by: Approving user
            remarks: Optional approval remarks

        Returns:
            Updated Separation object
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        separation = await self.get(separation_id)
        if not separation:
            raise ValueError(f"Separation {separation_id} not found")

        if separation.status not in [SeparationStatus.INITIATED, SeparationStatus.PENDING_APPROVAL]:
            raise ValueError(f"Separation cannot be approved in status: {separation.status}")

        # §8.4: initiator (the employee OR HR who filed) cannot approve.
        ensure_maker_is_not_checker(
            maker_user_id=separation.created_by,
            checker_user_id=approved_by,
        )

        # Calculate notice period served
        notice_served = (approved_last_working_date - separation.initiation_date).days
        notice_shortfall = max(0, separation.notice_period_days - notice_served)

        separation.status = SeparationStatus.APPROVED
        separation.approved_last_working_date = approved_last_working_date
        separation.approved_by = approved_by
        separation.approved_at = datetime.utcnow()
        separation.notice_period_served = notice_served
        separation.notice_period_shortfall = notice_shortfall

        if remarks:
            separation.remarks = remarks

        # Initialize clearance items
        await self._initialize_clearance(separation)

        await self.db.flush()
        await self.db.refresh(separation)

        return separation

    async def reject_separation(
        self,
        separation_id: UUID,
        rejection_reason: str,
        rejected_by: UUID,
    ) -> Separation:
        """Reject a separation request."""
        separation = await self.get(separation_id)
        if not separation:
            raise ValueError(f"Separation {separation_id} not found")

        separation.status = SeparationStatus.REJECTED
        separation.rejection_reason = rejection_reason
        separation.approved_by = rejected_by
        separation.approved_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(separation)

        return separation

    async def withdraw_separation(
        self,
        separation_id: UUID,
        withdrawn_by: UUID,
        reason: str | None = None,
    ) -> Separation:
        """Withdraw a separation request (by employee)."""
        separation = await self.get(separation_id)
        if not separation:
            raise ValueError(f"Separation {separation_id} not found")

        if separation.status in [SeparationStatus.COMPLETED, SeparationStatus.FNF_PAID]:
            raise ValueError("Cannot withdraw a completed separation")

        separation.status = SeparationStatus.WITHDRAWN
        if reason:
            separation.remarks = f"Withdrawn: {reason}"

        await self.db.flush()
        await self.db.refresh(separation)

        return separation

    async def get(self, separation_id: UUID) -> Separation | None:
        """Get separation by ID with related data."""
        result = await self.db.execute(
            select(Separation)
            .options(
                selectinload(Separation.employee),
                selectinload(Separation.clearances).selectinload(SeparationClearance.checklist),
                selectinload(Separation.fnf_settlement),
            )
            .where(Separation.id == separation_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        status: SeparationStatus | None = None,
        separation_type: SeparationType | None = None,
        employee_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Separation], int]:
        """List separations with filters."""
        query = select(Separation).where(
            and_(
                Separation.organization_id == organization_id,
                Separation.is_active == True,
            )
        )

        if status:
            query = query.where(Separation.status == status)
        if separation_type:
            query = query.where(Separation.separation_type == separation_type)
        if employee_id:
            query = query.where(Separation.employee_id == employee_id)
        if from_date:
            query = query.where(Separation.initiation_date >= from_date)
        if to_date:
            query = query.where(Separation.initiation_date <= to_date)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Results
        query = query.options(selectinload(Separation.employee))
        query = query.order_by(Separation.initiation_date.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)

        return result.scalars().all(), total

    async def _initialize_clearance(self, separation: Separation) -> None:
        """Initialize clearance items for a separation."""
        # Get clearance checklist for organization
        result = await self.db.execute(
            select(ClearanceChecklist)
            .where(
                and_(
                    ClearanceChecklist.organization_id == separation.organization_id,
                    ClearanceChecklist.is_active == True,
                )
            )
            .order_by(ClearanceChecklist.display_order)
        )
        checklist_items = result.scalars().all()

        for item in checklist_items:
            clearance = SeparationClearance(
                separation_id=separation.id,
                checklist_id=item.id,
                status=ClearanceStatus.PENDING,
                created_by=separation.created_by,
            )
            self.db.add(clearance)

        # Update separation status to clearance if all approvals done
        separation.status = SeparationStatus.NOTICE_PERIOD

    async def _get_employee(self, employee_id: UUID) -> Employee | None:
        """Get employee with related data."""
        result = await self.db.execute(
            select(Employee)
            .options(
                selectinload(Employee.salaries).selectinload(EmployeeSalary.components),
            )
            .where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()


class ClearanceService:
    """Service for clearance operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_clearance(
        self,
        clearance_id: UUID,
        status: ClearanceStatus,
        cleared_by: UUID,
        has_recovery: bool = False,
        recovery_amount: Decimal | None = None,
        recovery_description: str | None = None,
        remarks: str | None = None,
    ) -> SeparationClearance:
        """Update clearance item status."""
        result = await self.db.execute(
            select(SeparationClearance).where(SeparationClearance.id == clearance_id)
        )
        clearance = result.scalar_one_or_none()
        if not clearance:
            raise ValueError(f"Clearance item {clearance_id} not found")

        clearance.status = status
        clearance.cleared_by = cleared_by
        clearance.cleared_at = datetime.utcnow()
        clearance.has_recovery = has_recovery
        clearance.recovery_amount = recovery_amount
        clearance.recovery_description = recovery_description
        clearance.remarks = remarks

        await self.db.flush()
        await self.db.refresh(clearance)

        # Check if all clearances are done
        await self._check_clearance_complete(clearance.separation_id)

        return clearance

    async def get_clearance_status(self, separation_id: UUID) -> dict[str, Any]:
        """Get overall clearance status for a separation."""
        result = await self.db.execute(
            select(SeparationClearance)
            .options(selectinload(SeparationClearance.checklist))
            .where(SeparationClearance.separation_id == separation_id)
        )
        clearances = result.scalars().all()

        total = len(clearances)
        cleared = sum(
            1
            for c in clearances
            if c.status in [ClearanceStatus.CLEARED, ClearanceStatus.NOT_APPLICABLE]
        )
        pending = sum(1 for c in clearances if c.status == ClearanceStatus.PENDING)
        recovery_pending = sum(
            1 for c in clearances if c.status == ClearanceStatus.RECOVERY_PENDING
        )
        total_recovery = sum(c.recovery_amount or Decimal("0") for c in clearances)

        return {
            "total_items": total,
            "cleared": cleared,
            "pending": pending,
            "recovery_pending": recovery_pending,
            "total_recovery_amount": total_recovery,
            "is_complete": pending == 0 and recovery_pending == 0,
            "items": [
                {
                    "id": str(c.id),
                    "checklist_item": c.checklist.checklist_item if c.checklist else None,
                    "status": c.status,
                    "has_recovery": c.has_recovery,
                    "recovery_amount": c.recovery_amount,
                    "cleared_at": c.cleared_at,
                }
                for c in clearances
            ],
        }

    async def _check_clearance_complete(self, separation_id: UUID) -> None:
        """Check if all clearance items are complete and update separation status."""
        status = await self.get_clearance_status(separation_id)
        if status["is_complete"]:
            result = await self.db.execute(select(Separation).where(Separation.id == separation_id))
            separation = result.scalar_one_or_none()
            if separation and separation.status == SeparationStatus.CLEARANCE:
                separation.status = SeparationStatus.FNF_PENDING
                await self.db.flush()


class FnFService:
    """Service for Full & Final settlement operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_fnf(
        self,
        separation_id: UUID,
        calculated_by: UUID,
        include_gratuity: bool = True,
        include_leave_encashment: bool = True,
        additional_earnings: dict[str, Decimal] | None = None,
        additional_deductions: dict[str, Decimal] | None = None,
    ) -> FnFSettlement:
        """
        Calculate Full & Final settlement for a separation.

        Calculates:
        - Pending salary (prorated for the last month)
        - Leave encashment (Basic/26 × leave balance days)
        - Gratuity (15/26 × last drawn salary × years of service, if eligible)
        - Notice period recovery (if shortfall)
        - Clearance recoveries
        - TDS on FnF components

        Args:
            separation_id: Separation ID
            calculated_by: User performing calculation
            include_gratuity: Whether to include gratuity
            include_leave_encashment: Whether to include leave encashment
            additional_earnings: Additional earnings to include
            additional_deductions: Additional deductions to include

        Returns:
            Calculated FnFSettlement
        """
        # Get separation with employee data
        result = await self.db.execute(
            select(Separation)
            .options(
                selectinload(Separation.employee)
                .selectinload(Employee.salaries)
                .selectinload(EmployeeSalary.components),
                selectinload(Separation.clearances),
            )
            .where(Separation.id == separation_id)
        )
        separation = result.scalar_one_or_none()
        if not separation:
            raise ValueError(f"Separation {separation_id} not found")

        employee = separation.employee
        last_working_date = (
            separation.approved_last_working_date or separation.requested_last_working_date
        )

        # Get active salary
        salary = await self._get_active_salary(employee.id)
        if not salary:
            raise ValueError(f"No active salary found for employee {employee.id}")

        # Calculate basic and gross salary from components
        basic_salary = self._get_component_amount(salary, "BASIC")
        gross_monthly = salary.monthly_gross

        # Calculate years of service
        years_of_service = self._calculate_years_of_service(
            employee.date_of_joining, last_working_date
        )

        # Initialize FnF settlement
        fnf = FnFSettlement(
            separation_id=separation_id,
            employee_id=employee.id,
            last_working_date=last_working_date,
            status=FnFStatus.DRAFT,
            created_by=calculated_by,
        )

        # 1. Calculate pending salary (prorated for last month)
        pending_salary = await self._calculate_pending_salary(
            employee.id, last_working_date, gross_monthly
        )
        fnf.pending_salary = pending_salary

        # 2. Calculate leave encashment
        if include_leave_encashment:
            leave_encashment, leave_days = await self._calculate_leave_encashment(
                employee.id, basic_salary
            )
            fnf.leave_encashment = leave_encashment
            fnf.leave_encashment_days = leave_days

        # 3. Calculate gratuity
        if include_gratuity:
            gratuity, is_eligible = self._calculate_gratuity(basic_salary, years_of_service)
            fnf.gratuity_amount = gratuity
            fnf.gratuity_years = years_of_service
            fnf.gratuity_eligible = is_eligible
            fnf.gratuity_basic_salary = basic_salary
            fnf.gratuity_calculation_method = "15/26"

        # 4. Calculate notice recovery
        if separation.notice_period_shortfall > 0 and not separation.is_notice_buyout:
            daily_salary = gross_monthly / Decimal("30")
            fnf.notice_recovery = (
                daily_salary * Decimal(str(separation.notice_period_shortfall))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fnf.notice_shortfall_days = separation.notice_period_shortfall

        # 5. Calculate clearance recovery
        clearance_recovery = await self._calculate_clearance_recovery(separation_id)
        fnf.clearance_recovery = clearance_recovery

        # 6. Add additional earnings/deductions
        if additional_earnings:
            fnf.other_earnings = sum(additional_earnings.values())
            fnf.other_earnings_detail = additional_earnings

        if additional_deductions:
            fnf.other_deductions = sum(additional_deductions.values())
            fnf.other_deductions_detail = additional_deductions

        # 7. Calculate totals
        fnf.calculate_totals()

        # 8. Calculate TDS on FnF (simplified - should integrate with TDS module)
        fnf.tds_amount = await self._calculate_fnf_tds(
            fnf.total_earnings, fnf.gratuity_amount, employee.pan_number
        )
        fnf.total_deductions += fnf.tds_amount
        fnf.net_payable = fnf.total_earnings - fnf.total_deductions

        # Store calculation details for audit
        fnf.calculation_details = {
            "basic_salary": str(basic_salary),
            "gross_monthly": str(gross_monthly),
            "years_of_service": str(years_of_service),
            "date_of_joining": str(employee.date_of_joining),
            "last_working_date": str(last_working_date),
            "calculated_at": datetime.utcnow().isoformat(),
        }

        fnf.calculated_by = calculated_by
        fnf.calculated_at = datetime.utcnow()
        fnf.status = FnFStatus.CALCULATED

        # Check for existing FnF and update or create
        existing_result = await self.db.execute(
            select(FnFSettlement).where(FnFSettlement.separation_id == separation_id)
        )
        existing_fnf = existing_result.scalar_one_or_none()

        if existing_fnf:
            # Update existing
            for attr in [
                "pending_salary",
                "leave_encashment",
                "leave_encashment_days",
                "gratuity_amount",
                "gratuity_years",
                "gratuity_eligible",
                "gratuity_basic_salary",
                "gratuity_calculation_method",
                "bonus_amount",
                "pending_reimbursements",
                "other_earnings",
                "other_earnings_detail",
                "total_earnings",
                "notice_recovery",
                "notice_shortfall_days",
                "advance_recovery",
                "loan_recovery",
                "asset_recovery",
                "clearance_recovery",
                "other_deductions",
                "other_deductions_detail",
                "tds_amount",
                "total_deductions",
                "net_payable",
                "calculation_details",
                "calculated_by",
                "calculated_at",
                "status",
                "last_working_date",
            ]:
                setattr(existing_fnf, attr, getattr(fnf, attr))
            fnf = existing_fnf
        else:
            self.db.add(fnf)

        # Update separation status
        separation.status = SeparationStatus.FNF_CALCULATED

        await self.db.flush()
        await self.db.refresh(fnf)

        return fnf

    async def approve_fnf(
        self,
        fnf_id: UUID,
        approved_by: UUID,
        remarks: str | None = None,
    ) -> FnFSettlement:
        """Approve FnF settlement.

        §8.4 maker-checker: the user who calculated the FnF cannot also
        approve it — FnF involves real cash disbursement.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        fnf = await self.get(fnf_id)
        if not fnf:
            raise ValueError(f"FnF Settlement {fnf_id} not found")

        if fnf.status != FnFStatus.CALCULATED:
            raise ValueError(f"FnF cannot be approved in status: {fnf.status}")

        ensure_maker_is_not_checker(
            maker_user_id=fnf.created_by,
            checker_user_id=approved_by,
        )

        fnf.status = FnFStatus.APPROVED
        fnf.approved_by = approved_by
        fnf.approved_at = datetime.utcnow()
        if remarks:
            fnf.remarks = remarks

        # Update separation status
        fnf.separation.status = SeparationStatus.FNF_APPROVED

        await self.db.flush()
        await self.db.refresh(fnf)

        return fnf

    async def process_payment(
        self,
        fnf_id: UUID,
        payment_date: date,
        payment_mode: str,
        payment_reference: str,
        processed_by: UUID,
    ) -> FnFSettlement:
        """Process FnF payment."""
        fnf = await self.get(fnf_id)
        if not fnf:
            raise ValueError(f"FnF Settlement {fnf_id} not found")

        if fnf.status != FnFStatus.APPROVED:
            raise ValueError(f"FnF cannot be paid in status: {fnf.status}")

        fnf.status = FnFStatus.PAID
        fnf.payment_date = payment_date
        fnf.payment_mode = payment_mode
        fnf.payment_reference = payment_reference
        fnf.settlement_date = date.today()

        # Get employee bank details
        employee = fnf.separation.employee
        if employee.bank_accounts:
            primary_bank = next((b for b in employee.bank_accounts if b.is_primary), None)
            if primary_bank:
                fnf.bank_account_number = primary_bank.account_number
                fnf.bank_ifsc = primary_bank.ifsc_code

        # Update separation status
        fnf.separation.status = SeparationStatus.FNF_PAID

        await self.db.flush()
        await self.db.refresh(fnf)

        return fnf

    async def get(self, fnf_id: UUID) -> FnFSettlement | None:
        """Get FnF settlement by ID."""
        result = await self.db.execute(
            select(FnFSettlement)
            .options(
                selectinload(FnFSettlement.separation).selectinload(Separation.employee),
            )
            .where(FnFSettlement.id == fnf_id)
        )
        return result.scalar_one_or_none()

    async def get_by_separation(self, separation_id: UUID) -> FnFSettlement | None:
        """Get FnF settlement by separation ID."""
        result = await self.db.execute(
            select(FnFSettlement)
            .options(
                selectinload(FnFSettlement.separation).selectinload(Separation.employee),
            )
            .where(FnFSettlement.separation_id == separation_id)
        )
        return result.scalar_one_or_none()

    async def _get_active_salary(self, employee_id: UUID) -> EmployeeSalary | None:
        """Get employee's active salary."""
        result = await self.db.execute(
            select(EmployeeSalary)
            .options(
                selectinload(EmployeeSalary.components).selectinload(
                    EmployeeSalaryComponent.component
                )
            )
            .where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.status == "ACTIVE",
                )
            )
        )
        return result.scalar_one_or_none()

    def _get_component_amount(self, salary: EmployeeSalary, component_code: str) -> Decimal:
        """Get amount for a specific salary component."""
        for comp in salary.components:
            if comp.component and comp.component.component_code == component_code:
                return comp.monthly_amount
        return Decimal("0")

    def _calculate_years_of_service(self, joining_date: date, last_working_date: date) -> Decimal:
        """Calculate years of service with decimal precision."""
        days = (last_working_date - joining_date).days
        years = Decimal(str(days)) / Decimal("365.25")
        return years.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def _calculate_pending_salary(
        self,
        employee_id: UUID,
        last_working_date: date,
        monthly_gross: Decimal,
    ) -> Decimal:
        """Calculate pending salary for partial month."""
        # Days worked in the last month
        month_start = date(last_working_date.year, last_working_date.month, 1)
        days_in_month = 30  # Standard month days
        days_worked = (last_working_date - month_start).days + 1

        daily_salary = monthly_gross / Decimal(str(days_in_month))
        pending = (daily_salary * Decimal(str(days_worked))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return pending

    async def _calculate_leave_encashment(
        self,
        employee_id: UUID,
        basic_salary: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate leave encashment amount.

        Formula: (Basic / 26) × Leave Balance Days
        """
        # Get encashable leave balance
        result = await self.db.execute(
            select(LeaveBalance).where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.is_active == True,
                )
            )
        )
        balances = result.scalars().all()

        total_encashable_days = Decimal("0")
        for balance in balances:
            # Only earned leave (EL) is typically encashable at separation
            # This should be configured per leave type
            total_encashable_days += balance.closing_balance or Decimal("0")

        if total_encashable_days <= 0:
            return Decimal("0"), Decimal("0")

        per_day_amount = (basic_salary / Decimal(str(LEAVE_ENCASHMENT_DIVISOR))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        encashment_amount = (per_day_amount * total_encashable_days).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return encashment_amount, total_encashable_days

    def _calculate_gratuity(
        self,
        basic_salary: Decimal,
        years_of_service: Decimal,
    ) -> tuple[Decimal, bool]:
        """
        Calculate gratuity amount.

        Formula: (15/26) × Last Drawn Salary × Years of Service
        Eligibility: 5+ years of continuous service
        Maximum: ₹20 Lakhs

        Args:
            basic_salary: Last drawn basic salary (or basic + DA)
            years_of_service: Years of service

        Returns:
            Tuple of (gratuity_amount, is_eligible)
        """
        if years_of_service < GRATUITY_YEARS_REQUIRED:
            return Decimal("0"), False

        # Gratuity formula: (15/26) × basic × years
        gratuity = (
            Decimal(str(GRATUITY_FORMULA_DAYS))
            / Decimal(str(GRATUITY_DIVISOR))
            * basic_salary
            * years_of_service
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Cap at maximum limit
        gratuity = min(gratuity, GRATUITY_MAX_AMOUNT)

        return gratuity, True

    async def _calculate_clearance_recovery(self, separation_id: UUID) -> Decimal:
        """Calculate total recovery from clearance items."""
        result = await self.db.execute(
            select(func.sum(SeparationClearance.recovery_amount)).where(
                and_(
                    SeparationClearance.separation_id == separation_id,
                    SeparationClearance.has_recovery == True,
                )
            )
        )
        return result.scalar() or Decimal("0")

    async def _calculate_fnf_tds(
        self,
        total_earnings: Decimal,
        gratuity_amount: Decimal,
        pan_number: str | None,
    ) -> Decimal:
        """
        Calculate TDS on FnF.

        Note: This is simplified. In production, should integrate with TDS module
        and consider exemptions (gratuity up to ₹20L exempt, leave encashment
        exemption for govt employees, etc.)
        """
        # Gratuity is exempt up to ₹20 Lakhs
        taxable_gratuity = max(Decimal("0"), gratuity_amount - GRATUITY_MAX_AMOUNT)

        # For simplicity, assuming 10% TDS on taxable components
        # Real implementation should use proper tax slabs
        taxable_earnings = total_earnings - gratuity_amount + taxable_gratuity

        if not pan_number:
            # Higher TDS rate (20%) if PAN not available
            tds_rate = Decimal("0.20")
        else:
            # Standard rate (10%) - should use actual tax computation
            tds_rate = Decimal("0.10")

        tds = (taxable_earnings * tds_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return max(Decimal("0"), tds)


class ClearanceChecklistService:
    """Service for clearance checklist management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization_id: UUID,
        checklist_code: str,
        checklist_item: str,
        department_id: UUID | None = None,
        is_mandatory: bool = True,
        can_have_recovery: bool = False,
        display_order: int = 0,
        created_by: UUID = None,
    ) -> ClearanceChecklist:
        """Create a clearance checklist item."""
        checklist = ClearanceChecklist(
            organization_id=organization_id,
            checklist_code=checklist_code,
            checklist_item=checklist_item,
            department_id=department_id,
            is_mandatory=is_mandatory,
            can_have_recovery=can_have_recovery,
            display_order=display_order,
            created_by=created_by,
        )
        self.db.add(checklist)
        await self.db.flush()
        await self.db.refresh(checklist)
        return checklist

    async def list(
        self,
        organization_id: UUID,
        active_only: bool = True,
    ) -> list[ClearanceChecklist]:
        """List clearance checklist items."""
        query = select(ClearanceChecklist).where(
            ClearanceChecklist.organization_id == organization_id
        )
        if active_only:
            query = query.where(ClearanceChecklist.is_active == True)
        query = query.order_by(ClearanceChecklist.display_order)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get(self, checklist_id: UUID) -> ClearanceChecklist | None:
        """Get checklist item by ID."""
        result = await self.db.execute(
            select(ClearanceChecklist).where(ClearanceChecklist.id == checklist_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        checklist_id: UUID,
        checklist_item: str | None = None,
        department_id: UUID | None = None,
        is_mandatory: bool | None = None,
        can_have_recovery: bool | None = None,
        display_order: int | None = None,
        is_active: bool | None = None,
        updated_by: UUID = None,
    ) -> ClearanceChecklist | None:
        """Update a clearance checklist item."""
        checklist = await self.get(checklist_id)
        if not checklist:
            return None

        if checklist_item is not None:
            checklist.checklist_item = checklist_item
        if department_id is not None:
            checklist.department_id = department_id
        if is_mandatory is not None:
            checklist.is_mandatory = is_mandatory
        if can_have_recovery is not None:
            checklist.can_have_recovery = can_have_recovery
        if display_order is not None:
            checklist.display_order = display_order
        if is_active is not None:
            checklist.is_active = is_active

        checklist.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(checklist)
        return checklist

    async def seed_default_checklist(
        self,
        organization_id: UUID,
        created_by: UUID,
    ) -> builtins.list[ClearanceChecklist]:
        """Seed default clearance checklist items for an organization."""
        default_items = [
            ("IT", "Laptop/Desktop/Mobile returned", True, True, 1),
            ("IT", "Email and system access revoked", True, False, 2),
            ("IT", "Software licenses released", False, False, 3),
            ("ADMIN", "ID Card returned", True, True, 4),
            ("ADMIN", "Office keys returned", False, True, 5),
            ("ADMIN", "Parking card returned", False, True, 6),
            ("FIN", "Travel/Expense advances settled", True, True, 7),
            ("FIN", "Personal loans cleared", True, True, 8),
            ("FIN", "Salary advances cleared", True, True, 9),
            ("HR", "All HR documents submitted", True, False, 10),
            ("HR", "No objection from department", True, False, 11),
            ("HR", "Exit interview completed", False, False, 12),
            ("DEPT", "Knowledge transfer completed", True, False, 13),
            ("DEPT", "All pending tasks handed over", True, False, 14),
            ("DEPT", "Department clearance", True, False, 15),
        ]

        created = []
        for code, item, mandatory, recovery, order in default_items:
            checklist = await self.create(
                organization_id=organization_id,
                checklist_code=code,
                checklist_item=item,
                is_mandatory=mandatory,
                can_have_recovery=recovery,
                display_order=order,
                created_by=created_by,
            )
            created.append(checklist)

        return created
