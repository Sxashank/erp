from __future__ import annotations

"""
Payroll Service

Business logic for payroll processing, payslips, and statutory calculations.
"""

import csv
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.payroll_statutory import compute_esi, compute_pf, compute_pt_maharashtra
from app.core.constants import GLEntrySourceType
from app.models.finance.gl_entry import GLEntry
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
from app.models.hris.attendance import MonthlyAttendanceSummary
from app.repositories.finance.financial_year_repo import (
    FinancialPeriodRepository,
    FinancialYearRepository,
)
from app.schemas.payroll.payroll import (
    PayrollBankFileResponse,
    PayrollBatchCreate,
    PayrollBatchUpdate,
    PayrollGLPostRequest,
    PayrollGLPostResponse,
    PayslipUpdate,
    StatutorySetupCreate,
    StatutorySetupUpdate,
)
from app.services.audit import record_financial_action
from app.services.finance.gl_posting_service import GLPostingService


class StatutorySetupService:
    """Service for statutory setup operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: StatutorySetupCreate, created_by: UUID) -> StatutorySetup:
        """Create statutory setup"""
        result = await self.db.execute(
            select(StatutorySetup).where(
                and_(
                    StatutorySetup.organization_id == data.organization_id,
                    StatutorySetup.statutory_type == data.statutory_type,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(
                f"{data.statutory_type} statutory setup already exists; update the existing setup"
            )

        setup = StatutorySetup(**data.model_dump(), created_by=created_by)
        self.db.add(setup)
        await self.db.flush()
        await self.db.refresh(setup)
        return setup

    async def get(self, id: UUID, organization_id: Optional[UUID] = None) -> Optional[StatutorySetup]:
        """Get statutory setup by ID"""
        query = select(StatutorySetup).where(StatutorySetup.id == id)
        if organization_id:
            query = query.where(StatutorySetup.organization_id == organization_id)

        result = await self.db.execute(
            query
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
        updated_by: UUID,
        organization_id: Optional[UUID] = None,
    ) -> Optional[StatutorySetup]:
        """Update statutory setup"""
        setup = await self.get(id, organization_id)
        if not setup:
            return None

        if data.effective_to and data.effective_from and data.effective_to < data.effective_from:
            raise ValueError("Effective to date cannot be before effective from date")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setup, field, value)
        setup.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(setup)
        return setup


class PayrollBatchService:
    """Service for payroll batch operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: PayrollBatchCreate, created_by: UUID) -> PayrollBatch:
        """Create a new payroll batch"""
        self._validate_payroll_period(data)
        await self._ensure_unique_period(data.organization_id, data.payroll_year, data.payroll_month)

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
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    def _validate_payroll_period(self, data: PayrollBatchCreate) -> None:
        if data.pay_period_from > data.pay_period_to:
            raise ValueError("Pay period start cannot be after pay period end")
        if data.pay_period_from.year != data.payroll_year or data.pay_period_to.year != data.payroll_year:
            raise ValueError("Pay period must be in the payroll year")
        if (
            data.pay_period_from.month != data.payroll_month
            or data.pay_period_to.month != data.payroll_month
        ):
            raise ValueError("Pay period must be in the payroll month")

    async def _ensure_unique_period(self, organization_id: UUID, year: int, month: int) -> None:
        result = await self.db.execute(
            select(PayrollBatch.id).where(
                and_(
                    PayrollBatch.organization_id == organization_id,
                    PayrollBatch.payroll_year == year,
                    PayrollBatch.payroll_month == month,
                    PayrollBatch.status != PayrollBatchStatus.CANCELLED,
                )
            ).limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError("A payroll batch already exists for this month")

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

    async def get(self, id: UUID, organization_id: Optional[UUID] = None) -> Optional[PayrollBatch]:
        """Get payroll batch by ID"""
        query = (
            select(PayrollBatch)
            .options(selectinload(PayrollBatch.payslips))
            .where(PayrollBatch.id == id)
        )
        if organization_id:
            query = query.where(PayrollBatch.organization_id == organization_id)

        result = await self.db.execute(
            query
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
        updated_by: UUID,
        organization_id: Optional[UUID] = None,
    ) -> Optional[PayrollBatch]:
        """Update payroll batch"""
        batch = await self.get(id, organization_id) if organization_id else await self.get(id)
        if not batch:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)
        batch.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def approve(
        self,
        id: UUID,
        approved_by: UUID,
        remarks: Optional[str] = None,
        organization_id: Optional[UUID] = None,
    ) -> Optional[PayrollBatch]:
        """Approve payroll batch (PROCESSED → APPROVED — the locking step)."""
        batch = await self.get(id, organization_id) if organization_id else await self.get(id)
        if not batch or batch.status != PayrollBatchStatus.PROCESSED:
            return None

        before_status = batch.status
        before_total_gross = batch.total_gross
        before_total_net = batch.total_net
        before_total_employees = batch.total_employees

        batch.status = PayrollBatchStatus.APPROVED
        batch.approved_by = approved_by
        batch.approved_at = datetime.utcnow()
        if remarks:
            batch.remarks = remarks

        # Update all payslips to approved
        for payslip in batch.payslips:
            payslip.status = PayslipStatus.APPROVED

        await self.db.flush()
        await self.db.refresh(batch)

        # Domain audit: payroll finalize (approve) — §8.5 / §4.11.
        # The PROCESSED → APPROVED transition is the locking step: once
        # approved, payslips cannot be edited and the batch is ready for
        # bank-file generation + payment.
        await record_financial_action(
            self.db,
            organization_id=batch.organization_id,
            entity_type="PAYROLL_BATCH",
            entity_id=batch.id,
            entity_reference=batch.batch_number,
            action="PAYROLL_FINALIZE",
            user_id=approved_by,
            before={
                "status": before_status,
                "total_gross": before_total_gross,
                "total_net": before_total_net,
                "total_employees": before_total_employees,
            },
            after={
                "status": batch.status,
                "total_gross": batch.total_gross,
                "total_net": batch.total_net,
                "total_employees": batch.total_employees,
                "approved_at": batch.approved_at,
            },
            metadata={
                "transaction_type": "PAYROLL_FINALIZE",
                "payroll_year": batch.payroll_year,
                "payroll_month": batch.payroll_month,
                "total_gross": str(batch.total_gross),
                "total_net": str(batch.total_net),
                "total_deductions": str(batch.total_deductions),
                "employee_count": batch.total_employees,
                "payslip_count": len(batch.payslips),
                "remarks": remarks,
            },
            change_reason="Payroll batch approved (finalized)",
        )

        return batch

    async def mark_paid(
        self,
        id: UUID,
        updated_by: UUID,
        payment_reference: Optional[str] = None,
        organization_id: Optional[UUID] = None,
    ) -> Optional[PayrollBatch]:
        """Mark payroll batch as paid"""
        batch = await self.get(id, organization_id) if organization_id else await self.get(id)
        if not batch or batch.status != PayrollBatchStatus.APPROVED:
            return None

        reference = (payment_reference or "").strip()
        if not reference:
            raise ValueError("Payment reference is required before marking payroll paid")

        self._validate_payroll_bank_details(batch)

        batch.status = PayrollBatchStatus.PAID
        batch.paid_at = datetime.utcnow()

        # Update all payslips to paid
        for payslip in batch.payslips:
            payslip.status = PayslipStatus.PAID
            payslip.paid_at = datetime.utcnow()
            payslip.payment_reference = reference

        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def export_bank_file(
        self,
        id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> PayrollBankFileResponse:
        """Generate a manual bank-upload CSV for an approved or paid payroll batch."""
        batch = await self.get(id, organization_id) if organization_id else await self.get(id)
        if not batch:
            raise ValueError("Batch not found")
        if batch.status not in [PayrollBatchStatus.APPROVED, PayrollBatchStatus.PAID]:
            raise ValueError("Bank payout export is available only after approval")

        payable_payslips = self._validate_payroll_bank_details(batch)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "employee_code",
            "employee_name",
            "bank_account_number",
            "ifsc",
            "amount",
            "narration",
            "payment_reference",
        ])

        total_amount = Decimal("0")
        for payslip in payable_payslips:
            total_amount += payslip.net_salary
            writer.writerow([
                payslip.employee_code,
                payslip.employee_name,
                payslip.bank_account_number,
                payslip.bank_ifsc,
                f"{payslip.net_salary:.2f}",
                f"Salary {batch.payroll_year}-{batch.payroll_month:02d}",
                payslip.payment_reference or "",
            ])

        safe_batch_number = batch.batch_number.replace("/", "_")
        return PayrollBankFileResponse(
            file_name=f"salary_payout_{safe_batch_number}.csv",
            file_content=output.getvalue(),
            record_count=len(payable_payslips),
            total_amount=total_amount,
            generated_at=datetime.now(timezone.utc),
        )

    def _validate_payroll_bank_details(self, batch: PayrollBatch) -> list[Payslip]:
        """Return payable payslips only after validating salary bank details."""
        payable_payslips = [p for p in batch.payslips if p.net_salary > 0]
        missing_bank = [
            f"{p.employee_code} - {p.employee_name}"
            for p in payable_payslips
            if not p.bank_account_number or not p.bank_ifsc
        ]
        if missing_bank:
            raise ValueError(f"Missing salary bank details for: {', '.join(missing_bank)}")
        return payable_payslips

    async def post_to_gl(
        self,
        id: UUID,
        data: PayrollGLPostRequest,
        posted_by: UUID,
        organization_id: Optional[UUID] = None,
    ) -> PayrollGLPostResponse:
        """Post approved payroll batch to finance as a balanced source voucher."""
        batch = await self.get(id, organization_id) if organization_id else await self.get(id)
        if not batch:
            raise ValueError("Batch not found")
        if batch.status not in [PayrollBatchStatus.APPROVED, PayrollBatchStatus.PAID]:
            raise ValueError("Only approved or paid payroll can be posted to GL")

        source_reference = f"PAYROLL:{batch.batch_number}"
        existing = await self.db.execute(
            select(GLEntry.id).where(
                and_(
                    GLEntry.source_id == batch.id,
                    GLEntry.source_reference == source_reference,
                )
            ).limit(1)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Payroll batch is already posted to GL")

        voucher_date = data.voucher_date or batch.payment_date or batch.pay_period_to
        fy = await FinancialYearRepository(self.db).get_by_date(batch.organization_id, voucher_date)
        if not fy:
            raise ValueError(f"No financial year found for {voucher_date}")
        period = await FinancialPeriodRepository(self.db).get_by_date(fy.id, voucher_date)
        if not period:
            raise ValueError(f"No financial period found for {voucher_date}")

        known_employee_deductions = (
            batch.total_pf_employee
            + batch.total_esi_employee
            + batch.total_pt
            + batch.total_tds
        )
        other_deductions = batch.total_deductions - known_employee_deductions
        if other_deductions < 0:
            other_deductions = Decimal("0")

        required_payables: list[tuple[Decimal, Optional[UUID], str]] = [
            (batch.total_pf_employee + batch.total_pf_employer, data.pf_payable_account_id, "PF payable account"),
            (batch.total_esi_employee + batch.total_esi_employer, data.esi_payable_account_id, "ESI payable account"),
            (batch.total_pt, data.pt_payable_account_id, "PT payable account"),
            (batch.total_tds, data.tds_payable_account_id, "TDS payable account"),
            (other_deductions, data.other_deductions_payable_account_id, "Other deductions payable account"),
        ]
        for amount, account_id, label in required_payables:
            if amount > 0 and not account_id:
                raise ValueError(f"{label} is required")
        if batch.total_employer_statutory > 0 and not data.employer_contribution_expense_account_id:
            raise ValueError("Employer contribution expense account is required")

        lines = [
            {
                "account_id": data.salary_expense_account_id,
                "debit_amount": batch.total_gross,
                "credit_amount": Decimal("0"),
                "cost_center_id": data.cost_center_id,
                "narration": "Payroll salary expense",
            },
            {
                "account_id": data.net_salary_payable_account_id,
                "debit_amount": Decimal("0"),
                "credit_amount": batch.total_net,
                "cost_center_id": data.cost_center_id,
                "narration": "Net salary payable",
            },
        ]

        if batch.total_employer_statutory > 0:
            lines.append({
                "account_id": data.employer_contribution_expense_account_id,
                "debit_amount": batch.total_employer_statutory,
                "credit_amount": Decimal("0"),
                "cost_center_id": data.cost_center_id,
                "narration": "Employer statutory contribution expense",
            })

        for amount, account_id, narration in [
            (batch.total_pf_employee + batch.total_pf_employer, data.pf_payable_account_id, "PF payable"),
            (batch.total_esi_employee + batch.total_esi_employer, data.esi_payable_account_id, "ESI payable"),
            (batch.total_pt, data.pt_payable_account_id, "Professional tax payable"),
            (batch.total_tds, data.tds_payable_account_id, "TDS payable"),
            (other_deductions, data.other_deductions_payable_account_id, "Other payroll deductions payable"),
        ]:
            if amount > 0:
                lines.append({
                    "account_id": account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": amount,
                    "cost_center_id": data.cost_center_id,
                    "narration": narration,
                })

        gl_entries = await GLPostingService(self.db).post_entries(
            organization_id=batch.organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=voucher_date,
            source_type=GLEntrySourceType.PAYROLL,
            source_id=batch.id,
            source_reference=source_reference,
            lines=lines,
            narration=data.narration or f"Payroll posting {batch.batch_number}",
            posted_by=posted_by,
        )

        await self.db.flush()
        voucher_number = gl_entries[0].voucher_number if gl_entries else None
        total_debit = sum(entry.debit_amount for entry in gl_entries)
        total_credit = sum(entry.credit_amount for entry in gl_entries)
        return PayrollGLPostResponse(
            posted=True,
            source_reference=source_reference,
            gl_entry_count=len(gl_entries),
            voucher_number=voucher_number,
            total_debit=total_debit,
            total_credit=total_credit,
        )


class PayrollProcessingService:
    """Service for payroll processing logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_payroll(
        self,
        batch_id: UUID,
        employee_ids: Optional[List[UUID]] = None,
        processed_by: UUID = None,
        organization_id: Optional[UUID] = None,
    ) -> PayrollBatch:
        """Process payroll for a batch"""
        batch_filters = [PayrollBatch.id == batch_id]
        if organization_id:
            batch_filters.append(PayrollBatch.organization_id == organization_id)
        batch_result = await self.db.execute(
            select(PayrollBatch).where(and_(*batch_filters))
        )
        batch = batch_result.scalar_one_or_none()
        if not batch:
            raise ValueError("Batch not found")

        if batch.status not in [PayrollBatchStatus.DRAFT, PayrollBatchStatus.PROCESSING]:
            raise ValueError("Batch is not in draft or processing status")

        if batch.pay_period_from > batch.pay_period_to:
            raise ValueError("Pay period start cannot be after pay period end")

        if (
            batch.pay_period_to.year != batch.payroll_year
            or batch.pay_period_to.month != batch.payroll_month
        ):
            raise ValueError("Pay period end must fall in the payroll month")

        batch.status = PayrollBatchStatus.PROCESSING
        batch.total_employees = 0
        batch.total_gross = Decimal("0")
        batch.total_deductions = Decimal("0")
        batch.total_net = Decimal("0")
        batch.total_pf_employee = Decimal("0")
        batch.total_pf_employer = Decimal("0")
        batch.total_esi_employee = Decimal("0")
        batch.total_esi_employer = Decimal("0")
        batch.total_pt = Decimal("0")
        batch.total_tds = Decimal("0")
        batch.total_employer_statutory = Decimal("0")

        await self.db.execute(delete(Payslip).where(Payslip.batch_id == batch.id))
        await self.db.flush()

        # Get employees with active salary
        employee_query = select(Employee).options(
            selectinload(Employee.salaries),
            selectinload(Employee.department),
            selectinload(Employee.designation),
            selectinload(Employee.bank_accounts),
            selectinload(Employee.statutory_info),
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
        pf_setup = await self._get_statutory_setup(batch.organization_id, "PF", batch.pay_period_to)
        esi_setup = await self._get_statutory_setup(batch.organization_id, "ESI", batch.pay_period_to)
        pt_setup = await self._get_statutory_setup(batch.organization_id, "PT", batch.pay_period_to)

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
                employee.id, batch.payroll_year, batch.payroll_month
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

        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def _get_statutory_setup(
        self,
        organization_id: UUID,
        statutory_type: str,
        as_of_date: Optional[date] = None,
    ) -> Optional[StatutorySetup]:
        """Get effective statutory setup"""
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
        year: int,
        month: int
    ) -> dict:
        """Get locked monthly attendance summary for payroll."""
        result = await self.db.execute(
            select(MonthlyAttendanceSummary).where(
                and_(
                    MonthlyAttendanceSummary.employee_id == employee_id,
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                )
            )
        )
        summary = result.scalar_one_or_none()

        if not summary or not summary.is_processed:
            raise ValueError("Attendance summary is not processed for employee")

        if not summary.is_locked:
            raise ValueError("Attendance must be locked before payroll processing")

        half_days = Decimal(str(summary.half_days or 0)) * Decimal("0.5")
        return {
            "working_days": Decimal(str(summary.working_days or 0)),
            "days_present": Decimal(str(summary.present_days or 0)) + half_days,
            "days_absent": Decimal(str(summary.absent_days or 0)),
            "leave_days": Decimal(str(summary.paid_leave_days or 0)),
            "lop_days": Decimal(str(summary.lop_days or 0)),
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
        department_name = employee.department.name if employee.department else None
        designation_name = employee.designation.name if employee.designation else None

        # Get bank details
        bank_account = None
        bank_ifsc = None
        if employee.bank_accounts:
            primary_bank = next((b for b in employee.bank_accounts if b.is_primary), None)
            if primary_bank:
                bank_account = primary_bank.account_number
                bank_ifsc = primary_bank.ifsc_code

        # Get statutory numbers
        uan_number = employee.uan_number
        esi_number = employee.esic_number
        if employee.statutory_info:
            uan_number = employee.uan_number or employee.statutory_info.pf_account_number
            esi_number = employee.statutory_info.esi_number or employee.esic_number

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
            pf = compute_pf(pf_wage)
            pf_employee = pf.employee_contribution
            pf_employer = pf.employer_total

            # Create PF statutory record
            pf_statutory = PayrollStatutory(
                payslip_id=payslip.id,
                statutory_type="PF",
                wage_base=pf.pf_wages,
                employee_rate=Decimal("12.00"),
                employee_amount=pf_employee,
                employer_rate=Decimal("12.00"),
                employer_amount=pf_employer,
                eps_amount=pf.employer_eps,
                admin_charges=pf.employer_admin,
                total_amount=pf_employee + pf_employer,
                created_by=created_by
            )
            self.db.add(pf_statutory)
            total_deductions += pf_employee

        # ESI Calculation
        if esi_setup:
            esi = compute_esi(esi_wage)
            esi_employee = esi.employee_contribution
            esi_employer = esi.employer_contribution

            # Create ESI statutory record
            if esi.applicable:
                esi_statutory = PayrollStatutory(
                    payslip_id=payslip.id,
                    statutory_type="ESI",
                    wage_base=esi_wage,
                    employee_rate=Decimal("0.75"),
                    employee_amount=esi_employee,
                    employer_rate=Decimal("3.25"),
                    employer_amount=esi_employer,
                    total_amount=esi_employee + esi_employer,
                    created_by=created_by
                )
                self.db.add(esi_statutory)
                total_deductions += esi_employee

        # PT Calculation
        if pt_setup:
            if pt_setup.pt_slabs:
                pt_amount = self._calculate_pt(total_earnings, pt_setup.pt_slabs)
            elif not pt_setup.pt_state or pt_setup.pt_state.upper() == "MAHARASHTRA":
                pt_amount = compute_pt_maharashtra(total_earnings)
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

    async def get(self, id: UUID, organization_id: Optional[UUID] = None) -> Optional[Payslip]:
        """Get payslip by ID"""
        query = (
            select(Payslip)
            .options(
                selectinload(Payslip.components),
                selectinload(Payslip.statutory)
            )
            .where(Payslip.id == id)
        )
        if organization_id:
            query = query.join(PayrollBatch).where(PayrollBatch.organization_id == organization_id)

        result = await self.db.execute(
            query
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        batch_id: Optional[UUID] = None,
        employee_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Payslip], int]:
        """List payslips with filters"""
        query = select(Payslip).join(PayrollBatch).where(PayrollBatch.organization_id == organization_id)

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
        updated_by: UUID,
        organization_id: Optional[UUID] = None,
    ) -> Optional[Payslip]:
        """Update payslip (manual adjustments)"""
        payslip = await self.get(id, organization_id)
        if not payslip:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payslip, field, value)
        payslip.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(payslip)
        return payslip

    async def get_employee_payslips(
        self,
        organization_id: UUID,
        employee_id: UUID,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 12
    ) -> Tuple[List[Payslip], int]:
        """Get payslips for an employee"""
        query = select(Payslip).join(PayrollBatch).where(
            and_(
                PayrollBatch.organization_id == organization_id,
                Payslip.employee_id == employee_id,
            )
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
