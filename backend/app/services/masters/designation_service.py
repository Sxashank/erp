"""Designation service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.masters.designation import Designation
from app.repositories.masters.designation_repo import DesignationRepository
from app.repositories.masters.department_repo import DepartmentRepository
from app.schemas.masters.designation import DesignationCreate, DesignationUpdate


class DesignationService:
    """Service for designation management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DesignationRepository(session)
        self.dept_repo = DepartmentRepository(session)

    async def create(
        self,
        data: DesignationCreate,
        created_by: Optional[UUID] = None,
    ) -> Designation:
        """Create a new designation."""
        # Check if code exists
        if await self.repo.code_exists(data.code):
            raise ConflictException(f"Designation code '{data.code}' already exists")

        # Verify department if provided
        if data.department_id:
            dept = await self.dept_repo.get(data.department_id)
            if not dept:
                raise NotFoundException("Department not found")

        # Verify reporting designation if provided
        if data.reporting_to_id:
            reporting_to = await self.repo.get(data.reporting_to_id)
            if not reporting_to:
                raise NotFoundException("Reporting designation not found")

        desig_data = data.model_dump()
        desig_data["created_by"] = created_by

        return await self.repo.create(desig_data)

    async def update(
        self,
        desig_id: UUID,
        data: DesignationUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Designation:
        """Update an existing designation."""
        desig = await self.repo.get(desig_id)
        if not desig:
            raise NotFoundException("Designation not found")

        # Check circular reporting if reporting_to is being updated
        if data.reporting_to_id:
            if data.reporting_to_id == desig_id:
                raise BadRequestException("Designation cannot report to itself")

            # Check if new reporting designation reports to this one
            hierarchy = await self.repo.get_reporting_hierarchy(data.reporting_to_id)
            if any(d.id == desig_id for d in hierarchy):
                raise BadRequestException("Cannot create circular reporting structure")

        # Verify department if provided
        if data.department_id:
            dept = await self.dept_repo.get(data.department_id)
            if not dept:
                raise NotFoundException("Department not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(desig, update_data)

    async def get(self, desig_id: UUID) -> Designation:
        """Get designation by ID."""
        desig = await self.repo.get(desig_id)
        if not desig:
            raise NotFoundException("Designation not found")
        return desig

    async def get_all(
        self,
        department_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Designation], int]:
        """Get paginated list of designations."""
        if department_id:
            desigs = await self.repo.get_by_department(department_id, include_inactive)
            return desigs[skip:skip+limit], len(desigs)
        else:
            desigs = await self.repo.get_all_with_relations(skip, limit, include_inactive)
            total = await self.repo.count(include_inactive)
            return desigs, total

    async def get_reports(self, desig_id: UUID) -> List[Designation]:
        """Get designations that report to this designation."""
        return await self.repo.get_reports(desig_id)

    async def get_hierarchy(self, desig_id: UUID) -> List[Designation]:
        """Get reporting hierarchy for a designation."""
        return await self.repo.get_reporting_hierarchy(desig_id)

    async def delete(
        self,
        desig_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Designation:
        """Soft delete a designation."""
        desig = await self.repo.get(desig_id)
        if not desig:
            raise NotFoundException("Designation not found")

        # Check if designation has reports
        if await self.repo.has_reports(desig_id):
            raise BadRequestException("Cannot delete designation with reporting designations")

        return await self.repo.soft_delete(desig_id, deleted_by)
