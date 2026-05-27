"""
Fixed Deposit API Endpoints
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.models.fixed_deposits.fixed_deposit import FDStatus
from app.schemas.fixed_deposits.fixed_deposit import (
    FixedDepositCreate,
    FixedDepositUpdate,
    FixedDepositResponse,
    FixedDepositListResponse,
    FixedDepositSummary,
    FDInterestAccrualResponse,
    FDTransactionResponse,
    FDNomineeCreate,
    FDNomineeResponse,
    FDMaturityProjection,
    FDClosureRequest,
    FDRenewalRequest,
)
from app.services.fixed_deposits.fd_service import (
    FixedDepositService,
    FDInterestService,
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


# Fixed Deposit CRUD
@router.get("", response_model=FixedDepositListResponse, response_model_by_alias=True)
async def list_deposits(
    customer_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    status: Optional[FDStatus] = None,
    maturing_before: Optional[date] = None,
    maturing_after: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List all fixed deposits with filters."""
    service = FixedDepositService(db)
    return await service.list_fds(
        organization_id=_require_organization_id(current_user),
        customer_id=customer_id,
        product_id=product_id,
        status=status,
        maturing_before=maturing_before,
        maturing_after=maturing_after,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=FixedDepositResponse, response_model_by_alias=True, status_code=201)
async def create_deposit(
    data: FixedDepositCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new fixed deposit."""
    service = FixedDepositService(db)
    try:
        payload = data.model_copy(
            update={"organization_id": _require_organization_id(current_user)}
        )
        return await service.create_fd(payload)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/summary", response_model=FixedDepositSummary, response_model_by_alias=True)
async def get_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get FD summary statistics."""
    service = FixedDepositService(db)
    return await service.get_summary(_require_organization_id(current_user))


@router.get("/{fd_id}", response_model=FixedDepositResponse, response_model_by_alias=True)
async def get_deposit(
    fd_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get fixed deposit by ID."""
    service = FixedDepositService(db)
    fd = await service.get_fd(fd_id)
    if not fd:
        raise NotFoundException(
            detail="Fixed deposit not found", error_code="FIXED_DEPOSIT_NOT_FOUND"
        )

    response = FixedDepositResponse.model_validate(fd)
    if fd.product:
        response.product_code = fd.product.product_code
        response.product_name = fd.product.product_name
    return response


@router.put("/{fd_id}", response_model=FixedDepositResponse, response_model_by_alias=True)
async def update_deposit(
    fd_id: UUID,
    data: FixedDepositUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update fixed deposit details."""
    service = FixedDepositService(db)
    try:
        fd = await service.update_fd(fd_id, data)
        if not fd:
            raise NotFoundException(
                detail="Fixed deposit not found",
                error_code="FIXED_DEPOSIT_NOT_FOUND",
            )
        return fd
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{fd_id}/approve", response_model=FixedDepositResponse, response_model_by_alias=True)
async def approve_deposit(
    fd_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Approve and activate a fixed deposit."""
    service = FixedDepositService(db)
    try:
        fd = await service.approve_fd(fd_id, current_user.id)
        if not fd:
            raise NotFoundException(
                detail="Fixed deposit not found",
                error_code="FIXED_DEPOSIT_NOT_FOUND",
            )
        return fd
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{fd_id}/close", response_model=FixedDepositResponse, response_model_by_alias=True)
async def close_deposit(
    fd_id: UUID,
    request: FDClosureRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Close a fixed deposit (maturity or premature)."""
    service = FixedDepositService(db)
    try:
        return await service.close_fd(fd_id, request)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{fd_id}/renew", response_model=FixedDepositResponse, response_model_by_alias=True)
async def renew_deposit(
    fd_id: UUID,
    request: FDRenewalRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Renew a fixed deposit."""
    service = FixedDepositService(db)
    try:
        return await service.renew_fd(fd_id, request)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# Maturity Projection
@router.get(
    "/{fd_id}/projection", response_model=FDMaturityProjection, response_model_by_alias=True
)
async def get_projection(
    fd_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get maturity projection for an FD."""
    service = FDInterestService(db)
    try:
        return await service.get_maturity_projection(fd_id)
    except ValueError as e:
        raise NotFoundException(detail=str(e), error_code="NOT_FOUND")


# Nominee Management
@router.post(
    "/{fd_id}/nominees",
    response_model=FDNomineeResponse,
    response_model_by_alias=True,
    status_code=201,
)
async def add_nominee(
    fd_id: UUID,
    data: FDNomineeCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add nominee to a fixed deposit."""
    service = FixedDepositService(db)

    # Verify FD exists
    fd = await service.get_fd(fd_id)
    if not fd:
        raise NotFoundException(
            detail="Fixed deposit not found", error_code="FIXED_DEPOSIT_NOT_FOUND"
        )

    return await service.add_nominee(fd_id, data)


@router.delete("/nominees/{nominee_id}")
async def remove_nominee(
    nominee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Remove nominee from a fixed deposit."""
    service = FixedDepositService(db)
    if not await service.remove_nominee(nominee_id):
        raise NotFoundException(detail="Nominee not found", error_code="NOMINEE_NOT_FOUND")
    return {"message": "Nominee removed successfully"}


# Interest Operations
@router.post("/interest/accrue")
async def run_interest_accrual(
    accrual_date: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Run daily interest accrual for all active FDs."""
    service = FDInterestService(db)
    return await service.run_interest_accrual(_require_organization_id(current_user), accrual_date)


@router.post("/interest/payout")
async def process_interest_payout(
    payout_date: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Process interest payout for eligible FDs."""
    service = FDInterestService(db)
    return await service.process_interest_payout(
        _require_organization_id(current_user), payout_date
    )


# Transactions
@router.get(
    "/{fd_id}/transactions",
    response_model=List[FDTransactionResponse],
    response_model_by_alias=True,
)
async def get_transactions(
    fd_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all transactions for a fixed deposit."""
    service = FixedDepositService(db)
    fd = await service.get_fd(fd_id)
    if not fd:
        raise NotFoundException(
            detail="Fixed deposit not found", error_code="FIXED_DEPOSIT_NOT_FOUND"
        )

    return [FDTransactionResponse.model_validate(t) for t in fd.transactions]


# Interest Accruals
@router.get(
    "/{fd_id}/accruals",
    response_model=List[FDInterestAccrualResponse],
    response_model_by_alias=True,
)
async def get_accruals(
    fd_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all interest accruals for a fixed deposit."""
    service = FixedDepositService(db)
    fd = await service.get_fd(fd_id)
    if not fd:
        raise NotFoundException(
            detail="Fixed deposit not found", error_code="FIXED_DEPOSIT_NOT_FOUND"
        )

    return [FDInterestAccrualResponse.model_validate(a) for a in fd.interest_accruals]
