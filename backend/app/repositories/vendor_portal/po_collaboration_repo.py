"""PO Collaboration Repositories."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.vendor_portal.po_collaboration import (
    POAcknowledgement,
    POChangeRequest,
)
from app.models.vendor_portal.enums import (
    POAcknowledgementStatus,
    ChangeRequestType,
    ChangeRequestStatus,
)


class POAcknowledgementRepository(BaseRepository[POAcknowledgement]):
    """Repository for PO acknowledgement operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(POAcknowledgement, session)

    async def get_with_change_requests(self, id: UUID) -> Optional[POAcknowledgement]:
        """Get acknowledgement with change requests."""
        query = (
            select(self.model)
            .options(selectinload(self.model.change_requests))
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_po(self, purchase_order_id: UUID) -> Optional[POAcknowledgement]:
        """Get acknowledgement for a PO."""
        query = select(self.model).where(
            and_(
                self.model.purchase_order_id == purchase_order_id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_by_vendor(
        self, vendor_id: UUID
    ) -> List[POAcknowledgement]:
        """Get pending acknowledgements for a vendor."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.vendor_id == vendor_id,
                    self.model.status == POAcknowledgementStatus.PENDING,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_by_vendor(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[POAcknowledgementStatus] = None,
    ) -> Tuple[List[POAcknowledgement], int]:
        """Get all acknowledgements for a vendor."""
        conditions = [
            self.model.vendor_id == vendor_id,
            self.model.is_active == True,
        ]

        if status:
            conditions.append(self.model.status == status)

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

    async def count_pending_by_vendor(self, vendor_id: UUID) -> int:
        """Count pending acknowledgements for a vendor."""
        query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.status == POAcknowledgementStatus.PENDING,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0


class POChangeRequestRepository(BaseRepository[POChangeRequest]):
    """Repository for PO change request operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(POChangeRequest, session)

    async def get_by_acknowledgement(
        self, acknowledgement_id: UUID
    ) -> List[POChangeRequest]:
        """Get all change requests for an acknowledgement."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.acknowledgement_id == acknowledgement_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.submitted_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_by_organization(
        self, organization_id: UUID
    ) -> List[POChangeRequest]:
        """Get pending change requests for an organization."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.status == ChangeRequestStatus.PENDING,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.submitted_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_request_number(self, organization_id: UUID) -> str:
        """Generate unique change request number."""
        year = datetime.now().year
        prefix = f"CR/{year}/"

        query = select(func.count(self.model.id)).where(
            and_(
                self.model.organization_id == organization_id,
                self.model.request_number.like(f"{prefix}%"),
            )
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1

        return f"{prefix}{count:06d}"
