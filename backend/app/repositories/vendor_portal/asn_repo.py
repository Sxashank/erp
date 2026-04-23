"""ASN Repositories."""

from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.vendor_portal.asn import (
    AdvancedShippingNotice,
    ASNLine,
)
from app.models.vendor_portal.enums import ASNStatus


class ASNRepository(BaseRepository[AdvancedShippingNotice]):
    """Repository for ASN operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AdvancedShippingNotice, session)

    async def get_with_lines(self, id: UUID) -> Optional[AdvancedShippingNotice]:
        """Get ASN with lines."""
        query = (
            select(self.model)
            .options(selectinload(self.model.lines))
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_asn_number(self, asn_number: str) -> Optional[AdvancedShippingNotice]:
        """Get ASN by number."""
        query = select(self.model).where(
            and_(
                self.model.asn_number == asn_number,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_po(
        self, purchase_order_id: UUID
    ) -> List[AdvancedShippingNotice]:
        """Get all ASNs for a PO."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.purchase_order_id == purchase_order_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_by_vendor(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ASNStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[AdvancedShippingNotice], int]:
        """Get all ASNs for a vendor."""
        conditions = [
            self.model.vendor_id == vendor_id,
            self.model.is_active == True,
        ]

        if status:
            conditions.append(self.model.status == status)
        if from_date:
            conditions.append(self.model.asn_date >= from_date)
        if to_date:
            conditions.append(self.model.asn_date <= to_date)

        # Count query
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_in_transit(
        self, organization_id: UUID
    ) -> List[AdvancedShippingNotice]:
        """Get all in-transit ASNs for an organization."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.status.in_([
                        ASNStatus.DISPATCHED,
                        ASNStatus.IN_TRANSIT,
                    ]),
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.expected_delivery_date.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_tracking_number(
        self, tracking_number: str
    ) -> Optional[AdvancedShippingNotice]:
        """Get ASN by tracking number."""
        query = select(self.model).where(
            and_(
                self.model.tracking_number == tracking_number,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_asn_number(
        self, organization_id: UUID, vendor_code: str
    ) -> str:
        """Generate unique ASN number."""
        year = datetime.now().year
        prefix = f"ASN/{vendor_code}/{year}/"

        query = select(func.count(self.model.id)).where(
            and_(
                self.model.organization_id == organization_id,
                self.model.asn_number.like(f"{prefix}%"),
            )
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1

        return f"{prefix}{count:05d}"

    async def count_by_vendor_status(
        self, vendor_id: UUID, status: ASNStatus
    ) -> int:
        """Count ASNs by vendor and status."""
        query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.status == status,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0


class ASNLineRepository(BaseRepository[ASNLine]):
    """Repository for ASN line operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ASNLine, session)

    async def get_by_asn(self, asn_id: UUID) -> List[ASNLine]:
        """Get all lines for an ASN."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.asn_id == asn_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.line_number.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_line_number(self, asn_id: UUID) -> int:
        """Get next line number for an ASN."""
        query = select(func.max(self.model.line_number)).where(
            self.model.asn_id == asn_id
        )
        result = await self.session.execute(query)
        max_line = result.scalar() or 0
        return max_line + 1

    async def get_by_po_line(
        self, po_line_id: UUID
    ) -> List[ASNLine]:
        """Get all ASN lines for a PO line."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.po_line_id == po_line_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
