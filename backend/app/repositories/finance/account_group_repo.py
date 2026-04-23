"""Account Group repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.finance.account_group import AccountGroup
from app.models.finance.account import Account


class AccountGroupRepository(BaseRepository[AccountGroup]):
    """Repository for Account Group operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AccountGroup, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[AccountGroup]:
        """Get all account groups for an organization."""
        query = select(AccountGroup).where(
            AccountGroup.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(AccountGroup.is_active == True)
        query = query.order_by(AccountGroup.sequence, AccountGroup.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_root_groups(
        self,
        organization_id: UUID,
    ) -> List[AccountGroup]:
        """Get root account groups (no parent) for an organization."""
        query = (
            select(AccountGroup)
            .where(
                and_(
                    AccountGroup.organization_id == organization_id,
                    AccountGroup.parent_group_id == None,
                    AccountGroup.is_active == True,
                )
            )
            .order_by(AccountGroup.sequence, AccountGroup.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_children(self, id: UUID) -> Optional[AccountGroup]:
        """Get account group with child groups loaded."""
        query = (
            select(AccountGroup)
            .options(selectinload(AccountGroup.child_groups))
            .where(
                and_(
                    AccountGroup.id == id,
                    AccountGroup.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_children(self, parent_id: UUID) -> List[AccountGroup]:
        """Get child account groups."""
        query = (
            select(AccountGroup)
            .where(
                and_(
                    AccountGroup.parent_group_id == parent_id,
                    AccountGroup.is_active == True,
                )
            )
            .order_by(AccountGroup.sequence, AccountGroup.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def code_exists(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if an account group code exists in the organization."""
        query = select(AccountGroup.id).where(
            and_(
                AccountGroup.code == code,
                AccountGroup.organization_id == organization_id,
                AccountGroup.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(AccountGroup.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def has_children(self, id: UUID) -> bool:
        """Check if account group has child groups."""
        query = select(func.count(AccountGroup.id)).where(
            and_(
                AccountGroup.parent_group_id == id,
                AccountGroup.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

    async def has_accounts(self, id: UUID) -> bool:
        """Check if account group has accounts."""
        query = select(func.count(Account.id)).where(
            and_(
                Account.account_group_id == id,
                Account.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

    async def get_account_count(self, id: UUID) -> int:
        """Get count of accounts in the group."""
        query = select(func.count(Account.id)).where(
            and_(
                Account.account_group_id == id,
                Account.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update_hierarchy(self, group: AccountGroup) -> None:
        """Update level and path based on parent."""
        if group.parent_group_id:
            parent = await self.get(group.parent_group_id)
            if parent:
                group.level = parent.level + 1
                group.path = f"{parent.path or ''}/{parent.id}"
        else:
            group.level = 0
            group.path = None
        await self.session.flush()
