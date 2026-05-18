"""
Separation and Full & Final Settlement API endpoints.

Handles:
- Employee separation (resignation, termination, retirement)
- Clearance workflow
- FnF calculation and payment
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.hris.separation_service import (
    SeparationService,
    ClearanceService,
    FnFService,
    ClearanceChecklistService,
)
from app.models.hris.separation import (
    SeparationType,
    SeparationStatus,
    ResignationReason,
    ClearanceStatus,
    FnFStatus,
)

from app.api.deps import get_db_with_tenant
from app.core.exceptions import BadRequestException, NotFoundException
router = APIRouter(prefix="/separation", tags=["Separation & FnF"])


# ============ Request/Response Schemas ============

class SeparationInitiateRequest(BaseModel):
    """Request to initiate employee separation."""
    employee_id: UUID
    separation_type: SeparationType
    requested_last_working_date: date
    reason_category: Optional[ResignationReason] = None
    reason_detail: Optional[str] = None
    resignation_letter_path: Optional[str] = None


class SeparationApproveRequest(BaseModel):
    """Request to approve separation."""
    approved_last_working_date: date
    remarks: Optional[str] = None


class SeparationRejectRequest(BaseModel):
    """Request to reject separation."""
    rejection_reason: str


class SeparationWithdrawRequest(BaseModel):
    """Request to withdraw separation."""
    reason: Optional[str] = None


class SeparationResponse(BaseModel):
    """Separation response."""
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    separation_type: str
    status: str
    initiation_date: date
    requested_last_working_date: Optional[date] = None
    approved_last_working_date: Optional[date] = None
    actual_last_working_date: Optional[date] = None
    notice_period_days: int
    notice_period_served: int
    notice_period_shortfall: int
    is_notice_buyout: bool
    reason_category: Optional[str] = None
    exit_interview_done: bool
    relieving_letter_issued: bool
    experience_letter_issued: bool
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class SeparationListResponse(BaseModel):
    """List of separations."""
    items: List[SeparationResponse]
    total: int


class ClearanceUpdateRequest(BaseModel):
    """Request to update clearance status."""
    status: ClearanceStatus
    has_recovery: bool = False
    recovery_amount: Optional[Decimal] = None
    recovery_description: Optional[str] = None
    remarks: Optional[str] = None


class ClearanceStatusResponse(BaseModel):
    """Clearance status response."""
    total_items: int
    cleared: int
    pending: int
    recovery_pending: int
    total_recovery_amount: Decimal
    is_complete: bool
    items: List[Dict[str, Any]]


class FnFCalculateRequest(BaseModel):
    """Request to calculate FnF."""
    include_gratuity: bool = True
    include_leave_encashment: bool = True
    additional_earnings: Optional[Dict[str, Decimal]] = None
    additional_deductions: Optional[Dict[str, Decimal]] = None


class FnFPaymentRequest(BaseModel):
    """Request to process FnF payment."""
    payment_date: date
    payment_mode: str = Field(..., pattern="^(BANK_TRANSFER|CHEQUE|CASH)$")
    payment_reference: str


class FnFResponse(BaseModel):
    """FnF settlement response."""
    id: str
    separation_id: str
    employee_id: str
    last_working_date: date
    settlement_date: Optional[date] = None
    status: str
    # Earnings
    pending_salary: Decimal
    leave_encashment: Decimal
    leave_encashment_days: Decimal
    gratuity_amount: Decimal
    gratuity_years: Decimal
    gratuity_eligible: bool
    bonus_amount: Decimal
    pending_reimbursements: Decimal
    other_earnings: Decimal
    total_earnings: Decimal
    # Deductions
    notice_recovery: Decimal
    notice_shortfall_days: int
    advance_recovery: Decimal
    loan_recovery: Decimal
    asset_recovery: Decimal
    clearance_recovery: Decimal
    other_deductions: Decimal
    tds_amount: Decimal
    total_deductions: Decimal
    # Net
    net_payable: Decimal
    # Payment
    payment_date: Optional[date] = None
    payment_mode: Optional[str] = None
    payment_reference: Optional[str] = None

    class Config:
        from_attributes = True


class ClearanceChecklistRequest(BaseModel):
    """Request to create clearance checklist item."""
    checklist_code: str = Field(..., max_length=20)
    checklist_item: str = Field(..., max_length=200)
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    is_mandatory: bool = True
    can_have_recovery: bool = False
    display_order: int = 0


class ClearanceChecklistResponse(BaseModel):
    """Clearance checklist response."""
    id: str
    checklist_code: str
    checklist_item: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    is_mandatory: bool
    can_have_recovery: bool
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


# ============ Dependencies ============

def get_separation_service(
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
) -> SeparationService:
    return SeparationService(session)


def get_clearance_service(
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
) -> ClearanceService:
    return ClearanceService(session)


def get_fnf_service(
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
) -> FnFService:
    return FnFService(session)


def get_checklist_service(
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
) -> ClearanceChecklistService:
    return ClearanceChecklistService(session)


# ============ Separation Endpoints ============

@router.post(
    "",
    response_model=SeparationResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate employee separation",
)
async def initiate_separation(
    organization_id: UUID,
    request: SeparationInitiateRequest,
    service: Annotated[SeparationService, Depends(get_separation_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> SeparationResponse:
    """
    Initiate employee separation process.

    - Supports resignation, termination, retirement, etc.
    - Creates separation record in INITIATED status
    - Calculates notice period requirements
    """
    created_by = UUID("00000000-0000-0000-0000-000000000000")  # Replace with current_user.id

    try:
        separation = await service.initiate_separation(
            organization_id=organization_id,
            employee_id=request.employee_id,
            separation_type=request.separation_type,
            requested_last_working_date=request.requested_last_working_date,
            reason_category=request.reason_category,
            reason_detail=request.reason_detail,
            resignation_letter_path=request.resignation_letter_path,
            created_by=created_by,
        )
        return _map_separation_response(separation)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/{separation_id}",
    response_model=SeparationResponse, response_model_by_alias=True,
    summary="Get separation details",
)
async def get_separation(
    separation_id: UUID,
    service: Annotated[SeparationService, Depends(get_separation_service)],
) -> SeparationResponse:
    """Get separation details by ID."""
    separation = await service.get(separation_id)
    if not separation:
        raise NotFoundException(
            detail=f"Separation {separation_id} not found",
            error_code="SEPARATION_NOT_FOUND",
        )
    return _map_separation_response(separation)


@router.get(
    "",
    response_model=SeparationListResponse, response_model_by_alias=True,
    summary="List separations",
)
async def list_separations(
    organization_id: UUID,
    service: Annotated[SeparationService, Depends(get_separation_service)],
    status_filter: Optional[SeparationStatus] = Query(None, alias="status"),
    separation_type: Optional[SeparationType] = None,
    employee_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
) -> SeparationListResponse:
    """List separations with filters."""
    separations, total = await service.list(
        organization_id=organization_id,
        status=status_filter,
        separation_type=separation_type,
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    return SeparationListResponse(
        items=[_map_separation_response(s) for s in separations],
        total=total,
    )


@router.post(
    "/{separation_id}/approve",
    response_model=SeparationResponse, response_model_by_alias=True,
    summary="Approve separation",
)
async def approve_separation(
    separation_id: UUID,
    request: SeparationApproveRequest,
    service: Annotated[SeparationService, Depends(get_separation_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> SeparationResponse:
    """
    Approve separation request.

    - Sets final last working date
    - Initializes clearance items
    """
    approved_by = UUID("00000000-0000-0000-0000-000000000000")  # Replace with current_user.id

    try:
        separation = await service.approve_separation(
            separation_id=separation_id,
            approved_last_working_date=request.approved_last_working_date,
            approved_by=approved_by,
            remarks=request.remarks,
        )
        return _map_separation_response(separation)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{separation_id}/reject",
    response_model=SeparationResponse, response_model_by_alias=True,
    summary="Reject separation",
)
async def reject_separation(
    separation_id: UUID,
    request: SeparationRejectRequest,
    service: Annotated[SeparationService, Depends(get_separation_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> SeparationResponse:
    """Reject separation request."""
    rejected_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        separation = await service.reject_separation(
            separation_id=separation_id,
            rejection_reason=request.rejection_reason,
            rejected_by=rejected_by,
        )
        return _map_separation_response(separation)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/{separation_id}/withdraw",
    response_model=SeparationResponse, response_model_by_alias=True,
    summary="Withdraw separation",
)
async def withdraw_separation(
    separation_id: UUID,
    request: SeparationWithdrawRequest,
    service: Annotated[SeparationService, Depends(get_separation_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> SeparationResponse:
    """Withdraw separation request (by employee)."""
    withdrawn_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        separation = await service.withdraw_separation(
            separation_id=separation_id,
            withdrawn_by=withdrawn_by,
            reason=request.reason,
        )
        return _map_separation_response(separation)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============ Clearance Endpoints ============

@router.get(
    "/{separation_id}/clearance",
    response_model=ClearanceStatusResponse, response_model_by_alias=True,
    summary="Get clearance status",
)
async def get_clearance_status(
    separation_id: UUID,
    service: Annotated[ClearanceService, Depends(get_clearance_service)],
) -> ClearanceStatusResponse:
    """Get overall clearance status for a separation."""
    status_data = await service.get_clearance_status(separation_id)
    return ClearanceStatusResponse(**status_data)


@router.put(
    "/clearance/{clearance_id}",
    summary="Update clearance item",
)
async def update_clearance(
    clearance_id: UUID,
    request: ClearanceUpdateRequest,
    service: Annotated[ClearanceService, Depends(get_clearance_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Update clearance item status."""
    cleared_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        clearance = await service.update_clearance(
            clearance_id=clearance_id,
            status=request.status,
            cleared_by=cleared_by,
            has_recovery=request.has_recovery,
            recovery_amount=request.recovery_amount,
            recovery_description=request.recovery_description,
            remarks=request.remarks,
        )
        return {
            "id": str(clearance.id),
            "status": clearance.status,
            "has_recovery": clearance.has_recovery,
            "recovery_amount": clearance.recovery_amount,
            "cleared_at": clearance.cleared_at,
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============ FnF Endpoints ============

@router.post(
    "/{separation_id}/fnf/calculate",
    response_model=FnFResponse, response_model_by_alias=True,
    summary="Calculate FnF settlement",
)
async def calculate_fnf(
    separation_id: UUID,
    request: FnFCalculateRequest,
    service: Annotated[FnFService, Depends(get_fnf_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FnFResponse:
    """
    Calculate Full & Final settlement.

    Calculates:
    - Pending salary (prorated)
    - Leave encashment (Basic/26 × days)
    - Gratuity (15/26 × salary × years, if 5+ years service)
    - Notice period recovery
    - Clearance recoveries
    - TDS deduction
    """
    calculated_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        fnf = await service.calculate_fnf(
            separation_id=separation_id,
            calculated_by=calculated_by,
            include_gratuity=request.include_gratuity,
            include_leave_encashment=request.include_leave_encashment,
            additional_earnings=request.additional_earnings,
            additional_deductions=request.additional_deductions,
        )
        return _map_fnf_response(fnf)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/{separation_id}/fnf",
    response_model=FnFResponse, response_model_by_alias=True,
    summary="Get FnF settlement",
)
async def get_fnf(
    separation_id: UUID,
    service: Annotated[FnFService, Depends(get_fnf_service)],
) -> FnFResponse:
    """Get FnF settlement for a separation."""
    fnf = await service.get_by_separation(separation_id)
    if not fnf:
        raise NotFoundException(
            detail=f"FnF settlement not found for separation {separation_id}",
            error_code="FNF_SETTLEMENT_NOT_FOUND_FOR_SEPARATION",
        )
    return _map_fnf_response(fnf)


@router.post(
    "/fnf/{fnf_id}/approve",
    response_model=FnFResponse, response_model_by_alias=True,
    summary="Approve FnF settlement",
)
async def approve_fnf(
    fnf_id: UUID,
    service: Annotated[FnFService, Depends(get_fnf_service)],
    remarks: Optional[str] = None,
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FnFResponse:
    """Approve FnF settlement."""
    approved_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        fnf = await service.approve_fnf(
            fnf_id=fnf_id,
            approved_by=approved_by,
            remarks=remarks,
        )
        return _map_fnf_response(fnf)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/fnf/{fnf_id}/pay",
    response_model=FnFResponse, response_model_by_alias=True,
    summary="Process FnF payment",
)
async def process_fnf_payment(
    fnf_id: UUID,
    request: FnFPaymentRequest,
    service: Annotated[FnFService, Depends(get_fnf_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FnFResponse:
    """Process FnF payment."""
    processed_by = UUID("00000000-0000-0000-0000-000000000000")

    try:
        fnf = await service.process_payment(
            fnf_id=fnf_id,
            payment_date=request.payment_date,
            payment_mode=request.payment_mode,
            payment_reference=request.payment_reference,
            processed_by=processed_by,
        )
        return _map_fnf_response(fnf)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============ Clearance Checklist Endpoints ============

@router.post(
    "/checklist",
    response_model=ClearanceChecklistResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create clearance checklist item",
)
async def create_checklist_item(
    organization_id: UUID,
    request: ClearanceChecklistRequest,
    service: Annotated[ClearanceChecklistService, Depends(get_checklist_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> ClearanceChecklistResponse:
    """Create a new clearance checklist item."""
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    checklist = await service.create(
        organization_id=organization_id,
        checklist_code=request.checklist_code,
        checklist_item=request.checklist_item,
        department_id=request.department_id,
        is_mandatory=request.is_mandatory,
        can_have_recovery=request.can_have_recovery,
        display_order=request.display_order,
        created_by=created_by,
    )
    return _map_checklist_response(checklist)


@router.get(
    "/checklist",
    response_model=List[ClearanceChecklistResponse], response_model_by_alias=True,
    summary="List clearance checklist items",
)
async def list_checklist_items(
    organization_id: UUID,
    service: Annotated[ClearanceChecklistService, Depends(get_checklist_service)],
    active_only: bool = True,
) -> List[ClearanceChecklistResponse]:
    """List clearance checklist items for an organization."""
    items = await service.list(organization_id, active_only)
    return [_map_checklist_response(item) for item in items]


@router.post(
    "/checklist/seed",
    response_model=List[ClearanceChecklistResponse], response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Seed default checklist items",
)
async def seed_default_checklist(
    organization_id: UUID,
    service: Annotated[ClearanceChecklistService, Depends(get_checklist_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> List[ClearanceChecklistResponse]:
    """Seed default clearance checklist items for an organization."""
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    items = await service.seed_default_checklist(organization_id, created_by)
    return [_map_checklist_response(item) for item in items]


# ============ Helper Functions ============

def _map_separation_response(separation) -> SeparationResponse:
    """Map separation model to response."""
    return SeparationResponse(
        id=str(separation.id),
        employee_id=str(separation.employee_id),
        employee_name=separation.employee.full_name if separation.employee else None,
        employee_code=separation.employee.employee_code if separation.employee else None,
        separation_type=separation.separation_type,
        status=separation.status,
        initiation_date=separation.initiation_date,
        requested_last_working_date=separation.requested_last_working_date,
        approved_last_working_date=separation.approved_last_working_date,
        actual_last_working_date=separation.actual_last_working_date,
        notice_period_days=separation.notice_period_days,
        notice_period_served=separation.notice_period_served,
        notice_period_shortfall=separation.notice_period_shortfall,
        is_notice_buyout=separation.is_notice_buyout,
        reason_category=separation.reason_category,
        exit_interview_done=separation.exit_interview_done,
        relieving_letter_issued=separation.relieving_letter_issued,
        experience_letter_issued=separation.experience_letter_issued,
        remarks=separation.remarks,
    )


def _map_fnf_response(fnf) -> FnFResponse:
    """Map FnF model to response."""
    return FnFResponse(
        id=str(fnf.id),
        separation_id=str(fnf.separation_id),
        employee_id=str(fnf.employee_id),
        last_working_date=fnf.last_working_date,
        settlement_date=fnf.settlement_date,
        status=fnf.status,
        pending_salary=fnf.pending_salary,
        leave_encashment=fnf.leave_encashment,
        leave_encashment_days=fnf.leave_encashment_days,
        gratuity_amount=fnf.gratuity_amount,
        gratuity_years=fnf.gratuity_years,
        gratuity_eligible=fnf.gratuity_eligible,
        bonus_amount=fnf.bonus_amount,
        pending_reimbursements=fnf.pending_reimbursements,
        other_earnings=fnf.other_earnings,
        total_earnings=fnf.total_earnings,
        notice_recovery=fnf.notice_recovery,
        notice_shortfall_days=fnf.notice_shortfall_days,
        advance_recovery=fnf.advance_recovery,
        loan_recovery=fnf.loan_recovery,
        asset_recovery=fnf.asset_recovery,
        clearance_recovery=fnf.clearance_recovery,
        other_deductions=fnf.other_deductions,
        tds_amount=fnf.tds_amount,
        total_deductions=fnf.total_deductions,
        net_payable=fnf.net_payable,
        payment_date=fnf.payment_date,
        payment_mode=fnf.payment_mode,
        payment_reference=fnf.payment_reference,
    )


def _map_checklist_response(checklist) -> ClearanceChecklistResponse:
    """Map checklist model to response."""
    return ClearanceChecklistResponse(
        id=str(checklist.id),
        checklist_code=checklist.checklist_code,
        checklist_item=checklist.checklist_item,
        description=checklist.description,
        department_id=str(checklist.department_id) if checklist.department_id else None,
        is_mandatory=checklist.is_mandatory,
        can_have_recovery=checklist.can_have_recovery,
        display_order=checklist.display_order,
        is_active=checklist.is_active,
    )
