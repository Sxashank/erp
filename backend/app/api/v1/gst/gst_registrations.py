"""GST Registration API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.gst.gst_registration_service import GSTRegistrationService
from app.schemas.gst.gst_registration import (
    GSTRegistrationCreate,
    GSTRegistrationUpdate,
    GSTRegistrationResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(reg) -> GSTRegistrationResponse:
    """Convert model to response."""
    return GSTRegistrationResponse(
        id=reg.id,
        gstin=reg.gstin,
        legal_name=reg.legal_name,
        trade_name=reg.trade_name,
        registration_type=reg.registration_type,
        state_code=reg.state_code,
        state_name=reg.state_name,
        address=reg.address,
        pincode=reg.pincode,
        is_e_invoice_enabled=reg.is_e_invoice_enabled,
        e_invoice_username=reg.e_invoice_username,
        is_e_way_bill_enabled=reg.is_e_way_bill_enabled,
        organization_id=reg.organization_id,
        organization_name=reg.organization.name if reg.organization else None,
        unit_id=reg.unit_id,
        unit_name=reg.unit.name if reg.unit else None,
        created_at=reg.created_at,
        updated_at=reg.updated_at,
        is_active=reg.is_active,
    )


@router.get("", response_model=PaginatedResponse[GSTRegistrationResponse])
async def list_gst_registrations(
    organization_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get GST registrations for an organization."""
    service = GSTRegistrationService(db)
    skip = (page - 1) * page_size
    regs, total = await service.get_by_organization(
        organization_id, skip, page_size, include_inactive
    )
    items = [_to_response(r) for r in regs]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=GSTRegistrationResponse)
async def create_gst_registration(
    data: GSTRegistrationCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new GST registration."""
    service = GSTRegistrationService(db)
    reg = await service.create(data, current_user.id)
    return _to_response(reg)


@router.get("/{registration_id}", response_model=GSTRegistrationResponse)
async def get_gst_registration(
    registration_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get GST registration by ID."""
    service = GSTRegistrationService(db)
    reg = await service.get(registration_id)
    return _to_response(reg)


@router.get("/gstin/{gstin}", response_model=GSTRegistrationResponse)
async def get_by_gstin(
    gstin: str,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get GST registration by GSTIN."""
    service = GSTRegistrationService(db)
    reg = await service.get_by_gstin(gstin)
    return _to_response(reg)


@router.put("/{registration_id}", response_model=GSTRegistrationResponse)
async def update_gst_registration(
    registration_id: UUID,
    data: GSTRegistrationUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a GST registration."""
    service = GSTRegistrationService(db)
    reg = await service.update(registration_id, data, current_user.id)
    return _to_response(reg)


@router.delete("/{registration_id}")
async def delete_gst_registration(
    registration_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a GST registration."""
    service = GSTRegistrationService(db)
    await service.delete(registration_id, current_user.id)
    return {"message": "GST registration deleted successfully"}
