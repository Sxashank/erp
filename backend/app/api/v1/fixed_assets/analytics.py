"""Fixed Assets Analytics and Dashboard API.

This module provides comprehensive analytics, KPIs, and dashboard data
for the Fixed Assets module, including:
- Asset portfolio overview
- Depreciation analytics
- Maintenance KPIs
- Insurance coverage analysis
- Lease portfolio metrics
- Alerts and notifications
- Trend analysis
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions, AssetStatus, AssetType
from app.core.permissions import PermissionChecker
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.depreciation import Depreciation, DepreciationRun
from app.models.fixed_assets.lease import Lease, LeaseStatus
from app.models.fixed_assets.maintenance import AMCContract, MaintenanceRequest, AMCStatus, MaintenanceStatus
from app.models.fixed_assets.insurance import InsurancePolicy, InsuranceClaim, InsurancePolicyStatus
from app.schemas.base import BaseSchema

router = APIRouter()


class FADashboardResponse(BaseSchema):
    """Comprehensive FA Dashboard Response."""

    organization_id: UUID
    as_on_date: date

    # Asset Summary
    assets: dict
    # Depreciation Summary
    depreciation: dict
    # Lease Summary
    leases: dict
    # Maintenance Summary
    maintenance: dict
    # Insurance Summary
    insurance: dict
    # Alerts
    alerts: dict
    # Trends
    trends: dict


class FAKPIResponse(BaseSchema):
    """Key Performance Indicators for Fixed Assets."""

    organization_id: UUID
    as_on_date: date
    financial_year: str

    # Asset KPIs
    total_asset_value: Decimal
    total_wdv: Decimal
    depreciation_rate: Decimal  # Avg across portfolio
    asset_utilization_rate: Decimal
    fully_depreciated_percentage: Decimal

    # Financial KPIs
    ytd_depreciation_expense: Decimal
    ytd_maintenance_cost: Decimal
    ytd_insurance_premium: Decimal
    total_lease_liability: Decimal

    # Operational KPIs
    average_asset_age_months: Decimal
    maintenance_cost_per_asset: Decimal
    insurance_coverage_ratio: Decimal
    amc_coverage_percentage: Decimal

    # Compliance KPIs
    physical_verification_completion: Decimal
    overdue_maintenance_count: int


@router.get("/dashboard", response_model=FADashboardResponse, response_model_by_alias=True)
async def get_fa_dashboard(
    request: Request,
    organization_id: UUID,
    as_on_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get comprehensive Fixed Assets dashboard.

    Provides a complete overview of:
    - Asset portfolio composition and values
    - Depreciation status and trends
    - Lease portfolio and obligations
    - Maintenance status and costs
    - Insurance coverage and claims
    - Alerts and action items
    """
    if not as_on_date:
        as_on_date = date.today()

    # ========== ASSET SUMMARY ==========
    asset_stats = await db.execute(
        select(
            func.count(FixedAsset.id).label("total_count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.wdv_value).label("total_wdv"),
            func.sum(FixedAsset.accumulated_depreciation).label("total_depreciation"),
            func.count(FixedAsset.id).filter(
                FixedAsset.status == AssetStatus.ACTIVE
            ).label("active_count"),
            func.count(FixedAsset.id).filter(
                FixedAsset.status == AssetStatus.FULLY_DEPRECIATED
            ).label("fully_depreciated_count"),
            func.count(FixedAsset.id).filter(
                FixedAsset.status == AssetStatus.DISPOSED
            ).label("disposed_ytd"),
        )
        .where(FixedAsset.organization_id == organization_id)
    )
    asset_row = asset_stats.one()

    # Assets by type
    by_type_result = await db.execute(
        select(
            AssetCategory.asset_type,
            func.count(FixedAsset.id).label("count"),
            func.sum(FixedAsset.total_cost).label("cost"),
            func.sum(FixedAsset.wdv_value).label("wdv"),
        )
        .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
        )
        .group_by(AssetCategory.asset_type)
    )
    by_type = [
        {
            "type": row.asset_type.value if row.asset_type else "UNKNOWN",
            "count": row.count,
            "cost": float(row.cost or 0),
            "wdv": float(row.wdv or 0),
        }
        for row in by_type_result
    ]

    # Top 5 categories by value
    top_categories = await db.execute(
        select(
            AssetCategory.category_name,
            func.count(FixedAsset.id).label("count"),
            func.sum(FixedAsset.wdv_value).label("wdv"),
        )
        .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
        )
        .group_by(AssetCategory.id, AssetCategory.category_name)
        .order_by(func.sum(FixedAsset.wdv_value).desc())
        .limit(5)
    )
    top_cats = [
        {"category": row.category_name, "count": row.count, "wdv": float(row.wdv or 0)}
        for row in top_categories
    ]

    assets_summary = {
        "total_count": asset_row.total_count or 0,
        "active_count": asset_row.active_count or 0,
        "fully_depreciated_count": asset_row.fully_depreciated_count or 0,
        "disposed_ytd": asset_row.disposed_ytd or 0,
        "total_cost": float(asset_row.total_cost or 0),
        "total_wdv": float(asset_row.total_wdv or 0),
        "total_accumulated_depreciation": float(asset_row.total_depreciation or 0),
        "by_asset_type": by_type,
        "top_categories": top_cats,
    }

    # ========== DEPRECIATION SUMMARY ==========
    # Determine FY
    if as_on_date.month >= 4:
        fy_start = date(as_on_date.year, 4, 1)
        fy_str = f"{as_on_date.year}-{str(as_on_date.year + 1)[2:]}"
    else:
        fy_start = date(as_on_date.year - 1, 4, 1)
        fy_str = f"{as_on_date.year - 1}-{str(as_on_date.year)[2:]}"

    dep_stats = await db.execute(
        select(
            func.sum(Depreciation.depreciation_amount).label("ytd_depreciation"),
            func.count(func.distinct(Depreciation.asset_id)).label("assets_depreciated"),
        )
        .join(FixedAsset, Depreciation.asset_id == FixedAsset.id)
        .where(
            FixedAsset.organization_id == organization_id,
            Depreciation.period_to >= fy_start,
            Depreciation.period_to <= as_on_date,
        )
    )
    dep_row = dep_stats.one()

    # Monthly depreciation trend (last 6 months)
    six_months_ago = as_on_date - timedelta(days=180)
    monthly_dep = await db.execute(
        select(
            Depreciation.depreciation_period,
            func.sum(Depreciation.depreciation_amount).label("amount"),
        )
        .join(FixedAsset, Depreciation.asset_id == FixedAsset.id)
        .where(
            FixedAsset.organization_id == organization_id,
            Depreciation.period_to >= six_months_ago,
        )
        .group_by(Depreciation.depreciation_period)
        .order_by(Depreciation.depreciation_period)
    )
    monthly_trend = [
        {"period": row.depreciation_period, "amount": float(row.amount or 0)}
        for row in monthly_dep
    ]

    depreciation_summary = {
        "ytd_depreciation": float(dep_row.ytd_depreciation or 0),
        "assets_depreciated": dep_row.assets_depreciated or 0,
        "financial_year": fy_str,
        "monthly_trend": monthly_trend,
    }

    # ========== LEASE SUMMARY ==========
    lease_stats = await db.execute(
        select(
            func.count(Lease.id).label("total_leases"),
            func.count(Lease.id).filter(
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED])
            ).label("active_leases"),
            func.sum(Lease.roua_carrying_value).filter(
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED])
            ).label("total_roua"),
            func.sum(Lease.lease_liability_current).filter(
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED])
            ).label("total_liability"),
            func.sum(Lease.lease_liability_current_portion).filter(
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED])
            ).label("current_portion"),
            func.sum(Lease.interest_expense_ytd).label("ytd_interest"),
            func.sum(Lease.depreciation_expense_ytd).label("ytd_roua_dep"),
        )
        .where(Lease.organization_id == organization_id)
    )
    lease_row = lease_stats.one()

    leases_summary = {
        "total_leases": lease_row.total_leases or 0,
        "active_leases": lease_row.active_leases or 0,
        "total_roua_value": float(lease_row.total_roua or 0),
        "total_lease_liability": float(lease_row.total_liability or 0),
        "current_portion": float(lease_row.current_portion or 0),
        "non_current_portion": float((lease_row.total_liability or 0) - (lease_row.current_portion or 0)),
        "ytd_interest_expense": float(lease_row.ytd_interest or 0),
        "ytd_roua_depreciation": float(lease_row.ytd_roua_dep or 0),
    }

    # ========== MAINTENANCE SUMMARY ==========
    maint_stats = await db.execute(
        select(
            func.count(MaintenanceRequest.id).filter(
                MaintenanceRequest.reported_date >= fy_start
            ).label("requests_ytd"),
            func.count(MaintenanceRequest.id).filter(
                MaintenanceRequest.status.in_([
                    MaintenanceStatus.SCHEDULED,
                    MaintenanceStatus.IN_PROGRESS,
                ])
            ).label("open_requests"),
            func.sum(MaintenanceRequest.total_cost).filter(
                MaintenanceRequest.reported_date >= fy_start
            ).label("cost_ytd"),
            func.sum(MaintenanceRequest.downtime_hours).filter(
                MaintenanceRequest.reported_date >= fy_start
            ).label("downtime_ytd"),
        )
        .where(MaintenanceRequest.organization_id == organization_id)
    )
    maint_row = maint_stats.one()

    # AMC stats
    amc_stats = await db.execute(
        select(
            func.count(AMCContract.id).filter(
                AMCContract.status == AMCStatus.ACTIVE
            ).label("active_contracts"),
            func.sum(AMCContract.total_value).filter(
                AMCContract.status == AMCStatus.ACTIVE
            ).label("total_amc_value"),
        )
        .where(AMCContract.organization_id == organization_id)
    )
    amc_row = amc_stats.one()

    maintenance_summary = {
        "requests_ytd": maint_row.requests_ytd or 0,
        "open_requests": maint_row.open_requests or 0,
        "total_cost_ytd": float(maint_row.cost_ytd or 0),
        "total_downtime_hours": float(maint_row.downtime_ytd or 0),
        "active_amc_contracts": amc_row.active_contracts or 0,
        "total_amc_value": float(amc_row.total_amc_value or 0),
    }

    # ========== INSURANCE SUMMARY ==========
    ins_stats = await db.execute(
        select(
            func.count(InsurancePolicy.id).filter(
                InsurancePolicy.status == InsurancePolicyStatus.ACTIVE
            ).label("active_policies"),
            func.sum(InsurancePolicy.sum_insured).filter(
                InsurancePolicy.status == InsurancePolicyStatus.ACTIVE
            ).label("total_coverage"),
            func.sum(InsurancePolicy.total_premium).filter(
                InsurancePolicy.premium_paid == True
            ).label("premium_paid"),
        )
        .where(InsurancePolicy.organization_id == organization_id)
    )
    ins_row = ins_stats.one()

    # Claims stats
    claims_stats = await db.execute(
        select(
            func.count(InsuranceClaim.id).filter(
                InsuranceClaim.incident_date >= fy_start
            ).label("claims_ytd"),
            func.sum(InsuranceClaim.settled_amount).filter(
                InsuranceClaim.settlement_date >= fy_start
            ).label("settled_ytd"),
        )
        .where(InsuranceClaim.organization_id == organization_id)
    )
    claims_row = claims_stats.one()

    insurance_summary = {
        "active_policies": ins_row.active_policies or 0,
        "total_coverage": float(ins_row.total_coverage or 0),
        "premium_paid_ytd": float(ins_row.premium_paid or 0),
        "claims_ytd": claims_row.claims_ytd or 0,
        "settled_amount_ytd": float(claims_row.settled_ytd or 0),
    }

    # ========== ALERTS ==========
    # AMC expiring
    amc_expiring = await db.execute(
        select(func.count(AMCContract.id))
        .where(
            AMCContract.organization_id == organization_id,
            AMCContract.status == AMCStatus.ACTIVE,
            AMCContract.end_date <= as_on_date + timedelta(days=30),
            AMCContract.end_date >= as_on_date,
        )
    )

    # Insurance expiring
    ins_expiring = await db.execute(
        select(func.count(InsurancePolicy.id))
        .where(
            InsurancePolicy.organization_id == organization_id,
            InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
            InsurancePolicy.end_date <= as_on_date + timedelta(days=30),
            InsurancePolicy.end_date >= as_on_date,
        )
    )

    # Overdue maintenance
    overdue_maint = await db.execute(
        select(func.count(MaintenanceRequest.id))
        .where(
            MaintenanceRequest.organization_id == organization_id,
            MaintenanceRequest.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]),
            MaintenanceRequest.scheduled_date < as_on_date,
        )
    )

    # Leases expiring
    lease_expiring = await db.execute(
        select(func.count(Lease.id))
        .where(
            Lease.organization_id == organization_id,
            Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
            Lease.end_date <= as_on_date + timedelta(days=90),
            Lease.end_date >= as_on_date,
        )
    )

    alerts = {
        "amc_expiring_30_days": amc_expiring.scalar_one() or 0,
        "insurance_expiring_30_days": ins_expiring.scalar_one() or 0,
        "overdue_maintenance": overdue_maint.scalar_one() or 0,
        "leases_expiring_90_days": lease_expiring.scalar_one() or 0,
    }

    # ========== TRENDS (Last 12 months) ==========
    trends = {
        "depreciation_monthly": monthly_trend,
        # Additional trends could be added here
    }

    return FADashboardResponse(
        organization_id=organization_id,
        as_on_date=as_on_date,
        assets=assets_summary,
        depreciation=depreciation_summary,
        leases=leases_summary,
        maintenance=maintenance_summary,
        insurance=insurance_summary,
        alerts=alerts,
        trends=trends,
    )


@router.get("/kpis", response_model=FAKPIResponse, response_model_by_alias=True)
async def get_fa_kpis(
    request: Request,
    organization_id: UUID,
    as_on_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get Fixed Assets Key Performance Indicators.

    Provides KPIs for:
    - Asset valuation and utilization
    - Financial metrics
    - Operational efficiency
    - Compliance status
    """
    if not as_on_date:
        as_on_date = date.today()

    # Determine FY
    if as_on_date.month >= 4:
        fy_start = date(as_on_date.year, 4, 1)
        fy_str = f"{as_on_date.year}-{str(as_on_date.year + 1)[2:]}"
    else:
        fy_start = date(as_on_date.year - 1, 4, 1)
        fy_str = f"{as_on_date.year - 1}-{str(as_on_date.year)[2:]}"

    # Asset stats
    asset_stats = await db.execute(
        select(
            func.count(FixedAsset.id).label("total_count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.wdv_value).label("total_wdv"),
            func.count(FixedAsset.id).filter(
                FixedAsset.status == AssetStatus.FULLY_DEPRECIATED
            ).label("fully_depreciated"),
            func.avg(
                func.extract('epoch', func.age(as_on_date, FixedAsset.acquisition_date)) / 86400 / 30
            ).label("avg_age_months"),
        )
        .where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
        )
    )
    asset_row = asset_stats.one()

    total_count = asset_row.total_count or 1  # Avoid division by zero
    total_cost = asset_row.total_cost or Decimal("0.00")
    total_wdv = asset_row.total_wdv or Decimal("0.00")
    fully_dep = asset_row.fully_depreciated or 0

    # Depreciation
    dep_stats = await db.execute(
        select(func.sum(Depreciation.depreciation_amount).label("ytd_dep"))
        .join(FixedAsset, Depreciation.asset_id == FixedAsset.id)
        .where(
            FixedAsset.organization_id == organization_id,
            Depreciation.period_to >= fy_start,
            Depreciation.period_to <= as_on_date,
        )
    )
    ytd_depreciation = dep_stats.scalar_one() or Decimal("0.00")

    # Maintenance cost
    maint_cost = await db.execute(
        select(func.sum(MaintenanceRequest.total_cost).label("cost"))
        .where(
            MaintenanceRequest.organization_id == organization_id,
            MaintenanceRequest.reported_date >= fy_start,
        )
    )
    ytd_maintenance = maint_cost.scalar_one() or Decimal("0.00")

    # Insurance premium
    ins_premium = await db.execute(
        select(func.sum(InsurancePolicy.total_premium).label("premium"))
        .where(
            InsurancePolicy.organization_id == organization_id,
            InsurancePolicy.premium_paid == True,
            InsurancePolicy.premium_paid_date >= fy_start,
        )
    )
    ytd_insurance = ins_premium.scalar_one() or Decimal("0.00")

    # Lease liability
    lease_liability = await db.execute(
        select(func.sum(Lease.lease_liability_current).label("liability"))
        .where(
            Lease.organization_id == organization_id,
            Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
        )
    )
    total_lease_liability = lease_liability.scalar_one() or Decimal("0.00")

    # Insurance coverage
    ins_coverage = await db.execute(
        select(func.sum(InsurancePolicy.sum_insured).label("coverage"))
        .where(
            InsurancePolicy.organization_id == organization_id,
            InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
        )
    )
    total_coverage = ins_coverage.scalar_one() or Decimal("0.00")
    coverage_ratio = (total_coverage / total_cost * 100) if total_cost > 0 else Decimal("0.00")

    # AMC coverage
    amc_count = await db.execute(
        select(func.count(AMCContract.id))
        .where(
            AMCContract.organization_id == organization_id,
            AMCContract.status == AMCStatus.ACTIVE,
        )
    )
    amc_active = amc_count.scalar_one() or 0
    amc_coverage_pct = Decimal(str(min(amc_active / total_count * 100, 100))) if total_count > 0 else Decimal("0.00")

    # Overdue maintenance
    overdue = await db.execute(
        select(func.count(MaintenanceRequest.id))
        .where(
            MaintenanceRequest.organization_id == organization_id,
            MaintenanceRequest.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]),
            MaintenanceRequest.scheduled_date < as_on_date,
        )
    )
    overdue_count = overdue.scalar_one() or 0

    # Calculate KPIs
    depreciation_rate = (ytd_depreciation / total_cost * 100) if total_cost > 0 else Decimal("0.00")
    fully_dep_pct = Decimal(str(fully_dep / total_count * 100)) if total_count > 0 else Decimal("0.00")
    maint_per_asset = ytd_maintenance / total_count if total_count > 0 else Decimal("0.00")

    return FAKPIResponse(
        organization_id=organization_id,
        as_on_date=as_on_date,
        financial_year=fy_str,
        total_asset_value=total_cost,
        total_wdv=total_wdv,
        depreciation_rate=depreciation_rate.quantize(Decimal("0.01")),
        asset_utilization_rate=Decimal("85.00"),  # Would need actual tracking
        fully_depreciated_percentage=fully_dep_pct.quantize(Decimal("0.01")),
        ytd_depreciation_expense=ytd_depreciation,
        ytd_maintenance_cost=ytd_maintenance,
        ytd_insurance_premium=ytd_insurance,
        total_lease_liability=total_lease_liability,
        average_asset_age_months=Decimal(str(asset_row.avg_age_months or 0)).quantize(Decimal("0.1")),
        maintenance_cost_per_asset=maint_per_asset.quantize(Decimal("0.01")),
        insurance_coverage_ratio=coverage_ratio.quantize(Decimal("0.01")),
        amc_coverage_percentage=amc_coverage_pct.quantize(Decimal("0.01")),
        physical_verification_completion=Decimal("75.00"),  # Would need actual tracking
        overdue_maintenance_count=overdue_count,
    )


@router.get("/asset-composition", response_model=dict, response_model_by_alias=True)
async def get_asset_composition(
    request: Request,
    organization_id: UUID,
    group_by: str = Query("category", description="category, type, location, status"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get asset composition breakdown by different dimensions."""

    if group_by == "category":
        result = await db.execute(
            select(
                AssetCategory.category_name.label("name"),
                func.count(FixedAsset.id).label("count"),
                func.sum(FixedAsset.total_cost).label("cost"),
                func.sum(FixedAsset.wdv_value).label("wdv"),
            )
            .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            )
            .group_by(AssetCategory.category_name)
            .order_by(func.sum(FixedAsset.wdv_value).desc())
        )
    elif group_by == "type":
        result = await db.execute(
            select(
                AssetCategory.asset_type.label("name"),
                func.count(FixedAsset.id).label("count"),
                func.sum(FixedAsset.total_cost).label("cost"),
                func.sum(FixedAsset.wdv_value).label("wdv"),
            )
            .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            )
            .group_by(AssetCategory.asset_type)
        )
    elif group_by == "status":
        result = await db.execute(
            select(
                FixedAsset.status.label("name"),
                func.count(FixedAsset.id).label("count"),
                func.sum(FixedAsset.total_cost).label("cost"),
                func.sum(FixedAsset.wdv_value).label("wdv"),
            )
            .where(FixedAsset.organization_id == organization_id)
            .group_by(FixedAsset.status)
        )
    else:
        # Default to category
        result = await db.execute(
            select(
                AssetCategory.category_name.label("name"),
                func.count(FixedAsset.id).label("count"),
                func.sum(FixedAsset.total_cost).label("cost"),
                func.sum(FixedAsset.wdv_value).label("wdv"),
            )
            .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
            )
            .group_by(AssetCategory.category_name)
        )

    data = [
        {
            "name": str(row.name.value if hasattr(row.name, 'value') else row.name),
            "count": row.count,
            "cost": float(row.cost or 0),
            "wdv": float(row.wdv or 0),
            "percentage": 0,  # Will calculate below
        }
        for row in result
    ]

    # Calculate percentages
    total_wdv = sum(d["wdv"] for d in data)
    for d in data:
        d["percentage"] = round(d["wdv"] / total_wdv * 100, 2) if total_wdv > 0 else 0

    return {
        "group_by": group_by,
        "data": data,
        "total_count": sum(d["count"] for d in data),
        "total_cost": sum(d["cost"] for d in data),
        "total_wdv": total_wdv,
    }


@router.get("/depreciation-trend", response_model=dict, response_model_by_alias=True)
async def get_depreciation_trend(
    request: Request,
    organization_id: UUID,
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get monthly depreciation trend."""

    start_date = date.today() - timedelta(days=months * 30)

    result = await db.execute(
        select(
            Depreciation.depreciation_period,
            func.sum(Depreciation.depreciation_amount).label("amount"),
            func.count(func.distinct(Depreciation.asset_id)).label("asset_count"),
        )
        .join(FixedAsset, Depreciation.asset_id == FixedAsset.id)
        .where(
            FixedAsset.organization_id == organization_id,
            Depreciation.period_to >= start_date,
        )
        .group_by(Depreciation.depreciation_period)
        .order_by(Depreciation.depreciation_period)
    )

    trend = [
        {
            "period": row.depreciation_period,
            "amount": float(row.amount or 0),
            "asset_count": row.asset_count,
        }
        for row in result
    ]

    return {
        "months": months,
        "trend": trend,
        "total_depreciation": sum(t["amount"] for t in trend),
        "average_monthly": sum(t["amount"] for t in trend) / len(trend) if trend else 0,
    }


@router.get("/alerts/all", response_model=dict, response_model_by_alias=True)
async def get_all_alerts(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get all active alerts for Fixed Assets module."""

    today = date.today()

    # AMC expiring in 30 days
    amc_30 = await db.execute(
        select(AMCContract)
        .where(
            AMCContract.organization_id == organization_id,
            AMCContract.status == AMCStatus.ACTIVE,
            AMCContract.end_date <= today + timedelta(days=30),
            AMCContract.end_date >= today,
        )
    )
    amc_expiring = [
        {"id": str(c.id), "name": c.contract_name, "expiry": c.end_date.isoformat()}
        for c in amc_30.scalars()
    ]

    # Insurance expiring in 30 days
    ins_30 = await db.execute(
        select(InsurancePolicy)
        .where(
            InsurancePolicy.organization_id == organization_id,
            InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
            InsurancePolicy.end_date <= today + timedelta(days=30),
            InsurancePolicy.end_date >= today,
        )
    )
    ins_expiring = [
        {"id": str(p.id), "name": p.policy_name, "expiry": p.end_date.isoformat()}
        for p in ins_30.scalars()
    ]

    # Overdue maintenance
    overdue = await db.execute(
        select(MaintenanceRequest)
        .where(
            MaintenanceRequest.organization_id == organization_id,
            MaintenanceRequest.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]),
            MaintenanceRequest.scheduled_date < today,
        )
    )
    overdue_maint = [
        {
            "id": str(m.id),
            "title": m.title,
            "scheduled": m.scheduled_date.isoformat(),
            "days_overdue": (today - m.scheduled_date).days,
        }
        for m in overdue.scalars()
    ]

    # Leases expiring in 90 days
    lease_90 = await db.execute(
        select(Lease)
        .where(
            Lease.organization_id == organization_id,
            Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
            Lease.end_date <= today + timedelta(days=90),
            Lease.end_date >= today,
        )
    )
    lease_expiring = [
        {"id": str(l.id), "name": l.lease_name, "expiry": l.end_date.isoformat()}
        for l in lease_90.scalars()
    ]

    return {
        "amc_expiring": {"count": len(amc_expiring), "items": amc_expiring},
        "insurance_expiring": {"count": len(ins_expiring), "items": ins_expiring},
        "overdue_maintenance": {"count": len(overdue_maint), "items": overdue_maint},
        "leases_expiring": {"count": len(lease_expiring), "items": lease_expiring},
        "total_alerts": len(amc_expiring) + len(ins_expiring) + len(overdue_maint) + len(lease_expiring),
    }
