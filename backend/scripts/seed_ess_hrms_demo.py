#!/usr/bin/env python3
"""Seed an end-to-end ESS + HRMS demo employee.

This seed is intentionally manual-first: it creates ERP records that the live
ESS and HRMS screens read, with no external HR, biometric, bank, or statutory
portal dependency.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 - register ORM tables
from app.core.constants import (
    AssetAcquisitionType,
    AssetStatus,
    AssetType,
    AttendanceStatus,
    DepreciationMethod,
    EmploymentStatus,
    EmploymentType,
    EntityStatus,
    Gender,
    LeaveApplicationStatus,
    LeaveCategory,
    ShiftType,
    UnitType,
    UserStatus,
)
from app.core.security import get_password_hash
from app.database import async_session_factory
from app.models.auth.user import User
from app.models.ess.enums import (
    ClaimStatus,
    ClaimType,
    ESSUserStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.ess.ess_user import ESSUser
from app.models.ess.helpdesk import HelpdeskTicket, TicketCategoryMaster
from app.models.ess.it_declaration import ITDeclaration, ITDeclarationItem, ITDeclarationMaster
from app.models.ess.reimbursement import (
    ReimbursementCategory,
    ReimbursementClaim,
    ReimbursementLineItem,
)
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.hris.attendance import Attendance, AttendanceRegularization
from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveApplication, LeaveBalance, LeaveType
from app.models.hris.performance import AppraisalCycle, EmployeeAppraisal, PerformanceGoal
from app.models.hris.shift import Holiday, HolidayCalendar, Shift
from app.models.hris.training import TrainingNomination, TrainingProgram
from app.models.masters.department import Department
from app.models.masters.designation import Designation
from app.models.masters.organization import Organization
from app.models.masters.unit import Unit
from app.models.payroll.salary_component import ComponentCategory, ComponentType, SalaryComponent

DEMO_MOBILE = "9876543210"
DEMO_EMAIL = "ess.demo@smfc.com"
DEMO_EMPLOYEE_CODE = "ESSDEMO001"
DEMO_USERNAME = "ess.demo.employee"
DEMO_PASSWORD = "EssDemo@123"


def indian_financial_year(today: date) -> str:
    start_year = today.year if today.month >= 4 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


async def one_or_create(session: AsyncSession, model, where, defaults):
    result = await session.execute(select(model).filter_by(**where))
    row = result.scalar_one_or_none()
    if row:
        for key, value in defaults.items():
            setattr(row, key, value)
        return row
    row = model(**where, **defaults)
    session.add(row)
    await session.flush()
    return row


async def get_or_create_org(session: AsyncSession) -> Organization:
    result = await session.execute(
        select(Organization).order_by(Organization.created_at.asc()).limit(1)
    )
    org = result.scalar_one_or_none()
    if org:
        return org
    return await one_or_create(
        session,
        Organization,
        {"code": "SMFC_UAT"},
        {
            "name": "Sagarmala Finance Corporation",
            "legal_name": "Sagarmala Finance Corporation Limited",
            "short_name": "SFC",
            "pan": "AABCS1234F",
            "tan": "MUMS12345A",
            "gstin": "27AABCS1234F1Z5",
            "status": EntityStatus.ACTIVE,
        },
    )


async def seed_org_structure(session: AsyncSession, org: Organization):
    unit = await one_or_create(
        session,
        Unit,
        {"code": "ESS-HO"},
        {
            "organization_id": org.id,
            "name": "Head Office",
            "short_name": "HO",
            "unit_type": UnitType.HEAD_OFFICE.value,
            "level": 1,
            "status": EntityStatus.ACTIVE.value,
        },
    )
    department = await one_or_create(
        session,
        Department,
        {"code": "ESS-HR"},
        {
            "organization_id": org.id,
            "name": "Human Resources",
            "short_name": "HR",
            "level": 1,
            "status": EntityStatus.ACTIVE.value,
        },
    )
    designation = await one_or_create(
        session,
        Designation,
        {"code": "ESS-EXEC"},
        {
            "name": "Operations Executive",
            "short_name": "Executive",
            "department_id": department.id,
            "level": 3,
            "status": EntityStatus.ACTIVE.value,
        },
    )
    return unit, department, designation


async def seed_user_employee(
    session: AsyncSession,
    org: Organization,
    unit: Unit,
    department: Department,
    designation: Designation,
):
    user = await one_or_create(
        session,
        User,
        {"username": DEMO_USERNAME},
        {
            "email": DEMO_EMAIL,
            "full_name": "ESS Demo Employee",
            "employee_code": DEMO_EMPLOYEE_CODE,
            "password_hash": get_password_hash(DEMO_PASSWORD),
            "password_changed_at": datetime.now(UTC),
            "status": UserStatus.ACTIVE.value,
            "organization_id": org.id,
            "default_unit_id": unit.id,
            "phone": DEMO_MOBILE,
        },
    )
    employee = await one_or_create(
        session,
        Employee,
        {"organization_id": org.id, "employee_code": DEMO_EMPLOYEE_CODE},
        {
            "first_name": "ESS",
            "last_name": "Employee",
            "display_name": "ESS Demo Employee",
            "gender": Gender.MALE,
            "date_of_birth": date(1992, 8, 14),
            "personal_email": DEMO_EMAIL,
            "personal_mobile": DEMO_MOBILE,
            "official_email": DEMO_EMAIL,
            "department_id": department.id,
            "designation_id": designation.id,
            "unit_id": unit.id,
            "date_of_joining": date.today() - timedelta(days=420),
            "employment_type": EmploymentType.PERMANENT,
            "employment_status": EmploymentStatus.ACTIVE,
            "shift_id": None,
            "user_id": user.id,
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123412341234",
            "uan_number": "100200300400",
        },
    )
    ess_user = await one_or_create(
        session,
        ESSUser,
        {"organization_id": org.id, "employee_id": employee.id},
        {
            "mobile": DEMO_MOBILE,
            "email": DEMO_EMAIL,
            "is_mobile_verified": True,
            "is_email_verified": True,
            "status": ESSUserStatus.ACTIVE.value,
        },
    )
    return user, employee, ess_user


async def seed_attendance_leave(
    session: AsyncSession,
    org: Organization,
    employee: Employee,
    user: User,
):
    shift = await one_or_create(
        session,
        Shift,
        {"organization_id": org.id, "shift_code": "GEN"},
        {
            "shift_name": "General Shift",
            "shift_type": ShiftType.GENERAL,
            "start_time": time(9, 30),
            "end_time": time(18, 0),
            "break_duration_minutes": 30,
            "working_hours": 480,
            "half_day_hours": 240,
            "is_active": True,
        },
    )
    employee.shift_id = shift.id

    today = date.today()
    month_start = today.replace(day=1)
    calendar = await one_or_create(
        session,
        HolidayCalendar,
        {"organization_id": org.id, "year": today.year, "calendar_name": "ESS Demo Calendar"},
        {"description": "Demo holiday calendar", "is_active": True},
    )
    await one_or_create(
        session,
        Holiday,
        {"calendar_id": calendar.id, "holiday_date": month_start + timedelta(days=1)},
        {"holiday_name": "Demo Holiday", "holiday_type": "COMPANY", "is_optional": False},
    )

    leave_types = [
        ("EL", "Earned Leave", LeaveCategory.EARNED, Decimal("18.00")),
        ("SL", "Sick Leave", LeaveCategory.SICK, Decimal("12.00")),
        ("CL", "Casual Leave", LeaveCategory.CASUAL, Decimal("8.00")),
    ]
    seeded_types: list[LeaveType] = []
    for code, name, category, quota in leave_types:
        seeded_types.append(
            await one_or_create(
                session,
                LeaveType,
                {"organization_id": org.id, "leave_code": code},
                {
                    "leave_name": name,
                    "category": category,
                    "annual_quota": quota,
                    "min_days_per_application": Decimal("0.50"),
                    "is_active": True,
                    "display_order": len(seeded_types) + 1,
                },
            )
        )

    for leave_type in seeded_types:
        await one_or_create(
            session,
            LeaveBalance,
            {
                "employee_id": employee.id,
                "leave_type_id": leave_type.id,
                "year": today.year,
            },
            {
                "opening_balance": Decimal("0.00"),
                "accrued": leave_type.annual_quota,
                "carry_forward": (
                    Decimal("2.00") if leave_type.leave_code == "EL" else Decimal("0.00")
                ),
                "adjustment": Decimal("0.00"),
                "used": Decimal("2.00") if leave_type.leave_code == "EL" else Decimal("0.00"),
                "encashed": Decimal("0.00"),
                "lapsed": Decimal("0.00"),
            },
        )

    await one_or_create(
        session,
        LeaveApplication,
        {"application_number": f"ESS-LV-{today.year}-APPROVED"},
        {
            "employee_id": employee.id,
            "leave_type_id": seeded_types[0].id,
            "from_date": today - timedelta(days=15),
            "to_date": today - timedelta(days=14),
            "is_half_day": False,
            "total_days": Decimal("2.00"),
            "working_days": Decimal("2.00"),
            "reason": "Family function",
            "status": LeaveApplicationStatus.APPROVED,
            "approved_by": user.id,
            "approved_at": today - timedelta(days=16),
            "approver_remarks": "Approved for demo.",
        },
    )
    await one_or_create(
        session,
        LeaveApplication,
        {"application_number": f"ESS-LV-{today.year}-PENDING"},
        {
            "employee_id": employee.id,
            "leave_type_id": seeded_types[1].id,
            "from_date": today + timedelta(days=7),
            "to_date": today + timedelta(days=7),
            "is_half_day": False,
            "total_days": Decimal("1.00"),
            "working_days": Decimal("1.00"),
            "reason": "Medical consultation",
            "status": LeaveApplicationStatus.PENDING,
        },
    )

    for offset in range(0, min(today.day, 10)):
        attendance_date = month_start + timedelta(days=offset)
        is_weekoff = attendance_date.weekday() == 6
        await one_or_create(
            session,
            Attendance,
            {"employee_id": employee.id, "attendance_date": attendance_date},
            {
                "shift_id": shift.id,
                "scheduled_in": time(9, 30),
                "scheduled_out": time(18, 0),
                "first_in": None if is_weekoff else time(9, 24),
                "last_out": None if is_weekoff else time(18, 12),
                "status": AttendanceStatus.WEEK_OFF if is_weekoff else AttendanceStatus.PRESENT,
                "total_work_minutes": 0 if is_weekoff else 528,
                "break_minutes": 0 if is_weekoff else 30,
                "effective_work_minutes": 0 if is_weekoff else 498,
                "is_week_off": is_weekoff,
                "is_processed": True,
            },
        )

    await one_or_create(
        session,
        AttendanceRegularization,
        {"employee_id": employee.id, "attendance_date": today - timedelta(days=1)},
        {
            "request_type": "MISSED_PUNCH",
            "reason": "Forgot to punch out after late official meeting.",
            "requested_first_in": time(9, 30),
            "requested_last_out": time(18, 45),
            "status": "PENDING",
            "created_by": user.id,
        },
    )


async def seed_payroll(session: AsyncSession, org: Organization, employee: Employee):
    today = date.today()
    month = today.month - 1 or 12
    year = today.year if today.month > 1 else today.year - 1
    basic = await one_or_create(
        session,
        SalaryComponent,
        {"organization_id": org.id, "component_code": "BASIC"},
        {
            "component_name": "Basic Salary",
            "component_type": ComponentType.EARNING,
            "category": ComponentCategory.BASIC,
            "calculation_type": "FIXED",
            "default_value": Decimal("75000.00"),
            "is_taxable": True,
            "display_order": 1,
        },
    )
    tds = await one_or_create(
        session,
        SalaryComponent,
        {"organization_id": org.id, "component_code": "TDS"},
        {
            "component_name": "Tax Deducted at Source",
            "component_type": ComponentType.DEDUCTION,
            "category": ComponentCategory.STATUTORY,
            "calculation_type": "FIXED",
            "default_value": Decimal("8000.00"),
            "is_taxable": False,
            "display_order": 90,
        },
    )
    salary_result = await session.execute(
        text(
            """
            select id from payroll_employee_salary
            where employee_id = :employee_id and status = 'ACTIVE'::employeesalarystatus
            limit 1
            """
        ),
        {"employee_id": employee.id},
    )
    employee_salary_id = salary_result.scalar_one_or_none()
    if not employee_salary_id:
        employee_salary_id = uuid4()
        await session.execute(
            text(
                """
                insert into payroll_employee_salary (
                    id, employee_id, effective_from, gross_salary, net_salary, ctc,
                    status, annual_ctc, annual_gross, annual_net, monthly_ctc,
                    monthly_gross, monthly_basic, monthly_net, revision_number,
                    is_active, version
                ) values (
                    :id, :employee_id, :effective_from, 125000, 110500, 1500000,
                    'ACTIVE'::employeesalarystatus, 1500000, 1500000, 1326000,
                    125000, 125000, 75000, 110500, 1, true, 1
                )
                """
            ),
            {
                "id": employee_salary_id,
                "employee_id": employee.id,
                "effective_from": date(year, month, 1),
            },
        )

    batch_id = uuid4()
    await session.execute(
        text(
            """
            insert into payroll_batch (
                id, organization_id, batch_reference, batch_number, payroll_month,
                payroll_year, pay_period_from, pay_period_to, payment_date, status,
                total_employees, total_gross, total_deductions, total_net,
                total_employer_contribution, total_employer_statutory,
                total_pf_employee, total_pf_employer, total_esi_employee,
                total_esi_employer, total_pt, total_tds, paid_at, is_active, version
            ) values (
                :id, :organization_id, :batch_reference, :batch_number,
                :payroll_month, :payroll_year, :pay_period_from, :pay_period_to,
                :payment_date, 'PAID'::payrollbatchstatus, 1, 125000, 14500,
                110500, 0, 0, 1800, 1800, 0, 0, 200, 8000, now(), true, 1
            )
            on conflict (organization_id, payroll_month, payroll_year)
            do update set
                status = 'PAID'::payrollbatchstatus,
                total_employees = excluded.total_employees,
                total_gross = excluded.total_gross,
                total_deductions = excluded.total_deductions,
                total_net = excluded.total_net,
                paid_at = now()
            returning id
            """
        ),
        {
            "id": batch_id,
            "organization_id": org.id,
            "batch_reference": f"ESS-PAY-{year}-{month:02d}",
            "batch_number": f"ESS-PAY-{year}-{month:02d}",
            "payroll_month": month,
            "payroll_year": year,
            "pay_period_from": date(year, month, 1),
            "pay_period_to": date(year, month, 28),
            "payment_date": date(year, month, 28),
        },
    )
    batch_id = (
        await session.execute(
            text(
                """
                select id from payroll_batch
                where organization_id = :organization_id
                  and payroll_month = :payroll_month
                  and payroll_year = :payroll_year
                """
            ),
            {"organization_id": org.id, "payroll_month": month, "payroll_year": year},
        )
    ).scalar_one()

    payslip_id = uuid4()
    await session.execute(
        text(
            """
            insert into payroll_payslip (
                id, batch_id, employee_id, employee_salary_id, payroll_month,
                payroll_year, payslip_number, employee_code, employee_name,
                department_name, designation_name, pan_number, uan_number,
                working_days, paid_days, days_present, days_absent, leave_days,
                lop_days, basic_salary, gross_earnings, gross_salary,
                total_earnings, total_deductions, net_salary, pf_wage,
                taxable_income, status, payment_reference, paid_at, is_active, version
            ) values (
                :id, :batch_id, :employee_id, :employee_salary_id, :payroll_month,
                :payroll_year, :payslip_number, :employee_code, :employee_name,
                'Human Resources', 'Operations Executive', :pan_number, :uan_number,
                22, 22, 21, 0, 1, 0, 75000, 125000, 125000, 125000, 14500,
                110500, 15000, 1500000, 'PAID'::payslipstatus,
                'UTRDEMOESS001', now(), true, 1
            )
            on conflict (batch_id, employee_id)
            do update set
                status = 'PAID'::payslipstatus,
                gross_earnings = excluded.gross_earnings,
                total_deductions = excluded.total_deductions,
                net_salary = excluded.net_salary,
                payment_reference = excluded.payment_reference,
                paid_at = now()
            returning id
            """
        ),
        {
            "id": payslip_id,
            "batch_id": batch_id,
            "employee_id": employee.id,
            "employee_salary_id": employee_salary_id,
            "payroll_month": month,
            "payroll_year": year,
            "payslip_number": f"ESS-PS-{year}-{month:02d}-{DEMO_EMPLOYEE_CODE}",
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "pan_number": employee.pan_number,
            "uan_number": employee.uan_number,
        },
    )
    payslip_id = (
        await session.execute(
            text(
                """
                select id from payroll_payslip
                where batch_id = :batch_id and employee_id = :employee_id
                """
            ),
            {"batch_id": batch_id, "employee_id": employee.id},
        )
    ).scalar_one()
    await session.execute(
        text("delete from payroll_payslip_component where payslip_id = :payslip_id"),
        {"payslip_id": payslip_id},
    )
    await session.execute(
        text(
            """
            insert into payroll_payslip_component (
                payslip_id, component_id, component_name, component_type, amount, is_arrear
            ) values
                (:payslip_id, :basic_id, 'Basic Salary', 'EARNING'::componenttype, 75000, false),
                (
                    :payslip_id, :tds_id, 'Tax Deducted at Source',
                    'DEDUCTION'::componenttype, 8000, false
                )
            """
        ),
        {"payslip_id": payslip_id, "basic_id": basic.id, "tds_id": tds.id},
    )


async def seed_ess_operations(
    session: AsyncSession,
    org: Organization,
    employee: Employee,
    ess_user: ESSUser,
    user: User,
):
    category = await one_or_create(
        session,
        ReimbursementCategory,
        {"organization_id": org.id, "code": "TRAVEL"},
        {
            "name": "Official Travel",
            "claim_type": ClaimType.TRAVEL,
            "max_amount_per_claim": Decimal("25000.00"),
            "requires_approval": True,
            "requires_bills": True,
            "is_active": True,
        },
    )
    claim = await one_or_create(
        session,
        ReimbursementClaim,
        {"organization_id": org.id, "claim_number": "ESS-EXP-0001"},
        {
            "ess_user_id": ess_user.id,
            "employee_id": employee.id,
            "claim_date": date.today(),
            "category_id": category.id,
            "claim_type": ClaimType.TRAVEL,
            "expense_from": date.today() - timedelta(days=5),
            "expense_to": date.today() - timedelta(days=5),
            "claimed_amount": Decimal("2450.00"),
            "approved_amount": None,
            "description": "Local travel for client coordination",
            "purpose": "Demo reimbursement approval flow",
            "bills_attached": 1,
            "attachments": {
                "files": [
                    {"name": "travel-bill-demo.pdf", "url": "/demo/travel-bill-demo.pdf"}
                ]
            },
            "status": ClaimStatus.SUBMITTED.value,
        },
    )
    await one_or_create(
        session,
        ReimbursementLineItem,
        {"claim_id": claim.id, "line_number": 1},
        {
            "expense_date": date.today() - timedelta(days=5),
            "description": "Cab fare",
            "amount": Decimal("2450.00"),
            "bill_number": "CAB-DEMO-001",
            "attachment_url": "/demo/travel-bill-demo.pdf",
            "attachment_name": "travel-bill-demo.pdf",
        },
    )

    helpdesk_category = await one_or_create(
        session,
        TicketCategoryMaster,
        {"organization_id": org.id, "code": "HR_QUERY"},
        {
            "name": "HR Query",
            "category_type": TicketCategory.HR_QUERY,
            "department": "HR",
            "response_sla_hours": 4,
            "resolution_sla_hours": 48,
            "is_active": True,
        },
    )
    await one_or_create(
        session,
        HelpdeskTicket,
        {"organization_id": org.id, "ticket_number": "ESS-HD-0001"},
        {
            "ess_user_id": ess_user.id,
            "employee_id": employee.id,
            "subject": "Update emergency contact details",
            "description": "Need HR confirmation for changed emergency contact details.",
            "category_id": helpdesk_category.id,
            "category_type": TicketCategory.HR_QUERY.value,
            "priority": TicketPriority.NORMAL.value,
            "assigned_department": "HR",
            "sla_response_hours": 4,
            "sla_resolution_hours": 48,
            "status": TicketStatus.OPEN.value,
        },
    )

    fy = indian_financial_year(date.today())
    section = await one_or_create(
        session,
        ITDeclarationMaster,
        {"organization_id": org.id, "section_code": "80C"},
        {
            "section_name": "Section 80C",
            "description": "Investments eligible under section 80C.",
            "category": "DEDUCTION",
            "max_limit": Decimal("150000.00"),
            "is_combined_limit": False,
            "applicable_from_fy": fy,
            "requires_proof": True,
            "proof_types": ["RECEIPT", "CERTIFICATE"],
            "display_order": 1,
            "help_text": "PPF, ELSS, LIC and other eligible investments.",
            "applicable_in_old_regime": True,
            "applicable_in_new_regime": False,
            "is_active": True,
        },
    )
    declaration = await one_or_create(
        session,
        ITDeclaration,
        {"organization_id": org.id, "employee_id": employee.id, "financial_year": fy},
        {
            "ess_user_id": ess_user.id,
            "tax_regime": "OLD",
            "status": "DRAFT",
            "total_declared_amount": Decimal("50000.00"),
            "total_verified_amount": Decimal("0.00"),
            "total_approved_amount": Decimal("0.00"),
            "estimated_taxable_income": Decimal("1450000.00"),
            "estimated_tax_liability": Decimal("210000.00"),
            "monthly_tds": Decimal("17500.00"),
            "is_latest": True,
        },
    )
    await one_or_create(
        session,
        ITDeclarationItem,
        {
            "declaration_id": declaration.id,
            "section_id": section.id,
            "particular": "ELSS Mutual Fund",
        },
        {
            "section_code": "80C",
            "declared_amount": Decimal("50000.00"),
            "verified_amount": Decimal("0.00"),
            "investment_date": date.today() - timedelta(days=30),
            "institution_name": "Demo AMC",
            "is_verified": False,
        },
    )


async def seed_assets_training_performance(
    session: AsyncSession,
    org: Organization,
    unit: Unit,
    department: Department,
    employee: Employee,
    user: User,
):
    category = await one_or_create(
        session,
        AssetCategory,
        {"organization_id": org.id, "category_code": "LAPTOP"},
        {
            "category_name": "Laptop",
            "asset_type": AssetType.TANGIBLE,
            "depreciation_method": DepreciationMethod.SLM,
            "useful_life_years": 3,
            "residual_value_pct": Decimal("5.00"),
            "depreciation_rate_slm": Decimal("31.67"),
            "depreciation_rate_wdv": Decimal("40.00"),
            "capitalization_threshold": Decimal("5000.00"),
            "requires_insurance": False,
            "requires_amc": True,
        },
    )
    await one_or_create(
        session,
        FixedAsset,
        {"organization_id": org.id, "asset_code": "ESS-LAP-0001"},
        {
            "asset_name": "Dell Latitude Demo Laptop",
            "category_id": category.id,
            "location_id": unit.id,
            "department_id": department.id,
            "custodian_employee_id": employee.id,
            "acquisition_date": date.today() - timedelta(days=180),
            "put_to_use_date": date.today() - timedelta(days=170),
            "acquisition_type": AssetAcquisitionType.PURCHASE,
            "acquisition_cost": Decimal("95000.00"),
            "installation_cost": Decimal("0.00"),
            "other_costs": Decimal("0.00"),
            "total_cost": Decimal("95000.00"),
            "residual_value": Decimal("5000.00"),
            "depreciable_value": Decimal("90000.00"),
            "useful_life_months": 36,
            "depreciation_method": DepreciationMethod.SLM,
            "depreciation_rate": Decimal("31.67"),
            "wdv_value": Decimal("80500.00"),
            "serial_number": "ESS-DEMO-LAPTOP-001",
            "quantity": 1,
            "status": AssetStatus.ACTIVE,
        },
    )

    program = await one_or_create(
        session,
        TrainingProgram,
        {"organization_id": org.id, "program_code": "ESS-TRAIN-001"},
        {
            "title": "ERP Operations Training",
            "description": "Demo training program for ESS employee workflow.",
            "category": "Operations",
            "mode": "ONLINE",
            "trainer_type": "INTERNAL",
            "trainer_name": "HR Team",
            "start_date": date.today() + timedelta(days=10),
            "end_date": date.today() + timedelta(days=10),
            "duration_hours": Decimal("2.00"),
            "location": "Online",
            "max_participants": 25,
            "status": "SCHEDULED",
            "cost_per_participant": Decimal("0.00"),
            "is_mandatory": True,
            "certificate_provided": True,
        },
    )
    await one_or_create(
        session,
        TrainingNomination,
        {"program_id": program.id, "employee_id": employee.id},
        {"status": "NOMINATED", "attendance_marked": False, "created_by": user.id},
    )

    cycle = await one_or_create(
        session,
        AppraisalCycle,
        {"organization_id": org.id, "code": "ESS-APP-2026"},
        {
            "name": "ESS Demo Appraisal Cycle",
            "description": "Demo cycle for goals and self-appraisal.",
            "cycle_type": "ANNUAL",
            "start_date": date.today() - timedelta(days=30),
            "end_date": date.today() + timedelta(days=60),
            "goal_setting_start": date.today() - timedelta(days=30),
            "goal_setting_end": date.today() + timedelta(days=10),
            "self_appraisal_start": date.today() - timedelta(days=1),
            "self_appraisal_end": date.today() + timedelta(days=20),
            "manager_review_start": date.today() + timedelta(days=21),
            "manager_review_end": date.today() + timedelta(days=40),
            "status": "SELF_APPRAISAL",
            "rating_scale": 5,
            "allow_self_rating": True,
        },
    )
    await one_or_create(
        session,
        PerformanceGoal,
        {"appraisal_cycle_id": cycle.id, "employee_id": employee.id, "goal_number": 1},
        {
            "title": "Improve ESS adoption",
            "description": "Complete ESS workflows and provide feedback.",
            "category": "Operations",
            "weightage": Decimal("100.00"),
            "target_value": "100%",
            "measurement_criteria": "All employee workflows completed.",
            "start_date": date.today() - timedelta(days=20),
            "due_date": date.today() + timedelta(days=30),
            "status": "APPROVED",
            "progress_percent": Decimal("40.00"),
        },
    )
    await one_or_create(
        session,
        EmployeeAppraisal,
        {"appraisal_cycle_id": cycle.id, "employee_id": employee.id},
        {
            "reviewer_id": user.id,
            "status": "NOT_STARTED",
        },
    )


async def seed() -> None:
    async with async_session_factory() as session:
        org = await get_or_create_org(session)
        unit, department, designation = await seed_org_structure(session, org)
        user, employee, ess_user = await seed_user_employee(
            session, org, unit, department, designation
        )
        await seed_attendance_leave(session, org, employee, user)
        await seed_payroll(session, org, employee)
        await seed_ess_operations(session, org, employee, ess_user, user)
        await seed_assets_training_performance(session, org, unit, department, employee, user)
        await session.commit()
        print("ESS + HRMS demo seed complete")
        print(f"  ESS mobile: {DEMO_MOBILE}")
        print(f"  ESS email:  {DEMO_EMAIL}")
        print(f"  ESS linked admin user: {DEMO_USERNAME} / {DEMO_PASSWORD}")
        print("  Login is OTP-based; read OTP from ess_otp after Send OTP in local/demo.")


if __name__ == "__main__":
    asyncio.run(seed())
