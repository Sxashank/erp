"""Vendor repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.vendor import Vendor
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    """Repository for Vendor operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Vendor, session)

    async def get_by_code(self, code: str, organization_id: UUID) -> Optional[Vendor]:
        """Get vendor by code within an organization."""
        query = select(Vendor).where(
            and_(
                Vendor.code == code,
                Vendor.organization_id == organization_id,
                Vendor.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_gstin(self, gstin: str, organization_id: UUID) -> Optional[Vendor]:
        """Get vendor by GSTIN within an organization."""
        query = select(Vendor).where(
            and_(
                Vendor.gstin == gstin,
                Vendor.organization_id == organization_id,
                Vendor.is_active == True,
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
        vendor_type: Optional[str] = None,
    ) -> Tuple[List[Vendor], int]:
        """Get all vendors for an organization with filters."""
        base_query = select(Vendor).where(
            Vendor.organization_id == organization_id
        )

        if not include_inactive:
            base_query = base_query.where(Vendor.is_active == True)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Vendor.code.ilike(search_term),
                    Vendor.name.ilike(search_term),
                    Vendor.display_name.ilike(search_term),
                    Vendor.gstin.ilike(search_term),
                    Vendor.pan.ilike(search_term),
                )
            )

        if vendor_type:
            base_query = base_query.where(Vendor.vendor_type == vendor_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(Vendor.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_active_vendors(
        self,
        organization_id: UUID,
    ) -> List[Vendor]:
        """Get all active vendors for dropdown lists."""
        query = select(Vendor).where(
            and_(
                Vendor.organization_id == organization_id,
                Vendor.is_active == True,
            )
        ).order_by(Vendor.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_vendor_code(self, organization_id: UUID) -> str:
        """Generate next vendor code."""
        query = select(func.max(Vendor.code)).where(
            and_(
                Vendor.organization_id == organization_id,
                Vendor.code.like('V%'),
            )
        )
        result = await self.session.execute(query)
        max_code = result.scalar()

        if max_code:
            try:
                num = int(max_code[1:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"V{num:04d}"
