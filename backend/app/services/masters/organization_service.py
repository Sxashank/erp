"""Organization service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException
from app.models.masters.organization import Organization
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.masters.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    """Service for organization management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OrganizationRepository(session)

    async def create(
        self,
        data: OrganizationCreate,
        created_by: Optional[UUID] = None,
    ) -> Organization:
        """Create a new organization."""
        # Check if code exists
        if await self.repo.code_exists(data.code):
            raise ConflictException(f"Organization code '{data.code}' already exists")

        # Check if PAN exists
        if await self.repo.pan_exists(data.pan):
            raise ConflictException(f"PAN '{data.pan}' already exists")

        org_data = data.model_dump()
        org_data["created_by"] = created_by
        org_data["pan"] = data.pan.upper()

        return await self.repo.create(org_data)

    async def update(
        self,
        org_id: UUID,
        data: OrganizationUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Organization:
        """Update an existing organization."""
        org = await self.repo.get(org_id)
        if not org:
            raise NotFoundException("Organization not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(org, update_data)

    async def get(self, org_id: UUID) -> dict:
        """Get organization by ID with counts."""
        result = await self.repo.get_with_counts(org_id)
        if not result:
            raise NotFoundException("Organization not found")
        return result

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False,
    ) -> Tuple[List[Organization], int]:
        """Get paginated list of organizations."""
        orgs = await self.repo.get_all(skip, limit, include_inactive)
        total = await self.repo.count(include_inactive)
        return orgs, total

    async def get_primary(self) -> Optional[Organization]:
        """Get the primary organization."""
        return await self.repo.get_primary()

    async def delete(
        self,
        org_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Organization:
        """Soft delete an organization."""
        org = await self.repo.get(org_id)
        if not org:
            raise NotFoundException("Organization not found")

        return await self.repo.soft_delete(org_id, deleted_by)
