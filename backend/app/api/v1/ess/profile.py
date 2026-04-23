"""ESS Profile and Dashboard API endpoints."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.ess.profile_service import ESSProfileService
from app.models.ess.enums import ProfileUpdateType, ProfileUpdateStatus


router = APIRouter(prefix="/profile", tags=["ESS Profile"])


# ==================== Schemas ====================

class EmployeeProfileResponse(BaseModel):
    """Employee profile response."""
    id: str
    employee_code: str
    first_name: str
    last_name: str
    display_name: Optional[str]
    gender: str
    date_of_birth: date
    personal_email: Optional[str]
    personal_mobile: str
    official_email: Optional[str]
    official_mobile: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    unit: Optional[str]
    date_of_joining: Optional[date]
    blood_group: Optional[str]
    marital_status: Optional[str]


class ProfileUpdateRequestCreate(BaseModel):
    """Request to update profile."""
    update_type: ProfileUpdateType
    current_values: dict
    requested_values: dict
    change_reason: Optional[str] = None
    attachments: Optional[dict] = None


class ProfileUpdateRequestResponse(BaseModel):
    """Profile update request response."""
    id: str
    request_number: str
    update_type: str
    current_values: dict
    requested_values: dict
    change_reason: Optional[str]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    reviewer_remarks: Optional[str]
    created_at: str


class PayslipSummary(BaseModel):
    """Payslip summary."""
    id: str
    pay_period: str
    gross_salary: float
    total_deductions: float
    net_salary: float
    tax_deducted: float


class YTDSummary(BaseModel):
    """Year-to-date salary summary."""
    financial_year: str
    total_gross: float
    total_deductions: float
    total_net: float
    total_tax: float
    months_processed: int


class LeaveBalanceResponse(BaseModel):
    """Leave balance response."""
    type: str
    code: str
    balance: float
    used: float


class AttendanceSummaryResponse(BaseModel):
    """Attendance summary response."""
    month: str
    working_days: float
    present: int
    absent: int
    leave: int
    holiday: int
    half_day: int
    work_from_home: int


class DashboardResponse(BaseModel):
    """Dashboard response."""
    employee: dict
    leave_balance: List[LeaveBalanceResponse]
    latest_payslip: Optional[dict]
    attendance_this_month: dict
    pending_requests: int


# ==================== Endpoints ====================

@router.get("/me", response_model=EmployeeProfileResponse)
async def get_my_profile(
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get current user's profile."""
    service = ESSProfileService(session)
    employee = await service.get_employee_profile(employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return EmployeeProfileResponse(
        id=str(employee.id),
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        display_name=employee.display_name,
        gender=employee.gender,
        date_of_birth=employee.date_of_birth,
        personal_email=employee.personal_email,
        personal_mobile=employee.personal_mobile,
        official_email=employee.official_email,
        official_mobile=employee.official_mobile,
        department=employee.department.name if employee.department else None,
        designation=employee.designation.name if employee.designation else None,
        unit=employee.unit.name if employee.unit else None,
        date_of_joining=employee.date_of_joining,
        blood_group=employee.blood_group,
        marital_status=employee.marital_status,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get ESS dashboard data."""
    service = ESSProfileService(session)
    data = await service.get_dashboard_data(employee_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard data not found",
        )

    return data


@router.post("/update-requests", response_model=ProfileUpdateRequestResponse)
async def create_update_request(
    request: ProfileUpdateRequestCreate,
    organization_id: UUID,  # From authenticated user
    ess_user_id: UUID,  # From authenticated user
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Create a profile update request."""
    service = ESSProfileService(session)

    update_request = await service.request_profile_update(
        organization_id=organization_id,
        ess_user_id=ess_user_id,
        employee_id=employee_id,
        update_type=request.update_type,
        current_values=request.current_values,
        requested_values=request.requested_values,
        change_reason=request.change_reason,
        attachments=request.attachments,
    )

    await session.commit()

    return ProfileUpdateRequestResponse(
        id=str(update_request.id),
        request_number=update_request.request_number,
        update_type=update_request.update_type.value,
        current_values=update_request.current_values,
        requested_values=update_request.requested_values,
        change_reason=update_request.change_reason,
        status=update_request.status.value,
        reviewed_by=str(update_request.reviewed_by) if update_request.reviewed_by else None,
        reviewed_at=update_request.reviewed_at.isoformat() if update_request.reviewed_at else None,
        reviewer_remarks=update_request.reviewer_remarks,
        created_at=update_request.created_at.isoformat(),
    )


@router.get("/update-requests", response_model=List[ProfileUpdateRequestResponse])
async def get_update_requests(
    employee_id: UUID,  # From authenticated user
    status: Optional[ProfileUpdateStatus] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get profile update requests."""
    service = ESSProfileService(session)

    requests, total = await service.get_profile_update_requests(
        employee_id=employee_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return [
        ProfileUpdateRequestResponse(
            id=str(req.id),
            request_number=req.request_number,
            update_type=req.update_type.value,
            current_values=req.current_values,
            requested_values=req.requested_values,
            change_reason=req.change_reason,
            status=req.status.value,
            reviewed_by=str(req.reviewed_by) if req.reviewed_by else None,
            reviewed_at=req.reviewed_at.isoformat() if req.reviewed_at else None,
            reviewer_remarks=req.reviewer_remarks,
            created_at=req.created_at.isoformat(),
        )
        for req in requests
    ]


# ==================== Payslip Endpoints ====================

@router.get("/payslips", response_model=List[PayslipSummary])
async def get_payslips(
    employee_id: UUID,  # From authenticated user
    financial_year: Optional[str] = None,
    limit: int = Query(12, le=36),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get payslips for the employee."""
    service = ESSProfileService(session)

    payslips, total = await service.get_payslips(
        employee_id=employee_id,
        financial_year=financial_year,
        limit=limit,
        offset=offset,
    )

    return [
        PayslipSummary(
            id=str(p.id),
            pay_period=p.pay_period,
            gross_salary=float(p.gross_salary),
            total_deductions=float(p.total_deductions),
            net_salary=float(p.net_salary),
            tax_deducted=float(p.tax_deducted) if p.tax_deducted else 0,
        )
        for p in payslips
    ]


@router.get("/payslips/{payslip_id}")
async def get_payslip_detail(
    payslip_id: UUID,
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get detailed payslip."""
    service = ESSProfileService(session)

    payslip = await service.get_payslip_by_id(payslip_id, employee_id)

    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found",
        )

    # Return full payslip details
    return {
        "id": str(payslip.id),
        "pay_period": payslip.pay_period,
        "gross_salary": float(payslip.gross_salary),
        "basic_salary": float(payslip.basic_salary) if payslip.basic_salary else 0,
        "total_earnings": float(payslip.total_earnings) if payslip.total_earnings else 0,
        "total_deductions": float(payslip.total_deductions),
        "net_salary": float(payslip.net_salary),
        "tax_deducted": float(payslip.tax_deducted) if payslip.tax_deducted else 0,
        "earnings": payslip.earnings if hasattr(payslip, 'earnings') else {},
        "deductions": payslip.deductions if hasattr(payslip, 'deductions') else {},
    }


@router.get("/ytd-summary", response_model=YTDSummary)
async def get_ytd_summary(
    employee_id: UUID,  # From authenticated user
    financial_year: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get year-to-date salary summary."""
    service = ESSProfileService(session)
    summary = await service.get_ytd_summary(employee_id, financial_year)
    return YTDSummary(**summary)


# ==================== Leave Endpoints ====================

@router.get("/leave-balance", response_model=List[LeaveBalanceResponse])
async def get_leave_balance(
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get leave balances."""
    service = ESSProfileService(session)
    balances = await service.get_leave_balances(employee_id)

    return [
        LeaveBalanceResponse(
            type=lb.leave_type.name if lb.leave_type else "Unknown",
            code=lb.leave_type.code if lb.leave_type else "",
            balance=float(lb.balance),
            used=float(lb.used),
        )
        for lb in balances
    ]


# ==================== Attendance Endpoints ====================

@router.get("/attendance")
async def get_attendance(
    employee_id: UUID,  # From authenticated user
    from_date: date = Query(...),
    to_date: date = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Get attendance records."""
    service = ESSProfileService(session)
    records = await service.get_attendance(employee_id, from_date, to_date)

    return [
        {
            "date": r.attendance_date.isoformat(),
            "status": r.status,
            "in_time": r.in_time.isoformat() if r.in_time else None,
            "out_time": r.out_time.isoformat() if r.out_time else None,
            "working_hours": float(r.working_hours) if r.working_hours else 0,
            "shift": r.shift.name if hasattr(r, 'shift') and r.shift else None,
        }
        for r in records
    ]


@router.get("/attendance/summary", response_model=AttendanceSummaryResponse)
async def get_attendance_summary(
    employee_id: UUID,  # From authenticated user
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),  # YYYY-MM
    session: AsyncSession = Depends(get_session),
):
    """Get attendance summary for a month."""
    service = ESSProfileService(session)
    summary = await service.get_attendance_summary(employee_id, month)
    return AttendanceSummaryResponse(**summary)
