"""Vendor Compliance Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.models.vendor_portal.enums import (
    ComplianceDocumentType,
    VerificationStatus,
    NotificationCategory,
    NotificationPriority,
)


class ComplianceDocumentCreate(BaseSchema):
    """Create compliance document."""

    document_type: ComplianceDocumentType
    document_name: str = Field(..., max_length=255)
    document_number: Optional[str] = Field(None, max_length=100)

    issuing_authority: Optional[str] = Field(None, max_length=200)
    issued_by: Optional[str] = Field(None, max_length=200)

    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_perpetual: bool = False

    is_mandatory: bool = False
    vendor_remarks: Optional[str] = None


class ComplianceDocumentUpdate(BaseSchema):
    """Update compliance document."""

    document_name: Optional[str] = Field(None, max_length=255)
    document_number: Optional[str] = Field(None, max_length=100)

    issuing_authority: Optional[str] = Field(None, max_length=200)
    issued_by: Optional[str] = Field(None, max_length=200)

    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_perpetual: Optional[bool] = None

    vendor_remarks: Optional[str] = None


class ComplianceDocumentResponse(BaseSchema):
    """Compliance document response."""

    id: UUID
    vendor_id: UUID
    organization_id: UUID

    document_type: ComplianceDocumentType
    document_name: str
    document_number: Optional[str] = None
    file_path: str
    file_size: int
    mime_type: str

    issuing_authority: Optional[str] = None
    issued_by: Optional[str] = None

    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_perpetual: bool

    is_expired: bool
    days_to_expiry: Optional[int] = None

    verification_status: VerificationStatus
    is_verified: bool
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None

    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None

    is_renewal: bool
    previous_document_id: Optional[UUID] = None

    is_mandatory: bool
    vendor_remarks: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class ComplianceDocumentListResponse(BaseSchema):
    """Compliance document list item."""

    id: UUID
    document_type: ComplianceDocumentType
    document_name: str
    document_number: Optional[str] = None
    expiry_date: Optional[date] = None
    is_perpetual: bool
    is_expired: bool
    days_to_expiry: Optional[int] = None
    verification_status: VerificationStatus
    is_mandatory: bool
    created_at: datetime


class ExpiringDocument(BaseSchema):
    """Expiring document details."""

    id: UUID
    document_type: ComplianceDocumentType
    document_name: str
    document_number: Optional[str] = None
    expiry_date: date
    days_to_expiry: int
    is_mandatory: bool


class ExpiringDocumentsResponse(BaseSchema):
    """Expiring documents response."""

    vendor_id: UUID
    as_of_date: date
    days_threshold: int = 30

    expired_count: int
    expiring_soon_count: int

    expired_documents: List[ExpiringDocument] = []
    expiring_documents: List[ExpiringDocument] = []


class RequiredDocument(BaseSchema):
    """Required document details."""

    document_type: ComplianceDocumentType
    document_name: str
    description: Optional[str] = None
    is_mandatory: bool
    is_uploaded: bool
    is_verified: bool
    expiry_date: Optional[date] = None
    is_expired: bool = False
    document_id: Optional[UUID] = None


class RequiredDocumentsResponse(BaseSchema):
    """Required documents response."""

    vendor_id: UUID
    organization_id: UUID

    total_required: int
    uploaded_count: int
    verified_count: int
    pending_count: int
    expired_count: int

    documents: List[RequiredDocument] = []


class VendorNotificationResponse(BaseSchema):
    """Notification response."""

    id: UUID
    category: NotificationCategory
    title: str
    message: str
    priority: str

    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None

    action_url: Optional[str] = None

    is_read: bool
    read_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None
    created_at: datetime


class VendorNotificationListResponse(BaseSchema):
    """Notification list response."""

    total: int
    unread_count: int
    notifications: List[VendorNotificationResponse] = []


class DashboardSummaryResponse(BaseSchema):
    """Dashboard summary response."""

    vendor_id: UUID
    vendor_name: str
    vendor_code: str

    # PO Summary
    pending_po_count: int = 0
    pending_po_value: Decimal = Decimal("0")

    # Invoice Summary
    draft_invoice_count: int = 0
    submitted_invoice_count: int = 0
    approved_invoice_count: int = 0

    # Payment Summary
    total_receivable: Decimal = Decimal("0")
    overdue_amount: Decimal = Decimal("0")
    last_payment_date: Optional[date] = None
    last_payment_amount: Decimal = Decimal("0")

    # Compliance Summary
    expiring_documents_count: int = 0
    expired_documents_count: int = 0

    # ASN Summary
    pending_asn_count: int = 0
    in_transit_count: int = 0

    # Pending Actions
    pending_actions: List["PendingAction"] = []


class PendingAction(BaseSchema):
    """Pending action item."""

    action_type: str
    title: str
    description: str
    count: int = 1
    priority: str = "MEDIUM"
    action_url: Optional[str] = None


class ComplianceVerification(BaseSchema):
    """Verify compliance document."""

    status: VerificationStatus
    remarks: Optional[str] = None


class ComplianceSummary(BaseSchema):
    """Compliance summary for dashboard."""

    total_documents: int = 0
    verified_count: int = 0
    pending_count: int = 0
    rejected_count: int = 0
    expiring_count: int = 0
    expired_count: int = 0


class RequiredDocuments(BaseSchema):
    """Required documents response."""

    required: List[RequiredDocument] = []
    uploaded: List[ComplianceDocumentListResponse] = []


class NotificationResponse(BaseSchema):
    """Vendor notification response."""

    id: UUID
    category: NotificationCategory
    title: str
    message: str
    priority: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    action_url: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseSchema):
    """Notification list response."""

    total: int
    unread_count: int
    notifications: List[NotificationResponse] = []


# Fix forward references
DashboardSummaryResponse.model_rebuild()
