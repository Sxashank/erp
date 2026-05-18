"""Portal Module Models.

Provides customer self-service portal capabilities including:
- OTP-based authentication
- Loan dashboard and payments
- Document management
- Service requests
- Communication
"""

from app.models.portal.communication import (
    PortalAnnouncement,
    PortalMessage,
    PortalNotification,
    PortalTicket,
)
from app.models.portal.document import (
    PortalDocument,
    PortalDocumentRequest,
    PortalKYCVerification,
)
from app.models.portal.enums import (
    ConsentType,
    DeviceType,
    DocumentRequestStatus,
    KYCStatus,
    KYCType,
    MandateFrequency,
    MandateStatus,
    NotificationChannel,
    NotificationPriority,
    OTPPurpose,
    PaymentMode,
    PaymentStatus,
    PortalActorRole,
    PortalDocumentType,
    PortalRegistrationStatus,
    PortalUserStatus,
    ServiceRequestStatus,
    ServiceRequestType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.portal.payment import (
    PortalAutoDebitMandate,
    PortalPaymentRequest,
    PortalPaymentTransaction,
    PortalSavedPaymentMethod,
)
from app.models.portal.portal_user import (
    PortalConsent,
    PortalDevice,
    PortalOTP,
    PortalSession,
    PortalUser,
)
from app.models.portal.portal_user_entity import PortalUserEntity
from app.models.portal.service_request import (
    PortalServiceRequest,
    PortalServiceRequestDocument,
    PortalServiceRequestHistory,
)

__all__ = [
    # Enums
    "PortalUserStatus",
    "PortalRegistrationStatus",
    "PortalActorRole",
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
    "PortalUserEntity",
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
