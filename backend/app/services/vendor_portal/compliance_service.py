"""Vendor Compliance Service."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.repositories.vendor_portal.compliance_repo import (
    VendorComplianceDocumentRepository,
    VendorNotificationRepository,
)
from app.models.vendor_portal.compliance import (
    VendorComplianceDocument,
    VendorNotification,
)
from app.models.vendor_portal.enums import (
    ComplianceDocumentType,
    VerificationStatus,
    NotificationCategory,
    NotificationPriority,
)
from app.schemas.vendor_portal.compliance import (
    ComplianceDocumentCreate,
    ComplianceDocumentUpdate,
    ComplianceVerification,
)


class VendorComplianceService:
    """Service for vendor compliance operations."""

    # Required document types by default
    DEFAULT_REQUIRED_DOCUMENTS = [
        ComplianceDocumentType.PAN_CARD,
        ComplianceDocumentType.GST_CERTIFICATE,
        ComplianceDocumentType.CANCELLED_CHEQUE,
    ]

    # Expiry alert thresholds (in days)
    EXPIRY_ALERT_THRESHOLDS = [60, 30, 15, 7]

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = VendorComplianceDocumentRepository(session)
        self.notification_repo = VendorNotificationRepository(session)

    async def get_documents(
        self,
        vendor_id: UUID,
        include_inactive: bool = False,
    ) -> List[VendorComplianceDocument]:
        """Get all compliance documents for a vendor."""
        return await self.doc_repo.get_by_vendor(vendor_id, include_inactive)

    async def get_document(
        self,
        vendor_id: UUID,
        document_id: UUID,
    ) -> VendorComplianceDocument:
        """Get a compliance document."""
        document = await self.doc_repo.get(document_id)
        if not document:
            raise NotFoundException("Document not found")

        if document.vendor_id != vendor_id:
            raise NotFoundException("Document not found")

        return document

    async def upload_document(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        uploaded_by_id: UUID,
        data: ComplianceDocumentCreate,
        file_path: str,
        file_size: int,
        mime_type: str,
        original_filename: str,
    ) -> VendorComplianceDocument:
        """Upload a compliance document."""
        # Check if document type already exists
        existing = await self.doc_repo.get_by_type(vendor_id, data.document_type)
        if existing:
            # Soft delete the old one
            await self.doc_repo.soft_delete(existing.id)

        # Calculate days to expiry
        days_to_expiry = None
        is_expired = False
        if data.expiry_date and not data.is_perpetual:
            days_to_expiry = (data.expiry_date - date.today()).days
            is_expired = days_to_expiry < 0

        doc_data = data.model_dump()
        doc_data.update({
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "uploaded_by_id": uploaded_by_id,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "original_filename": original_filename,
            "days_to_expiry": days_to_expiry,
            "is_expired": is_expired,
            "verification_status": VerificationStatus.PENDING,
        })

        document = await self.doc_repo.create(doc_data)
        await self.session.commit()

        return document

    async def update_document(
        self,
        vendor_id: UUID,
        document_id: UUID,
        data: ComplianceDocumentUpdate,
    ) -> VendorComplianceDocument:
        """Update a compliance document."""
        document = await self.doc_repo.get(document_id)
        if not document:
            raise NotFoundException("Document not found")

        if document.vendor_id != vendor_id:
            raise NotFoundException("Document not found")

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate expiry if expiry_date changed
        if "expiry_date" in update_data:
            expiry_date = update_data["expiry_date"]
            if expiry_date and not document.is_perpetual:
                update_data["days_to_expiry"] = (expiry_date - date.today()).days
                update_data["is_expired"] = update_data["days_to_expiry"] < 0
            else:
                update_data["days_to_expiry"] = None
                update_data["is_expired"] = False

        document = await self.doc_repo.update(document, update_data)
        await self.session.commit()

        return document

    async def delete_document(
        self,
        vendor_id: UUID,
        document_id: UUID,
    ) -> None:
        """Delete (soft delete) a compliance document."""
        document = await self.doc_repo.get(document_id)
        if not document:
            raise NotFoundException("Document not found")

        if document.vendor_id != vendor_id:
            raise NotFoundException("Document not found")

        await self.doc_repo.soft_delete(document_id)
        await self.session.commit()

    async def verify_document(
        self,
        document_id: UUID,
        verified_by_id: UUID,
        data: ComplianceVerification,
    ) -> VendorComplianceDocument:
        """Verify a compliance document (admin operation)."""
        document = await self.doc_repo.get(document_id)
        if not document:
            raise NotFoundException("Document not found")

        document.verification_status = data.status
        document.verified_by_id = verified_by_id
        document.verified_at = datetime.utcnow()
        document.verification_remarks = data.remarks

        await self.session.commit()

        # Create notification for vendor
        await self._create_notification(
            vendor_id=document.vendor_id,
            organization_id=document.organization_id,
            category=NotificationCategory.COMPLIANCE,
            title=f"Document Verification: {document.document_type.value}",
            message=f"Your {document.document_type.value} has been {data.status.value.lower()}.",
            reference_type="compliance_document",
            reference_id=document_id,
        )

        return document

    async def get_expiring_documents(
        self,
        vendor_id: UUID,
        days_threshold: int = 30,
    ) -> List[VendorComplianceDocument]:
        """Get documents expiring within threshold."""
        return await self.doc_repo.get_expiring_by_vendor(vendor_id, days_threshold)

    async def get_expired_documents(
        self,
        vendor_id: UUID,
    ) -> List[VendorComplianceDocument]:
        """Get expired documents for a vendor."""
        documents = await self.doc_repo.get_by_vendor(vendor_id)
        return [doc for doc in documents if doc.is_expired]

    async def get_required_documents(
        self,
        vendor_id: UUID,
        organization_id: UUID,
    ) -> Dict[str, Any]:
        """Get required documents status for a vendor."""
        # Get uploaded documents
        uploaded = await self.doc_repo.get_by_vendor(vendor_id)
        uploaded_types = {doc.document_type for doc in uploaded}

        # Get required document types from organization settings
        # For now, use default list
        required_types = self.DEFAULT_REQUIRED_DOCUMENTS

        # Build status
        documents = []
        for doc_type in required_types:
            uploaded_doc = next(
                (doc for doc in uploaded if doc.document_type == doc_type),
                None
            )
            documents.append({
                "document_type": doc_type,
                "is_required": True,
                "is_uploaded": doc_type in uploaded_types,
                "document": uploaded_doc,
            })

        # Add optional documents that were uploaded
        for doc in uploaded:
            if doc.document_type not in required_types:
                documents.append({
                    "document_type": doc.document_type,
                    "is_required": False,
                    "is_uploaded": True,
                    "document": doc,
                })

        return {
            "total_required": len(required_types),
            "total_uploaded": len([d for d in documents if d["is_uploaded"] and d["is_required"]]),
            "is_complete": all(d["is_uploaded"] for d in documents if d["is_required"]),
            "documents": documents,
        }

    async def get_compliance_summary(
        self,
        vendor_id: UUID,
    ) -> Dict[str, Any]:
        """Get compliance summary for vendor dashboard."""
        return await self.doc_repo.count_by_vendor_status(vendor_id)

    async def check_expiry_alerts(
        self,
        organization_id: UUID,
    ) -> int:
        """Check and create expiry alerts for all vendors."""
        alert_count = 0

        for threshold in self.EXPIRY_ALERT_THRESHOLDS:
            expiring_docs = await self.doc_repo.get_expiring_documents(
                organization_id, threshold
            )

            for doc in expiring_docs:
                # Check if alert already sent for this threshold
                if doc.expiry_alert_sent and doc.days_to_expiry >= threshold:
                    continue

                # Create notification
                await self._create_notification(
                    vendor_id=doc.vendor_id,
                    organization_id=organization_id,
                    category=NotificationCategory.COMPLIANCE,
                    title=f"Document Expiring: {doc.document_type.value}",
                    message=f"Your {doc.document_type.value} expires in {doc.days_to_expiry} days. Please renew.",
                    priority=NotificationPriority.HIGH if threshold <= 15 else NotificationPriority.MEDIUM,
                    reference_type="compliance_document",
                    reference_id=doc.id,
                )

                doc.expiry_alert_sent = True
                doc.expiry_alert_sent_at = datetime.utcnow()
                alert_count += 1

        await self.session.commit()
        return alert_count

    async def update_expiry_status(
        self,
        organization_id: UUID,
    ) -> int:
        """Update expiry status for all documents."""
        today = date.today()
        documents = await self.doc_repo.get_by_vendor(organization_id)
        updated_count = 0

        for doc in documents:
            if doc.is_perpetual or not doc.expiry_date:
                continue

            days_to_expiry = (doc.expiry_date - today).days
            is_expired = days_to_expiry < 0

            if doc.days_to_expiry != days_to_expiry or doc.is_expired != is_expired:
                doc.days_to_expiry = days_to_expiry
                doc.is_expired = is_expired
                updated_count += 1

        await self.session.commit()
        return updated_count

    # Notification methods
    async def get_notifications(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Tuple[List[VendorNotification], int]:
        """Get notifications for a vendor."""
        return await self.notification_repo.get_by_vendor(
            vendor_id, skip, limit, unread_only
        )

    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Tuple[List[VendorNotification], int]:
        """Get notifications for a specific user."""
        return await self.notification_repo.get_by_user(
            user_id, skip, limit, unread_only
        )

    async def count_unread_notifications(
        self,
        vendor_id: UUID,
    ) -> int:
        """Count unread notifications."""
        return await self.notification_repo.count_unread(vendor_id)

    async def mark_notification_read(
        self,
        notification_id: UUID,
        read_by_id: UUID,
    ) -> VendorNotification:
        """Mark notification as read."""
        notification = await self.notification_repo.mark_as_read(
            notification_id, read_by_id
        )
        if not notification:
            raise NotFoundException("Notification not found")
        await self.session.commit()
        return notification

    async def mark_all_notifications_read(
        self,
        vendor_id: UUID,
        read_by_id: UUID,
    ) -> int:
        """Mark all notifications as read."""
        count = await self.notification_repo.mark_all_as_read(vendor_id, read_by_id)
        await self.session.commit()
        return count

    # Private helper methods
    async def _create_notification(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        category: NotificationCategory,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> VendorNotification:
        """Create a notification."""
        notification_data = {
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "category": category,
            "title": title,
            "message": message,
            "priority": priority,
            "reference_type": reference_type,
            "reference_id": reference_id,
        }

        notification = await self.notification_repo.create(notification_data)
        return notification
