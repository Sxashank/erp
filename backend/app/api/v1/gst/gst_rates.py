"""GST Rate API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.gst.gst_rate_service import GSTRateService
from app.schemas.gst.gst_rate import GSTRateCreate, GSTRateUpdate, GSTRateResponse
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(rate) -> GSTRateResponse:
    """Convert model to response."""
    return GSTRateResponse(
        id=rate.id,
        code=rate.code,
        name=rate.name,
        description=rate.description,
        rate=rate.rate,
        cgst_rate=rate.cgst_rate,
        sgst_rate=rate.sgst_rate,
        igst_rate=rate.igst_rate,
        cess_rate=rate.cess_rate,
        effective_from=rate.effective_from,
        effective_to=rate.effective_to,
        is_composition=rate.is_composition,
        is_reverse_charge=rate.is_reverse_charge,
        created_at=rate.created_at,
        updated_at=rate.updated_at,
        is_active=rate.is_active,
    )


@router.get("", response_model=PaginatedResponse[GSTRateResponse], response_model_by_alias=True)
async def list_gst_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of GST rates."""
    service = GSTRateService(db)
    skip = (page - 1) * page_size
    rates, total = await service.get_all(skip, page_size, include_inactive)
    items = [_to_response(r) for r in rates]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=PaginatedResponse[GSTRateResponse], response_model_by_alias=True)
async def list_active_gst_rates(
    as_of_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get active GST rates as of a specific date."""
    service = GSTRateService(db)
    skip = (page - 1) * page_size
    rates, total = await service.get_active(as_of_date, skip, page_size)
    items = [_to_response(r) for r in rates]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=GSTRateResponse, response_model_by_alias=True)
async def create_gst_rate(
    data: GSTRateCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new GST rate."""
    service = GSTRateService(db)
    rate = await service.create(data, current_user.id)
    return _to_response(rate)


@router.get("/{rate_id}", response_model=GSTRateResponse, response_model_by_alias=True)
async def get_gst_rate(
    rate_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get GST rate by ID."""
    service = GSTRateService(db)
    rate = await service.get(rate_id)
    return _to_response(rate)


@router.put("/{rate_id}", response_model=GSTRateResponse, response_model_by_alias=True)
async def update_gst_rate(
    rate_id: UUID,
    data: GSTRateUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a GST rate."""
    service = GSTRateService(db)
    rate = await service.update(rate_id, data, current_user.id)
    return _to_response(rate)


@router.delete("/{rate_id}")
async def delete_gst_rate(
    rate_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a GST rate."""
    service = GSTRateService(db)
    await service.delete(rate_id, current_user.id)
    return {"message": "GST rate deleted successfully"}
