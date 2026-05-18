"""Account API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.account_service import AccountService
from app.schemas.finance.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse
from app.core.constants import AccountType

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AccountResponse], response_model_by_alias=True)
async def list_accounts(
    account_group_id: Optional[UUID] = Query(None),
    account_type: Optional[AccountType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of accounts.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountService(db)
    skip = (page - 1) * page_size

    if account_group_id:
        accounts = await service.get_by_group(account_group_id, include_inactive)
        total = len(accounts)
        accounts = accounts[skip:skip + page_size]
    elif account_type:
        accounts = await service.get_by_type(current_user.organization_id, account_type)
        total = len(accounts)
        accounts = accounts[skip:skip + page_size]
    else:
        accounts, total = await service.get_all(
            current_user.organization_id, skip, page_size, include_inactive
        )

    items = [_account_to_response(a) for a in accounts]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=AccountResponse, response_model_by_alias=True)
async def create_account(
    data: AccountCreate,
    current_user: User = Depends(RequirePermissions("FIN_COA_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new account.
    Requires FIN_COA_CREATE permission.
    """
    service = AccountService(db)
    account = await service.create(data, current_user.id)

    return _account_to_response(account)


@router.get("/search", response_model=List[AccountResponse], response_model_by_alias=True)
async def search_accounts(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Search accounts by code or name.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountService(db)
    accounts = await service.search(current_user.organization_id, q, limit)

    return [_account_to_response(a) for a in accounts]


@router.get("/banks", response_model=List[AccountResponse], response_model_by_alias=True)
async def get_bank_accounts(
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all bank accounts.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountService(db)
    accounts = await service.get_bank_accounts(current_user.organization_id)

    return [_account_to_response(a) for a in accounts]


@router.get("/cash", response_model=List[AccountResponse], response_model_by_alias=True)
async def get_cash_accounts(
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all cash accounts.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountService(db)
    accounts = await service.get_cash_accounts(current_user.organization_id)

    return [_account_to_response(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountResponse, response_model_by_alias=True)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get account by ID.
    Requires FIN_COA_VIEW permission.
    """
    service = AccountService(db)
    account = await service.get(account_id)

    return _account_to_response(account)


@router.put("/{account_id}", response_model=AccountResponse, response_model_by_alias=True)
async def update_account(
    account_id: UUID,
    data: AccountUpdate,
    current_user: User = Depends(RequirePermissions("FIN_COA_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an account.
    Requires FIN_COA_UPDATE permission.
    """
    service = AccountService(db)
    account = await service.update(account_id, data, current_user.id)

    return _account_to_response(account)


@router.delete("/{account_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_account(
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_COA_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete an account.
    Requires FIN_COA_DELETE permission.
    """
    service = AccountService(db)
    await service.delete(account_id, current_user.id)

    return MessageResponse(message="Account deleted successfully")


def _account_to_response(account) -> AccountResponse:
    """Convert Account model to response."""
    return AccountResponse(
        id=account.id,
        code=account.code,
        name=account.name,
        account_group_id=account.account_group_id,
        account_group_name=account.account_group.name if account.account_group else None,
        account_group_nature=account.account_group.nature.value if account.account_group else None,
        account_type=account.account_type,
        is_control_account=account.is_control_account,
        control_type=account.control_type,
        currency_code=account.currency_code,
        opening_balance=account.opening_balance,
        opening_balance_type=account.opening_balance_type,
        current_balance=account.current_balance,
        current_balance_type=account.current_balance_type,
        description=account.description,
        gstin=account.gstin,
        pan=account.pan,
        tds_applicable=account.tds_applicable,
        tds_section=account.tds_section,
        is_bank_account=account.is_bank_account,
        bank_name=account.bank_name,
        bank_account_number=account.bank_account_number,
        bank_ifsc_code=account.bank_ifsc_code,
        bank_branch=account.bank_branch,
        is_cash_account=account.is_cash_account,
        allow_negative_balance=account.allow_negative_balance,
        is_reconciliation_required=account.is_reconciliation_required,
        is_system=account.is_system,
        organization_id=account.organization_id,
        created_at=account.created_at,
        updated_at=account.updated_at,
        is_active=account.is_active,
    )
