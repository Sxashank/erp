"""Vendor Portal Schemas."""

from app.schemas.vendor_portal.auth import (
    VendorLoginRequest,
    VendorLoginResponse,
    VendorOTPRequest,
    VendorOTPVerify,
    VendorPasswordReset,
    VendorTokenRefresh,
    VendorUserProfile,
    VendorUserProfileUpdate,
)
from app.schemas.vendor_portal.registration import (
    VendorRegistrationCreate,
    VendorRegistrationUpdate,
    VendorRegistrationResponse,
    VendorRegistrationDocumentCreate,
    VendorRegistrationDocumentResponse,
    VendorRegistrationSubmit,
)
from app.schemas.vendor_portal.profile import (
    VendorProfileResponse,
    VendorProfileUpdate,
    VendorBankAccountCreate,
    VendorBankAccountUpdate,
    VendorContactCreate,
    VendorContactUpdate,
    VendorUserCreate,
    VendorUserUpdate,
    VendorUserResponse,
)
from app.schemas.vendor_portal.purchase_order import (
    POListResponse,
    PODetailResponse,
    POAcknowledgeRequest,
    PORejectRequest,
    POChangeRequestCreate,
    POChangeRequestResponse,
)
from app.schemas.vendor_portal.invoice import (
    VendorInvoiceCreate,
    VendorInvoiceUpdate,
    VendorInvoiceResponse,
    VendorInvoiceLineCreate,
    VendorInvoiceLineUpdate,
    VendorInvoiceDocumentCreate,
    InvoiceMatchingResult,
    InvoiceSubmitResponse,
)
from app.schemas.vendor_portal.asn import (
    ASNCreate,
    ASNUpdate,
    ASNResponse,
    ASNLineCreate,
    ASNLineUpdate,
    ASNDispatchRequest,
    ASNTrackingUpdate,
)
from app.schemas.vendor_portal.payment import (
    PaymentListResponse,
    PaymentDetailResponse,
    PaymentAgingResponse,
    AccountStatementRequest,
    AccountStatementResponse,
)
from app.schemas.vendor_portal.compliance import (
    ComplianceDocumentCreate,
    ComplianceDocumentUpdate,
    ComplianceDocumentResponse,
    ExpiringDocumentsResponse,
    RequiredDocumentsResponse,
)

__all__ = [
    # Auth
    "VendorLoginRequest",
    "VendorLoginResponse",
    "VendorOTPRequest",
    "VendorOTPVerify",
    "VendorPasswordReset",
    "VendorTokenRefresh",
    "VendorUserProfile",
    "VendorUserProfileUpdate",
    # Registration
    "VendorRegistrationCreate",
    "VendorRegistrationUpdate",
    "VendorRegistrationResponse",
    "VendorRegistrationDocumentCreate",
    "VendorRegistrationDocumentResponse",
    "VendorRegistrationSubmit",
    # Profile
    "VendorProfileResponse",
    "VendorProfileUpdate",
    "VendorBankAccountCreate",
    "VendorBankAccountUpdate",
    "VendorContactCreate",
    "VendorContactUpdate",
    "VendorUserCreate",
    "VendorUserUpdate",
    "VendorUserResponse",
    # PO
    "POListResponse",
    "PODetailResponse",
    "POAcknowledgeRequest",
    "PORejectRequest",
    "POChangeRequestCreate",
    "POChangeRequestResponse",
    # Invoice
    "VendorInvoiceCreate",
    "VendorInvoiceUpdate",
    "VendorInvoiceResponse",
    "VendorInvoiceLineCreate",
    "VendorInvoiceLineUpdate",
    "VendorInvoiceDocumentCreate",
    "InvoiceMatchingResult",
    "InvoiceSubmitResponse",
    # ASN
    "ASNCreate",
    "ASNUpdate",
    "ASNResponse",
    "ASNLineCreate",
    "ASNLineUpdate",
    "ASNDispatchRequest",
    "ASNTrackingUpdate",
    # Payment
    "PaymentListResponse",
    "PaymentDetailResponse",
    "PaymentAgingResponse",
    "AccountStatementRequest",
    "AccountStatementResponse",
    # Compliance
    "ComplianceDocumentCreate",
    "ComplianceDocumentUpdate",
    "ComplianceDocumentResponse",
    "ExpiringDocumentsResponse",
    "RequiredDocumentsResponse",
]
