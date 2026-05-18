"""Vendor API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.ap_ar.vendor_service import VendorService
from app.schemas.ap_ar.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorListResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(vendor) -> VendorResponse:
    """Convert model to response."""
    return VendorResponse(
        id=vendor.id,
        code=vendor.code,
        name=vendor.name,
        display_name=vendor.display_name,
        vendor_type=vendor.vendor_type.value if vendor.vendor_type else None,
        organization_id=vendor.organization_id,
        pan=vendor.pan,
        gstin=vendor.gstin,
        gst_registration_type=vendor.gst_registration_type.value if vendor.gst_registration_type else None,
        msme_registered=vendor.msme_registered,
        msme_number=vendor.msme_number,
        tds_applicable=vendor.tds_applicable,
        tds_section_id=vendor.tds_section_id,
        tds_rate_override=vendor.tds_rate_override,
        contact_person=vendor.contact_person,
        email=vendor.email,
        phone=vendor.phone,
        mobile=vendor.mobile,
        address_line1=vendor.address_line1,
        address_line2=vendor.address_line2,
        city=vendor.city,
        state_code=vendor.state_code,
        pincode=vendor.pincode,
        country=vendor.country,
        bank_name=vendor.bank_name,
        bank_account_number=vendor.bank_account_number,
        bank_ifsc_code=vendor.bank_ifsc_code,
        bank_branch=vendor.bank_branch,
        payment_mode_preference=vendor.payment_mode_preference.value if vendor.payment_mode_preference else None,
        control_account_id=vendor.control_account_id,
        expense_account_id=vendor.expense_account_id,
        payment_terms_id=vendor.payment_terms_id,
        credit_days=vendor.credit_days,
        credit_limit=vendor.credit_limit,
        currency_code=vendor.currency_code,
        opening_balance=vendor.opening_balance,
        opening_balance_type=vendor.opening_balance_type.value if vendor.opening_balance_type else None,
        current_balance=vendor.current_balance,
        current_balance_type=vendor.current_balance_type.value if vendor.current_balance_type else None,
        remarks=vendor.remarks,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
        is_active=vendor.is_active,
    )


def _to_list_response(vendor) -> VendorListResponse:
    """Convert model to list response."""
    return VendorListResponse(
        id=vendor.id,
        code=vendor.code,
        name=vendor.name,
        display_name=vendor.display_name,
        vendor_type=vendor.vendor_type.value if vendor.vendor_type else None,
        gstin=vendor.gstin,
        pan=vendor.pan,
        city=vendor.city,
        state_code=vendor.state_code,
        current_balance=vendor.current_balance,
        current_balance_type=vendor.current_balance_type.value if vendor.current_balance_type else None,
        is_active=vendor.is_active,
    )


@router.get("", response_model=PaginatedResponse[VendorListResponse], response_model_by_alias=True)
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None, description="Search in code, name, GSTIN, PAN"),
    vendor_type: Optional[str] = Query(None, description="Filter by vendor type"),
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of vendors for an organization."""
    service = VendorService(db)
    skip = (page - 1) * page_size
    vendors, total = await service.get_all(
        current_user.organization_id, skip, page_size, include_inactive, search, vendor_type
    )
    items = [_to_list_response(v) for v in vendors]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=list[VendorListResponse], response_model_by_alias=True)
async def list_active_vendors(
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get active vendors for dropdown lists."""
    service = VendorService(db)
    vendors = await service.get_active(current_user.organization_id)
    return [_to_list_response(v) for v in vendors]


@router.get("/generate-code")
async def generate_vendor_code(
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Generate next vendor code."""
    service = VendorService(db)
    code = await service.generate_code(current_user.organization_id)
    return {"code": code}


@router.post("", response_model=VendorResponse, response_model_by_alias=True)
async def create_vendor(
    data: VendorCreate,
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new vendor."""
    service = VendorService(db)
    vendor = await service.create(data, current_user.id)
    return _to_response(vendor)


@router.get("/{vendor_id}", response_model=VendorResponse, response_model_by_alias=True)
async def get_vendor(
    vendor_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get vendor by ID."""
    service = VendorService(db)
    vendor = await service.get(vendor_id)
    return _to_response(vendor)


@router.put("/{vendor_id}", response_model=VendorResponse, response_model_by_alias=True)
async def update_vendor(
    vendor_id: UUID,
    data: VendorUpdate,
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a vendor."""
    service = VendorService(db)
    vendor = await service.update(vendor_id, data, current_user.id)
    return _to_response(vendor)


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_VENDOR_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a vendor."""
    service = VendorService(db)
    await service.delete(vendor_id, current_user.id)
    return {"message": "Vendor deleted successfully"}
