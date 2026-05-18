"""Fixed Assets Reports API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions, AssetStatus, AssetType
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.depreciation import (
    AssetRegisterResponse,
    DepreciationSummaryResponse,
)
from app.services.fixed_assets.reports_service import FAReportsService
from app.core.exceptions import BadRequestException

router = APIRouter()


@router.get("/asset-register", response_model=AssetRegisterResponse, response_model_by_alias=True)
async def get_asset_register(
    request: Request,
    organization_id: UUID,
    as_on_date: date = Query(default=None, description="As on date (defaults to today)"),
    category_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    asset_type: Optional[AssetType] = None,
    include_disposed: bool = Query(False, description="Include disposed assets"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get comprehensive asset register report.

    The Asset Register shows all fixed assets with:
    - Acquisition cost
    - Additions during the year
    - Disposals during the year
    - Revaluation adjustments
    - Depreciation for the period
    - Accumulated depreciation
    - Written Down Value (WDV)

    This is a key report for:
    - Board presentations
    - Audit requirements
    - Management reviews
    - Regulatory compliance
    """
    if not as_on_date:
        as_on_date = date.today()

    # Build status filter
    status_filter = [AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]
    if include_disposed:
        status_filter.append(AssetStatus.DISPOSED)

    service = FAReportsService(db)
    return await service.get_asset_register(
        organization_id=organization_id,
        as_on_date=as_on_date,
        category_id=category_id,
        location_id=location_id,
        asset_type=asset_type,
        status_filter=status_filter,
    )


@router.get("/depreciation-summary", response_model=DepreciationSummaryResponse, response_model_by_alias=True)
async def get_depreciation_summary(
    request: Request,
    organization_id: UUID,
    depreciation_period: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get depreciation summary by category for a period.

    Shows depreciation charged during the month grouped by asset category.
    Useful for:
    - Monthly depreciation review
    - GL reconciliation
    - Category-wise analysis
    """
    service = FAReportsService(db)
    return await service.get_depreciation_summary(
        organization_id=organization_id,
        depreciation_period=depreciation_period,
    )


@router.get("/nbs-7", response_model=dict, response_model_by_alias=True)
async def get_nbs7_schedule(
    request: Request,
    organization_id: UUID,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    quarter: int = Query(..., ge=1, le=4),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Generate NBS-7 Schedule for quarterly RBI filing.

    NBS-7 is a schedule required to be submitted quarterly by NBFCs to RBI.
    It shows fixed assets details in the prescribed format:

    Categories as per NBS-7:
    - Premises (Land & Buildings)
    - Furniture and Fixtures
    - Vehicles
    - Office Equipment
    - Other Fixed Assets
    - Intangible Assets

    Each category shows:
    - Opening balance
    - Additions during quarter
    - Deductions/Sales during quarter
    - Depreciation for quarter
    - Closing WDV
    """
    service = FAReportsService(db)
    try:
        return await service.get_nbs7_schedule(
            organization_id=organization_id,
            financial_year=financial_year,
            quarter=quarter,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get("/category-wise-summary", response_model=dict, response_model_by_alias=True)
async def get_category_wise_summary(
    request: Request,
    organization_id: UUID,
    as_on_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get category-wise asset summary.

    Quick summary showing:
    - Number of assets per category
    - Total cost per category
    - Total WDV per category
    """
    from sqlalchemy import select, func
    from app.models.fixed_assets.fixed_asset import FixedAsset
    from app.models.fixed_assets.asset_category import AssetCategory

    if not as_on_date:
        as_on_date = date.today()

    result = await db.execute(
        select(
            AssetCategory.id,
            AssetCategory.category_code,
            AssetCategory.category_name,
            func.count(FixedAsset.id).label("asset_count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.accumulated_depreciation).label("total_depreciation"),
            func.sum(FixedAsset.wdv_value).label("total_wdv"),
        )
        .join(FixedAsset, FixedAsset.category_id == AssetCategory.id)
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            FixedAsset.acquisition_date <= as_on_date,
        )
        .group_by(
            AssetCategory.id,
            AssetCategory.category_code,
            AssetCategory.category_name,
        )
        .order_by(AssetCategory.category_code)
    )
    rows = result.all()

    categories = []
    for row in rows:
        categories.append({
            "category_id": str(row.id),
            "category_code": row.category_code,
            "category_name": row.category_name,
            "asset_count": row.asset_count,
            "total_cost": float(row.total_cost or 0),
            "total_depreciation": float(row.total_depreciation or 0),
            "total_wdv": float(row.total_wdv or 0),
        })

    return {
        "organization_id": str(organization_id),
        "as_on_date": as_on_date.isoformat(),
        "categories": categories,
        "totals": {
            "asset_count": sum(c["asset_count"] for c in categories),
            "total_cost": sum(c["total_cost"] for c in categories),
            "total_depreciation": sum(c["total_depreciation"] for c in categories),
            "total_wdv": sum(c["total_wdv"] for c in categories),
        },
    }


@router.get("/location-wise-summary", response_model=dict, response_model_by_alias=True)
async def get_location_wise_summary(
    request: Request,
    organization_id: UUID,
    as_on_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get location-wise asset summary.

    Summary showing asset distribution across locations/branches.
    """
    from sqlalchemy import select, func
    from app.models.fixed_assets.fixed_asset import FixedAsset
    from app.models.masters.unit import Unit

    if not as_on_date:
        as_on_date = date.today()

    result = await db.execute(
        select(
            Unit.id,
            Unit.code,
            Unit.name,
            func.count(FixedAsset.id).label("asset_count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.wdv_value).label("total_wdv"),
        )
        .join(FixedAsset, FixedAsset.location_id == Unit.id)
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            FixedAsset.acquisition_date <= as_on_date,
        )
        .group_by(Unit.id, Unit.code, Unit.name)
        .order_by(Unit.code)
    )
    rows = result.all()

    locations = []
    for row in rows:
        locations.append({
            "location_id": str(row.id),
            "location_code": row.code,
            "location_name": row.name,
            "asset_count": row.asset_count,
            "total_cost": float(row.total_cost or 0),
            "total_wdv": float(row.total_wdv or 0),
        })

    # Get unassigned assets
    unassigned = await db.execute(
        select(
            func.count(FixedAsset.id).label("asset_count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.wdv_value).label("total_wdv"),
        )
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.location_id.is_(None),
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            FixedAsset.acquisition_date <= as_on_date,
        )
    )
    unassigned_row = unassigned.one()
    if unassigned_row.asset_count > 0:
        locations.append({
            "location_id": None,
            "location_code": "UNASSIGNED",
            "location_name": "Unassigned Location",
            "asset_count": unassigned_row.asset_count,
            "total_cost": float(unassigned_row.total_cost or 0),
            "total_wdv": float(unassigned_row.total_wdv or 0),
        })

    return {
        "organization_id": str(organization_id),
        "as_on_date": as_on_date.isoformat(),
        "locations": locations,
        "totals": {
            "asset_count": sum(l["asset_count"] for l in locations),
            "total_cost": sum(l["total_cost"] for l in locations),
            "total_wdv": sum(l["total_wdv"] for l in locations),
        },
    }
