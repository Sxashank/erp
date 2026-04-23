"""Unit service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.masters.unit import Unit
from app.repositories.masters.unit_repo import UnitRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.masters.unit import UnitCreate, UnitUpdate


class UnitService:
    """Service for unit management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UnitRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: UnitCreate,
        created_by: Optional[UUID] = None,
    ) -> Unit:
        """Create a new unit."""
        # Check if code exists
        if await self.repo.code_exists(data.code):
            raise ConflictException(f"Unit code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Verify parent unit if provided
        if data.parent_unit_id:
            parent = await self.repo.get(data.parent_unit_id)
            if not parent:
                raise NotFoundException("Parent unit not found")
            if parent.organization_id != data.organization_id:
                raise BadRequestException("Parent unit must belong to the same organization")

        # Check head office constraint
        if data.is_head_office:
            existing_ho = await self.repo.get_head_office(data.organization_id)
            if existing_ho:
                raise ConflictException("Organization already has a head office")

        unit_data = data.model_dump()
        unit_data["created_by"] = created_by

        unit = await self.repo.create(unit_data)

        # Update hierarchy
        await self.repo.update_hierarchy(unit)

        return unit

    async def update(
        self,
        unit_id: UUID,
        data: UnitUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Unit:
        """Update an existing unit."""
        unit = await self.repo.get(unit_id)
        if not unit:
            raise NotFoundException("Unit not found")

        # Check circular hierarchy if parent is being updated
        if data.parent_unit_id:
            if data.parent_unit_id == unit_id:
                raise BadRequestException("Unit cannot be its own parent")

            # Check if new parent is a child of this unit
            parent = await self.repo.get(data.parent_unit_id)
            if parent and parent.path and str(unit_id) in parent.path:
                raise BadRequestException("Cannot set a child unit as parent")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        unit = await self.repo.update(unit, update_data)

        # Update hierarchy if parent changed
        if data.parent_unit_id is not None:
            await self.repo.update_hierarchy(unit)

        return unit

    async def get(self, unit_id: UUID) -> Unit:
        """Get unit by ID."""
        unit = await self.repo.get(unit_id)
        if not unit:
            raise NotFoundException("Unit not found")
        return unit

    async def get_all(
        self,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Unit], int]:
        """Get paginated list of units."""
        if organization_id:
            units = await self.repo.get_by_organization(organization_id, include_inactive)
            return units[skip:skip+limit], len(units)
        else:
            units = await self.repo.get_all(skip, limit, include_inactive)
            total = await self.repo.count(include_inactive)
            return units, total

    async def get_tree(self, organization_id: UUID) -> List[dict]:
        """Get unit hierarchy tree as nested dictionaries."""
        # Get all units for the organization
        units = await self.repo.get_by_organization(organization_id, include_inactive=False)

        # Build a lookup map by id
        unit_map = {}
        for unit in units:
            unit_map[unit.id] = {
                "id": unit.id,
                "code": unit.code,
                "name": unit.name,
                "unit_type": unit.unit_type,
                "level": unit.level,
                "is_head_office": unit.is_head_office,
                "status": unit.status,
                "parent_unit_id": unit.parent_unit_id,
                "children": [],
            }

        # Build the tree by linking children to parents
        root_units = []
        for unit_id, unit_data in unit_map.items():
            parent_id = unit_data.pop("parent_unit_id")
            if parent_id is None:
                root_units.append(unit_data)
            elif parent_id in unit_map:
                unit_map[parent_id]["children"].append(unit_data)

        return root_units

    async def get_children(self, unit_id: UUID) -> List[Unit]:
        """Get child units."""
        return await self.repo.get_children(unit_id)

    async def delete(
        self,
        unit_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Unit:
        """Soft delete a unit."""
        unit = await self.repo.get(unit_id)
        if not unit:
            raise NotFoundException("Unit not found")

        # Check if unit has children
        if await self.repo.has_children(unit_id):
            raise BadRequestException("Cannot delete unit with child units")

        return await self.repo.soft_delete(unit_id, deleted_by)
