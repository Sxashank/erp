"""
Payroll Batch and Payslip API Endpoints
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.payroll.payroll import (
    StatutorySetupCreate,
    StatutorySetupUpdate,
    StatutorySetupResponse,
    PayrollBatchCreate,
    PayrollBatchUpdate,
    PayrollBatchResponse,
    PayrollBatchList,
    PayrollProcessRequest,
    PayrollApproveRequest,
    PayslipResponse,
    PayslipList,
    PayslipUpdate,
)
from app.services.payroll.payroll_service import (
    StatutorySetupService,
    PayrollBatchService,
    PayrollProcessingService,
    PayslipService,
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


# ============== Statutory Setup ==============

@router.get("/statutory-setup", response_model=List[StatutorySetupResponse], response_model_by_alias=True)
async def list_statutory_setup(
    statutory_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List statutory setup configurations"""
    service = StatutorySetupService(db)
    items = await service.list(current_user.organization_id, statutory_type)
    return [StatutorySetupResponse.model_validate(item) for item in items]


@router.post("/statutory-setup", response_model=StatutorySetupResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_statutory_setup(
    data: StatutorySetupCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create statutory setup"""
    service = StatutorySetupService(db)
    setup = await service.create(data, current_user.id)
    return StatutorySetupResponse.model_validate(setup)


@router.get("/statutory-setup/{id}", response_model=StatutorySetupResponse, response_model_by_alias=True)
async def get_statutory_setup(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get statutory setup by ID"""
    service = StatutorySetupService(db)
    setup = await service.get(id)
    if not setup:
        raise NotFoundException(detail="Setup not found", error_code="SETUP_NOT_FOUND")
    return StatutorySetupResponse.model_validate(setup)


@router.put("/statutory-setup/{id}", response_model=StatutorySetupResponse, response_model_by_alias=True)
async def update_statutory_setup(
    id: UUID,
    data: StatutorySetupUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update statutory setup"""
    service = StatutorySetupService(db)
    setup = await service.update(id, data, current_user.id)
    if not setup:
        raise NotFoundException(detail="Setup not found", error_code="SETUP_NOT_FOUND")
    return StatutorySetupResponse.model_validate(setup)


# ============== Payroll Batches ==============

@router.get("/batches", response_model=dict, response_model_by_alias=True)
async def list_payroll_batches(
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List payroll batches"""
    service = PayrollBatchService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        year=year,
        status=status,
        skip=skip,
        limit=limit
    )
    return {
        "items": [PayrollBatchList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/batches", response_model=PayrollBatchResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_payroll_batch(
    data: PayrollBatchCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new payroll batch"""
    service = PayrollBatchService(db)
    batch = await service.create(data, current_user.id)
    return PayrollBatchResponse.model_validate(batch)


@router.get("/batches/{id}", response_model=PayrollBatchResponse, response_model_by_alias=True)
async def get_payroll_batch(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get payroll batch by ID"""
    service = PayrollBatchService(db)
    batch = await service.get(id)
    if not batch:
        raise NotFoundException(detail="Batch not found", error_code="BATCH_NOT_FOUND")
    return PayrollBatchResponse.model_validate(batch)


@router.put("/batches/{id}", response_model=PayrollBatchResponse, response_model_by_alias=True)
async def update_payroll_batch(
    id: UUID,
    data: PayrollBatchUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update payroll batch"""
    service = PayrollBatchService(db)
    batch = await service.update(id, data, current_user.id)
    if not batch:
        raise NotFoundException(detail="Batch not found", error_code="BATCH_NOT_FOUND")
    return PayrollBatchResponse.model_validate(batch)


@router.post("/batches/{id}/process", response_model=PayrollBatchResponse, response_model_by_alias=True)
async def process_payroll_batch(
    id: UUID,
    data: Optional[PayrollProcessRequest] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Process payroll for a batch"""
    service = PayrollProcessingService(db)
    try:
        batch = await service.process_payroll(
            batch_id=id,
            employee_ids=data.employee_ids if data else None,
            processed_by=current_user.id
        )
        return PayrollBatchResponse.model_validate(batch)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/batches/{id}/approve", response_model=PayrollBatchResponse, response_model_by_alias=True)
async def approve_payroll_batch(
    id: UUID,
    data: Optional[PayrollApproveRequest] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Approve payroll batch"""
    service = PayrollBatchService(db)
    batch = await service.approve(
        id,
        approved_by=current_user.id,
        remarks=data.remarks if data else None
    )
    if not batch:
        raise BadRequestException(
            detail="Batch not found or not in processed status",
            error_code="BATCH_NOT_FOUND_OR_NOT_IN",
        )
    return PayrollBatchResponse.model_validate(batch)


@router.post("/batches/{id}/mark-paid", response_model=PayrollBatchResponse, response_model_by_alias=True)
async def mark_payroll_batch_paid(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Mark payroll batch as paid"""
    service = PayrollBatchService(db)
    batch = await service.mark_paid(id, current_user.id)
    if not batch:
        raise BadRequestException(
            detail="Batch not found or not in approved status",
            error_code="BATCH_NOT_FOUND_OR_NOT_IN",
        )
    return PayrollBatchResponse.model_validate(batch)


# ============== Payslips ==============

@router.get("/payslips", response_model=dict, response_model_by_alias=True)
async def list_payslips(
    batch_id: Optional[UUID] = Query(None),
    employee_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List payslips"""
    service = PayslipService(db)
    items, total = await service.list(
        batch_id=batch_id,
        employee_id=employee_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return {
        "items": [PayslipList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/payslips/{id}", response_model=PayslipResponse, response_model_by_alias=True)
async def get_payslip(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get payslip by ID"""
    service = PayslipService(db)
    payslip = await service.get(id)
    if not payslip:
        raise NotFoundException(detail="Payslip not found", error_code="PAYSLIP_NOT_FOUND")
    return PayslipResponse.model_validate(payslip)


@router.put("/payslips/{id}", response_model=PayslipResponse, response_model_by_alias=True)
async def update_payslip(
    id: UUID,
    data: PayslipUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update payslip (manual adjustments)"""
    service = PayslipService(db)
    payslip = await service.update(id, data, current_user.id)
    if not payslip:
        raise NotFoundException(detail="Payslip not found", error_code="PAYSLIP_NOT_FOUND")
    return PayslipResponse.model_validate(payslip)


@router.get("/payslips/employee/{employee_id}", response_model=dict, response_model_by_alias=True)
async def get_employee_payslips(
    employee_id: UUID,
    year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get payslips for an employee"""
    service = PayslipService(db)
    items, total = await service.get_employee_payslips(
        employee_id=employee_id,
        year=year,
        skip=skip,
        limit=limit
    )
    return {
        "items": [PayslipList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }
