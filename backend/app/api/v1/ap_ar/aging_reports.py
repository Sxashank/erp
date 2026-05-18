"""AP/AR Aging Reports API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
# from app.core.permissions import RequirePermissions
from app.models.auth.user import User
from app.services.ap_ar.aging_report_service import AgingReportService

router = APIRouter(prefix="/ap-ar/aging", tags=["AP/AR Aging Reports"])


@router.get(
    "/ap-summary",
    summary="AP Aging Summary"
)
async def get_ap_aging_summary(
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    vendor_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_with_tenant)) -> dict:
    """Get AP (Accounts Payable) aging summary by vendor."""
    if not as_of_date:
        as_of_date = date.today()

    service = AgingReportService(db)
    return await service.get_ap_aging_summary(
        organization_id=organization_id,
        as_of_date=as_of_date,
        vendor_id=vendor_id)


@router.get(
    "/ar-summary",
    summary="AR Aging Summary"
)
async def get_ar_aging_summary(
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    customer_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_with_tenant)) -> dict:
    """Get AR (Accounts Receivable) aging summary by customer."""
    if not as_of_date:
        as_of_date = date.today()

    service = AgingReportService(db)
    return await service.get_ar_aging_summary(
        organization_id=organization_id,
        as_of_date=as_of_date,
        customer_id=customer_id)


@router.get(
    "/ap-detail/{vendor_id}",
    summary="AP Aging Detail"
)
async def get_ap_aging_detail(
    vendor_id: UUID,
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant)) -> dict:
    """Get detailed AP aging for a specific vendor."""
    if not as_of_date:
        as_of_date = date.today()

    service = AgingReportService(db)
    return await service.get_ap_aging_detail(
        organization_id=organization_id,
        vendor_id=vendor_id,
        as_of_date=as_of_date)


@router.get(
    "/ar-detail/{customer_id}",
    summary="AR Aging Detail"
)
async def get_ar_aging_detail(
    customer_id: UUID,
    organization_id: UUID,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant)) -> dict:
    """Get detailed AR aging for a specific customer."""
    if not as_of_date:
        as_of_date = date.today()

    service = AgingReportService(db)
    return await service.get_ar_aging_detail(
        organization_id=organization_id,
        customer_id=customer_id,
        as_of_date=as_of_date)
