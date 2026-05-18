"""Stock API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.models.inventory.stock import TransactionType, TransactionStatus
from app.schemas.inventory.stock import (
    StockBalanceResponse,
    StockTransactionResponse,
    StockInCreate,
    StockOutCreate,
    StockTransferCreate,
    StockAdjustmentCreate,
)
from app.schemas.base import MessageResponse
from app.services.inventory.stock_service import StockService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _to_balance_response(balance) -> StockBalanceResponse:
    """Convert balance model to response schema."""
    return StockBalanceResponse(
        id=balance.id,
        organization_id=balance.organization_id,
        item_id=balance.item_id,
        item_code=balance.item.item_code if balance.item else None,
        item_name=balance.item.item_name if balance.item else None,
        warehouse_id=balance.warehouse_id,
        warehouse_code=balance.warehouse.warehouse_code if balance.warehouse else None,
        warehouse_name=balance.warehouse.warehouse_name if balance.warehouse else None,
        quantity_on_hand=balance.quantity_on_hand,
        quantity_reserved=balance.quantity_reserved,
        quantity_in_transit=balance.quantity_in_transit,
        available_quantity=balance.available_quantity,
        average_cost=balance.average_cost,
        total_value=balance.total_value,
        last_transaction_date=balance.last_transaction_date,
        is_active=balance.is_active,
        created_at=balance.created_at,
        updated_at=balance.updated_at,
        created_by=balance.created_by,
        updated_by=balance.updated_by,
    )


def _to_transaction_response(txn) -> StockTransactionResponse:
    """Convert transaction model to response schema."""
    return StockTransactionResponse(
        id=txn.id,
        organization_id=txn.organization_id,
        transaction_number=txn.transaction_number,
        transaction_type=txn.transaction_type,
        transaction_date=txn.transaction_date,
        status=txn.status,
        item_id=txn.item_id,
        item_code=txn.item.item_code if txn.item else None,
        item_name=txn.item.item_name if txn.item else None,
        warehouse_id=txn.warehouse_id,
        warehouse_code=txn.warehouse.warehouse_code if txn.warehouse else None,
        warehouse_name=txn.warehouse.warehouse_name if txn.warehouse else None,
        to_warehouse_id=txn.to_warehouse_id,
        to_warehouse_code=txn.to_warehouse.warehouse_code if txn.to_warehouse else None,
        to_warehouse_name=txn.to_warehouse.warehouse_name if txn.to_warehouse else None,
        quantity=txn.quantity,
        unit_cost=txn.unit_cost,
        total_cost=txn.total_cost,
        balance_before=txn.balance_before,
        balance_after=txn.balance_after,
        batch_number=txn.batch_number,
        serial_number=txn.serial_number,
        expiry_date=txn.expiry_date,
        reference_type=txn.reference_type,
        reference_id=txn.reference_id,
        reference_number=txn.reference_number,
        remarks=txn.remarks,
        approved_by=txn.approved_by,
        approved_at=txn.approved_at,
        rejection_reason=txn.rejection_reason,
        is_active=txn.is_active,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
        created_by=txn.created_by,
        updated_by=txn.updated_by,
    )


# ==========================================
# Stock Balance Endpoints
# ==========================================

@router.get("/balances", response_model=dict, response_model_by_alias=True)
async def list_stock_balances(
    request: Request,
    organization_id: UUID,
    warehouse_id: Optional[UUID] = None,
    item_id: Optional[UUID] = None,
    low_stock_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """List stock balances."""
    service = StockService(db)
    items = await service.list_balances(
        organization_id, warehouse_id, item_id, low_stock_only, skip, limit
    )
    total = await service.count_balances(organization_id, warehouse_id, item_id)

    return {
        "items": [_to_balance_response(bal) for bal in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/balances/{item_id}/{warehouse_id}", response_model=StockBalanceResponse, response_model_by_alias=True)
async def get_stock_balance(
    request: Request,
    item_id: UUID,
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """Get stock balance for item in warehouse."""
    service = StockService(db)
    balance = await service.get_balance(item_id, warehouse_id)
    if not balance:
        raise NotFoundException(detail="Stock balance not found", error_code="STOCK_BALANCE_NOT_FOUND")
    return _to_balance_response(balance)


# ==========================================
# Stock Transaction Endpoints
# ==========================================

@router.get("/transactions", response_model=dict, response_model_by_alias=True)
async def list_transactions(
    request: Request,
    organization_id: UUID,
    warehouse_id: Optional[UUID] = None,
    item_id: Optional[UUID] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """List stock transactions."""
    service = StockService(db)
    items = await service.list_transactions(
        organization_id, warehouse_id, item_id, transaction_type, status,
        from_date, to_date, skip, limit
    )
    total = await service.count_transactions(
        organization_id, warehouse_id, item_id, transaction_type, status
    )

    return {
        "items": [_to_transaction_response(txn) for txn in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/transactions/{id}", response_model=StockTransactionResponse, response_model_by_alias=True)
async def get_transaction(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_VIEW])),
):
    """Get transaction by ID."""
    service = StockService(db)
    txn = await service.get_transaction(id)
    if not txn:
        raise NotFoundException(detail="Transaction not found", error_code="TRANSACTION_NOT_FOUND")
    return _to_transaction_response(txn)


# ==========================================
# Stock In Endpoints
# ==========================================

@router.post("/in", response_model=StockTransactionResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_stock_in(
    request: Request,
    data: StockInCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_IN])),
):
    """Create stock in transaction."""
    service = StockService(db)
    try:
        txn = await service.create_stock_in(data, created_by=current_user.id)
        return _to_transaction_response(txn)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ==========================================
# Stock Out Endpoints
# ==========================================

@router.post("/out", response_model=StockTransactionResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_stock_out(
    request: Request,
    data: StockOutCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_OUT])),
):
    """Create stock out transaction."""
    service = StockService(db)
    try:
        txn = await service.create_stock_out(data, created_by=current_user.id)
        return _to_transaction_response(txn)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ==========================================
# Stock Transfer Endpoints
# ==========================================

@router.post("/transfer", response_model=dict, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_stock_transfer(
    request: Request,
    data: StockTransferCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_TRANSFER])),
):
    """Create stock transfer between warehouses."""
    service = StockService(db)
    try:
        transfer_out, transfer_in = await service.create_stock_transfer(
            data, created_by=current_user.id
        )
        return {
            "transfer_out": _to_transaction_response(transfer_out),
            "transfer_in": _to_transaction_response(transfer_in),
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ==========================================
# Stock Adjustment Endpoints
# ==========================================

@router.post("/adjustment", response_model=StockTransactionResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_stock_adjustment(
    request: Request,
    data: StockAdjustmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_ADJUST])),
):
    """Create stock adjustment."""
    service = StockService(db)
    try:
        txn = await service.create_stock_adjustment(data, created_by=current_user.id)
        return _to_transaction_response(txn)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ==========================================
# Approval Endpoints
# ==========================================

@router.post("/transactions/{id}/approve", response_model=StockTransactionResponse, response_model_by_alias=True)
async def approve_transaction(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_APPROVE])),
):
    """Approve a pending transaction."""
    service = StockService(db)
    try:
        txn = await service.approve_transaction(id, approved_by=current_user.id)
        return _to_transaction_response(txn)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post("/transactions/{id}/reject", response_model=StockTransactionResponse, response_model_by_alias=True)
async def reject_transaction(
    request: Request,
    id: UUID,
    rejection_reason: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.INV_STOCK_APPROVE])),
):
    """Reject a pending transaction."""
    service = StockService(db)
    try:
        txn = await service.reject_transaction(
            id, rejected_by=current_user.id, rejection_reason=rejection_reason
        )
        return _to_transaction_response(txn)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
