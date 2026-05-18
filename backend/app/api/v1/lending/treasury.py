"""Treasury and ALM API endpoints for the lending module."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.base import PaginatedResponse as PaginatedResponseBase
from app.schemas.lending.treasury import (
    ALMPositionDetailResponse,
    # ALM
    ALMPositionGenerate,
    ALMPositionListResponse,
    ALMPositionResponse,
    ALMSummary,
    # Covenant
    BorrowingCovenantCreate,
    BorrowingCovenantListResponse,
    BorrowingCovenantResponse,
    BorrowingCovenantUpdate,
    # Borrowing
    BorrowingCreate,
    BorrowingDetailResponse,
    BorrowingListItemResponse,
    BorrowingPaymentCreate,
    BorrowingPaymentListResponse,
    BorrowingPaymentResponse,
    BorrowingResponse,
    BorrowingScheduleListResponse,
    # Schedule
    BorrowingScheduleResponse,
    # Summary
    BorrowingSummary,
    BorrowingTrancheApprove,
    # Tranche
    BorrowingTrancheCreate,
    BorrowingTrancheDisbursement,
    BorrowingTrancheListResponse,
    BorrowingTrancheResponse,
    BorrowingUpdate,
    # Exposure
    ExposureLimitCreate,
    ExposureLimitListResponse,
    ExposureLimitResponse,
    ExposureLimitUpdate,
    ExposureSummary,
    ExposureTrackingListResponse,
    ExposureTrackingResponse,
    # Fund Deployment
    FundDeploymentCreate,
    FundDeploymentResponse,
    FundDeploymentSummary,
    FundProfitabilityResponse,
    # IRS
    IRSAnalysisGenerate,
    IRSAnalysisListResponse,
    IRSAnalysisResponse,
    IRSPreviewResponse,
    # Lender
    LenderCreate,
    LenderListItemResponse,
    LenderResponse,
    LenderUpdate,
    TreasurySummary,
)
from app.services.lending.fund_deployment_service import FundDeploymentService
from app.services.lending.treasury_service import TreasuryService
from app.core.exceptions import BadRequestException

router = APIRouter()


def _page_from_skip(skip: int, limit: int) -> int:
    return (skip // limit) + 1 if limit else 1


# =============================================================================
# Summary Endpoints
# =============================================================================


@router.get(
    "/summary",
    response_model=TreasurySummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_treasury_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get overall treasury summary including borrowings, ALM, and exposures."""
    service = TreasuryService(db)
    return await service.get_treasury_summary(current_user.organization_id)


@router.get(
    "/summary/borrowings",
    response_model=BorrowingSummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_borrowing_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get borrowing summary."""
    service = TreasuryService(db)
    return await service.get_borrowing_summary(current_user.organization_id)


@router.get(
    "/summary/alm",
    response_model=ALMSummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_alm_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get ALM summary."""
    service = TreasuryService(db)
    return await service.get_alm_summary(current_user.organization_id)


@router.get(
    "/summary/exposures",
    response_model=ExposureSummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_exposure_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get exposure summary."""
    service = TreasuryService(db)
    return await service.get_exposure_summary(current_user.organization_id)


# =============================================================================
# Fund Deployment / Source-of-Funds Endpoints
# =============================================================================


@router.get(
    "/fund-deployments/summary",
    response_model=FundDeploymentSummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_fund_deployment_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Summarize borrowed funds mapped to corporate loan deployments."""
    service = FundDeploymentService(db)
    return await service.get_summary(current_user.organization_id)


@router.get(
    "/fund-deployments/profitability",
    response_model=FundProfitabilityResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_fund_deployment_profitability(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Show lending yield, borrowing cost, spread and estimated NII by loan."""
    service = FundDeploymentService(db)
    return await service.get_profitability(current_user.organization_id, limit=limit)


@router.post(
    "/fund-deployments",
    response_model=FundDeploymentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_fund_deployment(
    data: FundDeploymentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Map a borrowing drawdown to a loan account or specific disbursement."""
    service = FundDeploymentService(db)
    try:
        deployment = await service.create_deployment(
            current_user.organization_id,
            data,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc
    await db.commit()
    return FundDeploymentResponse.model_validate(deployment)


@router.get(
    "/fund-deployments",
    response_model=PaginatedResponseBase[FundDeploymentResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_fund_deployments(
    borrowing_id: UUID | None = Query(None),
    loan_account_id: UUID | None = Query(None),
    deployment_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List source-of-funds mappings for treasury review."""
    service = FundDeploymentService(db)
    skip = (page - 1) * page_size
    deployments, total = await service.list_deployments(
        current_user.organization_id,
        borrowing_id=borrowing_id,
        loan_account_id=loan_account_id,
        status=deployment_status,
        skip=skip,
        limit=page_size,
    )
    items = [FundDeploymentResponse.model_validate(item) for item in deployments]
    return PaginatedResponseBase.create(items, total, page, page_size)


# =============================================================================
# Lender Endpoints
# =============================================================================


@router.post(
    "/lenders",
    response_model=LenderResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_lender(
    data: LenderCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new lender/funding source."""
    service = TreasuryService(db)
    lender = await service.create_lender(current_user.organization_id, data, current_user.user_id)
    await db.commit()
    return LenderResponse.model_validate(lender)


@router.get(
    "/lenders",
    response_model=PaginatedResponseBase[LenderListItemResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_lenders(
    lender_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List lenders with optional filters (paginated, camelCase)."""
    service = TreasuryService(db)
    skip = (page - 1) * page_size
    lenders, total = await service.list_lenders(
        current_user.organization_id, lender_type, skip, page_size
    )
    items = [LenderListItemResponse.model_validate(l) for l in lenders]
    return PaginatedResponseBase.create(items, total, page, page_size)


@router.get(
    "/lenders/{lender_id}",
    response_model=LenderResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_lender(
    lender_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get lender details."""
    service = TreasuryService(db)
    lender = await service.get_lender(lender_id)
    return LenderResponse.model_validate(lender)


@router.put(
    "/lenders/{lender_id}",
    response_model=LenderResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_lender(
    lender_id: UUID,
    data: LenderUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a lender."""
    service = TreasuryService(db)
    lender = await service.update_lender(lender_id, data, current_user.user_id)
    await db.commit()
    return LenderResponse.model_validate(lender)


# =============================================================================
# Borrowing Endpoints
# =============================================================================


@router.post(
    "/borrowings",
    response_model=BorrowingResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_borrowing(
    data: BorrowingCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new borrowing facility."""
    service = TreasuryService(db)
    borrowing = await service.create_borrowing(
        current_user.organization_id, data, current_user.user_id
    )
    await db.commit()
    return BorrowingResponse.model_validate(borrowing)


@router.get(
    "/borrowings",
    response_model=PaginatedResponseBase[BorrowingListItemResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_borrowings(
    lender_id: UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List borrowings with optional filters (paginated, camelCase)."""
    service = TreasuryService(db)
    skip = (page - 1) * page_size
    borrowings, total = await service.list_borrowings(
        current_user.organization_id, lender_id, status, skip, page_size
    )
    items = [BorrowingListItemResponse.model_validate(b) for b in borrowings]
    return PaginatedResponseBase.create(items, total, page, page_size)


@router.get(
    "/borrowings/{borrowing_id}",
    response_model=BorrowingDetailResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_borrowing(
    borrowing_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get borrowing details with tranches, schedule, and covenants."""
    service = TreasuryService(db)
    borrowing = await service.get_borrowing_with_details(borrowing_id)
    return BorrowingDetailResponse.model_validate(borrowing)


@router.put(
    "/borrowings/{borrowing_id}",
    response_model=BorrowingResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_borrowing(
    borrowing_id: UUID,
    data: BorrowingUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a borrowing."""
    service = TreasuryService(db)
    borrowing = await service.update_borrowing(borrowing_id, data, current_user.user_id)
    await db.commit()
    return BorrowingResponse.model_validate(borrowing)


# =============================================================================
# Tranche/Drawdown Endpoints
# =============================================================================


@router.post(
    "/tranches",
    response_model=BorrowingTrancheResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_tranche(
    data: BorrowingTrancheCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a drawdown request."""
    service = TreasuryService(db)
    tranche = await service.create_tranche(data, current_user.user_id)
    await db.commit()
    return BorrowingTrancheResponse.model_validate(tranche)


@router.get(
    "/borrowings/{borrowing_id}/tranches",
    response_model=BorrowingTrancheListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_tranches(
    borrowing_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List tranches for a borrowing."""
    service = TreasuryService(db)
    tranches, total = await service.tranche_repo.get_by_borrowing(borrowing_id, skip, limit)
    return BorrowingTrancheListResponse.create(
        [BorrowingTrancheResponse.model_validate(t) for t in tranches],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


@router.post(
    "/tranches/{tranche_id}/approve",
    response_model=BorrowingTrancheResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_APPROVE"))],
)
async def approve_tranche(
    tranche_id: UUID,
    data: BorrowingTrancheApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Approve a drawdown request."""
    service = TreasuryService(db)
    tranche = await service.approve_tranche(tranche_id, current_user.user_id, data.remarks)
    await db.commit()
    return BorrowingTrancheResponse.model_validate(tranche)


@router.post(
    "/tranches/{tranche_id}/disburse",
    response_model=BorrowingTrancheResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def disburse_tranche(
    tranche_id: UUID,
    data: BorrowingTrancheDisbursement,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Process tranche disbursement."""
    service = TreasuryService(db)
    tranche = await service.disburse_tranche(tranche_id, data, current_user.user_id)
    await db.commit()
    return BorrowingTrancheResponse.model_validate(tranche)


# =============================================================================
# Schedule Endpoints
# =============================================================================


@router.post(
    "/borrowings/{borrowing_id}/schedule/generate",
    response_model=BorrowingScheduleListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def generate_schedule(
    borrowing_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate repayment schedule for a borrowing."""
    service = TreasuryService(db)
    schedules = await service.generate_schedule(borrowing_id, current_user.user_id)
    await db.commit()
    return BorrowingScheduleListResponse.create(
        [BorrowingScheduleResponse.model_validate(s) for s in schedules],
        len(schedules),
        1,
        max(len(schedules), 1),
    )


@router.get(
    "/borrowings/{borrowing_id}/schedule",
    response_model=BorrowingScheduleListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_schedule(
    borrowing_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get repayment schedule for a borrowing."""
    service = TreasuryService(db)
    schedules, total = await service.get_schedule(borrowing_id, skip, limit)
    return BorrowingScheduleListResponse.create(
        [BorrowingScheduleResponse.model_validate(s) for s in schedules],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


# =============================================================================
# Payment Endpoints
# =============================================================================


@router.post(
    "/payments",
    response_model=BorrowingPaymentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def record_payment(
    data: BorrowingPaymentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Record a borrowing payment (interest/principal)."""
    service = TreasuryService(db)
    payment = await service.record_payment(data, current_user.user_id)
    await db.commit()
    return BorrowingPaymentResponse.model_validate(payment)


@router.get(
    "/borrowings/{borrowing_id}/payments",
    response_model=BorrowingPaymentListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_payments(
    borrowing_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List payments for a borrowing."""
    service = TreasuryService(db)
    payments, total = await service.list_payments(borrowing_id, skip, limit)
    return BorrowingPaymentListResponse.create(
        [BorrowingPaymentResponse.model_validate(p) for p in payments],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


# =============================================================================
# Covenant Endpoints
# =============================================================================


@router.post(
    "/covenants",
    response_model=BorrowingCovenantResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_covenant(
    data: BorrowingCovenantCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a borrowing covenant."""
    service = TreasuryService(db)
    covenant = await service.create_covenant(data, current_user.user_id)
    await db.commit()
    return BorrowingCovenantResponse.model_validate(covenant)


@router.get(
    "/borrowings/{borrowing_id}/covenants",
    response_model=BorrowingCovenantListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_covenants(
    borrowing_id: UUID,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List covenants for a borrowing."""
    service = TreasuryService(db)
    covenants = await service.covenant_repo.get_by_borrowing(borrowing_id, active_only)
    return BorrowingCovenantListResponse.create(
        [BorrowingCovenantResponse.model_validate(c) for c in covenants],
        len(covenants),
        1,
        max(len(covenants), 1),
    )


@router.put(
    "/covenants/{covenant_id}",
    response_model=BorrowingCovenantResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_covenant(
    covenant_id: UUID,
    data: BorrowingCovenantUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a covenant."""
    service = TreasuryService(db)
    covenant = await service.update_covenant(covenant_id, data, current_user.user_id)
    await db.commit()
    return BorrowingCovenantResponse.model_validate(covenant)


@router.post(
    "/covenants/{covenant_id}/test",
    response_model=BorrowingCovenantResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def test_covenant(
    covenant_id: UUID,
    current_value: Decimal = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Test a covenant with current value and update compliance status."""
    service = TreasuryService(db)
    covenant = await service.test_covenant(covenant_id, current_value, current_user.user_id)
    await db.commit()
    return BorrowingCovenantResponse.model_validate(covenant)


# =============================================================================
# ALM Endpoints
# =============================================================================


@router.post(
    "/alm/positions/generate",
    response_model=ALMPositionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def generate_alm_position(
    data: ALMPositionGenerate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate ALM position snapshot for a date."""
    service = TreasuryService(db)
    position = await service.generate_alm_position(
        current_user.organization_id, data, current_user.user_id
    )
    await db.commit()
    return ALMPositionResponse.model_validate(position)


@router.get(
    "/alm/positions",
    response_model=ALMPositionListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_alm_positions(
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List ALM position history."""
    service = TreasuryService(db)
    positions, total = await service.alm_position_repo.get_history(
        current_user.organization_id, skip, limit
    )
    return ALMPositionListResponse.create(
        [ALMPositionResponse.model_validate(p) for p in positions],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


@router.get(
    "/alm/positions/latest",
    response_model=ALMPositionDetailResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_latest_alm_position(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get latest ALM position with details."""
    service = TreasuryService(db)
    position = await service.get_latest_alm_position(current_user.organization_id)
    if position:
        position = await service.get_alm_position(position.position_id)
    return ALMPositionDetailResponse.model_validate(position) if position else None


@router.get(
    "/alm/positions/{position_id}",
    response_model=ALMPositionDetailResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_alm_position(
    position_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get ALM position with asset and liability breakdown."""
    service = TreasuryService(db)
    position = await service.get_alm_position(position_id)
    return ALMPositionDetailResponse.model_validate(position)


# =============================================================================
# IRS Analysis Endpoints
# =============================================================================


@router.get(
    "/irs/preview",
    response_model=IRSPreviewResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def preview_irs_analysis(
    as_of_date: date | None = Query(
        None,
        description="As-of date for the IRS preview (defaults to today).",
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Preview Interest Rate Sensitivity (IRS) analysis without persisting.

    Returns projected NII impact across a default set of rate-shock buckets
    (±50 / ±100 / ±200 bps), along with a summary block of RSA / RSL / Gap.
    """
    service = TreasuryService(db)
    return await service.preview_irs_analysis(current_user.organization_id, as_of_date)


@router.post(
    "/alm/irs/generate",
    response_model=IRSAnalysisResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def generate_irs_analysis(
    data: IRSAnalysisGenerate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate Interest Rate Sensitivity analysis."""
    service = TreasuryService(db)
    analysis = await service.generate_irs_analysis(
        current_user.organization_id, data, current_user.user_id
    )
    await db.commit()
    return IRSAnalysisResponse.model_validate(analysis)


@router.get(
    "/alm/irs",
    response_model=IRSAnalysisListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_irs_analyses(
    analysis_date: date | None = Query(None),
    shock_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List IRS analyses."""
    service = TreasuryService(db)
    if analysis_date:
        analyses = await service.irs_repo.get_by_date(
            current_user.organization_id, analysis_date, shock_type
        )
        return IRSAnalysisListResponse.create(
            [IRSAnalysisResponse.model_validate(a) for a in analyses],
            len(analyses),
            1,
            max(len(analyses), 1),
        )
    # Default to recent analyses
    analyses, total = await service.irs_repo.get_all(current_user.organization_id, skip, limit)
    return IRSAnalysisListResponse.create(
        [IRSAnalysisResponse.model_validate(a) for a in analyses],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


# =============================================================================
# Exposure Limit Endpoints
# =============================================================================


@router.post(
    "/exposure-limits",
    response_model=ExposureLimitResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_exposure_limit(
    data: ExposureLimitCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create an exposure limit."""
    service = TreasuryService(db)
    limit = await service.create_exposure_limit(
        current_user.organization_id, data, current_user.user_id
    )
    await db.commit()
    return ExposureLimitResponse.model_validate(limit)


@router.get(
    "/exposure-limits",
    response_model=ExposureLimitListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_exposure_limits(
    limit_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List exposure limits."""
    service = TreasuryService(db)
    if limit_type:
        limits = await service.exposure_limit_repo.get_by_type(
            current_user.organization_id, limit_type
        )
        return ExposureLimitListResponse.create(
            [ExposureLimitResponse.model_validate(l) for l in limits],
            len(limits),
            1,
            max(len(limits), 1),
        )
    limits, total = await service.exposure_limit_repo.get_all(
        current_user.organization_id, skip, limit
    )
    return ExposureLimitListResponse.create(
        [ExposureLimitResponse.model_validate(l) for l in limits],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


@router.get(
    "/exposure-limits/{limit_id}",
    response_model=ExposureLimitResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_exposure_limit(
    limit_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get exposure limit details."""
    service = TreasuryService(db)
    limit = await service.exposure_limit_repo.get(limit_id)
    return ExposureLimitResponse.model_validate(limit)


@router.put(
    "/exposure-limits/{limit_id}",
    response_model=ExposureLimitResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_exposure_limit(
    limit_id: UUID,
    data: ExposureLimitUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update an exposure limit."""
    service = TreasuryService(db)
    limit = await service.update_exposure_limit(limit_id, data, current_user.user_id)
    await db.commit()
    return ExposureLimitResponse.model_validate(limit)


@router.get(
    "/exposure-limits/{limit_id}/tracking",
    response_model=ExposureTrackingListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_exposure_tracking(
    limit_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get exposure tracking records for a limit."""
    service = TreasuryService(db)
    tracking, total = await service.exposure_tracking_repo.get_by_limit(limit_id, skip, limit)
    return ExposureTrackingListResponse.create(
        [ExposureTrackingResponse.model_validate(t) for t in tracking],
        total,
        _page_from_skip(skip, limit),
        limit,
    )


@router.post(
    "/exposure-check",
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def check_exposure(
    limit_type: str = Query(...),
    limit_key: str = Query(...),
    additional_exposure: Decimal = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Check if additional exposure would breach limit."""
    service = TreasuryService(db)
    result = await service.check_exposure(
        current_user.organization_id, limit_type, limit_key, additional_exposure
    )
    return result
