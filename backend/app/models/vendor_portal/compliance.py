"""Vendor Compliance and Notification Models.

Handles compliance document management and vendor notifications.
"""

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Index,
    Integer,
    Computed,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.vendor_portal.enums import (
    ComplianceDocumentType,
    VerificationStatus,
    NotificationCategory,
)

if TYPE_CHECKING:
    from app.models.vendor_portal.portal_vendor_user import PortalVendorUser
    from app.models.ap_ar.vendor import Vendor
    from app.models.masters.user import User


class VendorComplianceDocument(BaseModel):
    """Vendor compliance documents with expiry tracking.

    Stores and tracks vendor compliance documents like GST certificates,
    ISO certifications, insurance policies, etc.
    """

    __tablename__ = "portal_compliance_document"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
        index=True,
    )

    uploaded_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=False,
    )

    # Document Details
    document_type: Mapped[ComplianceDocumentType] = mapped_column(nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_number: Mapped[Optional[str]] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))

    # Issuing Authority
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(200))
    issued_by: Mapped[Optional[str]] = mapped_column(String(200))

    # Validity
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    is_perpetual: Mapped[bool] = mapped_column(Boolean, default=False)  # No expiry

    # Expiry Tracking (computed fields handled by application)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)
    days_to_expiry: Mapped[Optional[int]] = mapped_column(Integer)

    # Verification Status
    verification_status: Mapped[VerificationStatus] = mapped_column(
        default=VerificationStatus.PENDING
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Rejection
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    rejected_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Renewal Tracking
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_document_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_compliance_document.id"),
        nullable=True,
    )

    # Alerts
    expiry_alert_days: Mapped[int] = mapped_column(Integer, default=30)
    expiry_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    expiry_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    second_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    second_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Mandatory Flag
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    # Remarks
    vendor_remarks: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )
    uploaded_by: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser",
        foreign_keys=[uploaded_by_id],
    )
    verified_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by_id],
    )
    previous_document: Mapped[Optional["VendorComplianceDocument"]] = relationship(
        "VendorComplianceDocument",
        foreign_keys=[previous_document_id],
        remote_side="VendorComplianceDocument.id",
    )

    __table_args__ = (
        Index("ix_portal_compliance_doc_org_vendor", "organization_id", "vendor_id"),
        Index("ix_portal_compliance_doc_type", "vendor_id", "document_type"),
        Index("ix_portal_compliance_doc_expiry", "expiry_date", "is_expired"),
        Index("ix_portal_compliance_doc_status", "vendor_id", "verification_status"),
    )


class VendorNotification(BaseModel):
    """Notifications for vendor portal users.

    Stores notifications for PO receipts, invoice status, payments, etc.
    """

    __tablename__ = "portal_vendor_notification"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
        index=True,
    )

    # Target User (if specific user, otherwise all vendor users)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=True,
        index=True,
    )

    # Notification Details
    category: Mapped[NotificationCategory] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW

    # Reference
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))

    # Action URL (for click-through)
    action_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=True,
    )

    # Email/SMS Delivery
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sms_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Expiry (for time-sensitive notifications)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )
    user: Mapped[Optional["PortalVendorUser"]] = relationship(
        "PortalVendorUser",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index("ix_portal_vendor_notif_vendor_read", "vendor_id", "is_read"),
        Index("ix_portal_vendor_notif_user_read", "user_id", "is_read"),
        Index("ix_portal_vendor_notif_category", "vendor_id", "category"),
        Index("ix_portal_vendor_notif_ref", "reference_type", "reference_id"),
    )
