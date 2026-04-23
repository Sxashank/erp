"""
Payroll Service

Business logic for payroll processing, payslips, and statutory calculations.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payroll.payroll import (
    PayrollBatch,
    Payslip,
    PayslipComponent,
    PayrollStatutory,
    StatutorySetup,
    PayrollBatchStatus,
    PayslipStatus,
)
from app.models.payroll.salary_component import EmployeeSalary, EmployeeSalaryComponent
from app.models.hris.employee import Employee
from app.models.hris.attendance import DailyAttendanceSummary
from app.schemas.payroll.payroll import (
    PayrollBatchCreate,
    PayrollBatchUpdate,
    PayslipUpdate,
    StatutorySetupCreate,
    StatutorySetupUpdate,
)


class StatutorySetupService:
    """Service for statutory setup operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: StatutorySetupCreate, created_by: UUID) -> StatutorySetup:
        """Create statutory setup"""
        setup = StatutorySetup(**data.model_dump(), created_by=created_by)
        self.db.add(setup)
        await self.db.commit()
        await self.db.refresh(setup)
        return setup

    async def get(self, id: UUID) -> Optional[StatutorySetup]:
        """Get statutory setup by ID"""
        result = await self.db.execute(
            select(StatutorySetup).where(StatutorySetup.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        organization_id: UUID,
        statutory_type: str,
        as_of_date: Optional[date] = None
    ) -> Optional[StatutorySetup]:
        """Get effective statutory setup by type"""
        check_date = as_of_date or date.today()
        result = await self.db.execute(
            select(StatutorySetup).where(
                and_(
                    StatutorySetup.organization_id == organization_id,
                    StatutorySetup.statutory_type == statutory_type,
                    StatutorySetup.effective_from <= check_date,
                    (StatutorySetup.effective_to >= check_date) | (StatutorySetup.effective_to.is_(None)),
                    StatutorySetup.is_active == True
                )
            ).order_by(StatutorySetup.effective_from.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        statutory_type: Optional[str] = None
    ) -> List[StatutorySetup]:
        """List statutory setups"""
        query = select(StatutorySetup).where(
            StatutorySetup.organization_id == organization_id
        )
        if statutory_type:
            query = query.where(StatutorySetup.statutory_type == statutory_type)
        query = query.order_by(StatutorySetup.statutory_type, StatutorySetup.effective_from.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        id: UUID,
        data: StatutorySetupUpdate,
        updated_by: UUID
    ) -> Optional[StatutorySetup]:
        """Update statutory setup"""
        setup = await self.get(id)
        if not setup:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setup, field, value)
        setup.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(setup)
        return setup


class PayrollBatchService:
    """Service for payroll batch operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: PayrollBatchCreate, created_by: UUID) -> PayrollBatch:
        """Create a new payroll batch"""
        # Generate batch number
        batch_number = await self._generate_batch_number(
            data.organization_id, data.payroll_year, data.payroll_month
        )

        batch = PayrollBatch(
            **data.model_dump(),
            batch_number=batch_number,
            created_by=created_by
        )
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def _generate_batch_number(
        self,
        organization_id: UUID,
        year: int,
        month: int
    ) -> str:
        """Generate batch number: PAY/YYYY/MM/SEQ"""
        result = await self.db.execute(
            select(func.count()).where(
                and_(
                    PayrollBatch.organization_id == organization_id,
                    PayrollBatch.payroll_year == year
                )
            )
        )
        seq = (result.scalar() or 0) + 1
        return f"PAY/{year}/{month:02d}/{seq:03d}"

    async def get(self, id: UUID) -> Optional[PayrollBatch]:
        """Get payroll batch by ID"""
        result = await self.db.execute(
            select(PayrollBatch)
            .options(selectinload(PayrollBatch.payslips))
            .where(PayrollBatch.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[PayrollBatch], int]:
        """List payroll batches"""
        query = select(PayrollBatch).where(
            PayrollBatch.organization_id == organization_id
        )
        if year:
            query = query.where(PayrollBatch.payroll_year == year)
        if status:
            query = query.where(PayrollBatch.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(PayrollBatch.payroll_year.desc(), PayrollBatch.payroll_month.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: PayrollBatchUpdate,
        updated_by: UUID
    ) -> Optional[PayrollBatch]:
        """Update payroll batch"""
        batch = await self.get(id)
        if not batch:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)
        batch.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def approve(self, id: UUID, approved_by: UUID, remarks: Optional[str] = None) -> Optional[PayrollBatch]:
        """Approve payroll batch"""
        batch = await self.get(id)
        if not batch or batch.status != PayrollBatchStatus.PROCESSED:
            return None

        batch.status = PayrollBatchStatus.APPROVED
        batch.approved_by = approved_by
        batch.approved_at = datetime.utcnow()
        if remarks:
            batch.remarks = remarks

        # Update all payslips to approved
        for payslip in batch.payslips:
            payslip.status = PayslipStatus.APPROVED

        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def mark_paid(self, id: UUID, updated_by: UUID) -> Optional[PayrollBatch]:
        """Mark payroll batch as paid"""
        batch = await self.get(id)
        if not batch or batch.status != PayrollBatchStatus.APPROVED:
            return None

        batch.status = PayrollBatchStatus.PAID
        batch.paid_at = datetime.utcnow()

        # Update all payslips to paid
        for payslip in batch.payslips:
            payslip.status = PayslipStatus.PAID
            payslip.paid_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(batch)
        return batch


class PayrollProcessingService:
    """Service for payroll processing logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_payroll(
        self,
        batch_id: UUID,
        employee_ids: Optional[List[UUID]] = None,
        processed_by: UUID = None
    ) -> PayrollBatch:
        """Process payroll for a batch"""
        # Get batch
        batch_result = await self.db.execute(
            select(PayrollBatch).where(PayrollBatch.id == batch_id)
        )
        batch = batch_result.scalar_one_or_none()
        if not batch:
            raise ValueError("Batch not found")

        if batch.status not in [PayrollBatchStatus.DRAFT, PayrollBatchStatus.PROCESSING]:
            raise ValueError("Batch is not in draft or processing status")

        batch.status = PayrollBatchStatus.PROCESSING

        # Get employees with active salary
        employee_query = select(Employee).options(
            selectinload(Employee.salaries)
        ).where(
            and_(
                Employee.organization_id == batch.organization_id,
                Employee.is_active == True,
                Employee.employment_status == "ACTIVE"
            )
        )
        if employee_ids:
            employee_query = employee_query.where(Employee.id.in_(employee_ids))

        employees_result = await self.db.execute(employee_query)
        employees = employees_result.scalars().all()

        # Get statutory setup
        pf_setup = await self._get_statutory_setup(batch.organization_id, "PF")
        esi_setup = await self._get_statutory_setup(batch.organization_id, "ESI")
        pt_setup = await self._get_statutory_setup(batch.organization_id, "PT")

        # Initialize totals
        total_gross = Decimal("0")
        total_deductions = Decimal("0")
        total_net = Decimal("0")
        total_pf_employee = Decimal("0")
        total_pf_employer = Decimal("0")
        total_esi_employee = Decimal("0")
        total_esi_employer = Decimal("0")
        total_pt = Decimal("0")
        employee_count = 0

        for employee in employees:
            # Get active salary
            salary = await self._get_employee_salary(employee.id, batch.pay_period_to)
            if not salary:
                continue

            # Get attendance summary
            attendance = await self._get_attendance_summary(
                employee.id, batch.pay_period_from, batch.pay_period_to
            )

            # Generate payslip
            payslip = await self._generate_payslip(
                batch, employee, salary, attendance, pf_setup, esi_setup, pt_setup, processed_by
            )

            # Accumulate totals
            total_gross += payslip.gross_salary
            total_deductions += payslip.total_deductions
            total_net += payslip.net_salary
            total_pf_employee += await self._get_statutory_amount(payslip.id, "PF", "employee")
            total_pf_employer += payslip.employer_pf
            total_esi_employee += await self._get_statutory_amount(payslip.id, "ESI", "employee")
            total_esi_employer += payslip.employer_esi
            total_pt += await self._get_statutory_amount(payslip.id, "PT", "employee")
            employee_count += 1

        # Update batch totals
        batch.total_employees = employee_count
        batch.total_gross = total_gross
        batch.total_deductions = total_deductions
        batch.total_net = total_net
        batch.total_pf_employee = total_pf_employee
        batch.total_pf_employer = total_pf_employer
        batch.total_esi_employee = total_esi_employee
        batch.total_esi_employer = total_esi_employer
        batch.total_pt = total_pt
        batch.total_employer_statutory = total_pf_employer + total_esi_employer
        batch.status = PayrollBatchStatus.PROCESSED
        batch.processed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def _get_statutory_setup(
        self,
        organization_id: UUID,
        statutory_type: str
    ) -> Optional[StatutorySetup]:
        """Get effective statutory setup"""
        result = await self.db.execute(
            select(StatutorySetup).where(
                and_(
                    StatutorySetup.organization_id == organization_id,
                    StatutorySetup.statutory_type == statutory_type,
                    StatutorySetup.is_active == True
                )
            ).order_by(StatutorySetup.effective_from.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_employee_salary(
        self,
        employee_id: UUID,
        as_of_date: date
    ) -> Optional[EmployeeSalary]:
        """Get employee salary effective on date"""
        result = await self.db.execute(
            select(EmployeeSalary)
            .options(
                selectinload(EmployeeSalary.components)
                .selectinload(EmployeeSalaryComponent.component)
            )
            .where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.effective_from <= as_of_date,
                    (EmployeeSalary.effective_to >= as_of_date) | (EmployeeSalary.effective_to.is_(None)),
                    EmployeeSalary.status == "ACTIVE"
                )
            )
            .order_by(EmployeeSalary.effective_from.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_attendance_summary(
        self,
        employee_id: UUID,
        from_date: date,
        to_date: date
    ) -> dict:
        """Get attendance summary for the period"""
        result = await self.db.execute(
            select(DailyAttendanceSummary).where(
                and_(
                    DailyAttendanceSummary.employee_id == employee_id,
                    DailyAttendanceSummary.period_from <= to_date,
                    DailyAttendanceSummary.period_to >= from_date
                )
            )
        )
        summary = result.scalar_one_or_none()

        if summary:
            return {
                "working_days": summary.total_working_days or Decimal("26"),
                "days_present": summary.total_present_days or Decimal("26"),
                "days_absent": summary.total_absent_days or Decimal("0"),
                "leave_days": summary.total_leave_days or Decimal("0"),
                "lop_days": summary.lop_days or Decimal("0"),
            }

        # Default if no summary
        return {
            "working_days": Decimal("26"),
            "days_present": Decimal("26"),
            "days_absent": Decimal("0"),
            "leave_days": Decimal("0"),
            "lop_days": Decimal("0"),
        }

    async def _generate_payslip(
        self,
        batch: PayrollBatch,
        employee: Employee,
        salary: EmployeeSalary,
        attendance: dict,
        pf_setup: Optional[StatutorySetup],
        esi_setup: Optional[StatutorySetup],
        pt_setup: Optional[StatutorySetup],
        created_by: UUID
    ) -> Payslip:
        """Generate payslip for an employee"""
        # Calculate proration factor
        working_days = attendance["working_days"]
        payable_days = working_days - attendance["lop_days"]
        proration_factor = payable_days / working_days if working_days > 0 else Decimal("1")

        # Generate payslip number
        payslip_number = await self._generate_payslip_number(batch.batch_number, employee.employee_code)

        # Get employee snapshot data
        department_name = employee.department.department_name if employee.department else None
        designation_name = employee.designation.designation_name if employee.designation else None

        # Get bank details
        bank_account = None
        bank_ifsc = None
        if employee.bank_accounts:
            primary_bank = next((b for b in employee.bank_accounts if b.is_primary), None)
            if primary_bank:
                bank_account = primary_bank.account_number
                bank_ifsc = primary_bank.ifsc_code

        # Get statutory numbers
        uan_number = None
        esi_number = None
        if employee.statutory:
            uan_number = employee.statutory.uan_number
            esi_number = employee.statutory.esi_number

        # Create payslip
        payslip = Payslip(
            batch_id=batch.id,
            employee_id=employee.id,
            payslip_number=payslip_number,
            employee_code=employee.employee_code,
            employee_name=employee.full_name,
            department_name=department_name,
            designation_name=designation_name,
            pan_number=employee.pan_number,
            uan_number=uan_number,
            esi_number=esi_number,
            bank_account_number=bank_account,
            bank_ifsc=bank_ifsc,
            working_days=attendance["working_days"],
            days_present=attendance["days_present"],
            days_absent=attendance["days_absent"],
            leave_days=attendance["leave_days"],
            lop_days=attendance["lop_days"],
            gross_salary=salary.monthly_gross,
            total_earnings=Decimal("0"),
            total_deductions=Decimal("0"),
            net_salary=Decimal("0"),
            status=PayslipStatus.GENERATED,
            created_by=created_by
        )
        self.db.add(payslip)
        await self.db.flush()

        # Process salary components
        total_earnings = Decimal("0")
        total_deductions = Decimal("0")
        pf_wage = Decimal("0")
        esi_wage = Decimal("0")

        for sal_comp in salary.components:
            component = sal_comp.component
            standard_amount = sal_comp.monthly_amount
            actual_amount = (standard_amount * proration_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Create payslip component
            ps_component = PayslipComponent(
                payslip_id=payslip.id,
                component_id=component.id,
                component_code=component.component_code,
                component_name=component.component_name,
                component_type=component.component_type,
                standard_amount=standard_amount,
                actual_amount=actual_amount,
                is_taxable=component.is_taxable,
                taxable_amount=actual_amount if component.is_taxable else Decimal("0"),
                display_order=component.display_order,
                created_by=created_by
            )
            self.db.add(ps_component)

            if component.component_type == "EARNING":
                total_earnings += actual_amount
                if component.affects_pf:
                    pf_wage += actual_amount
                if component.affects_esi:
                    esi_wage += actual_amount
            else:
                total_deductions += actual_amount

        # Calculate statutory deductions
        pf_employee = Decimal("0")
        pf_employer = Decimal("0")
        esi_employee = Decimal("0")
        esi_employer = Decimal("0")
        pt_amount = Decimal("0")

        # PF Calculation
        if pf_setup and pf_wage > 0:
            pf_wage_capped = min(pf_wage, pf_setup.pf_wage_ceiling or Decimal("15000"))
            pf_employee = (pf_wage_capped * (pf_setup.pf_employee_rate or Decimal("12")) / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            pf_employer = (pf_wage_capped * (pf_setup.pf_employer_rate or Decimal("12")) / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )

            # Create PF statutory record
            pf_statutory = PayrollStatutory(
                payslip_id=payslip.id,
                statutory_type="PF",
                wage_base=pf_wage_capped,
                employee_rate=pf_setup.pf_employee_rate,
                employee_amount=pf_employee,
                employer_rate=pf_setup.pf_employer_rate,
                employer_amount=pf_employer,
                total_amount=pf_employee + pf_employer,
                created_by=created_by
            )
            self.db.add(pf_statutory)
            total_deductions += pf_employee

        # ESI Calculation
        if esi_setup and esi_wage <= (esi_setup.esi_wage_ceiling or Decimal("21000")):
            esi_employee = (esi_wage * (esi_setup.esi_employee_rate or Decimal("0.75")) / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            esi_employer = (esi_wage * (esi_setup.esi_employer_rate or Decimal("3.25")) / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )

            # Create ESI statutory record
            esi_statutory = PayrollStatutory(
                payslip_id=payslip.id,
                statutory_type="ESI",
                wage_base=esi_wage,
                employee_rate=esi_setup.esi_employee_rate,
                employee_amount=esi_employee,
                employer_rate=esi_setup.esi_employer_rate,
                employer_amount=esi_employer,
                total_amount=esi_employee + esi_employer,
                created_by=created_by
            )
            self.db.add(esi_statutory)
            total_deductions += esi_employee

        # PT Calculation (simplified - actual implementation should use slabs)
        if pt_setup and pt_setup.pt_slabs:
            pt_amount = self._calculate_pt(total_earnings, pt_setup.pt_slabs)
            if pt_amount > 0:
                pt_statutory = PayrollStatutory(
                    payslip_id=payslip.id,
                    statutory_type="PT",
                    wage_base=total_earnings,
                    employee_amount=pt_amount,
                    total_amount=pt_amount,
                    created_by=created_by
                )
                self.db.add(pt_statutory)
                total_deductions += pt_amount

        # Update payslip totals
        payslip.total_earnings = total_earnings
        payslip.total_deductions = total_deductions
        payslip.net_salary = total_earnings - total_deductions
        payslip.pf_wage = pf_wage
        payslip.esi_wage = esi_wage
        payslip.employer_pf = pf_employer
        payslip.employer_esi = esi_employer

        return payslip

    async def _generate_payslip_number(self, batch_number: str, employee_code: str) -> str:
        """Generate payslip number"""
        return f"{batch_number}/{employee_code}"

    def _calculate_pt(self, gross: Decimal, slabs: dict) -> Decimal:
        """Calculate professional tax based on slabs"""
        # Simple slab-based calculation
        for slab in slabs.get("slabs", []):
            min_amt = Decimal(str(slab.get("min", 0)))
            max_amt = Decimal(str(slab.get("max", 999999999)))
            if min_amt <= gross <= max_amt:
                return Decimal(str(slab.get("tax", 0)))
        return Decimal("0")

    async def _get_statutory_amount(
        self,
        payslip_id: UUID,
        statutory_type: str,
        contribution_type: str
    ) -> Decimal:
        """Get statutory amount from payslip"""
        result = await self.db.execute(
            select(PayrollStatutory).where(
                and_(
                    PayrollStatutory.payslip_id == payslip_id,
                    PayrollStatutory.statutory_type == statutory_type
                )
            )
        )
        statutory = result.scalar_one_or_none()
        if statutory:
            if contribution_type == "employee":
                return statutory.employee_amount
            elif contribution_type == "employer":
                return statutory.employer_amount
        return Decimal("0")


class PayslipService:
    """Service for payslip operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: UUID) -> Optional[Payslip]:
        """Get payslip by ID"""
        result = await self.db.execute(
            select(Payslip)
            .options(
                selectinload(Payslip.components),
                selectinload(Payslip.statutory)
            )
            .where(Payslip.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        batch_id: Optional[UUID] = None,
        employee_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Payslip], int]:
        """List payslips with filters"""
        query = select(Payslip)

        if batch_id:
            query = query.where(Payslip.batch_id == batch_id)
        if employee_id:
            query = query.where(Payslip.employee_id == employee_id)
        if status:
            query = query.where(Payslip.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(Payslip.employee_name)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: PayslipUpdate,
        updated_by: UUID
    ) -> Optional[Payslip]:
        """Update payslip (manual adjustments)"""
        payslip = await self.get(id)
        if not payslip:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payslip, field, value)
        payslip.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(payslip)
        return payslip

    async def get_employee_payslips(
        self,
        employee_id: UUID,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 12
    ) -> Tuple[List[Payslip], int]:
        """Get payslips for an employee"""
        query = select(Payslip).join(PayrollBatch).where(
            Payslip.employee_id == employee_id
        )

        if year:
            query = query.where(PayrollBatch.payroll_year == year)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(PayrollBatch.payroll_year.desc(), PayrollBatch.payroll_month.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count
