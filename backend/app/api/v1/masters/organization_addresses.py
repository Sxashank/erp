"""Organization Address API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.masters.organization_address_service import OrganizationAddressService
from app.schemas.masters.organization_address import (
    OrganizationAddressCreate,
    OrganizationAddressUpdate,
    OrganizationAddressResponse,
)
from app.schemas.base import MessageResponse

router = APIRouter()


def _to_response(address) -> OrganizationAddressResponse:
    """Convert model to response schema."""
    return OrganizationAddressResponse(
        id=address.id,
        organization_id=address.organization_id,
        address_type=address.address_type,
        address_label=address.address_label,
        address_line1=address.address_line1,
        address_line2=address.address_line2,
        address_line3=address.address_line3,
        landmark=address.landmark,
        city=address.city,
        district=address.district,
        state_code=address.state_code,
        state_name=address.state_name,
        pincode=address.pincode,
        country=address.country,
        contact_person=address.contact_person,
        phone=address.phone,
        email=address.email,
        latitude=address.latitude,
        longitude=address.longitude,
        is_primary=address.is_primary,
        created_at=address.created_at,
        updated_at=address.updated_at,
        is_active=address.is_active,
    )


@router.get("/{org_id}/addresses", response_model=List[OrganizationAddressResponse])
async def list_organization_addresses(
    org_id: UUID,
    address_type: str = Query(None),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all addresses for an organization.
    Optionally filter by address_type.
    Requires MASTER_ORG_VIEW permission.
    """
    service = OrganizationAddressService(db)
    if address_type:
        addresses = await service.get_by_type(org_id, address_type, include_inactive)
    else:
        addresses = await service.get_by_organization(org_id, include_inactive)
    return [_to_response(a) for a in addresses]


@router.post("/{org_id}/addresses", response_model=OrganizationAddressResponse)
async def create_organization_address(
    org_id: UUID,
    data: OrganizationAddressCreate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_ADDRESS_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new address for an organization.
    Requires MASTER_ORG_ADDRESS_CREATE permission.
    """
    # Override organization_id from path
    data.organization_id = org_id
    service = OrganizationAddressService(db)
    address = await service.create(data, current_user.id)
    return _to_response(address)


@router.get("/{org_id}/addresses/{address_id}", response_model=OrganizationAddressResponse)
async def get_organization_address(
    org_id: UUID,
    address_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific address.
    Requires MASTER_ORG_VIEW permission.
    """
    service = OrganizationAddressService(db)
    address = await service.get(address_id)
    return _to_response(address)


@router.put("/{org_id}/addresses/{address_id}", response_model=OrganizationAddressResponse)
async def update_organization_address(
    org_id: UUID,
    address_id: UUID,
    data: OrganizationAddressUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_ADDRESS_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing address.
    Requires MASTER_ORG_ADDRESS_UPDATE permission.
    """
    service = OrganizationAddressService(db)
    address = await service.update(address_id, data, current_user.id)
    return _to_response(address)


@router.delete("/{org_id}/addresses/{address_id}", response_model=MessageResponse)
async def delete_organization_address(
    org_id: UUID,
    address_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_ADDRESS_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete an address.
    Requires MASTER_ORG_ADDRESS_DELETE permission.
    """
    service = OrganizationAddressService(db)
    await service.delete(address_id, current_user.id)
    return MessageResponse(message="Address deleted successfully")


@router.post("/{org_id}/addresses/{address_id}/set-primary", response_model=OrganizationAddressResponse)
async def set_primary_address(
    org_id: UUID,
    address_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_ADDRESS_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Set an address as primary.
    Requires MASTER_ORG_ADDRESS_UPDATE permission.
    """
    service = OrganizationAddressService(db)
    address = await service.set_primary(address_id, current_user.id)
    return _to_response(address)
