"""
Regulatory Reports API Endpoints
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    RequirePermissions,
    get_current_user,
    get_db,
    get_db_with_tenant,
get_db_with_tenant,
)
from app.models.auth.user import User
from app.schemas.reports.regulatory import (
    CapitalCompositionResponse,
    CrarTrendResponse,
    InfrastructureRatioResponse,
)
from app.services.reports.regulatory_report_service import RegulatoryReportService

router = APIRouter()


@router.get("/alm")
async def get_alm_report(
    as_of_date: date = Query(default=None, description="Report date"),
    report_type: str = Query(default="STRUCTURAL", description="STRUCTURAL or DYNAMIC"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Asset Liability Management (ALM) Report
    Shows maturity profile of assets and liabilities in time buckets
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_alm_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
        report_type=report_type,
    )


@router.get("/npa")
async def get_npa_report(
    as_of_date: date = Query(default=None, description="Report date"),
    detailed: bool = Query(default=False, description="Include detailed breakdown"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate NPA Classification Report
    Shows asset classification as per RBI IRAC norms
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_npa_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
        detailed=detailed,
    )


@router.get("/crar")
async def get_crar_report(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Capital to Risk Assets Ratio (CRAR) Report
    Shows capital adequacy position
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_crar_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


@router.get("/liquidity")
async def get_liquidity_report(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Liquidity Coverage Ratio (LCR) Report
    Shows liquidity position and coverage
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_liquidity_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


@router.get("/large-exposure")
async def get_large_exposure_report(
    as_of_date: date = Query(default=None, description="Report date"),
    threshold_percentage: float = Query(default=10.0, description="Threshold % of Tier 1 capital"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Large Exposure Report
    Shows borrowers with exposure exceeding threshold
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_large_exposure_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
        threshold_percentage=threshold_percentage,
    )


@router.get("/sector-exposure")
async def get_sector_exposure_report(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate Sector-wise Exposure Report
    Shows concentration of advances across sectors
    """
    if as_of_date is None:
        as_of_date = date.today()

    service = RegulatoryReportService(db)
    return await service.generate_sector_exposure_report(
        org_id=current_user.organization_id,
        as_of_date=as_of_date,
    )


# ─────────────────────── CRAR sub-sections ───────────────────────
# Capital composition, historical trend, and NBFC-IFC infrastructure
# ratio — backing the matching sections in `CRARDashboard.tsx`.
# All three: `RequirePermissions("FIN_REPORT_VIEW")` + RLS via
# `get_db_with_tenant`. See CLAUDE.md §6.3 and §3.4.


@router.get(
    "/crar/composition",
    response_model=CapitalCompositionResponse, response_model_by_alias=True,
)
async def get_crar_composition(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
):
    """Capital composition — Tier-1 / Tier-2 line-item breakdown."""
    if as_of_date is None:
        as_of_date = date.today()
    service = RegulatoryReportService(db)
    payload = await service.get_capital_composition(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )
    return CapitalCompositionResponse.model_validate(payload)


@router.get(
    "/crar/trend",
    response_model=CrarTrendResponse, response_model_by_alias=True,
)
async def get_crar_trend(
    months: int = Query(
        default=12,
        ge=1,
        le=60,
        description="Trailing window in months (1–60)",
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
):
    """Historical CRAR series for the trend chart."""
    service = RegulatoryReportService(db)
    payload = await service.get_crar_trend(
        organization_id=current_user.organization_id,
        months=months,
    )
    return CrarTrendResponse.model_validate(payload)


@router.get(
    "/crar/infrastructure-ratio",
    response_model=InfrastructureRatioResponse, response_model_by_alias=True,
)
async def get_infrastructure_ratio(
    as_of_date: date = Query(default=None, description="Report date"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
):
    """NBFC-IFC infrastructure ratio (≥75% requirement)."""
    if as_of_date is None:
        as_of_date = date.today()
    service = RegulatoryReportService(db)
    payload = await service.get_infrastructure_ratio(
        organization_id=current_user.organization_id,
        as_of_date=as_of_date,
    )
    return InfrastructureRatioResponse.model_validate(payload)
