"""
Salary Service

Business logic for salary components, structures, and employee salaries.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payroll.salary_component import (
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
    EmployeeSalary,
    EmployeeSalaryComponent,
)
from app.schemas.payroll.salary_component import (
    SalaryComponentCreate,
    SalaryComponentUpdate,
    SalaryStructureCreate,
    SalaryStructureUpdate,
    EmployeeSalaryCreate,
    EmployeeSalaryUpdate,
)


class SalaryComponentService:
    """Service for salary component operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SalaryComponentCreate, created_by: UUID) -> SalaryComponent:
        """Create a new salary component"""
        component = SalaryComponent(
            **data.model_dump(),
            created_by=created_by
        )
        self.db.add(component)
        await self.db.commit()
        await self.db.refresh(component)
        return component

    async def get(self, id: UUID) -> Optional[SalaryComponent]:
        """Get salary component by ID"""
        result = await self.db.execute(
            select(SalaryComponent).where(SalaryComponent.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, organization_id: UUID, code: str) -> Optional[SalaryComponent]:
        """Get salary component by organization and code"""
        result = await self.db.execute(
            select(SalaryComponent).where(
                and_(
                    SalaryComponent.organization_id == organization_id,
                    SalaryComponent.component_code == code
                )
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        component_type: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SalaryComponent], int]:
        """List salary components with filters"""
        query = select(SalaryComponent).where(
            SalaryComponent.organization_id == organization_id
        )

        if component_type:
            query = query.where(SalaryComponent.component_type == component_type)
        if category:
            query = query.where(SalaryComponent.category == category)
        if active_only:
            query = query.where(SalaryComponent.is_active == True)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(SalaryComponent.display_order, SalaryComponent.component_name)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: SalaryComponentUpdate,
        updated_by: UUID
    ) -> Optional[SalaryComponent]:
        """Update a salary component"""
        component = await self.get(id)
        if not component:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)
        component.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(component)
        return component

    async def delete(self, id: UUID) -> bool:
        """Soft delete a salary component"""
        component = await self.get(id)
        if not component:
            return False

        component.is_active = False
        await self.db.commit()
        return True


class SalaryStructureService:
    """Service for salary structure operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SalaryStructureCreate, created_by: UUID) -> SalaryStructure:
        """Create a new salary structure with components"""
        # Create structure
        structure_data = data.model_dump(exclude={"components"})
        structure = SalaryStructure(**structure_data, created_by=created_by)
        self.db.add(structure)
        await self.db.flush()

        # Create structure components
        for comp_data in data.components:
            component = SalaryStructureComponent(
                structure_id=structure.id,
                **comp_data.model_dump(),
                created_by=created_by
            )
            self.db.add(component)

        await self.db.commit()
        await self.db.refresh(structure)
        return await self.get(structure.id)

    async def get(self, id: UUID) -> Optional[SalaryStructure]:
        """Get salary structure by ID with components"""
        result = await self.db.execute(
            select(SalaryStructure)
            .options(
                selectinload(SalaryStructure.components)
                .selectinload(SalaryStructureComponent.component)
            )
            .where(SalaryStructure.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SalaryStructure], int]:
        """List salary structures"""
        query = select(SalaryStructure).where(
            SalaryStructure.organization_id == organization_id
        )

        if active_only:
            query = query.where(SalaryStructure.is_active == True)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(SalaryStructure.structure_name)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: SalaryStructureUpdate,
        updated_by: UUID
    ) -> Optional[SalaryStructure]:
        """Update a salary structure"""
        structure = await self.get(id)
        if not structure:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={"components"})
        for field, value in update_data.items():
            setattr(structure, field, value)
        structure.updated_by = updated_by

        # Update components if provided
        if data.components is not None:
            # Delete existing components
            for comp in structure.components:
                await self.db.delete(comp)

            # Create new components
            for comp_data in data.components:
                component = SalaryStructureComponent(
                    structure_id=structure.id,
                    **comp_data.model_dump(),
                    created_by=updated_by
                )
                self.db.add(component)

        await self.db.commit()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        """Soft delete a salary structure"""
        structure = await self.get(id)
        if not structure:
            return False

        structure.is_active = False
        await self.db.commit()
        return True


class EmployeeSalaryService:
    """Service for employee salary operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: EmployeeSalaryCreate, created_by: UUID) -> EmployeeSalary:
        """Create a new employee salary assignment"""
        # Check for existing active salary and mark it superseded
        existing = await self.get_active_salary(data.employee_id)
        if existing:
            existing.status = "SUPERSEDED"
            existing.effective_to = data.effective_from

        # Create new salary
        salary_data = data.model_dump(exclude={"components"})
        salary = EmployeeSalary(
            **salary_data,
            revision_number=(existing.revision_number + 1) if existing else 1,
            previous_salary_id=existing.id if existing else None,
            created_by=created_by
        )
        self.db.add(salary)
        await self.db.flush()

        # Create salary components
        for comp_data in data.components:
            component = EmployeeSalaryComponent(
                employee_salary_id=salary.id,
                **comp_data.model_dump(),
                created_by=created_by
            )
            self.db.add(component)

        await self.db.commit()
        await self.db.refresh(salary)
        return await self.get(salary.id)

    async def get(self, id: UUID) -> Optional[EmployeeSalary]:
        """Get employee salary by ID with components"""
        result = await self.db.execute(
            select(EmployeeSalary)
            .options(
                selectinload(EmployeeSalary.components)
                .selectinload(EmployeeSalaryComponent.component),
                selectinload(EmployeeSalary.structure),
                selectinload(EmployeeSalary.employee)
            )
            .where(EmployeeSalary.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_salary(self, employee_id: UUID) -> Optional[EmployeeSalary]:
        """Get current active salary for an employee"""
        result = await self.db.execute(
            select(EmployeeSalary)
            .options(selectinload(EmployeeSalary.components))
            .where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.status == "ACTIVE"
                )
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: Optional[UUID] = None,
        employee_id: Optional[UUID] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EmployeeSalary], int]:
        """List employee salaries with filters"""
        query = select(EmployeeSalary).options(
            selectinload(EmployeeSalary.employee),
            selectinload(EmployeeSalary.structure)
        )

        if employee_id:
            query = query.where(EmployeeSalary.employee_id == employee_id)
        if active_only:
            query = query.where(EmployeeSalary.status == "ACTIVE")

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(EmployeeSalary.effective_from.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def get_salary_at_date(
        self,
        employee_id: UUID,
        as_of_date: date
    ) -> Optional[EmployeeSalary]:
        """Get employee's salary that was effective on a specific date"""
        result = await self.db.execute(
            select(EmployeeSalary)
            .options(selectinload(EmployeeSalary.components))
            .where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.effective_from <= as_of_date,
                    (EmployeeSalary.effective_to >= as_of_date) | (EmployeeSalary.effective_to.is_(None))
                )
            )
            .order_by(EmployeeSalary.effective_from.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
