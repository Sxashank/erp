"""Vendor Portal Compliance Routes."""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.compliance_service import VendorComplianceService
from app.models.vendor_portal.enums import ComplianceDocumentType, VerificationStatus
from app.schemas.vendor_portal.compliance import (
    ComplianceDocumentCreate,
    ComplianceDocumentUpdate,
    ComplianceDocumentResponse,
    ComplianceDocumentListResponse,
    ComplianceSummary,
    RequiredDocuments,
    ComplianceVerification,
    NotificationResponse,
    NotificationListResponse,
)

from app.api.deps import get_db_with_tenant
router = APIRouter()


@router.get("/", response_model=ComplianceDocumentListResponse, response_model_by_alias=True)
async def list_documents(
    vendor_id: UUID,  # From auth middleware
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List compliance documents for vendor."""
    service = VendorComplianceService(db)
    documents = await service.get_documents(vendor_id, include_inactive)
    return ComplianceDocumentListResponse(
        items=documents,
        total=len(documents),
    )


@router.get("/summary", response_model=ComplianceSummary, response_model_by_alias=True)
async def get_summary(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Get compliance summary."""
    service = VendorComplianceService(db)
    summary = await service.get_compliance_summary(vendor_id)
    return summary


@router.get("/required", response_model=RequiredDocuments, response_model_by_alias=True)
async def get_required_documents(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Get required documents status."""
    service = VendorComplianceService(db)
    result = await service.get_required_documents(vendor_id, organization_id)
    return result


@router.get("/expiring", response_model=List[ComplianceDocumentResponse], response_model_by_alias=True)
async def get_expiring_documents(
    vendor_id: UUID,  # From auth middleware
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get documents expiring within days."""
    service = VendorComplianceService(db)
    documents = await service.get_expiring_documents(vendor_id, days)
    return documents


@router.get("/expired", response_model=List[ComplianceDocumentResponse], response_model_by_alias=True)
async def get_expired_documents(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Get expired documents."""
    service = VendorComplianceService(db)
    documents = await service.get_expired_documents(vendor_id)
    return documents


@router.post("/", response_model=ComplianceDocumentResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def upload_document(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    document_type: ComplianceDocumentType,
    document_name: str,
    file: UploadFile = File(...),
    document_number: Optional[str] = None,
    issue_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    is_perpetual: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Upload a compliance document."""
    from datetime import date

    service = VendorComplianceService(db)

    # Save file (this would go to object storage in production)
    file_content = await file.read()
    file_path = f"compliance/{vendor_id}/{file.filename}"
    # TODO: Implement actual file storage

    data = ComplianceDocumentCreate(
        document_type=document_type,
        document_name=document_name,
        document_number=document_number,
        issue_date=date.fromisoformat(issue_date) if issue_date else None,
        expiry_date=date.fromisoformat(expiry_date) if expiry_date else None,
        is_perpetual=is_perpetual,
    )

    document = await service.upload_document(
        vendor_id=vendor_id,
        organization_id=organization_id,
        uploaded_by_id=user_id,
        data=data,
        file_path=file_path,
        file_size=len(file_content),
        mime_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "document",
    )

    return document


@router.get("/{document_id}", response_model=ComplianceDocumentResponse, response_model_by_alias=True)
async def get_document(
    vendor_id: UUID,  # From auth middleware
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Get document details."""
    service = VendorComplianceService(db)
    document = await service.get_document(vendor_id, document_id)
    return document


@router.put("/{document_id}", response_model=ComplianceDocumentResponse, response_model_by_alias=True)
async def update_document(
    vendor_id: UUID,  # From auth middleware
    document_id: UUID,
    data: ComplianceDocumentUpdate,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Update document details."""
    service = VendorComplianceService(db)
    document = await service.update_document(vendor_id, document_id, data)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    vendor_id: UUID,  # From auth middleware
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Delete a document."""
    service = VendorComplianceService(db)
    await service.delete_document(vendor_id, document_id)


# Admin endpoint for document verification
@router.post("/{document_id}/verify", response_model=ComplianceDocumentResponse, response_model_by_alias=True)
async def verify_document(
    document_id: UUID,
    user_id: UUID,  # From auth middleware (verifier)
    data: ComplianceVerification,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Verify a compliance document (admin)."""
    service = VendorComplianceService(db)
    document = await service.verify_document(document_id, user_id, data)
    return document


# Notification endpoints
@router.get("/notifications", response_model=NotificationListResponse, response_model_by_alias=True)
async def list_notifications(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List notifications for vendor."""
    service = VendorComplianceService(db)
    notifications, total = await service.get_notifications(
        vendor_id, skip, limit, unread_only
    )
    return NotificationListResponse(
        items=notifications,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/notifications/user", response_model=NotificationListResponse, response_model_by_alias=True)
async def list_user_notifications(
    user_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """List notifications for current user."""
    service = VendorComplianceService(db)
    notifications, total = await service.get_user_notifications(
        user_id, skip, limit, unread_only
    )
    return NotificationListResponse(
        items=notifications,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/notifications/unread-count")
async def count_unread_notifications(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Count unread notifications."""
    service = VendorComplianceService(db)
    count = await service.count_unread_notifications(vendor_id)
    return {"unread_count": count}


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse, response_model_by_alias=True)
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Mark notification as read."""
    service = VendorComplianceService(db)
    notification = await service.mark_notification_read(notification_id, user_id)
    return notification


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    vendor_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Mark all notifications as read."""
    service = VendorComplianceService(db)
    count = await service.mark_all_notifications_read(vendor_id, user_id)
    return {"marked_read": count}


# Admin endpoint for expiry check job
@router.post("/check-expiry")
async def check_document_expiry(
    organization_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Check and send expiry alerts (admin/scheduled job)."""
    service = VendorComplianceService(db)
    alert_count = await service.check_expiry_alerts(organization_id)
    return {"alerts_sent": alert_count}


@router.post("/update-expiry-status")
async def update_expiry_status(
    organization_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_with_tenant)],
):
    """Update expiry status for all documents (admin/scheduled job)."""
    service = VendorComplianceService(db)
    updated_count = await service.update_expiry_status(organization_id)
    return {"updated": updated_count}
