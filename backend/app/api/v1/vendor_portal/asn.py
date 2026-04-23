"""Vendor Portal ASN (Advanced Shipping Notice) Routes."""

from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.asn_service import VendorASNService
from app.models.vendor_portal.enums import ASNStatus
from app.schemas.vendor_portal.asn import (
    ASNCreate,
    ASNUpdate,
    ASNResponse,
    ASNListResponse,
    ASNLineCreate,
    ASNLineResponse,
    ASNDispatch,
    ASNTrackingUpdate,
    ASNSummary,
)

router = APIRouter()


@router.get("/", response_model=ASNListResponse)
async def list_asns(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[ASNStatus] = None,
    po_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """List ASNs for vendor."""
    service = VendorASNService(db)
    asns, total = await service.get_vendor_asns(
        vendor_id=vendor_id,
        skip=skip,
        limit=limit,
        status=status,
        po_id=po_id,
        from_date=from_date,
        to_date=to_date,
    )
    return ASNListResponse(
        items=asns,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", response_model=ASNSummary)
async def get_asn_summary(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get ASN summary for dashboard."""
    service = VendorASNService(db)
    summary = await service.get_asn_summary(vendor_id)
    return summary


@router.post("/", response_model=ASNResponse, status_code=status.HTTP_201_CREATED)
async def create_asn(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    data: ASNCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new ASN."""
    service = VendorASNService(db)
    asn = await service.create_asn(
        vendor_id=vendor_id,
        organization_id=organization_id,
        created_by_id=user_id,
        data=data,
    )
    return asn


@router.get("/po/{po_id}/available-lines")
async def get_available_po_lines(
    vendor_id: UUID,  # From auth middleware
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get available PO lines for creating ASN."""
    service = VendorASNService(db)
    lines = await service.get_po_lines_for_asn(vendor_id, po_id)
    return lines


@router.get("/{asn_id}", response_model=ASNResponse)
async def get_asn(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get ASN details."""
    service = VendorASNService(db)
    asn = await service.get_asn(vendor_id, asn_id)
    return asn


@router.put("/{asn_id}", response_model=ASNResponse)
async def update_asn(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    data: ASNUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an ASN draft."""
    service = VendorASNService(db)
    asn = await service.update_asn(vendor_id, asn_id, data)
    return asn


@router.post("/{asn_id}/lines", response_model=ASNLineResponse)
async def add_asn_line(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    data: ASNLineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add line item to ASN."""
    service = VendorASNService(db)
    line = await service.add_line(vendor_id, asn_id, data)
    return line


@router.put("/{asn_id}/lines/{line_id}", response_model=ASNLineResponse)
async def update_asn_line(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    line_id: UUID,
    data: ASNLineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update ASN line item."""
    service = VendorASNService(db)
    line = await service.update_line(vendor_id, asn_id, line_id, data)
    return line


@router.delete("/{asn_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_asn_line(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    line_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove ASN line item."""
    service = VendorASNService(db)
    await service.remove_line(vendor_id, asn_id, line_id)


@router.post("/{asn_id}/dispatch", response_model=ASNResponse)
async def dispatch_asn(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    asn_id: UUID,
    data: ASNDispatch,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark ASN as dispatched."""
    service = VendorASNService(db)
    asn = await service.dispatch_asn(vendor_id, asn_id, user_id, data)
    return asn


@router.put("/{asn_id}/tracking", response_model=ASNResponse)
async def update_tracking(
    vendor_id: UUID,  # From auth middleware
    asn_id: UUID,
    data: ASNTrackingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update tracking information."""
    service = VendorASNService(db)
    asn = await service.update_tracking(vendor_id, asn_id, data)
    return asn


@router.post("/{asn_id}/cancel", response_model=ASNResponse)
async def cancel_asn(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    asn_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel an ASN."""
    service = VendorASNService(db)
    asn = await service.cancel_asn(vendor_id, asn_id, user_id, reason)
    return asn


# Buyer/admin endpoint
@router.post("/{asn_id}/delivered", response_model=ASNResponse)
async def mark_delivered(
    asn_id: UUID,
    user_id: UUID,  # From auth middleware
    delivery_date: Optional[date] = None,
    remarks: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Mark ASN as delivered (buyer operation)."""
    service = VendorASNService(db)
    asn = await service.mark_delivered(asn_id, user_id, delivery_date, remarks)
    return asn
