"""Organization Bank Account API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.masters.organization_bank_account_service import OrganizationBankAccountService
from app.schemas.masters.organization_bank_account import (
    OrganizationBankAccountCreate,
    OrganizationBankAccountUpdate,
    OrganizationBankAccountResponse,
)
from app.schemas.base import MessageResponse

router = APIRouter()


def _to_response(account) -> OrganizationBankAccountResponse:
    """Convert model to response schema."""
    return OrganizationBankAccountResponse(
        id=account.id,
        organization_id=account.organization_id,
        account_name=account.account_name,
        account_number=account.account_number,
        ifsc_code=account.ifsc_code,
        bank_name=account.bank_name,
        branch_name=account.branch_name,
        branch_address=account.branch_address,
        micr_code=account.micr_code,
        swift_code=account.swift_code,
        account_type=account.account_type,
        ledger_account_id=account.ledger_account_id,
        sanctioned_limit=account.sanctioned_limit,
        drawing_power=account.drawing_power,
        is_primary=account.is_primary,
        allow_payments=account.allow_payments,
        allow_receipts=account.allow_receipts,
        created_at=account.created_at,
        updated_at=account.updated_at,
        is_active=account.is_active,
    )


@router.get("/{org_id}/bank-accounts", response_model=List[OrganizationBankAccountResponse], response_model_by_alias=True)
async def list_organization_bank_accounts(
    org_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all bank accounts for an organization.
    Requires MASTER_ORG_VIEW permission.
    """
    service = OrganizationBankAccountService(db)
    accounts = await service.get_by_organization(org_id, include_inactive)
    return [_to_response(a) for a in accounts]


@router.post("/{org_id}/bank-accounts", response_model=OrganizationBankAccountResponse, response_model_by_alias=True)
async def create_organization_bank_account(
    org_id: UUID,
    data: OrganizationBankAccountCreate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_BANK_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new bank account for an organization.
    Requires MASTER_ORG_BANK_CREATE permission.
    """
    # Override organization_id from path
    data.organization_id = org_id
    service = OrganizationBankAccountService(db)
    account = await service.create(data, current_user.id)
    return _to_response(account)


@router.get("/{org_id}/bank-accounts/{account_id}", response_model=OrganizationBankAccountResponse, response_model_by_alias=True)
async def get_organization_bank_account(
    org_id: UUID,
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get a specific bank account.
    Requires MASTER_ORG_VIEW permission.
    """
    service = OrganizationBankAccountService(db)
    account = await service.get(account_id)
    return _to_response(account)


@router.put("/{org_id}/bank-accounts/{account_id}", response_model=OrganizationBankAccountResponse, response_model_by_alias=True)
async def update_organization_bank_account(
    org_id: UUID,
    account_id: UUID,
    data: OrganizationBankAccountUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_BANK_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing bank account.
    Requires MASTER_ORG_BANK_UPDATE permission.
    """
    service = OrganizationBankAccountService(db)
    account = await service.update(account_id, data, current_user.id)
    return _to_response(account)


@router.delete("/{org_id}/bank-accounts/{account_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_organization_bank_account(
    org_id: UUID,
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_BANK_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a bank account.
    Requires MASTER_ORG_BANK_DELETE permission.
    """
    service = OrganizationBankAccountService(db)
    await service.delete(account_id, current_user.id)
    return MessageResponse(message="Bank account deleted successfully")


@router.post("/{org_id}/bank-accounts/{account_id}/set-primary", response_model=OrganizationBankAccountResponse, response_model_by_alias=True)
async def set_primary_bank_account(
    org_id: UUID,
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_BANK_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Set a bank account as primary.
    Requires MASTER_ORG_BANK_UPDATE permission.
    """
    service = OrganizationBankAccountService(db)
    account = await service.set_primary(account_id, current_user.id)
    return _to_response(account)
