"""Payment Terms API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.ap_ar.payment_terms_service import PaymentTermsService
from app.schemas.ap_ar.payment_terms import (
    PaymentTermsCreate,
    PaymentTermsUpdate,
    PaymentTermsResponse,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_response(terms) -> PaymentTermsResponse:
    """Convert model to response."""
    return PaymentTermsResponse(
        id=terms.id,
        code=terms.code,
        name=terms.name,
        description=terms.description,
        days=terms.days,
        discount_days=terms.discount_days,
        discount_percent=terms.discount_percent,
        organization_id=terms.organization_id,
        created_at=terms.created_at,
        updated_at=terms.updated_at,
        is_active=terms.is_active,
    )


@router.get("", response_model=PaginatedResponse[PaymentTermsResponse], response_model_by_alias=True)
async def list_payment_terms(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("APAR_TERMS_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of payment terms for an organization."""
    service = PaymentTermsService(db)
    skip = (page - 1) * page_size
    terms_list, total = await service.get_all(
        current_user.organization_id, skip, page_size, include_inactive
    )
    items = [_to_response(t) for t in terms_list]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/active", response_model=list[PaymentTermsResponse], response_model_by_alias=True)
async def list_active_payment_terms(
    current_user: User = Depends(RequirePermissions("APAR_TERMS_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get active payment terms for dropdown lists."""
    service = PaymentTermsService(db)
    terms_list = await service.get_active(current_user.organization_id)
    return [_to_response(t) for t in terms_list]


@router.post("", response_model=PaymentTermsResponse, response_model_by_alias=True)
async def create_payment_terms(
    data: PaymentTermsCreate,
    current_user: User = Depends(RequirePermissions("APAR_TERMS_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create new payment terms."""
    service = PaymentTermsService(db)
    terms = await service.create(data, current_user.id)
    return _to_response(terms)


@router.get("/{terms_id}", response_model=PaymentTermsResponse, response_model_by_alias=True)
async def get_payment_terms(
    terms_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_TERMS_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get payment terms by ID."""
    service = PaymentTermsService(db)
    terms = await service.get(terms_id)
    return _to_response(terms)


@router.put("/{terms_id}", response_model=PaymentTermsResponse, response_model_by_alias=True)
async def update_payment_terms(
    terms_id: UUID,
    data: PaymentTermsUpdate,
    current_user: User = Depends(RequirePermissions("APAR_TERMS_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update payment terms."""
    service = PaymentTermsService(db)
    terms = await service.update(terms_id, data, current_user.id)
    return _to_response(terms)


@router.delete("/{terms_id}")
async def delete_payment_terms(
    terms_id: UUID,
    current_user: User = Depends(RequirePermissions("APAR_TERMS_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete payment terms."""
    service = PaymentTermsService(db)
    await service.delete(terms_id, current_user.id)
    return {"message": "Payment terms deleted successfully"}
