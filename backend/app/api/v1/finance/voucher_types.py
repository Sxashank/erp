"""Voucher Type API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.finance.voucher_type_service import VoucherTypeService
from app.schemas.finance.voucher_type import (
    VoucherTypeCreate,
    VoucherTypeUpdate,
    VoucherTypeResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse
from app.core.constants import VoucherClass

router = APIRouter()


@router.get("", response_model=PaginatedResponse[VoucherTypeResponse])
async def list_voucher_types(
    organization_id: UUID = Query(...),
    voucher_class: Optional[VoucherClass] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_VTYPE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of voucher types.
    Requires FIN_VTYPE_VIEW permission.
    """
    service = VoucherTypeService(db)
    skip = (page - 1) * page_size

    if voucher_class:
        vtypes = await service.get_by_class(organization_id, voucher_class)
        total = len(vtypes)
        vtypes = vtypes[skip:skip + page_size]
    else:
        vtypes, total = await service.get_all(
            organization_id, skip, page_size, include_inactive
        )

    items = [_vtype_to_response(v) for v in vtypes]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=VoucherTypeResponse)
async def create_voucher_type(
    data: VoucherTypeCreate,
    current_user: User = Depends(RequirePermissions("FIN_VTYPE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new voucher type.
    Requires FIN_VTYPE_CREATE permission.
    """
    service = VoucherTypeService(db)
    vtype = await service.create(data, current_user.id)

    return _vtype_to_response(vtype)


@router.get("/{vtype_id}", response_model=VoucherTypeResponse)
async def get_voucher_type(
    vtype_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VTYPE_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get voucher type by ID.
    Requires FIN_VTYPE_VIEW permission.
    """
    service = VoucherTypeService(db)
    vtype = await service.get(vtype_id)

    return _vtype_to_response(vtype)


@router.put("/{vtype_id}", response_model=VoucherTypeResponse)
async def update_voucher_type(
    vtype_id: UUID,
    data: VoucherTypeUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VTYPE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a voucher type.
    Requires FIN_VTYPE_UPDATE permission.
    """
    service = VoucherTypeService(db)
    vtype = await service.update(vtype_id, data, current_user.id)

    return _vtype_to_response(vtype)


@router.delete("/{vtype_id}", response_model=MessageResponse)
async def delete_voucher_type(
    vtype_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VTYPE_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a voucher type.
    Requires FIN_VTYPE_DELETE permission.
    """
    service = VoucherTypeService(db)
    await service.delete(vtype_id, current_user.id)

    return MessageResponse(message="Voucher type deleted successfully")


def _vtype_to_response(vtype) -> VoucherTypeResponse:
    """Convert VoucherType model to response."""
    return VoucherTypeResponse(
        id=vtype.id,
        code=vtype.code,
        name=vtype.name,
        voucher_class=vtype.voucher_class,
        prefix=vtype.prefix,
        auto_numbering=vtype.auto_numbering,
        starting_number=vtype.starting_number,
        current_number=vtype.current_number,
        number_format=vtype.number_format,
        requires_approval=vtype.requires_approval,
        approval_levels=vtype.approval_levels,
        default_narration=vtype.default_narration,
        description=vtype.description,
        is_system=vtype.is_system,
        organization_id=vtype.organization_id,
        created_at=vtype.created_at,
        updated_at=vtype.updated_at,
        is_active=vtype.is_active,
    )
