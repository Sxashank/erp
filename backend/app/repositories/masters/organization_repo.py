"""Organization repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.masters.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def get_by_code(self, code: str) -> Optional[Organization]:
        """Get organization by code."""
        return await self.get_by_field("code", code)

    async def get_by_pan(self, pan: str) -> Optional[Organization]:
        """Get organization by PAN."""
        return await self.get_by_field("pan", pan.upper())

    async def get_primary(self) -> Optional[Organization]:
        """Get the primary organization."""
        query = select(Organization).where(
            and_(
                Organization.is_primary == True,
                Organization.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_counts(self, id: UUID) -> Optional[dict]:
        """Get organization with related counts."""
        org = await self.get(id)
        if not org:
            return None

        # Count units
        from app.models.masters.unit import Unit
        unit_count_query = select(func.count(Unit.id)).where(
            and_(
                Unit.organization_id == id,
                Unit.is_active == True,
            )
        )
        unit_count = await self.session.execute(unit_count_query)

        # Count departments
        from app.models.masters.department import Department
        dept_count_query = select(func.count(Department.id)).where(
            and_(
                Department.organization_id == id,
                Department.is_active == True,
            )
        )
        dept_count = await self.session.execute(dept_count_query)

        # Count users
        from app.models.auth.user import User
        user_count_query = select(func.count(User.id)).where(
            and_(
                User.organization_id == id,
                User.is_active == True,
            )
        )
        user_count = await self.session.execute(user_count_query)

        return {
            "organization": org,
            "unit_count": unit_count.scalar() or 0,
            "department_count": dept_count.scalar() or 0,
            "user_count": user_count.scalar() or 0,
        }

    async def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if organization code already exists."""
        query = select(Organization.id).where(Organization.code == code)
        if exclude_id:
            query = query.where(Organization.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def pan_exists(self, pan: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if PAN already exists."""
        query = select(Organization.id).where(Organization.pan == pan.upper())
        if exclude_id:
            query = query.where(Organization.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
