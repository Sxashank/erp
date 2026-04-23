"""Department service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.masters.department import Department
from app.repositories.masters.department_repo import DepartmentRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.masters.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    """Service for department management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DepartmentRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: DepartmentCreate,
        created_by: Optional[UUID] = None,
    ) -> Department:
        """Create a new department."""
        # Check if code exists
        if await self.repo.code_exists(data.code):
            raise ConflictException(f"Department code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Verify parent department if provided
        if data.parent_dept_id:
            parent = await self.repo.get(data.parent_dept_id)
            if not parent:
                raise NotFoundException("Parent department not found")
            if parent.organization_id != data.organization_id:
                raise BadRequestException("Parent department must belong to the same organization")

        dept_data = data.model_dump()
        dept_data["created_by"] = created_by

        dept = await self.repo.create(dept_data)

        # Update hierarchy
        await self.repo.update_hierarchy(dept)

        return dept

    async def update(
        self,
        dept_id: UUID,
        data: DepartmentUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Department:
        """Update an existing department."""
        dept = await self.repo.get(dept_id)
        if not dept:
            raise NotFoundException("Department not found")

        # Check circular hierarchy if parent is being updated
        if data.parent_dept_id:
            if data.parent_dept_id == dept_id:
                raise BadRequestException("Department cannot be its own parent")

            # Check if new parent is a child of this department
            parent = await self.repo.get(data.parent_dept_id)
            if parent and parent.path and str(dept_id) in parent.path:
                raise BadRequestException("Cannot set a child department as parent")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        dept = await self.repo.update(dept, update_data)

        # Update hierarchy if parent changed
        if data.parent_dept_id is not None:
            await self.repo.update_hierarchy(dept)

        return dept

    async def get(self, dept_id: UUID) -> dict:
        """Get department by ID with counts."""
        result = await self.repo.get_with_designation_count(dept_id)
        if not result:
            raise NotFoundException("Department not found")
        return result

    async def get_all(
        self,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Department], int]:
        """Get paginated list of departments."""
        if organization_id:
            depts = await self.repo.get_by_organization(organization_id, include_inactive)
            return depts[skip:skip+limit], len(depts)
        else:
            depts = await self.repo.get_all(skip, limit, include_inactive)
            total = await self.repo.count(include_inactive)
            return depts, total

    async def get_tree(self, organization_id: UUID) -> List[dict]:
        """Get department hierarchy tree as nested dictionaries."""
        # Get all departments for the organization
        depts = await self.repo.get_by_organization(organization_id, include_inactive=False)

        # Build a lookup map by id
        dept_map = {}
        for dept in depts:
            dept_map[dept.id] = {
                "id": dept.id,
                "code": dept.code,
                "name": dept.name,
                "level": dept.level,
                "cost_center_code": dept.cost_center_code,
                "status": dept.status,
                "parent_dept_id": dept.parent_dept_id,
                "children": [],
            }

        # Build the tree by linking children to parents
        root_depts = []
        for dept_id, dept_data in dept_map.items():
            parent_id = dept_data.pop("parent_dept_id")
            if parent_id is None:
                root_depts.append(dept_data)
            elif parent_id in dept_map:
                dept_map[parent_id]["children"].append(dept_data)

        return root_depts

    async def get_children(self, dept_id: UUID) -> List[Department]:
        """Get child departments."""
        return await self.repo.get_children(dept_id)

    async def delete(
        self,
        dept_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Department:
        """Soft delete a department."""
        dept = await self.repo.get(dept_id)
        if not dept:
            raise NotFoundException("Department not found")

        # Check if department has children
        if await self.repo.has_children(dept_id):
            raise BadRequestException("Cannot delete department with child departments")

        return await self.repo.soft_delete(dept_id, deleted_by)
