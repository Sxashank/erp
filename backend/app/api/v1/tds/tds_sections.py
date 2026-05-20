"""TDS Section API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.tds.tds_section_service import TDSSectionService
from app.schemas.tds.tds_section import TDSSectionCreate, TDSSectionUpdate, TDSSectionResponse
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(section) -> TDSSectionResponse:
    """Convert model to response."""
    return TDSSectionResponse(
        id=section.id,
        section_code=section.section_code,
        section_name=section.section_name,
        description=section.description,
        rate_individual=section.rate_individual,
        rate_company=section.rate_company,
        rate_no_pan=section.rate_no_pan,
        rate_lower_deduction=section.rate_lower_deduction,
        threshold_single=section.threshold_single,
        threshold_annual=section.threshold_annual,
        is_tcs=section.is_tcs,
        surcharge_applicable=section.surcharge_applicable,
        cess_rate=section.cess_rate,
        effective_from=section.effective_from,
        effective_to=section.effective_to,
        return_form=section.return_form,
        nature_of_payment_code=section.nature_of_payment_code,
        created_at=section.created_at,
        updated_at=section.updated_at,
        is_active=section.is_active,
    )


@router.get("", response_model=PaginatedResponse[TDSSectionResponse], response_model_by_alias=True)
async def list_tds_sections(
    return_form: Optional[str] = Query(
        None, alias="returnForm", description="Filter by return form (24Q, 26Q, etc.)"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of TDS sections."""
    service = TDSSectionService(db)
    skip = (page - 1) * page_size
    sections, total = await service.get_all(skip, page_size, include_inactive, return_form)
    items = [_to_response(s) for s in sections]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=PaginatedResponse[TDSSectionResponse], response_model_by_alias=True)
async def list_active_tds_sections(
    as_of_date: Optional[date] = Query(None, alias="asOfDate"),
    is_tcs: bool = Query(False, alias="isTcs", description="Get TCS sections instead of TDS"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get active TDS/TCS sections as of a specific date."""
    service = TDSSectionService(db)
    skip = (page - 1) * page_size
    sections, total = await service.get_active(as_of_date, is_tcs, skip, page_size)
    items = [_to_response(s) for s in sections]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=TDSSectionResponse, response_model_by_alias=True)
async def create_tds_section(
    data: TDSSectionCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new TDS section."""
    service = TDSSectionService(db)
    section = await service.create(data, current_user.id)
    return _to_response(section)


@router.get("/{section_id}", response_model=TDSSectionResponse, response_model_by_alias=True)
async def get_tds_section(
    section_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS section by ID."""
    service = TDSSectionService(db)
    section = await service.get(section_id)
    return _to_response(section)


@router.put("/{section_id}", response_model=TDSSectionResponse, response_model_by_alias=True)
async def update_tds_section(
    section_id: UUID,
    data: TDSSectionUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a TDS section."""
    service = TDSSectionService(db)
    section = await service.update(section_id, data, current_user.id)
    return _to_response(section)


@router.delete("/{section_id}")
async def delete_tds_section(
    section_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a TDS section."""
    service = TDSSectionService(db)
    await service.delete(section_id, current_user.id)
    return {"message": "TDS section deleted successfully"}
