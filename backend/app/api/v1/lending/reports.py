"""Lending reports API."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.services.reports import lending_reports

router = APIRouter()


@router.get(
    "/reports/lending/collection-efficiency", dependencies=[Depends(RequirePermissions("LMS_READ"))]
)
async def collection_efficiency(
    period_from: date = Query(...),
    period_to: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.collection_efficiency_report(
        db,
        organization_id=current_user.organization_id,
        period_from=period_from,
        period_to=period_to,
    )


@router.get("/reports/lending/npa-movement", dependencies=[Depends(RequirePermissions("LMS_READ"))])
async def npa_movement(
    as_of_date: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.npa_movement_report(
        db, organization_id=current_user.organization_id, as_of_date=as_of_date
    )


@router.get(
    "/reports/lending/dpd-distribution", dependencies=[Depends(RequirePermissions("LMS_READ"))]
)
async def dpd_distribution(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.dpd_distribution_report(
        db, organization_id=current_user.organization_id
    )


@router.get(
    "/reports/lending/prepayment-volume", dependencies=[Depends(RequirePermissions("LMS_READ"))]
)
async def prepayment_volume(
    period_from: date = Query(...),
    period_to: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.prepayment_volume_report(
        db,
        organization_id=current_user.organization_id,
        period_from=period_from,
        period_to=period_to,
    )


@router.get("/reports/lending/aum", dependencies=[Depends(RequirePermissions("LMS_READ"))])
async def aum(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.aum_report(db, organization_id=current_user.organization_id)


@router.get(
    "/reports/lending/provisioning-summary", dependencies=[Depends(RequirePermissions("LMS_READ"))]
)
async def provisioning_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.provisioning_summary_report(
        db, organization_id=current_user.organization_id
    )


@router.get(
    "/reports/lending/doc-release-breach-watch",
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def doc_release_breach_watch(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.doc_release_breach_watch(
        db, organization_id=current_user.organization_id
    )


@router.get(
    "/reports/lending/write-off-summary", dependencies=[Depends(RequirePermissions("LMS_READ"))]
)
async def write_off_summary(
    period_from: date = Query(...),
    period_to: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.write_off_summary_report(
        db,
        organization_id=current_user.organization_id,
        period_from=period_from,
        period_to=period_to,
    )


@router.get("/reports/lending/tat-by-stage", dependencies=[Depends(RequirePermissions("LMS_READ"))])
async def tat_by_stage(
    period_from: date = Query(...),
    period_to: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    return await lending_reports.tat_by_stage_report(
        db,
        organization_id=current_user.organization_id,
        period_from=period_from,
        period_to=period_to,
    )
