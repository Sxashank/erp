"""
FD Product API Endpoints
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.fixed_deposits.fd_product import (
    FDProductCreate,
    FDProductUpdate,
    FDProductResponse,
    FDProductListResponse,
    FDInterestSlabCreate,
    FDInterestSlabUpdate,
    FDInterestSlabResponse,
)
from app.services.fixed_deposits.fd_product_service import FDProductService
from app.models.fixed_deposits.fd_product import FDCustomerCategory

from app.api.deps import get_db_with_tenant
from app.core.exceptions import NotFoundException
router = APIRouter()


@router.get("", response_model=FDProductListResponse, response_model_by_alias=True)
async def list_products(
    organization_id: UUID,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List all FD products for an organization."""
    service = FDProductService(db)
    return await service.list_products(
        organization_id=organization_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=FDProductResponse, response_model_by_alias=True, status_code=201)
async def create_product(
    data: FDProductCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new FD product."""
    service = FDProductService(db)
    return await service.create_product(data)


@router.get("/{product_id}", response_model=FDProductResponse, response_model_by_alias=True)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get FD product by ID."""
    service = FDProductService(db)
    product = await service.get_product(product_id)
    if not product:
        raise NotFoundException(detail="Product not found", error_code="PRODUCT_NOT_FOUND")
    return product


@router.put("/{product_id}", response_model=FDProductResponse, response_model_by_alias=True)
async def update_product(
    product_id: UUID,
    data: FDProductUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update an FD product."""
    service = FDProductService(db)
    product = await service.update_product(product_id, data)
    if not product:
        raise NotFoundException(detail="Product not found", error_code="PRODUCT_NOT_FOUND")
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Soft delete an FD product."""
    service = FDProductService(db)
    if not await service.delete_product(product_id):
        raise NotFoundException(detail="Product not found", error_code="PRODUCT_NOT_FOUND")
    return {"message": "Product deactivated successfully"}


# Interest Slab Endpoints
@router.post("/{product_id}/slabs", response_model=FDInterestSlabResponse, response_model_by_alias=True, status_code=201)
async def add_interest_slab(
    product_id: UUID,
    data: FDInterestSlabCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add interest slab to a product."""
    service = FDProductService(db)

    # Verify product exists
    product = await service.get_product(product_id)
    if not product:
        raise NotFoundException(detail="Product not found", error_code="PRODUCT_NOT_FOUND")

    return await service.add_interest_slab(product_id, data)


@router.put("/slabs/{slab_id}", response_model=FDInterestSlabResponse, response_model_by_alias=True)
async def update_interest_slab(
    slab_id: UUID,
    data: FDInterestSlabUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update an interest slab."""
    service = FDProductService(db)
    slab = await service.update_interest_slab(slab_id, data)
    if not slab:
        raise NotFoundException(detail="Interest slab not found", error_code="INTEREST_SLAB_NOT_FOUND")
    return slab


@router.delete("/slabs/{slab_id}")
async def delete_interest_slab(
    slab_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete an interest slab."""
    service = FDProductService(db)
    if not await service.delete_interest_slab(slab_id):
        raise NotFoundException(detail="Interest slab not found", error_code="INTEREST_SLAB_NOT_FOUND")
    return {"message": "Interest slab deleted successfully"}


@router.get("/{product_id}/rate")
async def get_applicable_rate(
    product_id: UUID,
    tenure_days: int = Query(..., ge=1),
    amount: Decimal = Query(..., gt=0),
    customer_category: FDCustomerCategory = FDCustomerCategory.GENERAL,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get applicable interest rate for given parameters."""
    service = FDProductService(db)

    rate = await service.get_applicable_rate(
        product_id=product_id,
        tenure_days=tenure_days,
        amount=amount,
        customer_category=customer_category,
        as_of_date=as_of_date,
    )

    if rate is None:
        raise NotFoundException(
            detail="No applicable interest rate found for given parameters",
            error_code="NO_APPLICABLE_INTEREST_RATE_FOUND_FOR",
        )

    return {
        "product_id": str(product_id),
        "tenure_days": tenure_days,
        "amount": float(amount),
        "customer_category": customer_category.value,
        "interest_rate": float(rate),
    }
