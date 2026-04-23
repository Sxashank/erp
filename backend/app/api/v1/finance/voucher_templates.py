"""Voucher Template API endpoints."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_current_user
from app.models.auth.user import User
from app.services.finance.template_service import VoucherTemplateService
from app.schemas.finance.voucher_template import (
    VoucherTemplateCreate,
    VoucherTemplateUpdate,
    VoucherTemplateResponse,
    VoucherTemplateListResponse,
    UseTemplateRequest,
    UseTemplateResponse,
    TemplateCategory,
    VoucherTemplateStats,
)

router = APIRouter()


@router.get(
    "",
    response_model=VoucherTemplateListResponse,
)
async def list_voucher_templates(
    organization_id: UUID,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """List voucher templates."""
    service = VoucherTemplateService(db)
    return await service.list(
        organization_id=organization_id,
        category=category,
        is_active=is_active,
        is_favorite=is_favorite,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/categories",
    response_model=list[TemplateCategory],
)
async def get_template_categories(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all unique template categories."""
    service = VoucherTemplateService(db)
    return await service.get_categories(organization_id)


@router.get(
    "/stats",
    response_model=VoucherTemplateStats,
)
async def get_template_stats(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for voucher templates."""
    service = VoucherTemplateService(db)
    return await service.get_stats(organization_id)


@router.get(
    "/{template_id}",
    response_model=VoucherTemplateResponse,
)
async def get_voucher_template(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a voucher template by ID."""
    service = VoucherTemplateService(db)
    result = await service.get_with_lines(template_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voucher template {template_id} not found",
        )
    return result


@router.post(
    "",
    response_model=VoucherTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voucher_template(
    data: VoucherTemplateCreate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new voucher template."""
    service = VoucherTemplateService(db)
    try:
        template = await service.create(data, current_user.id)
        await db.commit()
        return await service.get_with_lines(template.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{template_id}",
    response_model=VoucherTemplateResponse,
)
async def update_voucher_template(
    template_id: UUID,
    data: VoucherTemplateUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a voucher template."""
    service = VoucherTemplateService(db)
    try:
        template = await service.update(template_id, data, current_user.id)
        await db.commit()
        return await service.get_with_lines(template.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_voucher_template(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete (soft) a voucher template."""
    service = VoucherTemplateService(db)
    success = await service.delete(template_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voucher template {template_id} not found",
        )
    await db.commit()


@router.post(
    "/{template_id}/toggle-favorite",
    response_model=VoucherTemplateResponse,
)
async def toggle_template_favorite(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite status of a template."""
    service = VoucherTemplateService(db)
    try:
        await service.toggle_favorite(template_id, current_user.id)
        await db.commit()
        return await service.get_with_lines(template_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{template_id}/use",
    response_model=UseTemplateResponse,
)
async def use_voucher_template(
    template_id: UUID,
    request: UseTemplateRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a voucher from a template."""
    service = VoucherTemplateService(db)
    try:
        voucher_date = datetime.strptime(request.voucher_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    result = await service.use_template(
        template_id,
        current_user.id,
        voucher_date,
        request.narration_override,
        request.amount_multiplier,
    )
    if result.success:
        await db.commit()
    return result


@router.post(
    "/{template_id}/duplicate",
    response_model=VoucherTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_voucher_template(
    template_id: UUID,
    new_name: Optional[str] = Query(None),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Duplicate an existing template."""
    service = VoucherTemplateService(db)
    try:
        template = await service.duplicate(template_id, current_user.id, new_name)
        await db.commit()
        return await service.get_with_lines(template.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
