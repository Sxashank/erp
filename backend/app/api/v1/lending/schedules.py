"""Loan Schedule API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.lending import ScheduleService

router = APIRouter()


# Request/Response Schemas
class ScheduleGenerateRequest(BaseModel):
    """Request to generate loan schedule."""
    loan_account_id: UUID
    principal: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)
    disbursement_date: date
    emi_day: int = Field(default=1, ge=1, le=28)
    calculation_method: str = Field(default="reducing_balance")
    moratorium_months: int = Field(default=0, ge=0)


class ScheduleEntryResponse(BaseModel):
    """Single schedule entry."""
    id: Optional[UUID] = None
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    opening_balance: Decimal
    closing_balance: Decimal
    is_moratorium: bool = False
    is_paid: bool = False
    is_partial: bool = False


class ScheduleResponse(BaseModel):
    """Complete schedule response."""
    loan_account_id: UUID
    total_installments: int
    total_principal: Decimal
    total_interest: Decimal
    total_amount: Decimal
    entries: List[ScheduleEntryResponse]


class EMICalculateRequest(BaseModel):
    """Request to calculate EMI."""
    principal: Decimal = Field(..., gt=0)
    annual_rate: Decimal = Field(..., ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)


class EMIResponse(BaseModel):
    """EMI calculation response."""
    emi: Decimal
    total_interest: Decimal
    total_payment: Decimal
    principal: Decimal
    annual_rate: Decimal
    tenure_months: int


class RescheduleRequest(BaseModel):
    """Request to reschedule a loan."""
    loan_account_id: UUID
    new_tenure: Optional[int] = None
    new_rate: Optional[Decimal] = None
    new_emi: Optional[Decimal] = None
    effective_date: Optional[date] = None
    reason: str = ""


class MarkPaidRequest(BaseModel):
    """Request to mark installment as paid."""
    schedule_id: UUID
    payment_date: date
    principal_paid: Decimal
    interest_paid: Decimal
    receipt_id: Optional[UUID] = None


# Endpoints
@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Generate loan repayment schedule."""
    service = ScheduleService(db)

    schedules = await service.generate_schedule(
        loan_account_id=request.loan_account_id,
        principal=request.principal,
        interest_rate=request.interest_rate,
        tenure_months=request.tenure_months,
        disbursement_date=request.disbursement_date,
        emi_day=request.emi_day,
        calculation_method=request.calculation_method,
        moratorium_months=request.moratorium_months,
        user_id=current_user.id,
    )

    entries = [
        ScheduleEntryResponse(
            id=s.id,
            installment_number=s.installment_number,
            due_date=s.due_date,
            principal_amount=s.principal_amount,
            interest_amount=s.interest_amount,
            total_amount=s.total_amount,
            opening_balance=s.opening_balance,
            closing_balance=s.closing_balance,
            is_moratorium=s.is_moratorium,
            is_paid=s.is_paid if hasattr(s, 'is_paid') else False,
            is_partial=s.is_partial if hasattr(s, 'is_partial') else False,
        )
        for s in schedules
    ]

    total_principal = sum(e.principal_amount for e in entries)
    total_interest = sum(e.interest_amount for e in entries)

    return ScheduleResponse(
        loan_account_id=request.loan_account_id,
        total_installments=len(entries),
        total_principal=total_principal,
        total_interest=total_interest,
        total_amount=total_principal + total_interest,
        entries=entries,
    )


@router.post("/calculate-emi", response_model=EMIResponse)
async def calculate_emi(
    request: EMICalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Calculate EMI without generating schedule."""
    service = ScheduleService(db)

    result = await service.calculate_emi(
        principal=request.principal,
        annual_rate=request.annual_rate,
        tenure_months=request.tenure_months,
    )

    return EMIResponse(**result)


@router.get("/{loan_account_id}", response_model=ScheduleResponse)
async def get_schedule(
    loan_account_id: UUID,
    include_paid: bool = Query(default=True, description="Include paid installments"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get loan schedule for an account."""
    service = ScheduleService(db)

    schedules = await service.get_schedule(
        loan_account_id=loan_account_id,
        include_paid=include_paid,
    )

    if not schedules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No schedule found for this loan account",
        )

    entries = [
        ScheduleEntryResponse(
            id=s.id,
            installment_number=s.installment_number,
            due_date=s.due_date,
            principal_amount=s.principal_amount,
            interest_amount=s.interest_amount,
            total_amount=s.total_amount,
            opening_balance=s.opening_balance,
            closing_balance=s.closing_balance,
            is_moratorium=s.is_moratorium,
            is_paid=s.is_paid,
            is_partial=s.is_partial,
        )
        for s in schedules
    ]

    total_principal = sum(e.principal_amount for e in entries)
    total_interest = sum(e.interest_amount for e in entries)

    return ScheduleResponse(
        loan_account_id=loan_account_id,
        total_installments=len(entries),
        total_principal=total_principal,
        total_interest=total_interest,
        total_amount=total_principal + total_interest,
        entries=entries,
    )


@router.get("/{loan_account_id}/overdue")
async def get_overdue_installments(
    loan_account_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get overdue installments for a loan."""
    service = ScheduleService(db)

    installments = await service.get_overdue_installments(
        loan_account_id=loan_account_id,
        as_of_date=as_of_date,
    )

    return {
        "loan_account_id": str(loan_account_id),
        "as_of_date": as_of_date or date.today(),
        "overdue_count": len(installments),
        "installments": [
            {
                "id": str(i.id),
                "installment_number": i.installment_number,
                "due_date": i.due_date,
                "principal_amount": i.principal_amount,
                "interest_amount": i.interest_amount,
                "total_amount": i.total_amount,
                "days_overdue": (date.today() - i.due_date).days,
            }
            for i in installments
        ],
    }


@router.post("/reschedule", response_model=ScheduleResponse)
async def reschedule_loan(
    request: RescheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Reschedule a loan with new terms."""
    service = ScheduleService(db)

    schedules = await service.reschedule_loan(
        loan_account_id=request.loan_account_id,
        new_tenure=request.new_tenure,
        new_rate=request.new_rate,
        new_emi=request.new_emi,
        effective_date=request.effective_date,
        reason=request.reason,
        user_id=current_user.id,
    )

    entries = [
        ScheduleEntryResponse(
            id=s.id,
            installment_number=s.installment_number,
            due_date=s.due_date,
            principal_amount=s.principal_amount,
            interest_amount=s.interest_amount,
            total_amount=s.total_amount,
            opening_balance=s.opening_balance,
            closing_balance=s.closing_balance,
            is_moratorium=s.is_moratorium,
        )
        for s in schedules
    ]

    total_principal = sum(e.principal_amount for e in entries)
    total_interest = sum(e.interest_amount for e in entries)

    return ScheduleResponse(
        loan_account_id=request.loan_account_id,
        total_installments=len(entries),
        total_principal=total_principal,
        total_interest=total_interest,
        total_amount=total_principal + total_interest,
        entries=entries,
    )


@router.post("/mark-paid")
async def mark_installment_paid(
    request: MarkPaidRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Mark an installment as paid."""
    service = ScheduleService(db)

    schedule = await service.mark_installment_paid(
        schedule_id=request.schedule_id,
        payment_date=request.payment_date,
        principal_paid=request.principal_paid,
        interest_paid=request.interest_paid,
        receipt_id=request.receipt_id,
        user_id=current_user.id,
    )

    return {
        "schedule_id": str(schedule.id),
        "installment_number": schedule.installment_number,
        "is_paid": schedule.is_paid,
        "is_partial": schedule.is_partial,
        "payment_date": schedule.payment_date,
    }
