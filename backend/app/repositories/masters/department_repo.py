"""Department repository."""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.masters.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    """Repository for Department operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Department, session)

    async def get_by_code(self, code: str) -> Department | None:
        """Get department by code."""
        return await self.get_by_field("code", code)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Department]:
        """Get departments with response relationships eager loaded."""
        query = select(Department).options(
            selectinload(Department.organization),
            selectinload(Department.parent_dept),
        )
        if not include_inactive:
            query = query.where(Department.is_active == True)
        query = query.order_by(Department.level, Department.name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> list[Department]:
        """Get all departments for an organization."""
        query = (
            select(Department)
            .where(Department.organization_id == organization_id)
            .options(
                selectinload(Department.organization),
                selectinload(Department.parent_dept),
            )
        )
        if not include_inactive:
            query = query.where(Department.is_active == True)
        query = query.order_by(Department.level, Department.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_children(self, parent_dept_id: UUID) -> list[Department]:
        """Get child departments of a parent department."""
        query = (
            select(Department)
            .where(
                and_(
                    Department.parent_dept_id == parent_dept_id,
                    Department.is_active == True,
                )
            )
            .order_by(Department.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_tree(self, organization_id: UUID) -> list[Department]:
        """Get department tree for an organization."""
        query = (
            select(Department)
            .where(
                and_(
                    Department.organization_id == organization_id,
                    Department.is_active == True,
                )
            )
            .options(
                selectinload(Department.child_depts),
                selectinload(Department.designations),
            )
            .order_by(Department.level, Department.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_root_departments(self, organization_id: UUID) -> list[Department]:
        """Get root level departments (no parent) with children loaded recursively."""
        # First get all departments for this organization with children eager loaded
        query = (
            select(Department)
            .where(
                and_(
                    Department.organization_id == organization_id,
                    Department.is_active == True,
                )
            )
            .options(selectinload(Department.child_depts))
            .order_by(Department.level, Department.name)
        )

        result = await self.session.execute(query)
        all_depts = list(result.scalars().unique().all())

        # Filter to only root departments (those without parent)
        root_depts = [d for d in all_depts if d.parent_dept_id is None]
        return root_depts

    async def get_with_designation_count(self, id: UUID) -> dict | None:
        """Get department with designation count."""
        query = (
            select(Department)
            .where(Department.id == id)
            .options(
                selectinload(Department.organization),
                selectinload(Department.parent_dept),
            )
        )
        result = await self.session.execute(query)
        dept = result.scalar_one_or_none()
        if not dept:
            return None

        from app.models.masters.designation import Designation

        count_query = select(func.count(Designation.id)).where(
            and_(
                Designation.department_id == id,
                Designation.is_active == True,
            )
        )
        count_result = await self.session.execute(count_query)

        return {
            "department": dept,
            "designation_count": count_result.scalar() or 0,
        }

    async def code_exists(
        self,
        code: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """Check if department code already exists."""
        query = select(Department.id).where(Department.code == code)
        if exclude_id:
            query = query.where(Department.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def update_hierarchy(self, dept: Department) -> Department:
        """Update hierarchy path and level for a department."""
        if dept.parent_dept_id:
            parent = await self.get(dept.parent_dept_id)
            if parent:
                dept.level = parent.level + 1
                dept.path = f"{parent.path or ''}/{parent.id}"
            else:
                dept.level = 1
                dept.path = None
        else:
            dept.level = 1
            dept.path = None

        await self.session.flush()
        return dept

    async def has_children(self, dept_id: UUID) -> bool:
        """Check if department has child departments."""
        children = await self.get_children(dept_id)
        return len(children) > 0
