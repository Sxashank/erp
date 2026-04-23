"""Vendor Portal Profile Routes."""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.profile_service import VendorProfileService
from app.models.vendor_portal.enums import VendorPortalUserStatus
from app.schemas.vendor_portal.profile import (
    VendorProfileResponse,
    VendorProfileUpdate,
    VendorBankAccountCreate,
    VendorBankAccountUpdate,
    VendorBankAccountResponse,
    VendorContactCreate,
    VendorContactUpdate,
    VendorContactResponse,
    PortalUserCreate,
    PortalUserUpdate,
    PortalUserResponse,
    PortalUserListResponse,
    PortalUserPermissions,
)

router = APIRouter()


@router.get("/", response_model=VendorProfileResponse)
async def get_profile(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get vendor profile."""
    service = VendorProfileService(db)
    vendor = await service.get_vendor_profile(vendor_id)
    return vendor


@router.put("/", response_model=VendorProfileResponse)
async def update_profile(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    data: VendorProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update vendor profile."""
    service = VendorProfileService(db)
    vendor = await service.update_vendor_profile(vendor_id, user_id, data)
    return vendor


# Bank Account endpoints
@router.get("/bank-accounts", response_model=List[VendorBankAccountResponse])
async def get_bank_accounts(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get vendor bank accounts."""
    service = VendorProfileService(db)
    accounts = await service.get_bank_accounts(vendor_id)
    return accounts


@router.post("/bank-accounts", response_model=VendorBankAccountResponse, status_code=status.HTTP_201_CREATED)
async def add_bank_account(
    vendor_id: UUID,  # From auth middleware
    data: VendorBankAccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add bank account."""
    service = VendorProfileService(db)
    account = await service.add_bank_account(vendor_id, data)
    return account


@router.put("/bank-accounts/{account_id}", response_model=VendorBankAccountResponse)
async def update_bank_account(
    vendor_id: UUID,  # From auth middleware
    account_id: UUID,
    data: VendorBankAccountUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update bank account."""
    service = VendorProfileService(db)
    account = await service.update_bank_account(vendor_id, account_id, data)
    return account


# Contact endpoints
@router.get("/contacts", response_model=List[VendorContactResponse])
async def get_contacts(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get vendor contacts."""
    service = VendorProfileService(db)
    contacts = await service.get_contacts(vendor_id)
    return contacts


@router.post("/contacts", response_model=VendorContactResponse, status_code=status.HTTP_201_CREATED)
async def add_contact(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware (invited_by)
    data: VendorContactCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add contact."""
    service = VendorProfileService(db)
    contact = await service.add_contact(vendor_id, organization_id, data, user_id)
    return contact


@router.put("/contacts/{contact_id}", response_model=VendorContactResponse)
async def update_contact(
    vendor_id: UUID,  # From auth middleware
    contact_id: UUID,
    data: VendorContactUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update contact."""
    service = VendorProfileService(db)
    contact = await service.update_contact(vendor_id, contact_id, data)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    vendor_id: UUID,  # From auth middleware
    contact_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove contact."""
    service = VendorProfileService(db)
    await service.remove_contact(vendor_id, contact_id)


# Portal User endpoints
@router.get("/users", response_model=PortalUserListResponse)
async def get_portal_users(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[VendorPortalUserStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get portal users for vendor."""
    service = VendorProfileService(db)
    users, total = await service.get_portal_users(vendor_id, skip, limit, status)
    return PortalUserListResponse(
        items=users,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/users", response_model=PortalUserResponse, status_code=status.HTTP_201_CREATED)
async def create_portal_user(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware (created_by)
    data: PortalUserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create portal user."""
    service = VendorProfileService(db)
    user = await service.create_portal_user(vendor_id, organization_id, data, user_id)
    return user


@router.put("/users/{target_user_id}", response_model=PortalUserResponse)
async def update_portal_user(
    vendor_id: UUID,  # From auth middleware
    target_user_id: UUID,
    data: PortalUserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update portal user."""
    service = VendorProfileService(db)
    user = await service.update_portal_user(vendor_id, target_user_id, data)
    return user


@router.put("/users/{target_user_id}/permissions", response_model=PortalUserResponse)
async def update_user_permissions(
    vendor_id: UUID,  # From auth middleware
    target_user_id: UUID,
    permissions: PortalUserPermissions,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update user permissions."""
    service = VendorProfileService(db)
    user = await service.update_user_permissions(vendor_id, target_user_id, permissions)
    return user


@router.post("/users/{target_user_id}/activate", response_model=PortalUserResponse)
async def activate_user(
    target_user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate a pending user."""
    service = VendorProfileService(db)
    user = await service.activate_user(target_user_id)
    return user


@router.post("/users/{target_user_id}/deactivate", response_model=PortalUserResponse)
async def deactivate_user(
    vendor_id: UUID,  # From auth middleware
    target_user_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user."""
    service = VendorProfileService(db)
    user = await service.deactivate_user(vendor_id, target_user_id, reason)
    return user


@router.post("/users/{target_user_id}/set-primary", response_model=PortalUserResponse)
async def set_primary_contact(
    vendor_id: UUID,  # From auth middleware
    target_user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set user as primary contact."""
    service = VendorProfileService(db)
    user = await service.set_primary_contact(vendor_id, target_user_id)
    return user
