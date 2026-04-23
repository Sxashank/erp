"""Vendor Portal Module Enums."""

from enum import Enum


class VendorPortalUserStatus(str, Enum):
    """Vendor portal user account status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"


class BusinessType(str, Enum):
    """Business entity type for vendor registration."""

    PROPRIETORSHIP = "PROPRIETORSHIP"
    PARTNERSHIP = "PARTNERSHIP"
    LLP = "LLP"
    PRIVATE_LIMITED = "PRIVATE_LIMITED"
    PUBLIC_LIMITED = "PUBLIC_LIMITED"
    TRUST = "TRUST"
    SOCIETY = "SOCIETY"
    GOVERNMENT = "GOVERNMENT"
    OTHERS = "OTHERS"


class RegistrationStatus(str, Enum):
    """Vendor registration workflow status."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUIRED = "ADDITIONAL_INFO_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RegistrationDocumentType(str, Enum):
    """Document types for vendor registration."""

    PAN_CARD = "PAN_CARD"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    INCORPORATION_CERT = "INCORPORATION_CERT"
    PARTNERSHIP_DEED = "PARTNERSHIP_DEED"
    MOA_AOA = "MOA_AOA"
    CANCELLED_CHEQUE = "CANCELLED_CHEQUE"
    BANK_STATEMENT = "BANK_STATEMENT"
    MSME_CERTIFICATE = "MSME_CERTIFICATE"
    ADDRESS_PROOF = "ADDRESS_PROOF"
    AUTHORIZATION_LETTER = "AUTHORIZATION_LETTER"
    OTHER = "OTHER"


class POAcknowledgementStatus(str, Enum):
    """Purchase order acknowledgement status."""

    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    CHANGE_REQUESTED = "CHANGE_REQUESTED"


class ChangeRequestType(str, Enum):
    """Types of PO change requests from vendor."""

    PRICE = "PRICE"
    QUANTITY = "QUANTITY"
    DELIVERY_DATE = "DELIVERY_DATE"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    SPECIFICATIONS = "SPECIFICATIONS"
    OTHER = "OTHER"


class ChangeRequestStatus(str, Enum):
    """Status of PO change request."""

    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"


class InvoiceMatchingType(str, Enum):
    """Invoice matching type."""

    TWO_WAY = "TWO_WAY"      # Invoice vs PO
    THREE_WAY = "THREE_WAY"  # Invoice vs PO vs GRN


class InvoiceMatchingStatus(str, Enum):
    """Invoice matching result status."""

    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    EXCEPTION = "EXCEPTION"


class VendorInvoiceStatus(str, Enum):
    """Vendor submitted invoice status."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MATCHING_PENDING = "MATCHING_PENDING"
    MATCHED = "MATCHED"
    EXCEPTION = "EXCEPTION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class InvoiceDocumentType(str, Enum):
    """Types of documents attached to vendor invoice."""

    INVOICE_PDF = "INVOICE_PDF"
    E_INVOICE = "E_INVOICE"
    E_WAY_BILL = "E_WAY_BILL"
    DELIVERY_CHALLAN = "DELIVERY_CHALLAN"
    PACKING_LIST = "PACKING_LIST"
    QUALITY_CERT = "QUALITY_CERT"
    TEST_REPORT = "TEST_REPORT"
    OTHER = "OTHER"


class ASNStatus(str, Enum):
    """Advanced Shipping Notice status."""

    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    CANCELLED = "CANCELLED"


class ComplianceDocumentType(str, Enum):
    """Compliance document types that vendors must maintain."""

    PAN_CARD = "PAN_CARD"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    MSME_CERTIFICATE = "MSME_CERTIFICATE"
    CANCELLED_CHEQUE = "CANCELLED_CHEQUE"
    BANK_STATEMENT = "BANK_STATEMENT"
    ISO_CERTIFICATE = "ISO_CERTIFICATE"
    QUALITY_CERTIFICATE = "QUALITY_CERTIFICATE"
    TDS_CERTIFICATE = "TDS_CERTIFICATE"
    INSURANCE_POLICY = "INSURANCE_POLICY"
    POLLUTION_CERT = "POLLUTION_CERT"
    FACTORY_LICENSE = "FACTORY_LICENSE"
    TRADE_LICENSE = "TRADE_LICENSE"
    FSSAI_LICENSE = "FSSAI_LICENSE"
    DRUG_LICENSE = "DRUG_LICENSE"
    IMPORT_EXPORT_CODE = "IMPORT_EXPORT_CODE"
    BIS_CERTIFICATION = "BIS_CERTIFICATION"
    OTHER = "OTHER"


class VerificationStatus(str, Enum):
    """Document verification status."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class VendorOTPPurpose(str, Enum):
    """OTP generation purpose for vendor portal."""

    LOGIN = "LOGIN"
    REGISTRATION = "REGISTRATION"
    INVOICE_SUBMISSION = "INVOICE_SUBMISSION"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    BANK_UPDATE = "BANK_UPDATE"
    PASSWORD_RESET = "PASSWORD_RESET"


class NotificationCategory(str, Enum):
    """Notification categories for vendor portal."""

    PO_RECEIVED = "PO_RECEIVED"
    PO_AMENDED = "PO_AMENDED"
    PO_CANCELLED = "PO_CANCELLED"
    INVOICE_APPROVED = "INVOICE_APPROVED"
    INVOICE_REJECTED = "INVOICE_REJECTED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    PAYMENT_SCHEDULED = "PAYMENT_SCHEDULED"
    DOCUMENT_EXPIRING = "DOCUMENT_EXPIRING"
    DOCUMENT_EXPIRED = "DOCUMENT_EXPIRED"
    REGISTRATION_STATUS = "REGISTRATION_STATUS"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    COMPLIANCE = "COMPLIANCE"
    SYSTEM = "SYSTEM"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


# Aliases for backward compatibility
POChangeRequestStatus = ChangeRequestStatus
POChangeRequestType = ChangeRequestType
