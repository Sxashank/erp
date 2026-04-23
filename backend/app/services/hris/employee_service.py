"""Employee service for HRIS module."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hris.employee import (
    Employee,
    EmployeeDocument,
    EmployeeFamily,
    EmployeeBankAccount,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeStatutory,
    EmployeeLifecycleEvent,
)
from app.models.masters.department import Department
from app.models.masters.designation import Designation
from app.schemas.hris.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeFilters,
    EmployeeDocumentCreate,
    EmployeeDocumentUpdate,
    EmployeeFamilyCreate,
    EmployeeFamilyUpdate,
    EmployeeBankAccountCreate,
    EmployeeBankAccountUpdate,
    EmployeeEducationCreate,
    EmployeeEducationUpdate,
    EmployeeExperienceCreate,
    EmployeeExperienceUpdate,
    EmployeeStatutoryCreate,
    EmployeeStatutoryUpdate,
    EmployeeLifecycleEventCreate,
)
from app.core.constants import EmploymentStatus, LifecycleEventType


class EmployeeService:
    """Service for employee operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_employee_code(self, organization_id: UUID) -> str:
        """Generate next employee code for organization."""
        result = await self.db.execute(
            select(func.count(Employee.id))
            .where(Employee.organization_id == organization_id)
        )
        count = result.scalar() or 0
        return f"EMP{str(count + 1).zfill(5)}"

    async def create(self, data: EmployeeCreate, created_by: UUID) -> Employee:
        """Create a new employee."""
        # Generate employee code if not provided
        if not data.employee_code:
            data.employee_code = await self.generate_employee_code(data.organization_id)

        # Create employee
        employee_data = data.model_dump(
            exclude={"documents", "family_members", "bank_accounts", "education", "experience", "statutory_info"}
        )
        employee = Employee(**employee_data, created_by=created_by)
        self.db.add(employee)
        await self.db.flush()

        # Create nested records
        if data.documents:
            for doc_data in data.documents:
                doc = EmployeeDocument(
                    employee_id=employee.id,
                    **doc_data.model_dump(),
                    created_by=created_by,
                )
                self.db.add(doc)

        if data.family_members:
            for family_data in data.family_members:
                family = EmployeeFamily(
                    employee_id=employee.id,
                    **family_data.model_dump(),
                    created_by=created_by,
                )
                self.db.add(family)

        if data.bank_accounts:
            for bank_data in data.bank_accounts:
                bank = EmployeeBankAccount(
                    employee_id=employee.id,
                    **bank_data.model_dump(),
                    created_by=created_by,
                )
                self.db.add(bank)

        if data.education:
            for edu_data in data.education:
                edu = EmployeeEducation(
                    employee_id=employee.id,
                    **edu_data.model_dump(),
                    created_by=created_by,
                )
                self.db.add(edu)

        if data.experience:
            for exp_data in data.experience:
                exp = EmployeeExperience(
                    employee_id=employee.id,
                    **exp_data.model_dump(),
                    created_by=created_by,
                )
                self.db.add(exp)

        if data.statutory_info:
            statutory = EmployeeStatutory(
                employee_id=employee.id,
                **data.statutory_info.model_dump(),
                created_by=created_by,
            )
            self.db.add(statutory)

        # Create joining lifecycle event
        event = EmployeeLifecycleEvent(
            employee_id=employee.id,
            event_type=LifecycleEventType.JOINING,
            event_date=data.date_of_joining,
            effective_date=data.date_of_joining,
            new_values={
                "department_id": str(data.department_id) if data.department_id else None,
                "designation_id": str(data.designation_id) if data.designation_id else None,
                "employment_type": data.employment_type.value if data.employment_type else None,
            },
            created_by=created_by,
        )
        self.db.add(event)

        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get(self, employee_id: UUID, include_related: bool = False) -> Optional[Employee]:
        """Get employee by ID."""
        query = select(Employee).where(Employee.id == employee_id)

        if include_related:
            query = query.options(
                selectinload(Employee.documents),
                selectinload(Employee.family_members),
                selectinload(Employee.bank_accounts),
                selectinload(Employee.education),
                selectinload(Employee.experience),
                selectinload(Employee.statutory_info),
                selectinload(Employee.lifecycle_events),
                selectinload(Employee.department),
                selectinload(Employee.designation),
                selectinload(Employee.unit),
                selectinload(Employee.shift),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, organization_id: UUID, employee_code: str) -> Optional[Employee]:
        """Get employee by code."""
        result = await self.db.execute(
            select(Employee).where(
                Employee.organization_id == organization_id,
                Employee.employee_code == employee_code,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: EmployeeFilters,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Employee], int]:
        """List employees with filters."""
        query = select(Employee).options(
            selectinload(Employee.department),
            selectinload(Employee.designation),
        )

        # Apply filters
        conditions = []
        if filters.organization_id:
            conditions.append(Employee.organization_id == filters.organization_id)
        if filters.department_id:
            conditions.append(Employee.department_id == filters.department_id)
        if filters.designation_id:
            conditions.append(Employee.designation_id == filters.designation_id)
        if filters.unit_id:
            conditions.append(Employee.unit_id == filters.unit_id)
        if filters.employment_type:
            conditions.append(Employee.employment_type == filters.employment_type)
        if filters.employment_status:
            conditions.append(Employee.employment_status == filters.employment_status)
        if filters.reporting_manager_id:
            conditions.append(Employee.reporting_manager_id == filters.reporting_manager_id)
        if filters.date_of_joining_from:
            conditions.append(Employee.date_of_joining >= filters.date_of_joining_from)
        if filters.date_of_joining_to:
            conditions.append(Employee.date_of_joining <= filters.date_of_joining_to)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_code.ilike(search_term),
                    Employee.official_email.ilike(search_term),
                    Employee.personal_mobile.ilike(search_term),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count(Employee.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(Employee.employee_code).offset(skip).limit(limit)
        result = await self.db.execute(query)
        employees = list(result.scalars().all())

        return employees, total

    async def update(self, employee_id: UUID, data: EmployeeUpdate, updated_by: UUID) -> Optional[Employee]:
        """Update employee."""
        employee = await self.get(employee_id)
        if not employee:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        employee.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def delete(self, employee_id: UUID) -> bool:
        """Soft delete employee (set status to RELIEVED)."""
        employee = await self.get(employee_id)
        if not employee:
            return False

        employee.employment_status = EmploymentStatus.RELIEVED
        employee.date_of_leaving = date.today()
        await self.db.commit()
        return True

    # ============================================
    # Document Operations
    # ============================================
    async def add_document(
        self, employee_id: UUID, data: EmployeeDocumentCreate, created_by: UUID
    ) -> EmployeeDocument:
        """Add document to employee."""
        doc = EmployeeDocument(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def update_document(
        self, document_id: UUID, data: EmployeeDocumentUpdate, updated_by: UUID
    ) -> Optional[EmployeeDocument]:
        """Update employee document."""
        result = await self.db.execute(
            select(EmployeeDocument).where(EmployeeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        doc.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete employee document."""
        result = await self.db.execute(
            select(EmployeeDocument).where(EmployeeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return False

        await self.db.delete(doc)
        await self.db.commit()
        return True

    async def verify_document(self, document_id: UUID, verified_by: UUID) -> Optional[EmployeeDocument]:
        """Verify employee document."""
        result = await self.db.execute(
            select(EmployeeDocument).where(EmployeeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return None

        doc.is_verified = True
        doc.verified_by = verified_by
        doc.verified_at = date.today()
        doc.updated_by = verified_by
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    # ============================================
    # Family Operations
    # ============================================
    async def add_family_member(
        self, employee_id: UUID, data: EmployeeFamilyCreate, created_by: UUID
    ) -> EmployeeFamily:
        """Add family member to employee."""
        family = EmployeeFamily(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(family)
        await self.db.commit()
        await self.db.refresh(family)
        return family

    async def update_family_member(
        self, family_id: UUID, data: EmployeeFamilyUpdate, updated_by: UUID
    ) -> Optional[EmployeeFamily]:
        """Update family member."""
        result = await self.db.execute(
            select(EmployeeFamily).where(EmployeeFamily.id == family_id)
        )
        family = result.scalar_one_or_none()
        if not family:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(family, field, value)

        family.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(family)
        return family

    async def delete_family_member(self, family_id: UUID) -> bool:
        """Delete family member."""
        result = await self.db.execute(
            select(EmployeeFamily).where(EmployeeFamily.id == family_id)
        )
        family = result.scalar_one_or_none()
        if not family:
            return False

        await self.db.delete(family)
        await self.db.commit()
        return True

    # ============================================
    # Bank Account Operations
    # ============================================
    async def add_bank_account(
        self, employee_id: UUID, data: EmployeeBankAccountCreate, created_by: UUID
    ) -> EmployeeBankAccount:
        """Add bank account to employee."""
        # If primary, unset other primary accounts
        if data.is_primary:
            await self.db.execute(
                select(EmployeeBankAccount)
                .where(EmployeeBankAccount.employee_id == employee_id)
            )
            result = await self.db.execute(
                select(EmployeeBankAccount).where(
                    EmployeeBankAccount.employee_id == employee_id,
                    EmployeeBankAccount.is_primary == True,
                )
            )
            existing = result.scalars().all()
            for bank in existing:
                bank.is_primary = False

        bank = EmployeeBankAccount(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(bank)
        await self.db.commit()
        await self.db.refresh(bank)
        return bank

    async def update_bank_account(
        self, bank_id: UUID, data: EmployeeBankAccountUpdate, updated_by: UUID
    ) -> Optional[EmployeeBankAccount]:
        """Update bank account."""
        result = await self.db.execute(
            select(EmployeeBankAccount).where(EmployeeBankAccount.id == bank_id)
        )
        bank = result.scalar_one_or_none()
        if not bank:
            return None

        # If setting as primary, unset others
        if data.is_primary:
            result = await self.db.execute(
                select(EmployeeBankAccount).where(
                    EmployeeBankAccount.employee_id == bank.employee_id,
                    EmployeeBankAccount.is_primary == True,
                    EmployeeBankAccount.id != bank_id,
                )
            )
            existing = result.scalars().all()
            for other_bank in existing:
                other_bank.is_primary = False

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank, field, value)

        bank.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(bank)
        return bank

    async def delete_bank_account(self, bank_id: UUID) -> bool:
        """Delete bank account."""
        result = await self.db.execute(
            select(EmployeeBankAccount).where(EmployeeBankAccount.id == bank_id)
        )
        bank = result.scalar_one_or_none()
        if not bank:
            return False

        await self.db.delete(bank)
        await self.db.commit()
        return True

    # ============================================
    # Education Operations
    # ============================================
    async def add_education(
        self, employee_id: UUID, data: EmployeeEducationCreate, created_by: UUID
    ) -> EmployeeEducation:
        """Add education to employee."""
        edu = EmployeeEducation(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(edu)
        await self.db.commit()
        await self.db.refresh(edu)
        return edu

    async def update_education(
        self, education_id: UUID, data: EmployeeEducationUpdate, updated_by: UUID
    ) -> Optional[EmployeeEducation]:
        """Update education."""
        result = await self.db.execute(
            select(EmployeeEducation).where(EmployeeEducation.id == education_id)
        )
        edu = result.scalar_one_or_none()
        if not edu:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(edu, field, value)

        edu.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(edu)
        return edu

    async def delete_education(self, education_id: UUID) -> bool:
        """Delete education."""
        result = await self.db.execute(
            select(EmployeeEducation).where(EmployeeEducation.id == education_id)
        )
        edu = result.scalar_one_or_none()
        if not edu:
            return False

        await self.db.delete(edu)
        await self.db.commit()
        return True

    # ============================================
    # Experience Operations
    # ============================================
    async def add_experience(
        self, employee_id: UUID, data: EmployeeExperienceCreate, created_by: UUID
    ) -> EmployeeExperience:
        """Add experience to employee."""
        exp = EmployeeExperience(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def update_experience(
        self, experience_id: UUID, data: EmployeeExperienceUpdate, updated_by: UUID
    ) -> Optional[EmployeeExperience]:
        """Update experience."""
        result = await self.db.execute(
            select(EmployeeExperience).where(EmployeeExperience.id == experience_id)
        )
        exp = result.scalar_one_or_none()
        if not exp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exp, field, value)

        exp.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def delete_experience(self, experience_id: UUID) -> bool:
        """Delete experience."""
        result = await self.db.execute(
            select(EmployeeExperience).where(EmployeeExperience.id == experience_id)
        )
        exp = result.scalar_one_or_none()
        if not exp:
            return False

        await self.db.delete(exp)
        await self.db.commit()
        return True

    # ============================================
    # Statutory Operations
    # ============================================
    async def get_statutory(self, employee_id: UUID) -> Optional[EmployeeStatutory]:
        """Get employee statutory info."""
        result = await self.db.execute(
            select(EmployeeStatutory).where(EmployeeStatutory.employee_id == employee_id)
        )
        return result.scalar_one_or_none()

    async def upsert_statutory(
        self, employee_id: UUID, data: EmployeeStatutoryCreate, user_id: UUID
    ) -> EmployeeStatutory:
        """Create or update statutory info."""
        existing = await self.get_statutory(employee_id)
        if existing:
            update_data = data.model_dump()
            for field, value in update_data.items():
                setattr(existing, field, value)
            existing.updated_by = user_id
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            statutory = EmployeeStatutory(
                employee_id=employee_id,
                **data.model_dump(),
                created_by=user_id,
            )
            self.db.add(statutory)
            await self.db.commit()
            await self.db.refresh(statutory)
            return statutory

    # ============================================
    # Lifecycle Event Operations
    # ============================================
    async def add_lifecycle_event(
        self,
        employee_id: UUID,
        data: EmployeeLifecycleEventCreate,
        created_by: UUID,
    ) -> EmployeeLifecycleEvent:
        """Add lifecycle event to employee."""
        event = EmployeeLifecycleEvent(
            employee_id=employee_id,
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_lifecycle_events(self, employee_id: UUID) -> List[EmployeeLifecycleEvent]:
        """Get all lifecycle events for an employee."""
        result = await self.db.execute(
            select(EmployeeLifecycleEvent)
            .where(EmployeeLifecycleEvent.employee_id == employee_id)
            .order_by(EmployeeLifecycleEvent.event_date.desc())
        )
        return list(result.scalars().all())

    # ============================================
    # Utility Methods
    # ============================================
    async def get_team_members(self, manager_id: UUID) -> List[Employee]:
        """Get all employees reporting to a manager."""
        result = await self.db.execute(
            select(Employee)
            .where(Employee.reporting_manager_id == manager_id)
            .order_by(Employee.first_name)
        )
        return list(result.scalars().all())

    async def get_department_employees(
        self, department_id: UUID, active_only: bool = True
    ) -> List[Employee]:
        """Get all employees in a department."""
        query = select(Employee).where(Employee.department_id == department_id)
        if active_only:
            query = query.where(Employee.employment_status == EmploymentStatus.ACTIVE)
        query = query.order_by(Employee.first_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
