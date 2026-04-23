"""Loan Product API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.models.lending.enums import (
    ProductCategory,
    InterestType,
    FeeType,
    DocumentStage,
    EntityType,
)
from app.services.lending.product_service import ProductService
from app.schemas.lending.product import (
    LoanProductCreate,
    LoanProductUpdate,
    LoanProductResponse,
    LoanProductListResponse,
    LoanProductDetailResponse,
    InterestRateCreate,
    InterestRateUpdate,
    InterestRateResponse,
    FeeMasterCreate,
    FeeMasterUpdate,
    FeeMasterResponse,
    ProductFeeCreate,
    ProductFeeUpdate,
    ProductFeeResponse,
    DocumentChecklistCreate,
    DocumentChecklistUpdate,
    DocumentChecklistResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


# =============================================================================
# Interest Rate Endpoints
# =============================================================================


@router.get("/interest-rates", response_model=PaginatedResponse[InterestRateResponse])
async def list_interest_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    effective_date: Optional[date] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of interest rates."""
    service = ProductService(db)
    skip = (page - 1) * page_size
    rates, total = await service.get_all_interest_rates(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        effective_date=effective_date,
    )
    items = [InterestRateResponse.model_validate(r) for r in rates]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("/interest-rates", response_model=InterestRateResponse)
async def create_interest_rate(
    data: InterestRateCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new interest rate."""
    service = ProductService(db)
    rate = await service.create_interest_rate(data, current_user.id)
    return InterestRateResponse.model_validate(rate)


@router.get("/interest-rates/{rate_id}", response_model=InterestRateResponse)
async def get_interest_rate(
    rate_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get interest rate by ID."""
    service = ProductService(db)
    rate = await service.get_interest_rate(rate_id)
    return InterestRateResponse.model_validate(rate)


@router.put("/interest-rates/{rate_id}", response_model=InterestRateResponse)
async def update_interest_rate(
    rate_id: UUID,
    data: InterestRateUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update an interest rate."""
    service = ProductService(db)
    rate = await service.update_interest_rate(rate_id, data, current_user.id)
    return InterestRateResponse.model_validate(rate)


# =============================================================================
# Fee Master Endpoints
# =============================================================================


@router.get("/fee-masters", response_model=PaginatedResponse[FeeMasterResponse])
async def list_fee_masters(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    fee_type: Optional[FeeType] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of fee masters."""
    service = ProductService(db)
    skip = (page - 1) * page_size
    fees, total = await service.get_all_fee_masters(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        fee_type=fee_type,
    )
    items = [FeeMasterResponse.model_validate(f) for f in fees]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("/fee-masters", response_model=FeeMasterResponse)
async def create_fee_master(
    data: FeeMasterCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fee master."""
    service = ProductService(db)
    fee = await service.create_fee_master(data, current_user.id)
    return FeeMasterResponse.model_validate(fee)


@router.get("/fee-masters/{fee_id}", response_model=FeeMasterResponse)
async def get_fee_master(
    fee_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get fee master by ID."""
    service = ProductService(db)
    fee = await service.get_fee_master(fee_id)
    return FeeMasterResponse.model_validate(fee)


@router.put("/fee-masters/{fee_id}", response_model=FeeMasterResponse)
async def update_fee_master(
    fee_id: UUID,
    data: FeeMasterUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a fee master."""
    service = ProductService(db)
    fee = await service.update_fee_master(fee_id, data, current_user.id)
    return FeeMasterResponse.model_validate(fee)


# =============================================================================
# Loan Product Endpoints
# =============================================================================


@router.get("", response_model=PaginatedResponse[LoanProductListResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None),
    category: Optional[ProductCategory] = Query(None),
    interest_type: Optional[InterestType] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of loan products."""
    service = ProductService(db)
    skip = (page - 1) * page_size
    products, total = await service.get_all_products(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        search=search,
        category=category,
        interest_type=interest_type,
    )
    items = [LoanProductListResponse.model_validate(p) for p in products]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=list[LoanProductListResponse])
async def list_active_products(
    category: Optional[ProductCategory] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get active products for dropdown lists."""
    service = ProductService(db)
    products = await service.get_active_products(current_user.organization_id, category)
    return [LoanProductListResponse.model_validate(p) for p in products]


@router.get("/eligible", response_model=list[LoanProductListResponse])
async def get_eligible_products(
    entity_type: EntityType = Query(..., description="Entity type"),
    amount: Optional[float] = Query(None),
    tenure_months: Optional[int] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get eligible products based on criteria."""
    service = ProductService(db)
    products = await service.get_eligible_products(
        current_user.organization_id, entity_type, amount, tenure_months
    )
    return [LoanProductListResponse.model_validate(p) for p in products]


@router.post("", response_model=LoanProductResponse)
async def create_product(
    data: LoanProductCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new loan product."""
    service = ProductService(db)
    product = await service.create_product(data, current_user.id)
    return LoanProductResponse.model_validate(product)


@router.get("/{product_id}", response_model=LoanProductResponse)
async def get_product(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get loan product by ID."""
    service = ProductService(db)
    product = await service.get_product(product_id)
    return LoanProductResponse.model_validate(product)


@router.get("/{product_id}/details", response_model=LoanProductDetailResponse)
async def get_product_details(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get loan product with fees and checklist."""
    service = ProductService(db)
    product = await service.get_product_with_details(product_id)
    return LoanProductDetailResponse.model_validate(product)


@router.put("/{product_id}", response_model=LoanProductResponse)
async def update_product(
    product_id: UUID,
    data: LoanProductUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a loan product."""
    service = ProductService(db)
    product = await service.update_product(product_id, data, current_user.id)
    return LoanProductResponse.model_validate(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a loan product."""
    service = ProductService(db)
    await service.delete_product(product_id, current_user.id)
    return {"message": "Product deleted successfully"}


# =============================================================================
# Product Fee Endpoints
# =============================================================================


@router.get("/{product_id}/fees", response_model=list[ProductFeeResponse])
async def list_product_fees(
    product_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all fees for a product."""
    service = ProductService(db)
    fees = await service.get_product_fees(product_id, include_inactive)
    return [ProductFeeResponse.model_validate(f) for f in fees]


@router.post("/{product_id}/fees", response_model=ProductFeeResponse)
async def add_product_fee(
    product_id: UUID,
    data: ProductFeeCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add a fee to a product."""
    data.product_id = product_id
    service = ProductService(db)
    fee = await service.add_product_fee(data, current_user.id)
    return ProductFeeResponse.model_validate(fee)


@router.put("/fees/{fee_id}", response_model=ProductFeeResponse)
async def update_product_fee(
    fee_id: UUID,
    data: ProductFeeUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a product fee."""
    service = ProductService(db)
    fee = await service.update_product_fee(fee_id, data, current_user.id)
    return ProductFeeResponse.model_validate(fee)


@router.delete("/fees/{fee_id}")
async def delete_product_fee(
    fee_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a product fee."""
    service = ProductService(db)
    await service.delete_product_fee(fee_id, current_user.id)
    return {"message": "Product fee deleted successfully"}


# =============================================================================
# Document Checklist Endpoints
# =============================================================================


@router.get("/{product_id}/checklist", response_model=list[DocumentChecklistResponse])
async def list_document_checklist(
    product_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get document checklist for a product."""
    service = ProductService(db)
    checklist = await service.get_product_checklist(product_id, include_inactive)
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.get("/{product_id}/checklist/by-stage", response_model=list[DocumentChecklistResponse])
async def get_checklist_by_stage(
    product_id: UUID,
    stage: DocumentStage = Query(...),
    entity_type: Optional[EntityType] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get document checklist for a specific stage."""
    service = ProductService(db)
    checklist = await service.get_checklist_by_stage(product_id, stage, entity_type)
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.get("/{product_id}/checklist/mandatory", response_model=list[DocumentChecklistResponse])
async def get_mandatory_documents(
    product_id: UUID,
    stage: Optional[DocumentStage] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get mandatory documents for a product."""
    service = ProductService(db)
    checklist = await service.get_mandatory_documents(product_id, stage, entity_type)
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.post("/{product_id}/checklist", response_model=DocumentChecklistResponse)
async def add_document_checklist(
    product_id: UUID,
    data: DocumentChecklistCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add a document to product checklist."""
    data.product_id = product_id
    service = ProductService(db)
    checklist = await service.add_document_checklist(data, current_user.id)
    return DocumentChecklistResponse.model_validate(checklist)


@router.put("/checklist/{checklist_id}", response_model=DocumentChecklistResponse)
async def update_document_checklist(
    checklist_id: UUID,
    data: DocumentChecklistUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a document checklist item."""
    service = ProductService(db)
    checklist = await service.update_document_checklist(checklist_id, data, current_user.id)
    return DocumentChecklistResponse.model_validate(checklist)


@router.delete("/checklist/{checklist_id}")
async def delete_document_checklist(
    checklist_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document checklist item."""
    service = ProductService(db)
    await service.delete_document_checklist(checklist_id, current_user.id)
    return {"message": "Document checklist item deleted successfully"}
