"""Organization Bank Account repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.repositories.base import BaseRepository


class OrganizationBankAccountRepository(BaseRepository[OrganizationBankAccount]):
    """Repository for Organization Bank Account operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(OrganizationBankAccount, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[OrganizationBankAccount]:
        """Get all bank accounts for an organization."""
        query = select(OrganizationBankAccount).where(
            OrganizationBankAccount.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(OrganizationBankAccount.is_active == True)
        query = query.order_by(OrganizationBankAccount.is_primary.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_primary(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationBankAccount]:
        """Get the primary bank account for an organization."""
        query = select(OrganizationBankAccount).where(
            and_(
                OrganizationBankAccount.organization_id == organization_id,
                OrganizationBankAccount.is_primary == True,
                OrganizationBankAccount.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def account_number_exists(
        self,
        organization_id: UUID,
        account_number: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if account number already exists for the organization."""
        query = select(OrganizationBankAccount.id).where(
            and_(
                OrganizationBankAccount.organization_id == organization_id,
                OrganizationBankAccount.account_number == account_number,
            )
        )
        if exclude_id:
            query = query.where(OrganizationBankAccount.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def clear_primary(self, organization_id: UUID) -> None:
        """Clear primary flag from all accounts of an organization."""
        accounts = await self.get_by_organization(organization_id)
        for account in accounts:
            if account.is_primary:
                account.is_primary = False
        await self.session.flush()
