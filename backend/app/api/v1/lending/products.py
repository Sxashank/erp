"""Loan Product API endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import (
    DocumentStage,
    FeeType,
)
from app.schemas.base import PaginatedResponse
from app.schemas.lending.product import (
    DocumentChecklistCreate,
    DocumentChecklistResponse,
    DocumentChecklistUpdate,
    FeeMasterCreate,
    FeeMasterResponse,
    FeeMasterUpdate,
    InterestRateCreate,
    InterestRateResponse,
    InterestRateUpdate,
    LoanProductCreate,
    LoanProductDetailResponse,
    LoanProductListResponse,
    LoanProductResponse,
    LoanProductUpdate,
    ProductFeeCreate,
    ProductFeeResponse,
    ProductFeeUpdate,
)
from app.services.lending.product_service import ProductService

router = APIRouter()


# =============================================================================
# Interest Rate Endpoints
# =============================================================================


@router.get(
    "/interest-rates",
    response_model=PaginatedResponse[InterestRateResponse],
    response_model_by_alias=True,
)
async def list_interest_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    effective_date: date | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
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


@router.post(
    "/interest-rates",
    response_model=InterestRateResponse,
    response_model_by_alias=True,
)
async def create_interest_rate(
    data: InterestRateCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new interest rate."""
    data.organization_id = current_user.organization_id
    service = ProductService(db)
    rate = await service.create_interest_rate(data, current_user.id)
    return InterestRateResponse.model_validate(rate)


@router.get(
    "/interest-rates/{rate_id}",
    response_model=InterestRateResponse,
    response_model_by_alias=True,
)
async def get_interest_rate(
    rate_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get interest rate by ID."""
    service = ProductService(db)
    rate = await service.get_interest_rate(rate_id)
    return InterestRateResponse.model_validate(rate)


@router.put(
    "/interest-rates/{rate_id}",
    response_model=InterestRateResponse,
    response_model_by_alias=True,
)
async def update_interest_rate(
    rate_id: UUID,
    data: InterestRateUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update an interest rate."""
    service = ProductService(db)
    rate = await service.update_interest_rate(rate_id, data, current_user.id)
    return InterestRateResponse.model_validate(rate)


# =============================================================================
# Fee Master Endpoints
# =============================================================================


@router.get(
    "/fee-masters",
    response_model=PaginatedResponse[FeeMasterResponse],
    response_model_by_alias=True,
)
async def list_fee_masters(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    fee_type: FeeType | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
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


@router.post(
    "/fee-masters",
    response_model=FeeMasterResponse,
    response_model_by_alias=True,
)
async def create_fee_master(
    data: FeeMasterCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new fee master."""
    data.organization_id = current_user.organization_id
    service = ProductService(db)
    fee = await service.create_fee_master(data, current_user.id)
    return FeeMasterResponse.model_validate(fee)


@router.get(
    "/fee-masters/{fee_id}",
    response_model=FeeMasterResponse,
    response_model_by_alias=True,
)
async def get_fee_master(
    fee_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get fee master by ID."""
    service = ProductService(db)
    fee = await service.get_fee_master(fee_id)
    return FeeMasterResponse.model_validate(fee)


@router.put(
    "/fee-masters/{fee_id}",
    response_model=FeeMasterResponse,
    response_model_by_alias=True,
)
async def update_fee_master(
    fee_id: UUID,
    data: FeeMasterUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a fee master."""
    service = ProductService(db)
    fee = await service.update_fee_master(fee_id, data, current_user.id)
    return FeeMasterResponse.model_validate(fee)


# =============================================================================
# Loan Product Endpoints
# =============================================================================


@router.get(
    "",
    response_model=PaginatedResponse[LoanProductListResponse],
    response_model_by_alias=True,
)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    search: str | None = Query(None),
    category: str | None = Query(None),
    interest_type: str | None = Query(None, alias="interestType"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
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


@router.get(
    "/active",
    response_model=list[LoanProductListResponse],
    response_model_by_alias=True,
)
async def list_active_products(
    category: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get active products for dropdown lists."""
    service = ProductService(db)
    products = await service.get_active_products(current_user.organization_id, category)
    return [LoanProductListResponse.model_validate(p) for p in products]


@router.get(
    "/eligible",
    response_model=list[LoanProductListResponse],
    response_model_by_alias=True,
)
async def get_eligible_products(
    entity_type: str = Query(..., alias="entityType", description="Entity type"),
    amount: float | None = Query(None),
    tenure_months: int | None = Query(None, alias="tenureMonths"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get eligible products based on criteria."""
    service = ProductService(db)
    products = await service.get_eligible_products(
        current_user.organization_id, entity_type, amount, tenure_months
    )
    return [LoanProductListResponse.model_validate(p) for p in products]


@router.post(
    "",
    response_model=LoanProductResponse,
    response_model_by_alias=True,
)
async def create_product(
    data: LoanProductCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new loan product."""
    data.organization_id = current_user.organization_id
    service = ProductService(db)
    product = await service.create_product(data, current_user.id)
    return LoanProductResponse.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=LoanProductResponse,
    response_model_by_alias=True,
)
async def get_product(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan product by ID."""
    service = ProductService(db)
    product = await service.get_product(current_user.organization_id, product_id)
    return LoanProductResponse.model_validate(product)


@router.get(
    "/{product_id}/details",
    response_model=LoanProductDetailResponse,
    response_model_by_alias=True,
)
async def get_product_details(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan product with fees and checklist."""
    service = ProductService(db)
    product = await service.get_product_with_details(current_user.organization_id, product_id)
    return LoanProductDetailResponse.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=LoanProductResponse,
    response_model_by_alias=True,
)
async def update_product(
    product_id: UUID,
    data: LoanProductUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a loan product."""
    service = ProductService(db)
    product = await service.update_product(
        current_user.organization_id, product_id, data, current_user.id
    )
    return LoanProductResponse.model_validate(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Soft delete a loan product."""
    service = ProductService(db)
    await service.delete_product(current_user.organization_id, product_id, current_user.id)
    return {"message": "Product deleted successfully"}


# =============================================================================
# Product Fee Endpoints
# =============================================================================


@router.get(
    "/{product_id}/fees",
    response_model=list[ProductFeeResponse],
    response_model_by_alias=True,
)
async def list_product_fees(
    product_id: UUID,
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all fees for a product."""
    service = ProductService(db)
    fees = await service.get_product_fees(
        current_user.organization_id, product_id, include_inactive
    )
    return [ProductFeeResponse.model_validate(f) for f in fees]


@router.post(
    "/{product_id}/fees",
    response_model=ProductFeeResponse,
    response_model_by_alias=True,
)
async def add_product_fee(
    product_id: UUID,
    data: ProductFeeCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a fee to a product."""
    data.product_id = product_id
    service = ProductService(db)
    fee = await service.add_product_fee(current_user.organization_id, data, current_user.id)
    return ProductFeeResponse.model_validate(fee)


@router.put(
    "/fees/{fee_id}",
    response_model=ProductFeeResponse,
    response_model_by_alias=True,
)
async def update_product_fee(
    fee_id: UUID,
    data: ProductFeeUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a product fee."""
    service = ProductService(db)
    fee = await service.update_product_fee(
        current_user.organization_id, fee_id, data, current_user.id
    )
    return ProductFeeResponse.model_validate(fee)


@router.delete("/fees/{fee_id}")
async def delete_product_fee(
    fee_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a product fee."""
    service = ProductService(db)
    await service.delete_product_fee(current_user.organization_id, fee_id, current_user.id)
    return {"message": "Product fee deleted successfully"}


# =============================================================================
# Document Checklist Endpoints
# =============================================================================


@router.get(
    "/{product_id}/checklist",
    response_model=list[DocumentChecklistResponse],
    response_model_by_alias=True,
)
async def list_document_checklist(
    product_id: UUID,
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get document checklist for a product."""
    service = ProductService(db)
    checklist = await service.get_product_checklist(
        current_user.organization_id, product_id, include_inactive
    )
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.get(
    "/{product_id}/checklist/by-stage",
    response_model=list[DocumentChecklistResponse],
    response_model_by_alias=True,
)
async def get_checklist_by_stage(
    product_id: UUID,
    stage: DocumentStage = Query(...),
    entity_type: str | None = Query(None, alias="entityType"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get document checklist for a specific stage."""
    service = ProductService(db)
    checklist = await service.get_checklist_by_stage(
        current_user.organization_id, product_id, stage, entity_type
    )
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.get(
    "/{product_id}/checklist/mandatory",
    response_model=list[DocumentChecklistResponse],
    response_model_by_alias=True,
)
async def get_mandatory_documents(
    product_id: UUID,
    stage: DocumentStage | None = Query(None),
    entity_type: str | None = Query(None, alias="entityType"),
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get mandatory documents for a product."""
    service = ProductService(db)
    checklist = await service.get_mandatory_documents(
        current_user.organization_id, product_id, stage, entity_type
    )
    return [DocumentChecklistResponse.model_validate(c) for c in checklist]


@router.post(
    "/{product_id}/checklist",
    response_model=DocumentChecklistResponse,
    response_model_by_alias=True,
)
async def add_document_checklist(
    product_id: UUID,
    data: DocumentChecklistCreate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a document to product checklist."""
    data.product_id = product_id
    service = ProductService(db)
    checklist = await service.add_document_checklist(
        current_user.organization_id, data, current_user.id
    )
    return DocumentChecklistResponse.model_validate(checklist)


@router.put(
    "/checklist/{checklist_id}",
    response_model=DocumentChecklistResponse,
    response_model_by_alias=True,
)
async def update_document_checklist(
    checklist_id: UUID,
    data: DocumentChecklistUpdate,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a document checklist item."""
    service = ProductService(db)
    checklist = await service.update_document_checklist(
        current_user.organization_id, checklist_id, data, current_user.id
    )
    return DocumentChecklistResponse.model_validate(checklist)


@router.delete("/checklist/{checklist_id}")
async def delete_document_checklist(
    checklist_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_PRODUCT_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a document checklist item."""
    service = ProductService(db)
    await service.delete_document_checklist(
        current_user.organization_id, checklist_id, current_user.id
    )
    return {"message": "Document checklist item deleted successfully"}
