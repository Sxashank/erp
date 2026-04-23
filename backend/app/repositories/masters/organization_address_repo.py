"""Organization Address repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.masters.organization_address import OrganizationAddress
from app.repositories.base import BaseRepository


class OrganizationAddressRepository(BaseRepository[OrganizationAddress]):
    """Repository for Organization Address operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(OrganizationAddress, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[OrganizationAddress]:
        """Get all addresses for an organization."""
        query = select(OrganizationAddress).where(
            OrganizationAddress.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(OrganizationAddress.is_active == True)
        query = query.order_by(OrganizationAddress.is_primary.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        organization_id: UUID,
        address_type: str,
        include_inactive: bool = False,
    ) -> List[OrganizationAddress]:
        """Get addresses of a specific type for an organization."""
        query = select(OrganizationAddress).where(
            and_(
                OrganizationAddress.organization_id == organization_id,
                OrganizationAddress.address_type == address_type.upper(),
            )
        )
        if not include_inactive:
            query = query.where(OrganizationAddress.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_primary(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationAddress]:
        """Get the primary address for an organization."""
        query = select(OrganizationAddress).where(
            and_(
                OrganizationAddress.organization_id == organization_id,
                OrganizationAddress.is_primary == True,
                OrganizationAddress.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_registered_address(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationAddress]:
        """Get the registered address for an organization."""
        query = select(OrganizationAddress).where(
            and_(
                OrganizationAddress.organization_id == organization_id,
                OrganizationAddress.address_type == "REGISTERED",
                OrganizationAddress.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def clear_primary(self, organization_id: UUID) -> None:
        """Clear primary flag from all addresses of an organization."""
        addresses = await self.get_by_organization(organization_id)
        for address in addresses:
            if address.is_primary:
                address.is_primary = False
        await self.session.flush()
