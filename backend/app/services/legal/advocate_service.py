"""Advocate Management Service.

Provides business logic for managing law firms, advocates,
case assignments, and performance tracking.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.legal.advocate import (
    LawFirm,
    Advocate,
    AdvocateSpecialization,
    AdvocateAssignment,
    AdvocatePerformance,
)
from app.models.legal.enums import (
    AdvocateRole,
    FeeStructureType,
    SpecializationType,
    BarCouncilState,
)
from app.models.lending.collections import LegalCase


class AdvocateService:
    """Service for managing advocates and law firms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Law Firm Management
    # =========================================================================

    async def create_law_firm(
        self,
        organization_id: UUID,
        name: str,
        registration_number: Optional[str] = None,
        bar_council_id: Optional[str] = None,
        pan: Optional[str] = None,
        gstin: Optional[str] = None,
        address_line1: Optional[str] = None,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        pincode: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        empanelment_date: Optional[date] = None,
        empanelment_category: Optional[str] = None,
        default_fee_structure: Optional[FeeStructureType] = None,
        retainer_amount: Optional[Decimal] = None,
        specializations: Optional[List[str]] = None,
        created_by: Optional[UUID] = None,
    ) -> LawFirm:
        """Create a new law firm."""
        law_firm = LawFirm(
            organization_id=organization_id,
            name=name,
            registration_number=registration_number,
            bar_council_id=bar_council_id,
            pan=pan,
            gstin=gstin,
            address_line1=address_line1,
            city=city,
            state_code=state_code,
            pincode=pincode,
            phone=phone,
            email=email,
            is_empaneled=True,
            empanelment_date=empanelment_date or date.today(),
            empanelment_category=empanelment_category,
            default_fee_structure=default_fee_structure,
            retainer_amount=retainer_amount,
            specializations={"items": specializations} if specializations else None,
            created_by=created_by,
        )
        self.db.add(law_firm)
        await self.db.flush()
        return law_firm

    async def get_law_firm(self, law_firm_id: UUID) -> Optional[LawFirm]:
        """Get law firm by ID."""
        result = await self.db.execute(
            select(LawFirm)
            .options(selectinload(LawFirm.advocates))
            .where(LawFirm.id == law_firm_id)
        )
        return result.scalar_one_or_none()

    async def list_law_firms(
        self,
        organization_id: UUID,
        is_empaneled: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[LawFirm], int]:
        """List law firms with filtering and pagination."""
        query = select(LawFirm).where(
            and_(
                LawFirm.organization_id == organization_id,
                LawFirm.is_active == True,
            )
        )

        if is_empaneled is not None:
            query = query.where(LawFirm.is_empaneled == is_empaneled)

        if search:
            query = query.where(
                or_(
                    LawFirm.name.ilike(f"%{search}%"),
                    LawFirm.registration_number.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    # =========================================================================
    # Advocate Management
    # =========================================================================

    async def create_advocate(
        self,
        organization_id: UUID,
        first_name: str,
        last_name: str,
        enrollment_number: str,
        bar_council_state: BarCouncilState,
        law_firm_id: Optional[UUID] = None,
        middle_name: Optional[str] = None,
        salutation: Optional[str] = None,
        enrollment_date: Optional[date] = None,
        designation: str = "Advocate",
        pan: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        email: Optional[str] = None,
        address_line1: Optional[str] = None,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        pincode: Optional[str] = None,
        default_fee_structure: Optional[FeeStructureType] = None,
        fee_per_appearance: Optional[Decimal] = None,
        years_of_experience: Optional[int] = None,
        specializations: Optional[List[SpecializationType]] = None,
        created_by: Optional[UUID] = None,
    ) -> Advocate:
        """Create a new advocate."""
        # Build full name
        name_parts = [first_name]
        if middle_name:
            name_parts.append(middle_name)
        name_parts.append(last_name)
        full_name = " ".join(name_parts)
        if salutation:
            full_name = f"{salutation} {full_name}"

        advocate = Advocate(
            organization_id=organization_id,
            law_firm_id=law_firm_id,
            salutation=salutation,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            full_name=full_name,
            enrollment_number=enrollment_number,
            bar_council_state=bar_council_state,
            enrollment_date=enrollment_date,
            designation=designation,
            pan=pan,
            phone=phone,
            mobile=mobile,
            email=email,
            address_line1=address_line1,
            city=city,
            state_code=state_code,
            pincode=pincode,
            default_fee_structure=default_fee_structure,
            fee_per_appearance=fee_per_appearance,
            years_of_experience=years_of_experience,
            is_empaneled=True,
            empanelment_date=date.today(),
            created_by=created_by,
        )
        self.db.add(advocate)
        await self.db.flush()

        # Add specializations
        if specializations:
            for i, spec in enumerate(specializations):
                spec_record = AdvocateSpecialization(
                    advocate_id=advocate.id,
                    specialization_type=spec,
                    is_primary=(i == 0),
                    created_by=created_by,
                )
                self.db.add(spec_record)

        # Create performance record
        performance = AdvocatePerformance(
            advocate_id=advocate.id,
            created_by=created_by,
        )
        self.db.add(performance)

        await self.db.flush()
        return advocate

    async def get_advocate(self, advocate_id: UUID) -> Optional[Advocate]:
        """Get advocate by ID with related data."""
        result = await self.db.execute(
            select(Advocate)
            .options(
                selectinload(Advocate.law_firm),
                selectinload(Advocate.specializations),
                selectinload(Advocate.performance),
            )
            .where(Advocate.id == advocate_id)
        )
        return result.scalar_one_or_none()

    async def list_advocates(
        self,
        organization_id: UUID,
        law_firm_id: Optional[UUID] = None,
        specialization: Optional[SpecializationType] = None,
        is_empaneled: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Advocate], int]:
        """List advocates with filtering and pagination."""
        query = select(Advocate).where(
            and_(
                Advocate.organization_id == organization_id,
                Advocate.is_active == True,
            )
        )

        if law_firm_id:
            query = query.where(Advocate.law_firm_id == law_firm_id)

        if is_empaneled is not None:
            query = query.where(Advocate.is_empaneled == is_empaneled)

        if search:
            query = query.where(
                or_(
                    Advocate.full_name.ilike(f"%{search}%"),
                    Advocate.enrollment_number.ilike(f"%{search}%"),
                )
            )

        if specialization:
            query = query.join(Advocate.specializations).where(
                AdvocateSpecialization.specialization_type == specialization
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    # =========================================================================
    # Case Assignment
    # =========================================================================

    async def assign_to_case(
        self,
        advocate_id: UUID,
        legal_case_id: UUID,
        role: AdvocateRole = AdvocateRole.LEAD_COUNSEL,
        assigned_date: Optional[date] = None,
        fee_structure: Optional[FeeStructureType] = None,
        agreed_fee: Optional[Decimal] = None,
        success_fee_percentage: Optional[Decimal] = None,
        assignment_reason: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> AdvocateAssignment:
        """Assign advocate to a legal case."""
        assignment = AdvocateAssignment(
            advocate_id=advocate_id,
            legal_case_id=legal_case_id,
            role=role,
            assigned_date=assigned_date or date.today(),
            fee_structure=fee_structure,
            agreed_fee=agreed_fee,
            success_fee_percentage=success_fee_percentage,
            assignment_reason=assignment_reason,
            is_active=True,
            created_by=created_by,
        )
        self.db.add(assignment)
        await self.db.flush()

        # Update advocate's active cases count
        await self._update_advocate_performance(advocate_id)

        return assignment

    async def relieve_from_case(
        self,
        assignment_id: UUID,
        relieved_date: Optional[date] = None,
        relieving_reason: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> AdvocateAssignment:
        """Relieve advocate from a case."""
        result = await self.db.execute(
            select(AdvocateAssignment).where(AdvocateAssignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        assignment.is_active = False
        assignment.relieved_date = relieved_date or date.today()
        assignment.relieving_reason = relieving_reason
        assignment.updated_by = updated_by

        await self.db.flush()

        # Update advocate's active cases count
        await self._update_advocate_performance(assignment.advocate_id)

        return assignment

    async def get_case_advocates(
        self, legal_case_id: UUID, active_only: bool = True
    ) -> List[AdvocateAssignment]:
        """Get all advocates assigned to a case."""
        query = select(AdvocateAssignment).options(
            selectinload(AdvocateAssignment.advocate)
        ).where(AdvocateAssignment.legal_case_id == legal_case_id)

        if active_only:
            query = query.where(AdvocateAssignment.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_advocate_cases(
        self,
        advocate_id: UUID,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AdvocateAssignment], int]:
        """Get all cases assigned to an advocate."""
        query = select(AdvocateAssignment).where(
            AdvocateAssignment.advocate_id == advocate_id
        )

        if active_only:
            query = query.where(AdvocateAssignment.is_active == True)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    # =========================================================================
    # Performance Tracking
    # =========================================================================

    async def get_advocate_performance(
        self, advocate_id: UUID
    ) -> Optional[AdvocatePerformance]:
        """Get advocate performance metrics."""
        result = await self.db.execute(
            select(AdvocatePerformance).where(
                AdvocatePerformance.advocate_id == advocate_id
            )
        )
        return result.scalar_one_or_none()

    async def _update_advocate_performance(self, advocate_id: UUID) -> None:
        """Update advocate performance metrics."""
        # Get current performance record
        result = await self.db.execute(
            select(AdvocatePerformance).where(
                AdvocatePerformance.advocate_id == advocate_id
            )
        )
        performance = result.scalar_one_or_none()
        if not performance:
            return

        # Count active cases
        active_cases_query = select(func.count()).where(
            and_(
                AdvocateAssignment.advocate_id == advocate_id,
                AdvocateAssignment.is_active == True,
            )
        )
        active_cases = (await self.db.execute(active_cases_query)).scalar() or 0

        # Count total cases
        total_cases_query = select(func.count()).where(
            AdvocateAssignment.advocate_id == advocate_id
        )
        total_cases = (await self.db.execute(total_cases_query)).scalar() or 0

        # Update performance
        performance.active_cases = active_cases
        performance.total_cases_assigned = total_cases
        performance.last_calculated_at = datetime.utcnow()

        await self.db.flush()

    async def calculate_fee(
        self,
        advocate_id: UUID,
        fee_type: FeeStructureType,
        base_amount: Optional[Decimal] = None,
        recovery_amount: Optional[Decimal] = None,
    ) -> Decimal:
        """Calculate advocate fee based on fee structure."""
        advocate = await self.get_advocate(advocate_id)
        if not advocate:
            raise ValueError(f"Advocate {advocate_id} not found")

        if fee_type == FeeStructureType.FIXED:
            return base_amount or Decimal("0")

        elif fee_type == FeeStructureType.PER_APPEARANCE:
            return advocate.fee_per_appearance or Decimal("0")

        elif fee_type == FeeStructureType.SUCCESS_FEE:
            if recovery_amount and advocate.success_fee_percentage:
                return recovery_amount * advocate.success_fee_percentage / 100
            return Decimal("0")

        elif fee_type == FeeStructureType.HOURLY:
            hours = base_amount or Decimal("1")
            return hours * (advocate.hourly_rate or Decimal("0"))

        return base_amount or Decimal("0")
