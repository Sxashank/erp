"""Depreciation API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.depreciation import (
    DepreciationRunCreate,
    DepreciationRunResponse,
    DepreciationResponse,
    DepreciationScheduleResponse,
    DepreciationReverseRequest,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.depreciation_service import DepreciationService
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


def _dep_to_response(dep) -> DepreciationResponse:
    """Convert depreciation entry model to response schema."""
    return DepreciationResponse(
        id=dep.id,
        asset_id=dep.asset_id,
        asset_code=dep.asset.asset_code if dep.asset else None,
        asset_name=dep.asset.asset_name if dep.asset else None,
        depreciation_run_id=dep.depreciation_run_id,
        depreciation_period=dep.depreciation_period,
        period_from=dep.period_from,
        period_to=dep.period_to,
        days_in_period=dep.days_in_period,
        opening_wdv=dep.opening_wdv,
        depreciation_rate=dep.depreciation_rate,
        depreciation_amount=dep.depreciation_amount,
        accumulated_depreciation=dep.accumulated_depreciation,
        closing_wdv=dep.closing_wdv,
        depreciation_type=dep.depreciation_type,
        depreciation_book=dep.depreciation_book,
        voucher_id=dep.voucher_id,
        is_posted=dep.is_posted,
        is_reversed=dep.is_reversed,
        reversal_of_id=dep.reversal_of_id,
        reversed_by_id=dep.reversed_by_id,
        remarks=dep.remarks,
        is_active=True,
        created_at=dep.created_at,
        updated_at=dep.updated_at,
        created_by=dep.created_by,
        updated_by=dep.updated_by,
    )


@router.get("/runs", response_model=dict, response_model_by_alias=True)
async def list_depreciation_runs(
    request: Request,
    organization_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """List depreciation runs for an organization."""
    service = DepreciationService(db)
    runs, total = await service.list_runs(organization_id, skip, limit)

    return {
        "items": [_run_to_response(run) for run in runs],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/runs/{run_id}", response_model=DepreciationRunResponse, response_model_by_alias=True)
async def get_depreciation_run(
    request: Request,
    run_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get depreciation run by ID."""
    service = DepreciationService(db)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundException(
            detail="Depreciation run not found",
            error_code="DEPRECIATION_RUN_NOT_FOUND",
        )
    return _run_to_response(run)


@router.post("/run", response_model=DepreciationRunResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def run_depreciation(
    request: Request,
    data: DepreciationRunCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Run monthly depreciation for all eligible assets."""
    service = DepreciationService(db)
    try:
        run = await service.run_depreciation(data, run_by=current_user.id)
        return _run_to_response(run)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/runs/{run_id}/post", response_model=DepreciationRunResponse, response_model_by_alias=True)
async def post_depreciation_run(
    request: Request,
    run_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_RUN])),
):
    """Post depreciation run to GL."""
    service = DepreciationService(db)
    try:
        run = await service.post_depreciation_run(run_id, posted_by=current_user.id)
        return _run_to_response(run)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/runs/{run_id}/entries", response_model=dict, response_model_by_alias=True)
async def get_run_entries(
    request: Request,
    run_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get depreciation entries for a run."""
    service = DepreciationService(db)
    run = await service.get_run(run_id)
    if not run:
        raise NotFoundException(
            detail="Depreciation run not found",
            error_code="DEPRECIATION_RUN_NOT_FOUND",
        )

    entries = run.entries[skip:skip + limit] if run.entries else []
    total = len(run.entries) if run.entries else 0

    return {
        "items": [_dep_to_response(entry) for entry in entries],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/history/{asset_id}", response_model=dict, response_model_by_alias=True)
async def get_asset_depreciation_history(
    request: Request,
    asset_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get depreciation history for an asset."""
    service = DepreciationService(db)
    entries, total = await service.get_depreciation_history(asset_id, skip, limit)

    return {
        "items": [_dep_to_response(entry) for entry in entries],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/schedule/{asset_id}", response_model=DepreciationScheduleResponse, response_model_by_alias=True)
async def get_depreciation_schedule(
    request: Request,
    asset_id: UUID,
    periods: int = Query(60, ge=1, le=120),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_VIEW])),
):
    """Get projected depreciation schedule for an asset."""
    service = DepreciationService(db)
    try:
        schedule = await service.generate_depreciation_schedule(asset_id, periods)
        return schedule
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/{depreciation_id}/reverse", response_model=DepreciationResponse, response_model_by_alias=True)
async def reverse_depreciation(
    request: Request,
    depreciation_id: UUID,
    data: DepreciationReverseRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_DEPRECIATION_REVERSE])),
):
    """Reverse a depreciation entry."""
    service = DepreciationService(db)
    try:
        reversal = await service.reverse_depreciation(
            depreciation_id, data.reason, reversed_by=current_user.id
        )
        return _dep_to_response(reversal)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
