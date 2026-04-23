"""Organization Address service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.masters.organization_address import OrganizationAddress
from app.repositories.masters.organization_address_repo import OrganizationAddressRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.masters.organization_address import (
    OrganizationAddressCreate,
    OrganizationAddressUpdate,
)


class OrganizationAddressService:
    """Service for organization address management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OrganizationAddressRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: OrganizationAddressCreate,
        created_by: Optional[UUID] = None,
    ) -> OrganizationAddress:
        """Create a new address."""
        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # If this is set as primary, clear other primary flags
        if data.is_primary:
            await self.repo.clear_primary(data.organization_id)

        address_data = data.model_dump()
        address_data["created_by"] = created_by
        address_data["address_type"] = data.address_type.upper()

        return await self.repo.create(address_data)

    async def update(
        self,
        address_id: UUID,
        data: OrganizationAddressUpdate,
        updated_by: Optional[UUID] = None,
    ) -> OrganizationAddress:
        """Update an existing address."""
        address = await self.repo.get(address_id)
        if not address:
            raise NotFoundException("Address not found")

        # If is_primary is being set to True, clear other primary flags
        if data.is_primary and not address.is_primary:
            await self.repo.clear_primary(address.organization_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(address, update_data)

    async def get(self, address_id: UUID) -> OrganizationAddress:
        """Get address by ID."""
        address = await self.repo.get(address_id)
        if not address:
            raise NotFoundException("Address not found")
        return address

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[OrganizationAddress]:
        """Get all addresses for an organization."""
        return await self.repo.get_by_organization(organization_id, include_inactive)

    async def get_by_type(
        self,
        organization_id: UUID,
        address_type: str,
        include_inactive: bool = False,
    ) -> List[OrganizationAddress]:
        """Get addresses of a specific type for an organization."""
        return await self.repo.get_by_type(organization_id, address_type, include_inactive)

    async def get_primary(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationAddress]:
        """Get the primary address for an organization."""
        return await self.repo.get_primary(organization_id)

    async def get_registered(
        self,
        organization_id: UUID,
    ) -> Optional[OrganizationAddress]:
        """Get the registered address for an organization."""
        return await self.repo.get_registered_address(organization_id)

    async def delete(
        self,
        address_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> OrganizationAddress:
        """Soft delete an address."""
        address = await self.repo.get(address_id)
        if not address:
            raise NotFoundException("Address not found")

        return await self.repo.soft_delete(address_id, deleted_by)

    async def set_primary(
        self,
        address_id: UUID,
        updated_by: Optional[UUID] = None,
    ) -> OrganizationAddress:
        """Set an address as primary."""
        address = await self.repo.get(address_id)
        if not address:
            raise NotFoundException("Address not found")

        # Clear other primary flags
        await self.repo.clear_primary(address.organization_id)

        # Set this address as primary
        address.is_primary = True
        address.updated_by = updated_by
        await self.session.flush()
        await self.session.refresh(address)

        return address
