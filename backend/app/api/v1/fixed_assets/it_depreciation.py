"""IT Act Depreciation API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions, DepreciationBook
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.depreciation import (
    ITDepreciationRunCreate,
    ITBlockSummaryResponse,
    ITDepreciationReportResponse,
    ITDepreciationScheduleResponse,
    DepreciationComparisonResponse,
    DepreciationRunResponse,
    IT_BLOCK_NAMES,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.it_depreciation_service import ITDepreciationService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _run_to_response(run) -> DepreciationRunResponse:
    """Convert depreciation run model to response schema."""
    return DepreciationRunResponse(
        id=run.id,
        organization_id=run.organization_id,
        depreciation_book=run.depreciation_book,
        depreciation_period=run.depreciation_period,
        period_from=run.period_from,
        period_to=run.period_to,
        total_assets=run.total_assets,
        total_depreciation=run.total_depreciation,
        processed_assets=run.processed_assets,
        skipped_assets=run.skipped_assets,
        status=run.status,
        run_started_at=run.run_started_at,
        run_completed_at=run.run_completed_at,
        run_by=run.run_by,
        voucher_id=run.voucher_id,
        voucher_number=run.voucher.voucher_number if run.voucher else None,
        posted_at=run.posted_at,
        posted_by=run.posted_by,
        remarks=run.remarks,
        is_active=True,
        created_at=run.created_at,
        updated_at=run.updated_at,
        created_by=run.created_by,
        updated_by=run.updated_by,
    )


def _block_to_response(block) -> ITBlockSummaryResponse:
    """Convert IT block summary model to response schema."""
    return ITBlockSummaryResponse(
        id=block.id,
        organization_id=block.organization_id,
        it_block=block.it_block,
        it_block_name=IT_BLOCK_NAMES.get(block.it_block, str(block.it_block)),
        financial_year=block.financial_year,
        opening_wdv=block.opening_wdv,
        additions_during_year=block.additions_during_year,
        disposals_during_year=block.disposals_during_year,
        depreciation_rate=block.depreciation_rate,
        depreciation_amount=block.depreciation_amount,
        additional_depreciation=block.additional_depreciation,
        closing_wdv=block.closing_wdv,
        asset_count=block.asset_count,
        is_finalized=block.is_finalized,
        finalized_at=block.finalized_at,
        finalized_by=block.finalized_by,
        remarks=block.remarks,
        is_active=True,
        created_at=block.created_at,
        updated_at=block.updated_at,
        created_by=block.created_by,
        updated_by=block.updated_by,
    )


@router.get("/runs", response_model=dict, response_model_by_alias=True)
async def list_it_depreciation_runs(
    request: Request,
    organization_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """List IT Act depreciation runs for an organization."""
    service = ITDepreciationService(db)
    runs, total = await service.list_it_runs(organization_id, skip, limit)

    return {
        "items": [_run_to_response(run) for run in runs],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/runs/{run_id}", response_model=DepreciationRunResponse, response_model_by_alias=True)
async def get_it_depreciation_run(
    request: Request,
    run_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get IT Act depreciation run by ID."""
    service = ITDepreciationService(db)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundException(
            detail="IT depreciation run not found",
            error_code="IT_DEPRECIATION_RUN_NOT_FOUND",
        )
    if run.depreciation_book != DepreciationBook.IT_ACT:
        raise BadRequestException(
            detail="This is not an IT Act depreciation run",
            error_code="THIS_IS_NOT_AN_IT_ACT",
        )
    return _run_to_response(run)


@router.post("/run", response_model=DepreciationRunResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def run_it_depreciation(
    request: Request,
    data: ITDepreciationRunCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Run IT Act depreciation for a financial year.

    IT Act depreciation is calculated annually at block level:
    - Assets are grouped by IT block (as per Schedule II)
    - Half-rate applies if asset used < 180 days in first year
    - Additional 20% depreciation for new manufacturing assets
    """
    service = ITDepreciationService(db)
    try:
        run = await service.run_it_depreciation(data, run_by=current_user.id)
        return _run_to_response(run)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/blocks", response_model=dict, response_model_by_alias=True)
async def list_block_summaries(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get IT block summaries for a financial year."""
    service = ITDepreciationService(db)
    summaries = await service.get_block_summary(organization_id, financial_year)

    return {
        "items": [_block_to_response(block) for block in summaries],
        "total": len(summaries),
        "financial_year": financial_year,
    }


@router.post("/blocks/finalize", response_model=dict, response_model_by_alias=True)
async def finalize_block_summaries(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Finalize IT block summaries for a financial year."""
    service = ITDepreciationService(db)
    try:
        summaries = await service.finalize_block_summary(
            organization_id, financial_year, finalized_by=current_user.id
        )
        return {
            "message": f"Finalized {len(summaries)} block summaries",
            "items": [_block_to_response(block) for block in summaries],
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/report", response_model=ITDepreciationReportResponse, response_model_by_alias=True)
async def get_it_depreciation_report(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get IT Act depreciation report for a financial year.

    Returns block-wise depreciation summary as per IT Act Schedule II.
    """
    service = ITDepreciationService(db)
    return await service.get_it_depreciation_report(organization_id, financial_year)


@router.get("/comparison", response_model=DepreciationComparisonResponse, response_model_by_alias=True)
async def get_depreciation_comparison(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    as_on_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get comparison report between Companies Act and IT Act depreciation.

    This report helps in:
    - Deferred tax liability calculation
    - Tax computation workings
    - Reconciliation between book and tax depreciation
    """
    service = ITDepreciationService(db)
    return await service.get_depreciation_comparison(
        organization_id, financial_year, as_on_date
    )


@router.get("/schedule/{asset_id}", response_model=ITDepreciationScheduleResponse, response_model_by_alias=True)
async def get_it_depreciation_schedule(
    request: Request,
    asset_id: UUID,
    years: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get projected IT depreciation schedule for an asset.

    Projects IT Act depreciation until block is fully extinguished.
    """
    service = ITDepreciationService(db)
    try:
        schedule = await service.generate_it_depreciation_schedule(asset_id, years)
        return schedule
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
