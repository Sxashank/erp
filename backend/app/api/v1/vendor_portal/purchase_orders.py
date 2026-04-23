"""Vendor Portal Purchase Order Routes."""

from datetime import date
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.po_service import VendorPOService
from app.models.vendor_portal.enums import POAcknowledgementStatus, POChangeRequestStatus
from app.schemas.vendor_portal.purchase_order import (
    VendorPOListResponse,
    VendorPODetailResponse,
    POAcknowledgementCreate,
    POAcknowledgementResponse,
    PORejectRequest,
    POChangeRequestCreate,
    POChangeRequestResponse,
    POChangeRequestListResponse,
    POAcknowledgementSummary,
)

router = APIRouter()


@router.get("/", response_model=VendorPOListResponse)
async def list_purchase_orders(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List purchase orders for vendor."""
    service = VendorPOService(db)
    pos, total = await service.get_vendor_pos(
        vendor_id=vendor_id,
        skip=skip,
        limit=limit,
        status=status,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    return VendorPOListResponse(
        items=pos,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/pending", response_model=List[dict])
async def list_pending_acknowledgements(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List POs pending acknowledgement."""
    service = VendorPOService(db)
    pending = await service.get_pending_acknowledgements(vendor_id)
    return pending


@router.get("/summary", response_model=POAcknowledgementSummary)
async def get_acknowledgement_summary(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get acknowledgement summary."""
    service = VendorPOService(db)
    summary = await service.get_acknowledgement_summary(vendor_id)
    return summary


@router.get("/{po_id}", response_model=VendorPODetailResponse)
async def get_purchase_order(
    vendor_id: UUID,  # From auth middleware
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get purchase order details."""
    service = VendorPOService(db)
    result = await service.get_po_details(vendor_id, po_id)
    return result


@router.get("/{po_id}/lines")
async def get_po_lines(
    vendor_id: UUID,  # From auth middleware
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get PO line items."""
    service = VendorPOService(db)
    lines = await service.get_po_lines(vendor_id, po_id)
    return lines


@router.post("/{po_id}/acknowledge", response_model=POAcknowledgementResponse)
async def acknowledge_po(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    po_id: UUID,
    data: POAcknowledgementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Acknowledge a purchase order."""
    service = VendorPOService(db)
    acknowledgement = await service.acknowledge_po(vendor_id, po_id, user_id, data)
    return acknowledgement


@router.post("/{po_id}/reject", response_model=POAcknowledgementResponse)
async def reject_po(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    po_id: UUID,
    data: PORejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a purchase order."""
    service = VendorPOService(db)
    acknowledgement = await service.reject_po(vendor_id, po_id, user_id, data.reason)
    return acknowledgement


@router.post("/{po_id}/request-change", response_model=POChangeRequestResponse)
async def request_change(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    po_id: UUID,
    data: POChangeRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request a change to a purchase order."""
    service = VendorPOService(db)
    change_request = await service.request_change(vendor_id, po_id, user_id, data)
    return change_request


@router.get("/{po_id}/download")
async def download_po_pdf(
    vendor_id: UUID,  # From auth middleware
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download PO as PDF."""
    service = VendorPOService(db)
    pdf_bytes = await service.download_po_pdf(vendor_id, po_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=PO_{po_id}.pdf"
        },
    )


# Change request endpoints
@router.get("/change-requests", response_model=POChangeRequestListResponse)
async def list_change_requests(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    po_id: Optional[UUID] = None,
    status: Optional[POChangeRequestStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """List change requests."""
    service = VendorPOService(db)
    requests, total = await service.get_change_requests(
        vendor_id=vendor_id,
        po_id=po_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return POChangeRequestListResponse(
        items=requests,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/change-requests/{request_id}", response_model=POChangeRequestResponse)
async def get_change_request(
    vendor_id: UUID,  # From auth middleware
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get change request details."""
    service = VendorPOService(db)
    request = await service.get_change_request_details(vendor_id, request_id)
    return request


@router.post("/change-requests/{request_id}/cancel", response_model=POChangeRequestResponse)
async def cancel_change_request(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    request_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending change request."""
    service = VendorPOService(db)
    request = await service.cancel_change_request(vendor_id, request_id, user_id, reason)
    return request
