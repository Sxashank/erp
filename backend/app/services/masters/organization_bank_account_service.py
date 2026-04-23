"""Organization Bank Account service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException
from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.repositories.masters.organization_bank_account_repo import OrganizationBankAccountRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.masters.organization_bank_account import (
    OrganizationBankAccountCreate,
    OrganizationBankAccountUpdate,
)


class OrganizationBankAccountService:
    """Service for organization bank account management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OrganizationBankAccountRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: OrganizationBankAccountCreate,
        created_by: Optional[UUID] = None,
    ) -> OrganizationBankAccount:
        """Create a new bank account."""
        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Check if account number already exists for this organization
        if await self.repo.account_number_exists(data.organization_id, data.account_number):
            raise ConflictException(
                f"Account number '{data.account_number}' already exists for this organization"
            )

        # If this is set as primary, clear other primary flags
        if data.is_primary:
            await self.repo.clear_primary(data.organization_id)

        account_data = data.model_dump()
        account_data["created_by"] = created_by
        account_data["ifsc_code"] = data.ifsc_code.upper()
        account_data["account_type"] = data.account_type.upper()

        return await self.repo.create(account_data)

    async def update(
        self,
        account_id: UUID,
        data: OrganizationBankAccountUpdate,
        updated_by: Optional[UUID] = None,
    ) -> OrganizationBankAccount:
        """Update an existing bank account."""
        account = await self.repo.get(account_id)
        if not account:
            raise NotFoundException("Bank account not found")

        # If is_primary is being set to True, clear other primary flags
        if data.is_primary and not account.is_primary:
            await self.repo.clear_primary(account.organization_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(account, update_data)

    async def get(self, account_id: UUID) -> OrganizationBankAccount:
        """Get bank account by ID."""
        account = await self.repo.get(account_id)
        if not account:
            raise NotFoundException("Bank account not found")
        return account

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[OrganizationBankAccount]:
        """Get all bank accounts for an organization."""
        return await self.repo.get_by_organization(organization_id, include_inactive)

    async def get_primary(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationBankAccount]:
        """Get the primary bank account for an organization."""
        return await self.repo.get_primary(organization_id)

    async def delete(
        self,
        account_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> OrganizationBankAccount:
        """Soft delete a bank account."""
        account = await self.repo.get(account_id)
        if not account:
            raise NotFoundException("Bank account not found")

        return await self.repo.soft_delete(account_id, deleted_by)

    async def set_primary(
        self,
        account_id: UUID,
        updated_by: Optional[UUID] = None,
    ) -> OrganizationBankAccount:
        """Set a bank account as primary."""
        account = await self.repo.get(account_id)
        if not account:
            raise NotFoundException("Bank account not found")

        # Clear other primary flags
        await self.repo.clear_primary(account.organization_id)

        # Set this account as primary
        account.is_primary = True
        account.updated_by = updated_by
        await self.session.flush()
        await self.session.refresh(account)

        return account
