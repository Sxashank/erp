"""Vendor Compliance Repositories."""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.vendor_portal.compliance import (
    VendorComplianceDocument,
    VendorNotification,
)
from app.models.vendor_portal.enums import (
    ComplianceDocumentType,
    VerificationStatus,
    NotificationCategory,
)


class VendorComplianceDocumentRepository(BaseRepository[VendorComplianceDocument]):
    """Repository for vendor compliance document operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorComplianceDocument, session)

    async def get_by_vendor(
        self,
        vendor_id: UUID,
        include_inactive: bool = False,
    ) -> List[VendorComplianceDocument]:
        """Get all compliance documents for a vendor."""
        query = select(self.model).where(self.model.vendor_id == vendor_id)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        query = query.order_by(self.model.document_type.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        vendor_id: UUID,
        document_type: ComplianceDocumentType,
    ) -> Optional[VendorComplianceDocument]:
        """Get document by type for a vendor."""
        query = select(self.model).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.document_type == document_type,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_expiring_documents(
        self,
        organization_id: UUID,
        days_threshold: int = 30,
    ) -> List[VendorComplianceDocument]:
        """Get documents expiring within threshold days."""
        threshold_date = date.today() + timedelta(days=days_threshold)

        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.is_perpetual == False,
                    self.model.expiry_date != None,
                    self.model.expiry_date <= threshold_date,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.expiry_date.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired_documents(
        self,
        organization_id: UUID,
    ) -> List[VendorComplianceDocument]:
        """Get expired documents."""
        today = date.today()

        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.is_perpetual == False,
                    self.model.expiry_date != None,
                    self.model.expiry_date < today,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.expiry_date.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expiring_by_vendor(
        self,
        vendor_id: UUID,
        days_threshold: int = 30,
    ) -> List[VendorComplianceDocument]:
        """Get expiring documents for a vendor."""
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)

        query = (
            select(self.model)
            .where(
                and_(
                    self.model.vendor_id == vendor_id,
                    self.model.is_perpetual == False,
                    self.model.expiry_date != None,
                    self.model.expiry_date >= today,
                    self.model.expiry_date <= threshold_date,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.expiry_date.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_verification(
        self,
        organization_id: UUID,
    ) -> List[VendorComplianceDocument]:
        """Get documents pending verification."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.verification_status == VerificationStatus.PENDING,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_vendor_status(
        self,
        vendor_id: UUID,
    ) -> dict:
        """Count documents by status for a vendor."""
        today = date.today()

        # Total
        total_query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.is_active == True,
            )
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0

        # Verified
        verified_query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.verification_status == VerificationStatus.VERIFIED,
                self.model.is_active == True,
            )
        )
        verified_result = await self.session.execute(verified_query)
        verified = verified_result.scalar() or 0

        # Expired
        expired_query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.is_perpetual == False,
                self.model.expiry_date != None,
                self.model.expiry_date < today,
                self.model.is_active == True,
            )
        )
        expired_result = await self.session.execute(expired_query)
        expired = expired_result.scalar() or 0

        return {
            "total": total,
            "verified": verified,
            "pending": total - verified,
            "expired": expired,
        }


class VendorNotificationRepository(BaseRepository[VendorNotification]):
    """Repository for vendor notification operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorNotification, session)

    async def get_by_vendor(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Tuple[List[VendorNotification], int]:
        """Get notifications for a vendor."""
        conditions = [
            self.model.vendor_id == vendor_id,
            self.model.is_active == True,
        ]

        if unread_only:
            conditions.append(self.model.is_read == False)

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

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Tuple[List[VendorNotification], int]:
        """Get notifications for a specific user."""
        conditions = [
            or_(
                self.model.user_id == user_id,
                self.model.user_id == None,  # Vendor-wide notifications
            ),
            self.model.is_active == True,
        ]

        if unread_only:
            conditions.append(self.model.is_read == False)

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

    async def count_unread(self, vendor_id: UUID) -> int:
        """Count unread notifications for a vendor."""
        query = select(func.count(self.model.id)).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.is_read == False,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_as_read(
        self,
        notification_id: UUID,
        read_by_id: UUID,
    ) -> Optional[VendorNotification]:
        """Mark notification as read."""
        notification = await self.get(notification_id)
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            notification.read_by_id = read_by_id
            await self.session.flush()
            await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(
        self,
        vendor_id: UUID,
        read_by_id: UUID,
    ) -> int:
        """Mark all notifications as read for a vendor."""
        query = select(self.model).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.is_read == False,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        notifications = result.scalars().all()

        count = 0
        now = datetime.utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            notification.read_by_id = read_by_id
            count += 1

        await self.session.flush()
        return count

    async def get_by_reference(
        self,
        reference_type: str,
        reference_id: UUID,
    ) -> List[VendorNotification]:
        """Get notifications by reference."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.reference_type == reference_type,
                    self.model.reference_id == reference_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
