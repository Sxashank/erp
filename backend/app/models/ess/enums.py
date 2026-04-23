"""Enums for Employee Self-Service Portal module."""

from enum import Enum


class ESSUserStatus(str, Enum):
    """ESS User account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"


class ClaimType(str, Enum):
    """Reimbursement claim types."""
    TRAVEL = "TRAVEL"
    MEDICAL = "MEDICAL"
    CONVEYANCE = "CONVEYANCE"
    MOBILE = "MOBILE"
    INTERNET = "INTERNET"
    FOOD = "FOOD"
    LOCAL_TRAVEL = "LOCAL_TRAVEL"
    OUTSTATION_TRAVEL = "OUTSTATION_TRAVEL"
    RELOCATION = "RELOCATION"
    TRAINING = "TRAINING"
    CERTIFICATION = "CERTIFICATION"
    OTHER = "OTHER"


class ClaimStatus(str, Enum):
    """Reimbursement claim status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class TicketCategory(str, Enum):
    """Helpdesk ticket category."""
    HR_QUERY = "HR_QUERY"
    LEAVE_ISSUE = "LEAVE_ISSUE"
    SALARY_QUERY = "SALARY_QUERY"
    ATTENDANCE_ISSUE = "ATTENDANCE_ISSUE"
    POLICY_CLARIFICATION = "POLICY_CLARIFICATION"
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    IT_SUPPORT = "IT_SUPPORT"
    HARDWARE_ISSUE = "HARDWARE_ISSUE"
    SOFTWARE_ISSUE = "SOFTWARE_ISSUE"
    ACCESS_REQUEST = "ACCESS_REQUEST"
    NETWORK_ISSUE = "NETWORK_ISSUE"
    OTHER = "OTHER"


class TicketPriority(str, Enum):
    """Helpdesk ticket priority."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TicketStatus(str, Enum):
    """Helpdesk ticket status."""
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_INFO = "PENDING_INFO"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"


class ITDeclarationStatus(str, Enum):
    """IT Declaration status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    PROOF_PENDING = "PROOF_PENDING"
    PROOF_SUBMITTED = "PROOF_SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ITDeclarationSection(str, Enum):
    """IT Declaration sections (Indian Income Tax)."""
    SEC_80C = "80C"  # LIC, PPF, ELSS, etc.
    SEC_80CCC = "80CCC"  # Pension Fund
    SEC_80CCD_1 = "80CCD_1"  # NPS Employee
    SEC_80CCD_1B = "80CCD_1B"  # Additional NPS
    SEC_80CCD_2 = "80CCD_2"  # NPS Employer
    SEC_80D = "80D"  # Medical Insurance
    SEC_80DD = "80DD"  # Disabled Dependent
    SEC_80DDB = "80DDB"  # Medical Treatment
    SEC_80E = "80E"  # Education Loan Interest
    SEC_80EE = "80EE"  # Home Loan Interest (First-time)
    SEC_80EEA = "80EEA"  # Affordable Housing Loan
    SEC_80G = "80G"  # Donations
    SEC_80GG = "80GG"  # Rent Paid (No HRA)
    SEC_80TTA = "80TTA"  # Savings Interest
    SEC_80TTB = "80TTB"  # Senior Citizen Interest
    SEC_80U = "80U"  # Disability
    SEC_24B = "24B"  # Home Loan Interest
    HRA = "HRA"  # House Rent Allowance
    LTA = "LTA"  # Leave Travel Allowance


class RegularizationType(str, Enum):
    """Attendance regularization types."""
    FORGOT_PUNCH = "FORGOT_PUNCH"
    BIOMETRIC_FAILURE = "BIOMETRIC_FAILURE"
    ON_DUTY = "ON_DUTY"
    WORK_FROM_HOME = "WORK_FROM_HOME"
    CLIENT_VISIT = "CLIENT_VISIT"
    TRAINING = "TRAINING"
    OFFICIAL_WORK = "OFFICIAL_WORK"
    OTHER = "OTHER"


class RegularizationStatus(str, Enum):
    """Regularization request status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ProfileUpdateType(str, Enum):
    """Profile update request types."""
    PERSONAL_INFO = "PERSONAL_INFO"
    CONTACT_INFO = "CONTACT_INFO"
    ADDRESS = "ADDRESS"
    BANK_DETAILS = "BANK_DETAILS"
    EMERGENCY_CONTACT = "EMERGENCY_CONTACT"
    FAMILY_DETAILS = "FAMILY_DETAILS"
    EDUCATION = "EDUCATION"
    DOCUMENTS = "DOCUMENTS"


class ProfileUpdateStatus(str, Enum):
    """Profile update request status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
