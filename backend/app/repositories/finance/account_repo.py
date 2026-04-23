"""Account repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.finance.account import Account
from app.core.constants import AccountType, ControlAccountType


class AccountRepository(BaseRepository[Account]):
    """Repository for Account operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Account, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get all accounts for an organization."""
        query = (
            select(Account)
            .options(selectinload(Account.account_group))
            .where(Account.organization_id == organization_id)
        )
        if not include_inactive:
            query = query.where(Account.is_active == True)
        query = query.order_by(Account.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_group(
        self,
        account_group_id: UUID,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get all accounts in an account group."""
        query = (
            select(Account)
            .where(Account.account_group_id == account_group_id)
        )
        if not include_inactive:
            query = query.where(Account.is_active == True)
        query = query.order_by(Account.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        organization_id: UUID,
        account_type: AccountType,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get accounts by type (BANK, CASH, etc.)."""
        query = (
            select(Account)
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.account_type == account_type,
                )
            )
        )
        if not include_inactive:
            query = query.where(Account.is_active == True)
        query = query.order_by(Account.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_bank_accounts(
        self,
        organization_id: UUID,
    ) -> List[Account]:
        """Get all bank accounts."""
        query = (
            select(Account)
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.is_bank_account == True,
                    Account.is_active == True,
                )
            )
            .order_by(Account.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_cash_accounts(
        self,
        organization_id: UUID,
    ) -> List[Account]:
        """Get all cash accounts."""
        query = (
            select(Account)
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.is_cash_account == True,
                    Account.is_active == True,
                )
            )
            .order_by(Account.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_control_accounts(
        self,
        organization_id: UUID,
        control_type: Optional[ControlAccountType] = None,
    ) -> List[Account]:
        """Get control accounts, optionally filtered by type."""
        query = select(Account).where(
            and_(
                Account.organization_id == organization_id,
                Account.is_control_account == True,
                Account.is_active == True,
            )
        )
        if control_type:
            query = query.where(Account.control_type == control_type)
        query = query.order_by(Account.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_group(self, id: UUID) -> Optional[Account]:
        """Get account with group loaded."""
        query = (
            select(Account)
            .options(selectinload(Account.account_group))
            .where(
                and_(
                    Account.id == id,
                    Account.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def code_exists(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if an account code exists in the organization."""
        query = select(Account.id).where(
            and_(
                Account.code == code,
                Account.organization_id == organization_id,
                Account.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(Account.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> Optional[Account]:
        """Get account by code within an organization."""
        query = (
            select(Account)
            .options(selectinload(Account.account_group))
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.code == code,
                    Account.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        organization_id: UUID,
        query_str: str,
        limit: int = 20,
    ) -> List[Account]:
        """Search accounts by code or name."""
        query = (
            select(Account)
            .options(selectinload(Account.account_group))
            .where(
                and_(
                    Account.organization_id == organization_id,
                    Account.is_active == True,
                    (
                        Account.code.ilike(f"%{query_str}%")
                        | Account.name.ilike(f"%{query_str}%")
                    ),
                )
            )
            .order_by(Account.code)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
