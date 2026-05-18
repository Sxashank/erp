"""NPA Management API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.base import CamelSchema
from app.services.lending import NPAService
from app.core.exceptions import BadRequestException

router = APIRouter()


# Request/Response Schemas
class NPAClassificationRequest(CamelSchema):
    """Request to classify a loan."""

    loan_account_id: UUID
    as_of_date: date | None = None


class NPAClassificationResponse(CamelSchema):
    """NPA classification response."""

    loan_account_id: UUID
    dpd: int
    classification: str
    previous_classification: str | None = None
    classified_at: date


class ProvisionCalculationRequest(CamelSchema):
    """Request to calculate provision."""

    loan_account_id: UUID
    security_value: Decimal | None = None
    as_of_date: date | None = None


class ProvisionResponse(CamelSchema):
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


class NPABatchRequest(CamelSchema):
    """Request for batch NPA classification."""

    as_of_date: date | None = None
    auto_update: bool = Field(default=True, description="Auto update account status")


class NPABatchResponse(CamelSchema):
    """Batch classification response."""

    total_processed: int
    classifications: dict
    errors: list[dict] = []


class NPAUpgradeRequest(CamelSchema):
    """Request to upgrade NPA account."""

    loan_account_id: UUID
    upgrade_reason: str
    upgrade_date: date | None = None


class WriteOffRequest(CamelSchema):
    """Request to write off a loan."""

    loan_account_id: UUID
    write_off_reason: str
    board_approval_reference: str | None = None
    write_off_date: date | None = None


class NPASummaryResponse(CamelSchema):
    """NPA summary response."""

    as_of_date: date
    total_loans: int
    standard_loans: dict
    npa_loans: dict
    npa_ratio: Decimal


class NPAMovementResponse(CamelSchema):
    """NPA movement response."""

    from_date: date
    to_date: date
    opening: dict
    additions: dict
    reductions: dict
    closing: dict


class DPDResponse(CamelSchema):
    """Days-past-due response."""

    loan_account_id: UUID
    dpd: int


class NPAActionResponse(CamelSchema):
    """Response for state-changing NPA actions."""

    message: str
    loan_account_id: UUID


# Endpoints
@router.get(
    "/dpd/{loan_account_id}",
    response_model=DPDResponse,
    response_model_by_alias=True,
)
async def get_dpd(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get days past due for a loan account."""
    service = NPAService(db)
    dpd = await service.get_dpd(loan_account_id)
    return DPDResponse(loan_account_id=loan_account_id, dpd=dpd)


@router.post(
    "/classify",
    response_model=NPAClassificationResponse,
    response_model_by_alias=True,
)
async def classify_loan(
    request: NPAClassificationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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


@router.post(
    "/provision",
    response_model=ProvisionResponse,
    response_model_by_alias=True,
)
async def calculate_provision(
    request: ProvisionCalculationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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


@router.post(
    "/batch-classify",
    response_model=NPABatchResponse,
    response_model_by_alias=True,
)
async def batch_classify(
    request: NPABatchRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
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


@router.post(
    "/upgrade",
    response_model=NPAActionResponse,
    response_model_by_alias=True,
)
async def upgrade_npa(
    request: NPAUpgradeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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
        raise BadRequestException(
            detail="Unable to upgrade account - criteria not met",
            error_code="UNABLE_TO_UPGRADE_ACCOUNT_CRITERIA_NOT",
        )

    return NPAActionResponse(
        message="Account upgraded successfully",
        loan_account_id=request.loan_account_id,
    )


@router.post(
    "/write-off",
    response_model=NPAActionResponse,
    response_model_by_alias=True,
)
async def write_off_loan(
    request: WriteOffRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
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
        raise BadRequestException(
            detail="Unable to write off loan",
            error_code="UNABLE_TO_WRITE_OFF_LOAN",
        )

    return NPAActionResponse(
        message="Loan written off successfully",
        loan_account_id=request.loan_account_id,
    )


@router.get(
    "/summary",
    response_model=NPASummaryResponse,
    response_model_by_alias=True,
)
async def get_npa_summary(
    as_of_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get NPA summary for organization."""
    service = NPAService(db)

    summary = await service.get_npa_summary(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )

    return NPASummaryResponse(**summary)


@router.get(
    "/movement",
    response_model=NPAMovementResponse,
    response_model_by_alias=True,
)
async def get_npa_movement(
    from_date: date = Query(..., description="Period start date"),
    to_date: date = Query(..., description="Period end date"),
    db: AsyncSession = Depends(get_db_with_tenant),
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
