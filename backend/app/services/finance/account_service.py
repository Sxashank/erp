"""Account service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.finance.account import Account
from app.repositories.finance.account_repo import AccountRepository
from app.repositories.finance.account_group_repo import AccountGroupRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.finance.account import AccountCreate, AccountUpdate
from app.core.constants import AccountType


class AccountService:
    """Service for account/ledger management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AccountRepository(session)
        self.group_repo = AccountGroupRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: AccountCreate,
        created_by: Optional[UUID] = None,
    ) -> Account:
        """Create a new account."""
        # Check if code exists in organization
        if await self.repo.code_exists(data.code, data.organization_id):
            raise ConflictException(f"Account code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Verify account group exists
        group = await self.group_repo.get(data.account_group_id)
        if not group:
            raise NotFoundException("Account group not found")
        if group.organization_id != data.organization_id:
            raise BadRequestException(
                "Account group must belong to the same organization"
            )

        # Validate control account settings
        if data.is_control_account and not data.control_type:
            raise BadRequestException(
                "Control type is required for control accounts"
            )

        # Validate bank account settings
        if data.is_bank_account:
            if not data.bank_name or not data.bank_account_number:
                raise BadRequestException(
                    "Bank name and account number are required for bank accounts"
                )

        account_data = data.model_dump()
        account_data["created_by"] = created_by

        return await self.repo.create(account_data)

    async def update(
        self,
        id: UUID,
        data: AccountUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Account:
        """Update an account."""
        account = await self.repo.get_with_group(id)
        if not account:
            raise NotFoundException("Account not found")

        if account.is_system:
            raise BadRequestException("Cannot update system-defined account")

        # Check code uniqueness if being updated
        if data.code and data.code != account.code:
            if await self.repo.code_exists(data.code, account.organization_id, exclude_id=id):
                raise ConflictException(f"Account code '{data.code}' already exists")

        # Validate account group if changing
        if data.account_group_id and data.account_group_id != account.account_group_id:
            group = await self.group_repo.get(data.account_group_id)
            if not group:
                raise NotFoundException("Account group not found")
            if group.organization_id != account.organization_id:
                raise BadRequestException(
                    "Account group must belong to the same organization"
                )

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(account, update_data)

    async def get(self, id: UUID) -> Account:
        """Get account by ID with group."""
        account = await self.repo.get_with_group(id)
        if not account:
            raise NotFoundException("Account not found")
        return account

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Account], int]:
        """Get all accounts for an organization."""
        accounts = await self.repo.get_by_organization(organization_id, include_inactive)
        total = len(accounts)
        return accounts[skip:skip + limit], total

    async def get_by_group(
        self,
        account_group_id: UUID,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get accounts by account group."""
        return await self.repo.get_by_group(account_group_id, include_inactive)

    async def get_by_type(
        self,
        organization_id: UUID,
        account_type: AccountType,
    ) -> List[Account]:
        """Get accounts by type."""
        return await self.repo.get_by_type(organization_id, account_type)

    async def get_bank_accounts(self, organization_id: UUID) -> List[Account]:
        """Get all bank accounts."""
        return await self.repo.get_bank_accounts(organization_id)

    async def get_cash_accounts(self, organization_id: UUID) -> List[Account]:
        """Get all cash accounts."""
        return await self.repo.get_cash_accounts(organization_id)

    async def search(
        self,
        organization_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[Account]:
        """Search accounts by code or name."""
        return await self.repo.search(organization_id, query, limit)

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Account:
        """Soft delete an account."""
        account = await self.repo.get(id)
        if not account:
            raise NotFoundException("Account not found")

        if account.is_system:
            raise BadRequestException("Cannot delete system-defined account")

        # TODO: Check if account has transactions

        return await self.repo.soft_delete(id, deleted_by)
