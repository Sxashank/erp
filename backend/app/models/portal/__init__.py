"""Portal Module Models.

Provides customer self-service portal capabilities including:
- OTP-based authentication
- Loan dashboard and payments
- Document management
- Service requests
- Communication
"""

from app.models.portal.enums import (
    PortalUserStatus,
    DeviceType,
    OTPPurpose,
    ConsentType,
    NotificationChannel,
    NotificationPriority,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    PaymentMode,
    PaymentStatus,
    MandateStatus,
    MandateFrequency,
    PortalDocumentType,
    DocumentRequestStatus,
    KYCType,
    KYCStatus,
    ServiceRequestType,
    ServiceRequestStatus,
)

from app.models.portal.portal_user import (
    PortalUser,
    PortalSession,
    PortalDevice,
    PortalOTP,
    PortalConsent,
)

from app.models.portal.communication import (
    PortalNotification,
    PortalMessage,
    PortalTicket,
    PortalAnnouncement,
)

from app.models.portal.payment import (
    PortalPaymentRequest,
    PortalPaymentTransaction,
    PortalSavedPaymentMethod,
    PortalAutoDebitMandate,
)

from app.models.portal.document import (
    PortalDocument,
    PortalDocumentRequest,
    PortalKYCVerification,
)

from app.models.portal.service_request import (
    PortalServiceRequest,
    PortalServiceRequestDocument,
    PortalServiceRequestHistory,
)

__all__ = [
    # Enums
    "PortalUserStatus",
    "DeviceType",
    "OTPPurpose",
    "ConsentType",
    "NotificationChannel",
    "NotificationPriority",
    "TicketStatus",
    "TicketPriority",
    "TicketCategory",
    "PaymentMode",
    "PaymentStatus",
    "MandateStatus",
    "MandateFrequency",
    "PortalDocumentType",
    "DocumentRequestStatus",
    "KYCType",
    "KYCStatus",
    "ServiceRequestType",
    "ServiceRequestStatus",
    # Portal User
    "PortalUser",
    "PortalSession",
    "PortalDevice",
    "PortalOTP",
    "PortalConsent",
    # Communication
    "PortalNotification",
    "PortalMessage",
    "PortalTicket",
    "PortalAnnouncement",
    # Payment
    "PortalPaymentRequest",
    "PortalPaymentTransaction",
    "PortalSavedPaymentMethod",
    "PortalAutoDebitMandate",
    # Document
    "PortalDocument",
    "PortalDocumentRequest",
    "PortalKYCVerification",
    # Service Request
    "PortalServiceRequest",
    "PortalServiceRequestDocument",
    "PortalServiceRequestHistory",
]
