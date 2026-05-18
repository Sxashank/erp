"""Loan Schedule API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.schemas.base import CamelSchema
from app.services.lending import ScheduleService
from app.core.exceptions import NotFoundException

router = APIRouter()


# Request/Response Schemas
class ScheduleGenerateRequest(CamelSchema):
    """Request to generate loan schedule."""

    loan_account_id: UUID
    principal: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)
    disbursement_date: date
    emi_day: int = Field(default=1, ge=1, le=28)
    calculation_method: str = Field(default="reducing_balance")
    moratorium_months: int = Field(default=0, ge=0)


class SchedulePreviewRequest(CamelSchema):
    """Request to preview (without persisting) a loan schedule.

    Pure math; safe to call before a loan account exists.
    """

    principal: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)
    disbursement_date: date
    emi_day: int = Field(default=1, ge=1, le=28)
    calculation_method: str = Field(default="reducing_balance")
    moratorium_months: int = Field(default=0, ge=0)


class SchedulePreviewLine(CamelSchema):
    """Single preview row — Decimal money preserved on the wire (§6.2)."""

    installment_number: int
    due_date: date
    opening_balance: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    closing_balance: Decimal
    is_moratorium: bool = False


class SchedulePreviewSummary(CamelSchema):
    """Aggregate totals across preview rows."""

    total_installments: int
    total_principal: Decimal
    total_interest: Decimal
    total_amount: Decimal
    emi_amount: Decimal
    last_due_date: date


class SchedulePreviewResponse(CamelSchema):
    """Preview computation: rows + summary, no persistence."""

    entries: list[SchedulePreviewLine]
    summary: SchedulePreviewSummary


class ScheduleEntryResponse(CamelSchema):
    """Single schedule entry."""

    id: UUID | None = None
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


class ScheduleResponse(CamelSchema):
    """Complete schedule response."""

    loan_account_id: UUID
    total_installments: int
    total_principal: Decimal
    total_interest: Decimal
    total_amount: Decimal
    entries: list[ScheduleEntryResponse]


class EMICalculateRequest(CamelSchema):
    """Request to calculate EMI."""

    principal: Decimal = Field(..., gt=0)
    annual_rate: Decimal = Field(..., ge=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)


class EMIResponse(CamelSchema):
    """EMI calculation response."""

    emi: Decimal
    total_interest: Decimal
    total_payment: Decimal
    principal: Decimal
    annual_rate: Decimal
    tenure_months: int


class RescheduleRequest(CamelSchema):
    """Request to reschedule a loan."""

    loan_account_id: UUID
    new_tenure: int | None = None
    new_rate: Decimal | None = None
    new_emi: Decimal | None = None
    effective_date: date | None = None
    reason: str = ""


class MarkPaidRequest(CamelSchema):
    """Request to mark installment as paid."""

    schedule_id: UUID
    payment_date: date
    principal_paid: Decimal
    interest_paid: Decimal
    receipt_id: UUID | None = None


# Endpoints
class OverdueInstallmentResponse(CamelSchema):
    """Overdue installment response."""

    id: UUID
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    days_overdue: int


class OverdueInstallmentsResponse(CamelSchema):
    """Overdue installments response."""

    loan_account_id: UUID
    as_of_date: date
    overdue_count: int
    installments: list[OverdueInstallmentResponse]


class MarkPaidResponse(CamelSchema):
    """Mark installment paid response."""

    schedule_id: UUID
    installment_number: int
    is_paid: bool
    is_partial: bool
    payment_date: date | None


@router.post(
    "/preview",
    response_model=SchedulePreviewResponse,
    response_model_by_alias=True,
)
async def preview_schedule(
    request: SchedulePreviewRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """
    Preview a repayment schedule without persisting.

    Pure computation (no DB writes, no permission gate) — usable by
    LOS calculators, sanction what-if screens, and the borrower
    portal's prepayment / amortization preview.
    """
    service = ScheduleService(db)

    result = service.preview_schedule(
        principal=request.principal,
        interest_rate=request.interest_rate,
        tenure_months=request.tenure_months,
        disbursement_date=request.disbursement_date,
        emi_day=request.emi_day,
        calculation_method=request.calculation_method,
        moratorium_months=request.moratorium_months,
    )

    return SchedulePreviewResponse(
        entries=[SchedulePreviewLine(**row) for row in result["entries"]],
        summary=SchedulePreviewSummary(**result["summary"]),
    )


@router.post(
    "/generate",
    response_model=ScheduleResponse,
    response_model_by_alias=True,
)
async def generate_schedule(
    request: ScheduleGenerateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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
            is_paid=s.is_paid if hasattr(s, "is_paid") else False,
            is_partial=s.is_partial if hasattr(s, "is_partial") else False,
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


@router.post(
    "/calculate-emi",
    response_model=EMIResponse,
    response_model_by_alias=True,
)
async def calculate_emi(
    request: EMICalculateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Calculate EMI without generating schedule."""
    service = ScheduleService(db)

    result = await service.calculate_emi(
        principal=request.principal,
        annual_rate=request.annual_rate,
        tenure_months=request.tenure_months,
    )

    return EMIResponse(**result)


@router.get(
    "/{loan_account_id}",
    response_model=ScheduleResponse,
    response_model_by_alias=True,
)
async def get_schedule(
    loan_account_id: UUID,
    include_paid: bool = Query(default=True, description="Include paid installments"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get loan schedule for an account."""
    service = ScheduleService(db)

    schedules = await service.get_schedule(
        loan_account_id=loan_account_id,
        include_paid=include_paid,
    )

    if not schedules:
        raise NotFoundException(
            detail="No schedule found for this loan account",
            error_code="NO_SCHEDULE_FOUND_FOR_THIS_LOAN",
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


@router.get(
    "/{loan_account_id}/overdue",
    response_model=OverdueInstallmentsResponse,
    response_model_by_alias=True,
)
async def get_overdue_installments(
    loan_account_id: UUID,
    as_of_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get overdue installments for a loan."""
    service = ScheduleService(db)

    installments = await service.get_overdue_installments(
        loan_account_id=loan_account_id,
        as_of_date=as_of_date,
    )

    return {
        "loan_account_id": loan_account_id,
        "as_of_date": as_of_date or date.today(),
        "overdue_count": len(installments),
        "installments": [
            {
                "id": i.id,
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


@router.post(
    "/reschedule",
    response_model=ScheduleResponse,
    response_model_by_alias=True,
)
async def reschedule_loan(
    request: RescheduleRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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


@router.post(
    "/mark-paid",
    response_model=MarkPaidResponse,
    response_model_by_alias=True,
)
async def mark_installment_paid(
    request: MarkPaidRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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
        "schedule_id": schedule.id,
        "installment_number": schedule.installment_number,
        "is_paid": schedule.is_paid,
        "is_partial": schedule.is_partial,
        "payment_date": schedule.payment_date,
    }
