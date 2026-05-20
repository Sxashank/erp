"""Voucher API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.voucher_service import VoucherService
from app.schemas.finance.voucher import (
    VoucherCreate,
    VoucherUpdate,
    VoucherResponse,
    VoucherDetailResponse,
    VoucherLineResponse,
    VoucherApprovalRequest,
    VoucherRejectRequest,
    VoucherCancelRequest,
)
from app.schemas.base import PaginatedResponse, MessageResponse
from app.core.constants import VoucherStatus, VoucherClass

router = APIRouter()


@router.get("", response_model=PaginatedResponse[VoucherResponse], response_model_by_alias=True)
async def list_vouchers(
    status: Optional[VoucherStatus] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    voucher_class: Optional[VoucherClass] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of vouchers.
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = VoucherService(db)
    skip = (page - 1) * page_size

    if status:
        vouchers, total = await service.get_by_status(
            current_user.organization_id, status, skip, page_size
        )
    elif from_date and to_date:
        vouchers, total = await service.get_by_date_range(
            current_user.organization_id, from_date, to_date, voucher_class, skip, page_size
        )
    else:
        vouchers, total = await service.get_all(
            current_user.organization_id, skip, page_size, include_inactive
        )

    items = [_voucher_to_response(v) for v in vouchers]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=VoucherDetailResponse, response_model_by_alias=True)
async def create_voucher(
    data: VoucherCreate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new voucher.
    Requires FIN_VOUCHER_CREATE permission.
    """
    service = VoucherService(db)
    data = data.model_copy(update={"organization_id": current_user.organization_id})
    voucher = await service.create(data, current_user.id)

    # Reload with all relationships
    voucher = await service.get(voucher.id)

    return _voucher_to_detail_response(voucher)


@router.get("/pending-approval", response_model=List[VoucherResponse], response_model_by_alias=True)
async def list_pending_approval(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get vouchers pending approval.
    Requires FIN_VOUCHER_APPROVE permission.
    """
    service = VoucherService(db)
    skip = (page - 1) * page_size
    vouchers = await service.get_pending_approval(current_user.organization_id, skip, page_size)

    return [_voucher_to_response(v) for v in vouchers]


@router.get("/{voucher_id}", response_model=VoucherDetailResponse, response_model_by_alias=True)
async def get_voucher(
    voucher_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get voucher by ID with lines.
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = VoucherService(db)
    voucher = await service.get(voucher_id)

    return _voucher_to_detail_response(voucher)


@router.put("/{voucher_id}", response_model=VoucherDetailResponse, response_model_by_alias=True)
async def update_voucher(
    voucher_id: UUID,
    data: VoucherUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update a draft voucher.
    Requires FIN_VOUCHER_UPDATE permission.
    """
    service = VoucherService(db)
    voucher = await service.update(voucher_id, data, current_user.id)

    # Reload with all relationships
    voucher = await service.get(voucher.id)

    return _voucher_to_detail_response(voucher)


@router.post("/{voucher_id}/submit", response_model=VoucherResponse, response_model_by_alias=True)
async def submit_voucher(
    voucher_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Submit a voucher for approval.
    Requires FIN_VOUCHER_CREATE permission.
    """
    service = VoucherService(db)
    voucher = await service.submit_for_approval(voucher_id, current_user.id)

    return _voucher_to_response(voucher)


@router.post("/{voucher_id}/approve", response_model=VoucherResponse, response_model_by_alias=True)
async def approve_voucher(
    voucher_id: UUID,
    data: Optional[VoucherApprovalRequest] = None,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Approve a voucher.
    Requires FIN_VOUCHER_APPROVE permission.
    """
    service = VoucherService(db)
    remarks = data.remarks if data else None
    voucher = await service.approve(voucher_id, current_user.id, remarks)

    return _voucher_to_response(voucher)


@router.post("/{voucher_id}/reject", response_model=VoucherResponse, response_model_by_alias=True)
async def reject_voucher(
    voucher_id: UUID,
    data: VoucherRejectRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Reject a voucher.
    Requires FIN_VOUCHER_APPROVE permission.
    """
    service = VoucherService(db)
    voucher = await service.reject(voucher_id, current_user.id, data.reason)

    return _voucher_to_response(voucher)


@router.post("/{voucher_id}/post", response_model=VoucherResponse, response_model_by_alias=True)
async def post_voucher(
    voucher_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_POST")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Post an approved voucher to the ledger.
    Requires FIN_VOUCHER_POST permission.
    """
    service = VoucherService(db)
    voucher = await service.post(voucher_id, current_user.id)

    return _voucher_to_response(voucher)


@router.post("/{voucher_id}/cancel", response_model=VoucherResponse, response_model_by_alias=True)
async def cancel_voucher(
    voucher_id: UUID,
    data: VoucherCancelRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CANCEL")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Cancel a voucher.
    Requires FIN_VOUCHER_CANCEL permission.
    """
    service = VoucherService(db)
    voucher = await service.cancel(voucher_id, current_user.id, data.reason)

    return _voucher_to_response(voucher)


@router.delete("/{voucher_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_voucher(
    voucher_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a draft voucher.
    Requires FIN_VOUCHER_DELETE permission.
    """
    service = VoucherService(db)
    await service.delete(voucher_id, current_user.id)

    return MessageResponse(message="Voucher deleted successfully")


def _voucher_to_response(voucher) -> VoucherResponse:
    """Convert Voucher model to response."""
    return VoucherResponse(
        id=voucher.id,
        voucher_type_id=voucher.voucher_type_id,
        voucher_type_code=voucher.voucher_type.code if voucher.voucher_type else None,
        voucher_type_name=voucher.voucher_type.name if voucher.voucher_type else None,
        voucher_class=voucher.voucher_type.voucher_class if voucher.voucher_type else None,
        voucher_number=voucher.voucher_number,
        voucher_date=voucher.voucher_date,
        financial_year_id=voucher.financial_year_id,
        financial_year_code=voucher.financial_year.code if voucher.financial_year else None,
        period_id=voucher.period_id,
        reference_number=voucher.reference_number,
        narration=voucher.narration,
        total_debit=voucher.total_debit,
        total_credit=voucher.total_credit,
        status=voucher.status,
        organization_id=voucher.organization_id,
        unit_id=voucher.unit_id,
        unit_name=voucher.unit.name if voucher.unit else None,
        created_at=voucher.created_at,
        updated_at=voucher.updated_at,
        is_active=voucher.is_active,
    )


def _voucher_to_detail_response(voucher) -> VoucherDetailResponse:
    """Convert Voucher model to detail response with lines."""
    return VoucherDetailResponse(
        id=voucher.id,
        voucher_type_id=voucher.voucher_type_id,
        voucher_type_code=voucher.voucher_type.code if voucher.voucher_type else None,
        voucher_type_name=voucher.voucher_type.name if voucher.voucher_type else None,
        voucher_class=voucher.voucher_type.voucher_class if voucher.voucher_type else None,
        voucher_number=voucher.voucher_number,
        voucher_date=voucher.voucher_date,
        financial_year_id=voucher.financial_year_id,
        financial_year_code=voucher.financial_year.code if voucher.financial_year else None,
        period_id=voucher.period_id,
        reference_number=voucher.reference_number,
        reference_date=voucher.reference_date,
        narration=voucher.narration,
        total_debit=voucher.total_debit,
        total_credit=voucher.total_credit,
        status=voucher.status,
        approval_status=voucher.approval_status,
        current_approval_level=voucher.current_approval_level,
        submitted_at=voucher.submitted_at,
        approved_at=voucher.approved_at,
        posted_at=voucher.posted_at,
        cancelled_at=voucher.cancelled_at,
        cancellation_reason=voucher.cancellation_reason,
        rejection_reason=voucher.rejection_reason,
        is_reversed=voucher.is_reversed,
        reversal_voucher_id=voucher.reversal_voucher_id,
        original_voucher_id=voucher.original_voucher_id,
        organization_id=voucher.organization_id,
        unit_id=voucher.unit_id,
        unit_name=voucher.unit.name if voucher.unit else None,
        created_at=voucher.created_at,
        updated_at=voucher.updated_at,
        is_active=voucher.is_active,
        lines=[
            VoucherLineResponse(
                id=line.id,
                line_number=line.line_number,
                account_id=line.account_id,
                account_code=line.account.code if line.account else None,
                account_name=line.account.name if line.account else None,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                narration=line.narration,
                cost_center_id=line.cost_center_id,
                party_type=line.party_type,
                party_id=line.party_id,
                reference_type=line.reference_type,
                reference_id=line.reference_id,
                reference_number=line.reference_number,
                cheque_number=line.cheque_number,
                cheque_date=line.cheque_date,
            )
            for line in voucher.lines
        ],
    )
