"""Vendor PO Service."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.repositories.vendor_portal.po_collaboration_repo import (
    POAcknowledgementRepository,
    POChangeRequestRepository,
)
from app.repositories.ap_ar.purchase_order_repo import PurchaseOrderRepository
from app.models.vendor_portal.po_collaboration import (
    POAcknowledgement,
    POChangeRequest,
)
from app.models.vendor_portal.enums import (
    POAcknowledgementStatus,
    ChangeRequestStatus as POChangeRequestStatus,
    ChangeRequestType as POChangeRequestType,
)
from app.schemas.vendor_portal.purchase_order import (
    POAcknowledgementCreate,
    POChangeRequestCreate,
)


class VendorPOService:
    """Service for vendor PO operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ack_repo = POAcknowledgementRepository(session)
        self.change_repo = POChangeRequestRepository(session)
        self.po_repo = PurchaseOrderRepository(session)

    async def get_vendor_pos(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Any], int]:
        """Get purchase orders for a vendor."""
        return await self.po_repo.get_all_by_vendor(
            vendor_id=vendor_id,
            skip=skip,
            limit=limit,
            status=status,
            from_date=from_date,
            to_date=to_date,
            search=search,
        )

    async def get_po_details(
        self,
        vendor_id: UUID,
        po_id: UUID,
    ) -> Any:
        """Get PO details."""
        po = await self.po_repo.get_with_details(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # Get acknowledgement if exists
        acknowledgement = await self.ack_repo.get_by_po(po_id)

        return {
            "purchase_order": po,
            "acknowledgement": acknowledgement,
        }

    async def acknowledge_po(
        self,
        vendor_id: UUID,
        po_id: UUID,
        user_id: UUID,
        data: POAcknowledgementCreate,
    ) -> POAcknowledgement:
        """Acknowledge a purchase order."""
        po = await self.po_repo.get(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # Check if already acknowledged
        existing = await self.ack_repo.get_by_po(po_id)
        if existing:
            if existing.status == POAcknowledgementStatus.ACKNOWLEDGED:
                raise ValidationException("PO already acknowledged")

        # Create or update acknowledgement
        ack_data = {
            "purchase_order_id": po_id,
            "vendor_id": vendor_id,
            "organization_id": po.organization_id,
            "acknowledged_by_id": user_id,
            "status": POAcknowledgementStatus.ACKNOWLEDGED,
            "acknowledged_at": datetime.utcnow(),
            "committed_delivery_date": data.committed_delivery_date,
            "delivery_remarks": data.delivery_remarks,
            "response_history": [
                {
                    "action": "acknowledged",
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": str(user_id),
                    "committed_date": data.committed_delivery_date.isoformat()
                    if data.committed_delivery_date
                    else None,
                    "remarks": data.delivery_remarks,
                }
            ],
        }

        if existing:
            acknowledgement = await self.ack_repo.update(existing, ack_data)
        else:
            acknowledgement = await self.ack_repo.create(ack_data)

        # Update PO status
        po.acknowledgement_status = "ACKNOWLEDGED"
        po.acknowledged_at = datetime.utcnow()

        await self.session.flush()

        # TODO: Send notification to procurement

        return acknowledgement

    async def reject_po(
        self,
        vendor_id: UUID,
        po_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> POAcknowledgement:
        """Reject a purchase order."""
        po = await self.po_repo.get(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # Check if already processed
        existing = await self.ack_repo.get_by_po(po_id)

        ack_data = {
            "purchase_order_id": po_id,
            "vendor_id": vendor_id,
            "organization_id": po.organization_id,
            "acknowledged_by_id": user_id,
            "status": POAcknowledgementStatus.REJECTED,
            "rejected_at": datetime.utcnow(),
            "rejection_reason": reason,
            "response_history": [
                {
                    "action": "rejected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": str(user_id),
                    "reason": reason,
                }
            ],
        }

        if existing:
            # Append to response history
            history = existing.response_history or []
            history.append(ack_data["response_history"][0])
            ack_data["response_history"] = history
            acknowledgement = await self.ack_repo.update(existing, ack_data)
        else:
            acknowledgement = await self.ack_repo.create(ack_data)

        # Update PO status
        po.acknowledgement_status = "REJECTED"

        await self.session.flush()

        # TODO: Send notification to procurement

        return acknowledgement

    async def request_change(
        self,
        vendor_id: UUID,
        po_id: UUID,
        user_id: UUID,
        data: POChangeRequestCreate,
    ) -> POChangeRequest:
        """Request a change to a purchase order."""
        po = await self.po_repo.get(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # Create change request
        change_data = {
            "purchase_order_id": po_id,
            "vendor_id": vendor_id,
            "organization_id": po.organization_id,
            "requested_by_id": user_id,
            "request_type": data.change_type,
            "request_details": data.change_description,
            "line_changes": {
                "po_line_id": str(data.po_line_id) if data.po_line_id else None,
                "po_line_number": data.po_line_number,
                "original_value": data.original_value,
                "requested_value": data.requested_value,
            },
            "justification": data.justification,
            "status": POChangeRequestStatus.PENDING,
            "submitted_at": datetime.utcnow(),
        }

        change_request = await self.change_repo.create(change_data)

        # Update acknowledgement status
        existing_ack = await self.ack_repo.get_by_po(po_id)
        if existing_ack:
            existing_ack.status = POAcknowledgementStatus.CHANGE_REQUESTED
            existing_ack.change_request_id = change_request.id
        else:
            ack_data = {
                "purchase_order_id": po_id,
                "vendor_id": vendor_id,
                "organization_id": po.organization_id,
                "acknowledged_by_id": user_id,
                "status": POAcknowledgementStatus.CHANGE_REQUESTED,
                "change_request_id": change_request.id,
            }
            await self.ack_repo.create(ack_data)

        # Update PO status
        po.acknowledgement_status = "CHANGE_REQUESTED"

        await self.session.flush()

        # TODO: Send notification to procurement

        return change_request

    async def get_change_requests(
        self,
        vendor_id: UUID,
        po_id: Optional[UUID] = None,
        status: Optional[POChangeRequestStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[POChangeRequest], int]:
        """Get change requests for a vendor."""
        return await self.change_repo.get_all_by_vendor(
            vendor_id=vendor_id,
            po_id=po_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def get_change_request_details(
        self,
        vendor_id: UUID,
        request_id: UUID,
    ) -> POChangeRequest:
        """Get change request details."""
        request = await self.change_repo.get(request_id)
        if not request:
            raise NotFoundException("Change request not found")

        if request.vendor_id != vendor_id:
            raise NotFoundException("Change request not found")

        return request

    async def cancel_change_request(
        self,
        vendor_id: UUID,
        request_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> POChangeRequest:
        """Cancel a pending change request."""
        request = await self.change_repo.get(request_id)
        if not request:
            raise NotFoundException("Change request not found")

        if request.vendor_id != vendor_id:
            raise NotFoundException("Change request not found")

        if request.status != POChangeRequestStatus.PENDING:
            raise ValidationException(
                f"Cannot cancel change request in {request.status.value} status"
            )

        request.status = POChangeRequestStatus.CANCELLED
        request.cancelled_at = datetime.utcnow()
        request.cancellation_reason = reason

        await self.session.flush()

        return request

    async def get_pending_acknowledgements(
        self,
        vendor_id: UUID,
    ) -> List[Any]:
        """Get POs pending acknowledgement."""
        return await self.po_repo.get_pending_acknowledgement(vendor_id)

    async def get_acknowledgement_summary(
        self,
        vendor_id: UUID,
    ) -> Dict[str, int]:
        """Get acknowledgement summary for vendor dashboard."""
        summary = await self.ack_repo.get_summary_by_vendor(vendor_id)
        pending_pos = await self.po_repo.count_pending_acknowledgement(vendor_id)

        return {
            "pending_acknowledgement": pending_pos,
            "acknowledged": summary.get("acknowledged", 0),
            "rejected": summary.get("rejected", 0),
            "change_requested": summary.get("change_requested", 0),
            "total": sum(summary.values()) + pending_pos,
        }

    async def get_po_lines(
        self,
        vendor_id: UUID,
        po_id: UUID,
    ) -> List[Any]:
        """Get PO line items."""
        po = await self.po_repo.get(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        return await self.po_repo.get_lines(po_id)

    async def download_po_pdf(
        self,
        vendor_id: UUID,
        po_id: UUID,
    ) -> bytes:
        """Generate and return PO PDF."""
        po = await self.po_repo.get_with_details(po_id)
        if not po:
            raise NotFoundException("Purchase order not found")

        if po.vendor_id != vendor_id:
            raise NotFoundException("Purchase order not found")

        # TODO: Implement PDF generation
        raise NotImplementedError("PDF generation not yet implemented")
