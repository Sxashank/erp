"""Purchase Order repository."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ap_ar.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from app.repositories.base import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """Repository for PurchaseOrder model."""

    def __init__(self, db: AsyncSession):
        super().__init__(PurchaseOrder, db)

    async def get_with_details(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get PO with all lines and vendor details."""
        query = (
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.lines),
                selectinload(PurchaseOrder.vendor),
                selectinload(PurchaseOrder.organization),
            )
            .where(
                PurchaseOrder.id == po_id,
                PurchaseOrder.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_vendor(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get all purchase orders for a vendor with filters."""
        query = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.organization))
            .where(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.is_active == True,
                # Only show POs that have been sent to vendor
                PurchaseOrder.status.in_([
                    POStatus.SENT_TO_VENDOR,
                    POStatus.PARTIALLY_RECEIVED,
                    POStatus.RECEIVED,
                    POStatus.CLOSED,
                ]),
            )
        )

        if status:
            query = query.where(PurchaseOrder.status == status)

        if from_date:
            query = query.where(PurchaseOrder.po_date >= from_date)

        if to_date:
            query = query.where(PurchaseOrder.po_date <= to_date)

        if search:
            search_filter = or_(
                PurchaseOrder.po_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(PurchaseOrder.po_date.desc(), PurchaseOrder.po_number.desc())
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        pos = list(result.scalars().all())

        return pos, total

    async def get_pending_acknowledgement(
        self,
        vendor_id: UUID,
    ) -> List[PurchaseOrder]:
        """Get POs pending vendor acknowledgement."""
        query = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.organization))
            .where(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.is_active == True,
                PurchaseOrder.status == POStatus.SENT_TO_VENDOR,
                PurchaseOrder.acknowledgement_status == "PENDING",
            )
            .order_by(PurchaseOrder.po_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_pending_acknowledgement(
        self,
        vendor_id: UUID,
    ) -> int:
        """Count POs pending vendor acknowledgement."""
        query = (
            select(func.count())
            .select_from(PurchaseOrder)
            .where(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.is_active == True,
                PurchaseOrder.status == POStatus.SENT_TO_VENDOR,
                PurchaseOrder.acknowledgement_status == "PENDING",
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_lines(self, po_id: UUID) -> List[PurchaseOrderLine]:
        """Get all line items for a PO."""
        query = (
            select(PurchaseOrderLine)
            .where(PurchaseOrderLine.purchase_order_id == po_id)
            .order_by(PurchaseOrderLine.line_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        status: Optional[str] = None,
        vendor_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get all purchase orders with filters."""
        query = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.vendor))
            .where(
                PurchaseOrder.organization_id == organization_id,
                PurchaseOrder.deleted_at.is_(None),
            )
        )

        if not include_inactive:
            query = query.where(PurchaseOrder.is_active == True)

        if status:
            query = query.where(PurchaseOrder.status == status)

        if vendor_id:
            query = query.where(PurchaseOrder.vendor_id == vendor_id)

        if from_date:
            query = query.where(PurchaseOrder.po_date >= from_date)

        if to_date:
            query = query.where(PurchaseOrder.po_date <= to_date)

        if search:
            search_filter = or_(
                PurchaseOrder.po_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(PurchaseOrder.po_date.desc(), PurchaseOrder.po_number.desc())
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        pos = list(result.scalars().all())

        return pos, total

    async def get_next_number(self, organization_id: UUID, prefix: str = "PO") -> str:
        """Generate next PO number."""
        query = (
            select(PurchaseOrder.po_number)
            .where(
                PurchaseOrder.organization_id == organization_id,
                PurchaseOrder.po_number.like(f"{prefix}%"),
            )
            .order_by(PurchaseOrder.po_number.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        last_number = result.scalar_one_or_none()

        if last_number:
            try:
                num = int(last_number[len(prefix):]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:06d}"

    async def create_line(self, line_data: dict) -> PurchaseOrderLine:
        """Create a PO line."""
        line = PurchaseOrderLine(**line_data)
        self.session.add(line)
        return line

    async def delete_lines(self, po_id: UUID) -> None:
        """Delete all lines for a PO."""
        query = select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po_id)
        result = await self.session.execute(query)
        lines = result.scalars().all()
        for line in lines:
            await self.session.delete(line)
