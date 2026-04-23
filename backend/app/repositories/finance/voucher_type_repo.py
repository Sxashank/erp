"""Voucher Type repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.finance.voucher_type import VoucherType
from app.core.constants import VoucherClass


class VoucherTypeRepository(BaseRepository[VoucherType]):
    """Repository for Voucher Type operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VoucherType, session)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[VoucherType]:
        """Get all voucher types for an organization."""
        query = select(VoucherType).where(
            VoucherType.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(VoucherType.is_active == True)
        query = query.order_by(VoucherType.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_class(
        self,
        organization_id: UUID,
        voucher_class: VoucherClass,
        include_inactive: bool = False,
    ) -> List[VoucherType]:
        """Get voucher types by class."""
        query = select(VoucherType).where(
            and_(
                VoucherType.organization_id == organization_id,
                VoucherType.voucher_class == voucher_class,
            )
        )
        if not include_inactive:
            query = query.where(VoucherType.is_active == True)
        query = query.order_by(VoucherType.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_code(
        self,
        code: str,
        organization_id: UUID,
    ) -> Optional[VoucherType]:
        """Get voucher type by code."""
        query = select(VoucherType).where(
            and_(
                VoucherType.code == code,
                VoucherType.organization_id == organization_id,
                VoucherType.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def code_exists(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a voucher type code exists in the organization."""
        query = select(VoucherType.id).where(
            and_(
                VoucherType.code == code,
                VoucherType.organization_id == organization_id,
                VoucherType.is_active == True,
            )
        )
        if exclude_id:
            query = query.where(VoucherType.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_next_number(
        self,
        voucher_type_id: UUID,
        financial_year_code: str,
    ) -> str:
        """Get and increment the next voucher number."""
        vtype = await self.get(voucher_type_id)
        if vtype:
            return vtype.get_next_number(financial_year_code)
        return ""
