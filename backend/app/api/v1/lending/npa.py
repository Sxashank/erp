"""NPA Management API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.auth.user import User
from app.services.lending import NPAService

router = APIRouter()


# Request/Response Schemas
class NPAClassificationRequest(BaseModel):
    """Request to classify a loan."""
    loan_account_id: UUID
    as_of_date: Optional[date] = None


class NPAClassificationResponse(BaseModel):
    """NPA classification response."""
    loan_account_id: UUID
    dpd: int
    classification: str
    previous_classification: Optional[str] = None
    classified_at: date


class ProvisionCalculationRequest(BaseModel):
    """Request to calculate provision."""
    loan_account_id: UUID
    security_value: Optional[Decimal] = None
    as_of_date: Optional[date] = None


class ProvisionResponse(BaseModel):
    """Provision calculation response."""
    loan_account_id: UUID
    classification: str
    principal_outstanding: Decimal
    security_value: Decimal
    unsecured_portion: Decimal
    provision_rate: Decimal
    provision_amount: Decimal
    provision_held: Decimal
    provision_movement: Decimal


class NPABatchRequest(BaseModel):
    """Request for batch NPA classification."""
    as_of_date: Optional[date] = None
    auto_update: bool = Field(default=True, description="Auto update account status")


class NPABatchResponse(BaseModel):
    """Batch classification response."""
    total_processed: int
    classifications: dict
    errors: List[dict] = []


class NPAUpgradeRequest(BaseModel):
    """Request to upgrade NPA account."""
    loan_account_id: UUID
    upgrade_reason: str
    upgrade_date: Optional[date] = None


class WriteOffRequest(BaseModel):
    """Request to write off a loan."""
    loan_account_id: UUID
    write_off_reason: str
    board_approval_reference: Optional[str] = None
    write_off_date: Optional[date] = None


class NPASummaryResponse(BaseModel):
    """NPA summary response."""
    as_of_date: date
    total_loans: int
    standard_loans: dict
    npa_loans: dict
    npa_ratio: Decimal


class NPAMovementResponse(BaseModel):
    """NPA movement response."""
    from_date: date
    to_date: date
    opening: dict
    additions: dict
    reductions: dict
    closing: dict


# Endpoints
@router.get("/dpd/{loan_account_id}")
async def get_dpd(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get days past due for a loan account."""
    service = NPAService(db)
    dpd = await service.get_dpd(loan_account_id)
    return {"loan_account_id": str(loan_account_id), "dpd": dpd}


@router.post("/classify", response_model=NPAClassificationResponse)
async def classify_loan(
    request: NPAClassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Classify a single loan account."""
    service = NPAService(db)

    dpd = await service.get_dpd(request.loan_account_id)
    classification = await service.classify_loan(
        loan_account_id=request.loan_account_id,
        dpd=dpd,
        as_of_date=request.as_of_date,
        user_id=current_user.id,
    )

    return NPAClassificationResponse(
        loan_account_id=request.loan_account_id,
        dpd=dpd,
        classification=classification,
        classified_at=request.as_of_date or date.today(),
    )


@router.post("/provision", response_model=ProvisionResponse)
async def calculate_provision(
    request: ProvisionCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Calculate provision for a loan account."""
    service = NPAService(db)

    result = await service.calculate_provision(
        loan_account_id=request.loan_account_id,
        security_value=request.security_value,
        as_of_date=request.as_of_date,
        user_id=current_user.id,
    )

    return ProvisionResponse(**result)


@router.post("/batch-classify", response_model=NPABatchResponse)
async def batch_classify(
    request: NPABatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run batch NPA classification for all loans in organization."""
    service = NPAService(db)

    result = await service.run_npa_classification(
        organization_id=current_user.organization_id,
        as_of_date=request.as_of_date,
        auto_update=request.auto_update,
        user_id=current_user.id,
    )

    return NPABatchResponse(
        total_processed=result["total_processed"],
        classifications=result["classifications"],
        errors=result.get("errors", []),
    )


@router.post("/upgrade")
async def upgrade_npa(
    request: NPAUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Upgrade an NPA account to standard."""
    service = NPAService(db)

    success = await service.upgrade_npa(
        loan_account_id=request.loan_account_id,
        upgrade_reason=request.upgrade_reason,
        upgrade_date=request.upgrade_date,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to upgrade account - criteria not met",
        )

    return {"message": "Account upgraded successfully", "loan_account_id": str(request.loan_account_id)}


@router.post("/write-off")
async def write_off_loan(
    request: WriteOffRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Write off a loan account."""
    service = NPAService(db)

    success = await service.write_off_loan(
        loan_account_id=request.loan_account_id,
        write_off_reason=request.write_off_reason,
        board_approval_reference=request.board_approval_reference,
        write_off_date=request.write_off_date,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to write off loan",
        )

    return {"message": "Loan written off successfully", "loan_account_id": str(request.loan_account_id)}


@router.get("/summary", response_model=NPASummaryResponse)
async def get_npa_summary(
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get NPA summary for organization."""
    service = NPAService(db)

    summary = await service.get_npa_summary(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )

    return NPASummaryResponse(**summary)


@router.get("/movement", response_model=NPAMovementResponse)
async def get_npa_movement(
    from_date: date = Query(..., description="Period start date"),
    to_date: date = Query(..., description="Period end date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get NPA movement report for period."""
    service = NPAService(db)

    movement = await service.get_npa_movement(
        organization_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )

    return NPAMovementResponse(**movement)
