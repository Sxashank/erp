"""Customer API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.ap_ar.customer_service import CustomerService
from app.schemas.ap_ar.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(customer) -> CustomerResponse:
    """Convert model to response."""
    return CustomerResponse(
        id=customer.id,
        code=customer.code,
        name=customer.name,
        display_name=customer.display_name,
        customer_type=customer.customer_type.value if customer.customer_type else None,
        organization_id=customer.organization_id,
        pan=customer.pan,
        gstin=customer.gstin,
        gst_registration_type=customer.gst_registration_type.value if customer.gst_registration_type else None,
        place_of_supply_state=customer.place_of_supply_state,
        tcs_applicable=customer.tcs_applicable,
        tcs_section_id=customer.tcs_section_id,
        contact_person=customer.contact_person,
        email=customer.email,
        phone=customer.phone,
        mobile=customer.mobile,
        billing_address_line1=customer.billing_address_line1,
        billing_address_line2=customer.billing_address_line2,
        billing_city=customer.billing_city,
        billing_state_code=customer.billing_state_code,
        billing_pincode=customer.billing_pincode,
        billing_country=customer.billing_country,
        shipping_address_line1=customer.shipping_address_line1,
        shipping_address_line2=customer.shipping_address_line2,
        shipping_city=customer.shipping_city,
        shipping_state_code=customer.shipping_state_code,
        shipping_pincode=customer.shipping_pincode,
        shipping_country=customer.shipping_country,
        bank_name=customer.bank_name,
        bank_account_number=customer.bank_account_number,
        bank_ifsc_code=customer.bank_ifsc_code,
        bank_branch=customer.bank_branch,
        payment_mode_preference=customer.payment_mode_preference.value if customer.payment_mode_preference else None,
        control_account_id=customer.control_account_id,
        revenue_account_id=customer.revenue_account_id,
        payment_terms_id=customer.payment_terms_id,
        credit_days=customer.credit_days,
        credit_limit=customer.credit_limit,
        credit_limit_enabled=customer.credit_limit_enabled,
        currency_code=customer.currency_code,
        opening_balance=customer.opening_balance,
        opening_balance_type=customer.opening_balance_type.value if customer.opening_balance_type else None,
        current_balance=customer.current_balance,
        current_balance_type=customer.current_balance_type.value if customer.current_balance_type else None,
        remarks=customer.remarks,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        is_active=customer.is_active,
    )


def _to_list_response(customer) -> CustomerListResponse:
    """Convert model to list response."""
    return CustomerListResponse(
        id=customer.id,
        code=customer.code,
        name=customer.name,
        display_name=customer.display_name,
        customer_type=customer.customer_type.value if customer.customer_type else None,
        gstin=customer.gstin,
        pan=customer.pan,
        billing_city=customer.billing_city,
        billing_state_code=customer.billing_state_code,
        current_balance=customer.current_balance,
        current_balance_type=customer.current_balance_type.value if customer.current_balance_type else None,
        is_active=customer.is_active,
    )


@router.get("", response_model=PaginatedResponse[CustomerListResponse])
async def list_customers(
    organization_id: UUID = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None, description="Search in code, name, GSTIN, PAN"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type"),
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of customers for an organization."""
    service = CustomerService(db)
    skip = (page - 1) * page_size
    customers, total = await service.get_all(
        organization_id, skip, page_size, include_inactive, search, customer_type
    )
    items = [_to_list_response(c) for c in customers]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=list[CustomerListResponse])
async def list_active_customers(
    organization_id: UUID = Query(..., description="Organization ID"),
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get active customers for dropdown lists."""
    service = CustomerService(db)
    customers = await service.get_active(organization_id)
    return [_to_list_response(c) for c in customers]


@router.get("/generate-code")
async def generate_customer_code(
    organization_id: UUID = Query(..., description="Organization ID"),
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Generate next customer code."""
    service = CustomerService(db)
    code = await service.generate_code(organization_id)
    return {"code": code}


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new customer."""
    service = CustomerService(db)
    customer = await service.create(data, current_user.id)
    return _to_response(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get customer by ID."""
    service = CustomerService(db)
    customer = await service.get(customer_id)
    return _to_response(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a customer."""
    service = CustomerService(db)
    customer = await service.update(customer_id, data, current_user.id)
    return _to_response(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_CUSTOMER_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a customer."""
    service = CustomerService(db)
    await service.delete(customer_id, current_user.id)
    return {"message": "Customer deleted successfully"}
