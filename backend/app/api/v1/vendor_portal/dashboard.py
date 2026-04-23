"""Vendor Portal Dashboard Routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.po_service import VendorPOService
from app.services.vendor_portal.invoice_service import VendorInvoiceService
from app.services.vendor_portal.asn_service import VendorASNService
from app.services.vendor_portal.payment_service import VendorPaymentService
from app.services.vendor_portal.compliance_service import VendorComplianceService
from app.schemas.vendor_portal.compliance import NotificationListResponse

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get vendor dashboard summary."""
    po_service = VendorPOService(db)
    invoice_service = VendorInvoiceService(db)
    asn_service = VendorASNService(db)
    payment_service = VendorPaymentService(db)
    compliance_service = VendorComplianceService(db)

    # Get PO summary
    po_summary = await po_service.get_acknowledgement_summary(vendor_id)

    # Get invoice summary
    invoices, total_invoices = await invoice_service.get_vendor_invoices(
        vendor_id=vendor_id, skip=0, limit=1
    )

    # Get ASN summary
    asn_summary = await asn_service.get_asn_summary(vendor_id)

    # Get payment summary
    payment_summary = await payment_service.get_payment_summary(vendor_id)

    # Get compliance summary
    compliance_summary = await compliance_service.get_compliance_summary(vendor_id)

    return {
        "purchase_orders": {
            "pending_acknowledgement": po_summary.get("pending_acknowledgement", 0),
            "acknowledged": po_summary.get("acknowledged", 0),
            "change_requested": po_summary.get("change_requested", 0),
        },
        "invoices": {
            "total": total_invoices,
            "draft": 0,  # Would need additional query
            "submitted": 0,
            "approved": 0,
            "rejected": 0,
        },
        "asn": asn_summary,
        "payments": {
            "total_outstanding": payment_summary.get("total_outstanding"),
            "pending_payments": payment_summary.get("pending_payments"),
            "last_payment_date": payment_summary.get("last_payment_date"),
            "last_payment_amount": payment_summary.get("last_payment_amount"),
        },
        "compliance": {
            "total_documents": compliance_summary.get("total", 0),
            "verified": compliance_summary.get("verified", 0),
            "pending_verification": compliance_summary.get("pending", 0),
            "expired": compliance_summary.get("expired", 0),
        },
    }


@router.get("/pending-actions")
async def get_pending_actions(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get list of pending actions for vendor."""
    po_service = VendorPOService(db)
    compliance_service = VendorComplianceService(db)

    actions = []

    # Pending PO acknowledgements
    pending_pos = await po_service.get_pending_acknowledgements(vendor_id)
    for po in pending_pos:
        actions.append({
            "type": "po_acknowledgement",
            "title": "PO Pending Acknowledgement",
            "description": f"PO {getattr(po, 'po_number', 'N/A')} requires acknowledgement",
            "reference_id": str(getattr(po, 'id', '')),
            "priority": "high",
        })

    # Expiring compliance documents
    expiring_docs = await compliance_service.get_expiring_documents(vendor_id, 30)
    for doc in expiring_docs:
        actions.append({
            "type": "compliance_expiry",
            "title": "Document Expiring Soon",
            "description": f"{doc.document_type.value} expires in {doc.days_to_expiry} days",
            "reference_id": str(doc.id),
            "priority": "medium" if doc.days_to_expiry > 15 else "high",
        })

    # Expired documents
    expired_docs = await compliance_service.get_expired_documents(vendor_id)
    for doc in expired_docs:
        actions.append({
            "type": "compliance_expired",
            "title": "Document Expired",
            "description": f"{doc.document_type.value} has expired",
            "reference_id": str(doc.id),
            "priority": "critical",
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda x: priority_order.get(x["priority"], 4))

    return {
        "total": len(actions),
        "actions": actions,
    }


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get recent notifications for vendor dashboard."""
    service = VendorComplianceService(db)
    notifications, total = await service.get_notifications(
        vendor_id, skip=0, limit=10, unread_only=False
    )
    return NotificationListResponse(
        items=notifications,
        total=total,
        skip=0,
        limit=10,
    )


@router.get("/quick-stats")
async def get_quick_stats(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get quick stats for dashboard cards."""
    po_service = VendorPOService(db)
    payment_service = VendorPaymentService(db)
    compliance_service = VendorComplianceService(db)

    # Get counts
    po_summary = await po_service.get_acknowledgement_summary(vendor_id)
    unread_count = await compliance_service.count_unread_notifications(vendor_id)
    payment_summary = await payment_service.get_payment_summary(vendor_id)

    return {
        "pending_pos": po_summary.get("pending_acknowledgement", 0),
        "unread_notifications": unread_count,
        "outstanding_amount": payment_summary.get("total_outstanding"),
        "pending_payments": payment_summary.get("pending_payments", 0),
    }


@router.get("/recent-activity")
async def get_recent_activity(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10,
):
    """Get recent activity feed."""
    # This would aggregate recent activities across modules
    # For now, return notifications as activity
    service = VendorComplianceService(db)
    notifications, _ = await service.get_notifications(
        vendor_id, skip=0, limit=limit, unread_only=False
    )

    activities = []
    for n in notifications:
        activities.append({
            "id": str(n.id),
            "type": n.category.value if n.category else "general",
            "title": n.title,
            "message": n.message,
            "timestamp": n.created_at,
            "is_read": n.is_read,
        })

    return {
        "total": len(activities),
        "activities": activities,
    }
