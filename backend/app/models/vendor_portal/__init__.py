"""Vendor Portal Models.

Enterprise-grade vendor/supplier portal for self-service operations.
"""

from app.models.vendor_portal.enums import (
    VendorPortalUserStatus,
    BusinessType,
    RegistrationStatus,
    RegistrationDocumentType,
    POAcknowledgementStatus,
    ChangeRequestType,
    ChangeRequestStatus,
    InvoiceMatchingType,
    InvoiceMatchingStatus,
    VendorInvoiceStatus,
    InvoiceDocumentType,
    ASNStatus,
    ComplianceDocumentType,
    VerificationStatus,
    VendorOTPPurpose,
    NotificationCategory,
)
from app.models.vendor_portal.portal_vendor_user import (
    PortalVendorUser,
    PortalVendorSession,
    PortalVendorOTP,
)
from app.models.vendor_portal.registration import (
    VendorRegistration,
    VendorRegistrationDocument,
)
from app.models.vendor_portal.po_collaboration import (
    POAcknowledgement,
    POChangeRequest,
)
from app.models.vendor_portal.invoice import (
    VendorInvoice,
    VendorInvoiceLine,
    VendorInvoiceDocument,
)
from app.models.vendor_portal.asn import (
    AdvancedShippingNotice,
    ASNLine,
)
from app.models.vendor_portal.compliance import (
    VendorComplianceDocument,
    VendorNotification,
)

__all__ = [
    # Enums
    "VendorPortalUserStatus",
    "BusinessType",
    "RegistrationStatus",
    "RegistrationDocumentType",
    "POAcknowledgementStatus",
    "ChangeRequestType",
    "ChangeRequestStatus",
    "InvoiceMatchingType",
    "InvoiceMatchingStatus",
    "VendorInvoiceStatus",
    "InvoiceDocumentType",
    "ASNStatus",
    "ComplianceDocumentType",
    "VerificationStatus",
    "VendorOTPPurpose",
    "NotificationCategory",
    # Models
    "PortalVendorUser",
    "PortalVendorSession",
    "PortalVendorOTP",
    "VendorRegistration",
    "VendorRegistrationDocument",
    "POAcknowledgement",
    "POChangeRequest",
    "VendorInvoice",
    "VendorInvoiceLine",
    "VendorInvoiceDocument",
    "AdvancedShippingNotice",
    "ASNLine",
    "VendorComplianceDocument",
    "VendorNotification",
]
