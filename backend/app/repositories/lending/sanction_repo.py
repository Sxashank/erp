"""Loan Sanction repositories for the lending module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.sanction import (
    LoanSanction,
    SanctionCondition,
    LoanSecurity,
)
from app.models.lending.enums import (
    SanctionStatus,
    ConditionType,
    ConditionCategory,
    ConditionComplianceStatus,
    SecurityCategory,
    SecurityStatus,
)
from app.repositories.base import BaseRepository


class SanctionConditionRepository(BaseRepository[SanctionCondition]):
    """Repository for SanctionCondition operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(SanctionCondition, session)

    async def get_by_sanction(
        self, sanction_id: UUID, include_inactive: bool = False
    ) -> List[SanctionCondition]:
        """Get all conditions for a sanction."""
        query = select(SanctionCondition).where(
            SanctionCondition.sanction_id == sanction_id
        )
        if not include_inactive:
            query = query.where(SanctionCondition.is_active == True)
        query = query.order_by(
            SanctionCondition.condition_type, SanctionCondition.sequence
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self, sanction_id: UUID, condition_type: ConditionType
    ) -> List[SanctionCondition]:
        """Get conditions of a specific type."""
        query = select(SanctionCondition).where(
            and_(
                SanctionCondition.sanction_id == sanction_id,
                SanctionCondition.condition_type == condition_type,
                SanctionCondition.is_active == True,
            )
        )
        query = query.order_by(SanctionCondition.sequence)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_conditions(
        self, sanction_id: UUID, condition_type: Optional[ConditionType] = None
    ) -> List[SanctionCondition]:
        """Get pending conditions for a sanction."""
        query = select(SanctionCondition).where(
            and_(
                SanctionCondition.sanction_id == sanction_id,
                SanctionCondition.compliance_status == ConditionComplianceStatus.PENDING,
                SanctionCondition.is_active == True,
            )
        )
        if condition_type:
            query = query.where(SanctionCondition.condition_type == condition_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_mandatory_pending(
        self, sanction_id: UUID, condition_type: Optional[ConditionType] = None
    ) -> List[SanctionCondition]:
        """Get mandatory pending conditions."""
        query = select(SanctionCondition).where(
            and_(
                SanctionCondition.sanction_id == sanction_id,
                SanctionCondition.is_mandatory == True,
                SanctionCondition.compliance_status == ConditionComplianceStatus.PENDING,
                SanctionCondition.is_active == True,
            )
        )
        if condition_type:
            query = query.where(SanctionCondition.condition_type == condition_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def check_pre_disbursement_complied(
        self, sanction_id: UUID
    ) -> bool:
        """Check if all mandatory pre-disbursement conditions are complied."""
        query = select(func.count(SanctionCondition.id)).where(
            and_(
                SanctionCondition.sanction_id == sanction_id,
                SanctionCondition.condition_type == ConditionType.PRE_DISBURSEMENT,
                SanctionCondition.is_mandatory == True,
                SanctionCondition.compliance_status == ConditionComplianceStatus.PENDING,
                SanctionCondition.is_active == True,
            )
        )
        result = await self.session.execute(query)
        pending_count = result.scalar() or 0
        return pending_count == 0

    async def get_overdue_conditions(
        self, sanction_id: UUID, as_of_date: Optional[date] = None
    ) -> List[SanctionCondition]:
        """Get overdue conditions."""
        if as_of_date is None:
            as_of_date = date.today()

        query = select(SanctionCondition).where(
            and_(
                SanctionCondition.sanction_id == sanction_id,
                SanctionCondition.compliance_status == ConditionComplianceStatus.PENDING,
                SanctionCondition.compliance_due_date < as_of_date,
                SanctionCondition.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class LoanSecurityRepository(BaseRepository[LoanSecurity]):
    """Repository for LoanSecurity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanSecurity, session)

    async def get_by_sanction(
        self, sanction_id: UUID, include_inactive: bool = False
    ) -> List[LoanSecurity]:
        """Get all securities for a sanction."""
        query = select(LoanSecurity).where(LoanSecurity.sanction_id == sanction_id)
        if not include_inactive:
            query = query.where(LoanSecurity.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_category(
        self, sanction_id: UUID, security_category: SecurityCategory
    ) -> List[LoanSecurity]:
        """Get securities by category."""
        query = select(LoanSecurity).where(
            and_(
                LoanSecurity.sanction_id == sanction_id,
                LoanSecurity.security_category == security_category,
                LoanSecurity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_registered_securities(
        self, sanction_id: UUID
    ) -> List[LoanSecurity]:
        """Get securities that are registered."""
        query = select(LoanSecurity).where(
            and_(
                LoanSecurity.sanction_id == sanction_id,
                LoanSecurity.status == SecurityStatus.REGISTERED,
                LoanSecurity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_security_value(
        self, sanction_id: UUID
    ) -> float:
        """Get total security value for a sanction."""
        query = select(func.sum(LoanSecurity.market_value)).where(
            and_(
                LoanSecurity.sanction_id == sanction_id,
                LoanSecurity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)

    async def get_total_forced_sale_value(
        self, sanction_id: UUID
    ) -> float:
        """Get total forced sale value for a sanction."""
        query = select(func.sum(LoanSecurity.forced_sale_value)).where(
            and_(
                LoanSecurity.sanction_id == sanction_id,
                LoanSecurity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)

    async def get_expiring_insurance(
        self, sanction_id: UUID, days_ahead: int = 30
    ) -> List[LoanSecurity]:
        """Get securities with insurance expiring soon."""
        from datetime import timedelta

        cutoff_date = date.today() + timedelta(days=days_ahead)

        query = select(LoanSecurity).where(
            and_(
                LoanSecurity.sanction_id == sanction_id,
                LoanSecurity.insurance_required == True,
                LoanSecurity.insurance_validity <= cutoff_date,
                LoanSecurity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class LoanSanctionRepository(BaseRepository[LoanSanction]):
    """Repository for LoanSanction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanSanction, session)

    async def get_by_number(
        self, sanction_number: str, organization_id: UUID
    ) -> Optional[LoanSanction]:
        """Get sanction by number."""
        query = select(LoanSanction).where(
            and_(
                LoanSanction.sanction_number == sanction_number,
                LoanSanction.organization_id == organization_id,
                LoanSanction.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_application(
        self, application_id: UUID
    ) -> Optional[LoanSanction]:
        """Get sanction for an application."""
        query = select(LoanSanction).where(
            and_(
                LoanSanction.application_id == application_id,
                LoanSanction.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(
        self, sanction_id: UUID
    ) -> Optional[LoanSanction]:
        """Get sanction with conditions and securities."""
        query = (
            select(LoanSanction)
            .options(
                selectinload(LoanSanction.conditions),
                selectinload(LoanSanction.securities),
            )
            .where(
                and_(
                    LoanSanction.id == sanction_id,
                    LoanSanction.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[SanctionStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[LoanSanction], int]:
        """Get all sanctions for an organization with filters."""
        base_query = select(LoanSanction).where(
            LoanSanction.organization_id == organization_id
        )

        if not include_inactive:
            base_query = base_query.where(LoanSanction.is_active == True)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                LoanSanction.sanction_number.ilike(search_term)
            )

        if entity_id:
            base_query = base_query.where(LoanSanction.entity_id == entity_id)

        if status:
            base_query = base_query.where(LoanSanction.status == status)

        if from_date:
            base_query = base_query.where(LoanSanction.sanction_date >= from_date)

        if to_date:
            base_query = base_query.where(LoanSanction.sanction_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = (
            base_query.order_by(LoanSanction.sanction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[LoanSanction]:
        """Get all sanctions for an entity."""
        query = select(LoanSanction).where(LoanSanction.entity_id == entity_id)
        if not include_inactive:
            query = query.where(LoanSanction.is_active == True)
        query = query.order_by(LoanSanction.sanction_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_sanctions(
        self, entity_id: UUID
    ) -> List[LoanSanction]:
        """Get active sanctions for an entity."""
        query = select(LoanSanction).where(
            and_(
                LoanSanction.entity_id == entity_id,
                LoanSanction.status.in_(
                    [SanctionStatus.ACTIVE, SanctionStatus.ACCEPTED]
                ),
                LoanSanction.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expiring_sanctions(
        self, organization_id: UUID, days_ahead: int = 30
    ) -> List[LoanSanction]:
        """Get sanctions expiring soon."""
        from datetime import timedelta

        cutoff_date = date.today() + timedelta(days=days_ahead)

        query = select(LoanSanction).where(
            and_(
                LoanSanction.organization_id == organization_id,
                LoanSanction.status == SanctionStatus.APPROVED,
                LoanSanction.validity_date <= cutoff_date,
                LoanSanction.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_acceptance(
        self, organization_id: UUID
    ) -> List[LoanSanction]:
        """Get sanctions pending borrower acceptance."""
        query = select(LoanSanction).where(
            and_(
                LoanSanction.organization_id == organization_id,
                LoanSanction.status == SanctionStatus.APPROVED,
                LoanSanction.borrower_acceptance_date.is_(None),
                LoanSanction.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_sanction_number(
        self,
        organization_id: UUID,
        product_code: str,
        branch_code: str = "HO",
    ) -> str:
        """Generate next sanction number."""
        year = date.today().year
        prefix = f"SMFC/{product_code}/{branch_code}/{year}"
        pattern = f"{prefix}/S%"

        query = select(func.max(LoanSanction.sanction_number)).where(
            and_(
                LoanSanction.organization_id == organization_id,
                LoanSanction.sanction_number.like(pattern),
            )
        )
        result = await self.session.execute(query)
        max_number = result.scalar()

        if max_number:
            try:
                num = int(max_number.split("/")[-1][1:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}/S{num:05d}"

    async def get_total_sanctioned_amount(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> float:
        """Get total sanctioned amount for an organization."""
        query = select(func.sum(LoanSanction.sanctioned_amount)).where(
            and_(
                LoanSanction.organization_id == organization_id,
                LoanSanction.status.in_(
                    [
                        SanctionStatus.APPROVED,
                        SanctionStatus.ACTIVE,
                        SanctionStatus.ACCEPTED,
                    ]
                ),
                LoanSanction.is_active == True,
            )
        )

        if from_date:
            query = query.where(LoanSanction.sanction_date >= from_date)

        if to_date:
            query = query.where(LoanSanction.sanction_date <= to_date)

        result = await self.session.execute(query)
        return float(result.scalar() or 0)
