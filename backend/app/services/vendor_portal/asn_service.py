"""Vendor ASN (Advanced Shipping Notice) Service."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.repositories.vendor_portal.asn_repo import (
    ASNRepository,
    ASNLineRepository,
)
from app.repositories.ap_ar.purchase_order_repo import PurchaseOrderRepository
from app.models.vendor_portal.asn import (
    AdvancedShippingNotice,
    ASNLine,
)
from app.models.vendor_portal.enums import ASNStatus
from app.schemas.vendor_portal.asn import (
    ASNCreate,
    ASNUpdate,
    ASNLineCreate,
    ASNDispatch,
    ASNTrackingUpdate,
)


class VendorASNService:
    """Service for vendor ASN operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.asn_repo = ASNRepository(session)
        self.line_repo = ASNLineRepository(session)
        self.po_repo = PurchaseOrderRepository(session)

    async def create_asn(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        created_by_id: UUID,
        data: ASNCreate,
    ) -> AdvancedShippingNotice:
        """Create a new ASN."""
        # Validate PO
        po = await self.po_repo.get(data.purchase_order_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise ValidationException("Purchase order does not belong to vendor")

        # Generate ASN number
        asn_number = await self.asn_repo.generate_asn_number(organization_id)

        # Create ASN
        asn_data = data.model_dump(exclude={"lines"})
        asn_data.update({
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "created_by_id": created_by_id,
            "asn_number": asn_number,
            "status": ASNStatus.DRAFT,
        })

        asn = await self.asn_repo.create(asn_data)

        # Add lines
        for line_data in data.lines:
            await self._add_asn_line(asn.id, line_data)

        await self.session.commit()

        return await self.asn_repo.get_with_details(asn.id)

    async def update_asn(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        data: ASNUpdate,
    ) -> AdvancedShippingNotice:
        """Update an ASN."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status != ASNStatus.DRAFT:
            raise ValidationException("Only draft ASNs can be updated")

        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        asn = await self.asn_repo.update(asn, update_data)

        # Update lines if provided
        if data.lines is not None:
            # Remove existing lines
            await self.line_repo.delete_by_asn(asn_id)

            # Add new lines
            for line_data in data.lines:
                await self._add_asn_line(asn_id, line_data)

        await self.session.commit()

        return await self.asn_repo.get_with_details(asn_id)

    async def dispatch_asn(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        user_id: UUID,
        data: ASNDispatch,
    ) -> AdvancedShippingNotice:
        """Mark ASN as dispatched."""
        asn = await self.asn_repo.get_with_details(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status != ASNStatus.DRAFT:
            raise ValidationException(
                f"Cannot dispatch ASN in {asn.status.value} status"
            )

        # Validate ASN has lines
        if not asn.lines:
            raise ValidationException("ASN must have at least one line item")

        # Update ASN
        asn.status = ASNStatus.DISPATCHED
        asn.ship_date = data.ship_date or date.today()
        asn.expected_delivery_date = data.expected_delivery_date
        asn.carrier_name = data.carrier_name
        asn.tracking_number = data.tracking_number
        asn.vehicle_number = data.vehicle_number
        asn.driver_name = data.driver_name
        asn.driver_phone = data.driver_phone
        asn.dispatched_by_id = user_id
        asn.dispatched_at = datetime.utcnow()

        await self.session.commit()

        # TODO: Send notification to buyer

        return asn

    async def update_tracking(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        data: ASNTrackingUpdate,
    ) -> AdvancedShippingNotice:
        """Update tracking information."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status not in [ASNStatus.DISPATCHED, ASNStatus.IN_TRANSIT]:
            raise ValidationException(
                f"Cannot update tracking for ASN in {asn.status.value} status"
            )

        update_data = data.model_dump(exclude_unset=True)

        # Update status to in-transit if not already
        if asn.status == ASNStatus.DISPATCHED:
            update_data["status"] = ASNStatus.IN_TRANSIT

        asn = await self.asn_repo.update(asn, update_data)
        await self.session.commit()

        return asn

    async def mark_delivered(
        self,
        asn_id: UUID,
        delivered_by_id: UUID,
        delivery_date: Optional[date] = None,
        remarks: Optional[str] = None,
    ) -> AdvancedShippingNotice:
        """Mark ASN as delivered (usually by buyer)."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.status not in [ASNStatus.DISPATCHED, ASNStatus.IN_TRANSIT]:
            raise ValidationException(
                f"Cannot mark as delivered ASN in {asn.status.value} status"
            )

        asn.status = ASNStatus.DELIVERED
        asn.actual_delivery_date = delivery_date or date.today()
        asn.delivery_remarks = remarks

        await self.session.commit()

        return asn

    async def cancel_asn(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> AdvancedShippingNotice:
        """Cancel an ASN."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status not in [ASNStatus.DRAFT, ASNStatus.DISPATCHED]:
            raise ValidationException(
                f"Cannot cancel ASN in {asn.status.value} status"
            )

        asn.status = ASNStatus.CANCELLED
        asn.cancelled_by_id = user_id
        asn.cancelled_at = datetime.utcnow()
        asn.cancellation_reason = reason

        await self.session.commit()

        return asn

    async def get_asn(
        self,
        vendor_id: UUID,
        asn_id: UUID,
    ) -> AdvancedShippingNotice:
        """Get ASN by ID."""
        asn = await self.asn_repo.get_with_details(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        return asn

    async def get_vendor_asns(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ASNStatus] = None,
        po_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[AdvancedShippingNotice], int]:
        """Get all ASNs for a vendor."""
        return await self.asn_repo.get_all_by_vendor(
            vendor_id=vendor_id,
            skip=skip,
            limit=limit,
            status=status,
            po_id=po_id,
            from_date=from_date,
            to_date=to_date,
        )

    async def get_asn_summary(
        self,
        vendor_id: UUID,
    ) -> Dict[str, int]:
        """Get ASN summary for vendor dashboard."""
        return await self.asn_repo.get_summary_by_vendor(vendor_id)

    async def add_line(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        data: ASNLineCreate,
    ) -> ASNLine:
        """Add a line item to ASN."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status != ASNStatus.DRAFT:
            raise ValidationException("Only draft ASNs can be modified")

        line = await self._add_asn_line(asn_id, data)
        await self.session.commit()

        return line

    async def update_line(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        line_id: UUID,
        data: ASNLineCreate,
    ) -> ASNLine:
        """Update ASN line item."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status != ASNStatus.DRAFT:
            raise ValidationException("Only draft ASNs can be modified")

        line = await self.line_repo.get(line_id)
        if not line or line.asn_id != asn_id:
            raise NotFoundException("ASN line not found")

        update_data = data.model_dump(exclude_unset=True)
        line = await self.line_repo.update(line, update_data)
        await self.session.commit()

        return line

    async def remove_line(
        self,
        vendor_id: UUID,
        asn_id: UUID,
        line_id: UUID,
    ) -> None:
        """Remove ASN line item."""
        asn = await self.asn_repo.get(asn_id)
        if not asn:
            raise NotFoundException("ASN not found")

        if asn.vendor_id != vendor_id:
            raise NotFoundException("ASN not found")

        if asn.status != ASNStatus.DRAFT:
            raise ValidationException("Only draft ASNs can be modified")

        line = await self.line_repo.get(line_id)
        if not line or line.asn_id != asn_id:
            raise NotFoundException("ASN line not found")

        await self.line_repo.soft_delete(line_id)
        await self.session.commit()

    async def get_po_lines_for_asn(
        self,
        vendor_id: UUID,
        po_id: UUID,
    ) -> List[Any]:
        """Get available PO lines for creating ASN."""
        po = await self.po_repo.get(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # Get PO lines with pending quantities
        return await self.po_repo.get_lines_with_pending_shipment(po_id)

    # Private helper methods
    async def _add_asn_line(
        self,
        asn_id: UUID,
        data: ASNLineCreate,
    ) -> ASNLine:
        """Add a line item to ASN."""
        line_number = await self.line_repo.get_next_line_number(asn_id)

        line_data = data.model_dump()
        line_data.update({
            "asn_id": asn_id,
            "line_number": line_number,
        })

        line = await self.line_repo.create(line_data)
        return line
