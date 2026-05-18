"""Portal Module Enums."""

from enum import Enum


class PortalUserStatus(str, Enum):
    """Portal user account status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"


class PortalRegistrationStatus(str, Enum):
    """Borrower-portal registration approval lifecycle.

    PENDING_APPROVAL — OTP verified, awaiting tenant-admin link to an
    ``los_entity``. The portal-user row exists but ``get_portal_user``
    rejects sessions for this status (so logged-in flows are blocked).

    ACTIVE — at least one ``mst_portal_user_entity`` link exists; the
    user can transact on those entities.

    REJECTED — admin rejected the registration with a reason. Cannot
    log in.
    """

    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class PortalActorRole(str, Enum):
    """Integrated scheme-portal actor roles."""

    SCHEME_BORROWER = "scheme_borrower"
    SCHEME_LENDER = "scheme_lender"
    SCHEME_SMFCL_REVIEWER = "scheme_smfcl_reviewer"
    SCHEME_SMFCL_APPROVER = "scheme_smfcl_approver"
    SCHEME_MINISTRY_VIEWER = "scheme_ministry_viewer"
    SCHEME_ADMIN = "scheme_admin"


class DeviceType(str, Enum):
    """Device types for portal access."""

    WEB = "WEB"
    ANDROID = "ANDROID"
    IOS = "IOS"
    MOBILE_WEB = "MOBILE_WEB"


class OTPPurpose(str, Enum):
    """OTP generation purpose."""

    LOGIN = "LOGIN"
    REGISTRATION = "REGISTRATION"
    PAYMENT = "PAYMENT"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    AADHAAR_VERIFICATION = "AADHAAR_VERIFICATION"
    MANDATE_REGISTRATION = "MANDATE_REGISTRATION"


class ConsentType(str, Enum):
    """Customer consent types."""

    TERMS_AND_CONDITIONS = "TERMS_AND_CONDITIONS"
    PRIVACY_POLICY = "PRIVACY_POLICY"
    MARKETING_COMMUNICATIONS = "MARKETING_COMMUNICATIONS"
    E_STATEMENT = "E_STATEMENT"
    AUTO_DEBIT = "AUTO_DEBIT"
    DATA_SHARING = "DATA_SHARING"
    CREDIT_BUREAU = "CREDIT_BUREAU"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    IN_APP = "IN_APP"
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketStatus(str, Enum):
    """Support ticket status."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CUSTOMER = "WAITING_FOR_CUSTOMER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class TicketPriority(str, Enum):
    """Support ticket priority."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketCategory(str, Enum):
    """Support ticket categories."""

    PAYMENT = "PAYMENT"
    LOAN_QUERY = "LOAN_QUERY"
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    TECHNICAL_ISSUE = "TECHNICAL_ISSUE"
    COMPLAINT = "COMPLAINT"
    FEEDBACK = "FEEDBACK"
    FORECLOSURE = "FORECLOSURE"
    OTHER = "OTHER"


class PaymentMode(str, Enum):
    """Payment modes supported."""

    UPI = "UPI"
    NET_BANKING = "NET_BANKING"
    DEBIT_CARD = "DEBIT_CARD"
    CREDIT_CARD = "CREDIT_CARD"
    WALLET = "WALLET"
    NACH = "NACH"
    NEFT = "NEFT"
    RTGS = "RTGS"
    CHEQUE = "CHEQUE"


class PaymentStatus(str, Enum):
    """Payment transaction status."""

    INITIATED = "INITIATED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    EXPIRED = "EXPIRED"


class MandateStatus(str, Enum):
    """NACH/Auto-debit mandate status."""

    PENDING = "PENDING"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class MandateFrequency(str, Enum):
    """Mandate debit frequency."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"
    AS_PRESENTED = "AS_PRESENTED"


class PortalDocumentType(str, Enum):
    """Document types available in portal."""

    LOAN_AGREEMENT = "LOAN_AGREEMENT"
    SANCTION_LETTER = "SANCTION_LETTER"
    DISBURSEMENT_LETTER = "DISBURSEMENT_LETTER"
    REPAYMENT_SCHEDULE = "REPAYMENT_SCHEDULE"
    ACCOUNT_STATEMENT = "ACCOUNT_STATEMENT"
    INTEREST_CERTIFICATE = "INTEREST_CERTIFICATE"
    TDS_CERTIFICATE = "TDS_CERTIFICATE"
    NOC = "NOC"
    FORECLOSURE_STATEMENT = "FORECLOSURE_STATEMENT"
    BALANCE_CONFIRMATION = "BALANCE_CONFIRMATION"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"
    INSURANCE_POLICY = "INSURANCE_POLICY"


class DocumentRequestStatus(str, Enum):
    """Document request status."""

    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


class KYCType(str, Enum):
    """KYC verification types."""

    AADHAAR_OTP = "AADHAAR_OTP"
    AADHAAR_BIOMETRIC = "AADHAAR_BIOMETRIC"
    PAN_VERIFICATION = "PAN_VERIFICATION"
    VIDEO_KYC = "VIDEO_KYC"
    CKYC = "CKYC"


class KYCStatus(str, Enum):
    """KYC verification status."""

    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ServiceRequestType(str, Enum):
    """Service request types."""

    PREPAYMENT = "PREPAYMENT"
    FORECLOSURE = "FORECLOSURE"
    EMI_DATE_CHANGE = "EMI_DATE_CHANGE"
    ADDRESS_CHANGE = "ADDRESS_CHANGE"
    CONTACT_UPDATE = "CONTACT_UPDATE"
    NOC_REQUEST = "NOC_REQUEST"
    STATEMENT_REQUEST = "STATEMENT_REQUEST"
    CERTIFICATE_REQUEST = "CERTIFICATE_REQUEST"
    INSURANCE_CLAIM = "INSURANCE_CLAIM"
    LOAN_RESTRUCTURE = "LOAN_RESTRUCTURE"
    MORATORIUM = "MORATORIUM"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"


class ServiceRequestStatus(str, Enum):
    """Service request status."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
