"""Application constants and enums."""

from enum import Enum


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"
    PENDING = "PENDING"


class AuthType(str, Enum):
    """Authentication type."""
    LOCAL = "LOCAL"
    LDAP = "LDAP"
    SSO = "SSO"


class UnitType(str, Enum):
    """Organization unit type."""
    HEAD_OFFICE = "HEAD_OFFICE"
    BRANCH = "BRANCH"
    REGIONAL_OFFICE = "REGIONAL_OFFICE"
    PROJECT_OFFICE = "PROJECT_OFFICE"


class EntityStatus(str, Enum):
    """Generic entity status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"


class PermissionAction(str, Enum):
    """Permission action types."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    EXPORT = "EXPORT"


# Permission Modules
class PermissionModule(str, Enum):
    """Permission module categories."""
    MASTERS = "MASTERS"
    USER_MGMT = "USER_MGMT"
    FINANCE = "FINANCE"
    GL = "GL"
    GST = "GST"
    TDS = "TDS"
    LENDING = "LENDING"
    LOAN_MGMT = "LOAN_MGMT"
    TREASURY = "TREASURY"
    HR = "HR"
    PAYROLL = "PAYROLL"
    COMPLIANCE = "COMPLIANCE"
    REPORTS = "REPORTS"


# Default System Roles
SYSTEM_ROLES = [
    "SUPER_ADMIN",
    "ORG_ADMIN",
    "BRANCH_MANAGER",
    "OPERATOR",
    "VIEWER",
]


# Token Types
class TokenType(str, Enum):
    """Token types for JWT."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    MFA = "mfa"


# Finance Module Enums
class AccountNature(str, Enum):
    """Account nature/category in COA."""
    ASSETS = "ASSETS"
    LIABILITIES = "LIABILITIES"
    INCOME = "INCOME"
    EXPENSES = "EXPENSES"
    EQUITY = "EQUITY"


class AccountType(str, Enum):
    """Type of account in COA."""
    GROUP = "GROUP"
    LEDGER = "LEDGER"
    BANK = "BANK"
    CASH = "CASH"
    CONTROL = "CONTROL"


class ControlAccountType(str, Enum):
    """Type of control account for sub-ledgers."""
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    BANK = "BANK"
    EMPLOYEE = "EMPLOYEE"


class BalanceType(str, Enum):
    """Balance type - Debit or Credit."""
    DEBIT = "DR"
    CREDIT = "CR"


class VoucherClass(str, Enum):
    """Classification of voucher types."""
    JOURNAL = "JOURNAL"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    CONTRA = "CONTRA"
    SALES = "SALES"
    PURCHASE = "PURCHASE"
    DEBIT_NOTE = "DEBIT_NOTE"
    CREDIT_NOTE = "CREDIT_NOTE"


class VoucherStatus(str, Enum):
    """Status of a voucher in workflow."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PartyType(str, Enum):
    """Type of party for voucher lines."""
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"


class GSTRegistrationType(str, Enum):
    """GST registration type."""
    REGULAR = "REGULAR"
    COMPOSITION = "COMPOSITION"
    SEZ = "SEZ"
    DEEMED_EXPORT = "DEEMED_EXPORT"
    CASUAL = "CASUAL"
    NON_RESIDENT = "NON_RESIDENT"
    UNREGISTERED = "UNREGISTERED"


class HSNSACType(str, Enum):
    """Type of code - HSN for goods, SAC for services."""
    HSN = "HSN"
    SAC = "SAC"


class GSTTransactionType(str, Enum):
    """GST transaction type for invoice."""
    B2B = "B2B"  # Business to Business
    B2C_LARGE = "B2C_LARGE"  # B2C Large (>2.5L)
    B2C_SMALL = "B2C_SMALL"  # B2C Small
    EXPORT = "EXPORT"
    SEZ = "SEZ"
    NIL_RATED = "NIL_RATED"
    EXEMPT = "EXEMPT"


class TDSDeducteeType(str, Enum):
    """TDS deductee type for rate determination."""
    INDIVIDUAL = "INDIVIDUAL"
    HUF = "HUF"
    COMPANY = "COMPANY"
    FIRM = "FIRM"
    AOP_BOI = "AOP_BOI"
    LOCAL_AUTHORITY = "LOCAL_AUTHORITY"
    GOVERNMENT = "GOVERNMENT"
    TRUST = "TRUST"
    FOREIGN_COMPANY = "FOREIGN_COMPANY"


class TDSChallanStatus(str, Enum):
    """TDS challan payment status."""
    PENDING = "PENDING"
    PAID = "PAID"
    VERIFIED = "VERIFIED"


class TDSReturnType(str, Enum):
    """TDS return form type."""
    FORM_24Q = "24Q"  # Salary
    FORM_26Q = "26Q"  # Non-salary
    FORM_27Q = "27Q"  # Non-resident
    FORM_27EQ = "27EQ"  # TCS


class RecurrenceFrequency(str, Enum):
    """Frequency for recurring vouchers."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class GLEntryType(str, Enum):
    """Type of GL entry for audit trail."""
    NORMAL = "NORMAL"  # Regular posting
    REVERSAL = "REVERSAL"  # Reversal of a previous entry
    OPENING = "OPENING"  # Opening balance entry
    CLOSING = "CLOSING"  # Year-end closing entry
    ADJUSTMENT = "ADJUSTMENT"  # Adjustment entry (audit, correction)
    ACCRUAL = "ACCRUAL"  # Accrual entry (interest, provisions)
    DEPRECIATION = "DEPRECIATION"  # Depreciation entry
    REVALUATION = "REVALUATION"  # Revaluation (forex, investment)


# ============================================
# Fixed Assets Module Enums
# ============================================
class AssetType(str, Enum):
    """Type of fixed asset."""
    TANGIBLE = "TANGIBLE"
    INTANGIBLE = "INTANGIBLE"
    RIGHT_OF_USE = "RIGHT_OF_USE"


class DepreciationMethod(str, Enum):
    """Depreciation calculation method."""
    SLM = "SLM"  # Straight Line Method
    WDV = "WDV"  # Written Down Value
    UNIT_OF_PRODUCTION = "UNIT_OF_PRODUCTION"
    NO_DEPRECIATION = "NO_DEPRECIATION"


class AssetAcquisitionType(str, Enum):
    """How the asset was acquired."""
    PURCHASE = "PURCHASE"
    LEASE = "LEASE"
    DONATION = "DONATION"
    TRANSFER_IN = "TRANSFER_IN"
    CONSTRUCTED = "CONSTRUCTED"
    GIFT = "GIFT"


class AssetStatus(str, Enum):
    """Status of a fixed asset."""
    DRAFT = "DRAFT"  # Not yet capitalized
    ACTIVE = "ACTIVE"  # In use
    DISPOSED = "DISPOSED"  # Sold/scrapped
    TRANSFERRED = "TRANSFERRED"  # Transferred to another org/unit
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    FULLY_DEPRECIATED = "FULLY_DEPRECIATED"


class AssetDisposalType(str, Enum):
    """Type of asset disposal."""
    SALE = "SALE"
    SCRAP = "SCRAP"
    WRITE_OFF = "WRITE_OFF"
    TRANSFER_OUT = "TRANSFER_OUT"
    DONATION = "DONATION"
    EXCHANGE = "EXCHANGE"


class DepreciationType(str, Enum):
    """Type of depreciation entry."""
    REGULAR = "REGULAR"  # Normal monthly depreciation
    ADDITIONAL = "ADDITIONAL"  # Additional depreciation (IT Act)
    REVERSAL = "REVERSAL"  # Correction/reversal
    CATCH_UP = "CATCH_UP"  # Catch-up for missed periods


class DepreciationBook(str, Enum):
    """Depreciation book type for dual depreciation tracking."""
    COMPANIES_ACT = "COMPANIES_ACT"  # As per Companies Act (financial statements)
    IT_ACT = "IT_ACT"  # As per Income Tax Act (tax computation)


class ITActAssetBlock(str, Enum):
    """IT Act asset blocks as per Schedule II (Section 32)."""
    # Tangible Assets
    BLOCK_1 = "BLOCK_1"  # Buildings (5% - Residential)
    BLOCK_2 = "BLOCK_2"  # Buildings (10% - Non-residential)
    BLOCK_3 = "BLOCK_3"  # Buildings (40% - Temporary structures)
    BLOCK_4 = "BLOCK_4"  # Furniture & Fittings (10%)
    BLOCK_5 = "BLOCK_5"  # Machinery - General (15%)
    BLOCK_6 = "BLOCK_6"  # Machinery - High efficiency (30%)
    BLOCK_7 = "BLOCK_7"  # Ships/Vessels (20%)
    BLOCK_8 = "BLOCK_8"  # Motor Vehicles (15%)
    BLOCK_9 = "BLOCK_9"  # Motor Vehicles - Hire/Leasing (30%)
    BLOCK_10 = "BLOCK_10"  # Aircrafts (40%)
    BLOCK_11 = "BLOCK_11"  # Containers (50%)
    # Intangible Assets
    BLOCK_12 = "BLOCK_12"  # Intangible Assets (25%)


class AssetTransferStatus(str, Enum):
    """Status of asset transfer."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class RevaluationType(str, Enum):
    """Type of asset revaluation."""
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    IMPAIRMENT = "IMPAIRMENT"


class GLEntrySourceType(str, Enum):
    """Source of GL entry - tracks where the entry originated."""
    MANUAL = "MANUAL"  # Manual voucher entry
    PURCHASE_BILL = "PURCHASE_BILL"  # From purchase bill approval
    SALES_INVOICE = "SALES_INVOICE"  # From sales invoice approval
    PAYMENT = "PAYMENT"  # From payment approval
    RECEIPT = "RECEIPT"  # From receipt approval
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"  # From loan disbursement
    LOAN_RECEIPT = "LOAN_RECEIPT"  # From loan receipt/repayment
    INTEREST_ACCRUAL = "INTEREST_ACCRUAL"  # From interest accrual process
    FEE_ACCRUAL = "FEE_ACCRUAL"  # From fee accrual process
    NPA_PROVISION = "NPA_PROVISION"  # From NPA provisioning
    TDS = "TDS"  # From TDS deduction
    GST = "GST"  # From GST computation
    DEPRECIATION = "DEPRECIATION"  # From depreciation run
    FOREX = "FOREX"  # From forex revaluation
    BANK_CHARGES = "BANK_CHARGES"  # From bank reconciliation
    IMPORT = "IMPORT"  # Imported from external system
    FIXED_ASSET_CAPITALIZE = "FIXED_ASSET_CAPITALIZE"  # From asset capitalization
    FIXED_ASSET_DISPOSAL = "FIXED_ASSET_DISPOSAL"  # From asset disposal
    FIXED_ASSET_REVALUATION = "FIXED_ASSET_REVALUATION"  # From asset revaluation
    FIXED_ASSET_IMPAIRMENT = "FIXED_ASSET_IMPAIRMENT"  # From asset impairment


class RecurringVoucherStatus(str, Enum):
    """Status of recurring voucher template."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ============================================
# HRIS Module Enums
# ============================================
class Gender(str, Enum):
    """Gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MaritalStatus(str, Enum):
    """Marital status options."""
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"


class Salutation(str, Enum):
    """Name salutation."""
    MR = "MR"
    MS = "MS"
    MRS = "MRS"
    DR = "DR"
    PROF = "PROF"


class EmploymentType(str, Enum):
    """Type of employment."""
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    TRAINEE = "TRAINEE"
    INTERN = "INTERN"
    CONSULTANT = "CONSULTANT"
    PROBATION = "PROBATION"


class EmploymentStatus(str, Enum):
    """Employee status in organization."""
    ACTIVE = "ACTIVE"
    PROBATION = "PROBATION"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    RELIEVED = "RELIEVED"
    ABSCONDING = "ABSCONDING"
    TERMINATED = "TERMINATED"
    SUSPENDED = "SUSPENDED"


class DocumentType(str, Enum):
    """Types of employee documents."""
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    PASSPORT = "PASSPORT"
    VOTER_ID = "VOTER_ID"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    PHOTO = "PHOTO"
    OFFER_LETTER = "OFFER_LETTER"
    APPOINTMENT_LETTER = "APPOINTMENT_LETTER"
    EXPERIENCE_LETTER = "EXPERIENCE_LETTER"
    RELIEVING_LETTER = "RELIEVING_LETTER"
    PAYSLIP = "PAYSLIP"
    EDUCATION_CERTIFICATE = "EDUCATION_CERTIFICATE"
    OTHER = "OTHER"


class FamilyRelation(str, Enum):
    """Family member relationship."""
    FATHER = "FATHER"
    MOTHER = "MOTHER"
    SPOUSE = "SPOUSE"
    SON = "SON"
    DAUGHTER = "DAUGHTER"
    BROTHER = "BROTHER"
    SISTER = "SISTER"
    GUARDIAN = "GUARDIAN"
    OTHER = "OTHER"


class EducationLevel(str, Enum):
    """Education qualification level."""
    HIGH_SCHOOL = "HIGH_SCHOOL"
    INTERMEDIATE = "INTERMEDIATE"
    DIPLOMA = "DIPLOMA"
    GRADUATE = "GRADUATE"
    POST_GRADUATE = "POST_GRADUATE"
    DOCTORATE = "DOCTORATE"
    PROFESSIONAL = "PROFESSIONAL"
    OTHER = "OTHER"


class LifecycleEventType(str, Enum):
    """Types of employee lifecycle events."""
    JOINING = "JOINING"
    CONFIRMATION = "CONFIRMATION"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    DEPARTMENT_CHANGE = "DEPARTMENT_CHANGE"
    DESIGNATION_CHANGE = "DESIGNATION_CHANGE"
    SALARY_REVISION = "SALARY_REVISION"
    SUSPENSION = "SUSPENSION"
    REINSTATEMENT = "REINSTATEMENT"
    RESIGNATION = "RESIGNATION"
    TERMINATION = "TERMINATION"
    RETIREMENT = "RETIREMENT"
    RELIEVING = "RELIEVING"
    ABSCONDING = "ABSCONDING"


class ShiftType(str, Enum):
    """Type of work shift."""
    GENERAL = "GENERAL"
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    NIGHT = "NIGHT"
    ROTATIONAL = "ROTATIONAL"
    FLEXIBLE = "FLEXIBLE"


class HolidayType(str, Enum):
    """Type of holiday."""
    NATIONAL = "NATIONAL"
    STATE = "STATE"
    RESTRICTED = "RESTRICTED"
    COMPANY = "COMPANY"
    OPTIONAL = "OPTIONAL"


class LeaveCategory(str, Enum):
    """Category of leave type."""
    EARNED = "EARNED"
    CASUAL = "CASUAL"
    SICK = "SICK"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    BEREAVEMENT = "BEREAVEMENT"
    COMPENSATORY = "COMPENSATORY"
    LOP = "LOP"
    SABBATICAL = "SABBATICAL"
    OTHER = "OTHER"


class LeaveApplicationStatus(str, Enum):
    """Status of leave application."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    WITHDRAWN = "WITHDRAWN"


class AttendanceStatus(str, Enum):
    """Daily attendance status."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEK_OFF = "WEEK_OFF"
    LATE = "LATE"
    EARLY_LEAVE = "EARLY_LEAVE"
    WORK_FROM_HOME = "WORK_FROM_HOME"
    ON_DUTY = "ON_DUTY"


class AttendanceSource(str, Enum):
    """Source of attendance marking."""
    BIOMETRIC = "BIOMETRIC"
    WEB = "WEB"
    MOBILE = "MOBILE"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"


class RegularizationStatus(str, Enum):
    """Status of attendance regularization."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SalaryComponentType(str, Enum):
    """Type of salary component."""
    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"
    EMPLOYER_CONTRIBUTION = "EMPLOYER_CONTRIBUTION"
    REIMBURSEMENT = "REIMBURSEMENT"


class SalaryComponentCategory(str, Enum):
    """Category of salary component."""
    BASIC = "BASIC"
    HRA = "HRA"
    DA = "DA"
    CONVEYANCE = "CONVEYANCE"
    MEDICAL = "MEDICAL"
    SPECIAL = "SPECIAL"
    BONUS = "BONUS"
    INCENTIVE = "INCENTIVE"
    PF = "PF"
    ESI = "ESI"
    PT = "PT"
    TDS = "TDS"
    LWF = "LWF"
    LOAN = "LOAN"
    ADVANCE = "ADVANCE"
    OTHER = "OTHER"


class PayrollRunStatus(str, Enum):
    """Status of payroll processing run."""
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    LOCKED = "LOCKED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class PayslipStatus(str, Enum):
    """Status of individual payslip."""
    DRAFT = "DRAFT"
    PROCESSED = "PROCESSED"
    LOCKED = "LOCKED"
    PUBLISHED = "PUBLISHED"
    PAID = "PAID"


class SeparationType(str, Enum):
    """Type of employee separation."""
    RESIGNATION = "RESIGNATION"
    TERMINATION = "TERMINATION"
    RETIREMENT = "RETIREMENT"
    ABSCONDING = "ABSCONDING"
    DEATH = "DEATH"
    CONTRACT_END = "CONTRACT_END"


class SeparationStatus(str, Enum):
    """Status of separation process."""
    INITIATED = "INITIATED"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    CLEARANCE_PENDING = "CLEARANCE_PENDING"
    FNF_PENDING = "FNF_PENDING"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"


class ClearanceStatus(str, Enum):
    """Status of clearance item."""
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ============================================
# Approval/Maker-Checker Workflow Enums
# ============================================
class ApprovalWorkflowType(str, Enum):
    """Types of transactions requiring maker-checker approval."""
    # Fixed Assets
    FA_ASSET_CREATION = "FA_ASSET_CREATION"
    FA_ASSET_CAPITALIZATION = "FA_ASSET_CAPITALIZATION"
    FA_ASSET_DISPOSAL = "FA_ASSET_DISPOSAL"
    FA_ASSET_REVALUATION = "FA_ASSET_REVALUATION"
    FA_ASSET_IMPAIRMENT = "FA_ASSET_IMPAIRMENT"
    FA_ASSET_TRANSFER = "FA_ASSET_TRANSFER"
    FA_DEPRECIATION_RUN = "FA_DEPRECIATION_RUN"
    FA_INSURANCE_CLAIM = "FA_INSURANCE_CLAIM"
    FA_LEASE_ACTIVATION = "FA_LEASE_ACTIVATION"
    FA_LEASE_MODIFICATION = "FA_LEASE_MODIFICATION"
    FA_LEASE_TERMINATION = "FA_LEASE_TERMINATION"
    # Finance
    FIN_VOUCHER = "FIN_VOUCHER"
    FIN_JOURNAL = "FIN_JOURNAL"
    # Lending
    LOAN_SANCTION = "LOAN_SANCTION"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_WRITE_OFF = "LOAN_WRITE_OFF"
    LOAN_OTS = "LOAN_OTS"
    # AP/AR
    PAYMENT_RELEASE = "PAYMENT_RELEASE"
    # HR
    PAYROLL_POSTING = "PAYROLL_POSTING"


class ApprovalRequestStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"  # Returned for modification
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ApprovalAction(str, Enum):
    """Action taken by approver."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN = "RETURN"  # Return to maker for changes
    ESCALATE = "ESCALATE"  # Escalate to higher authority


# ============================================
# Permission Constants
# Single source of truth - matches exactly what's used in API endpoints
# ============================================

class Permissions:
    """
    Permission constants for the ERP system.

    These constants match the exact permission strings used in RequirePermissions()
    decorators across the codebase. Always use these constants instead of string
    literals to ensure consistency and enable IDE autocomplete/refactoring.
    """

    # ==========================================
    # SUPER ADMIN
    # ==========================================
    SUPER_ADMIN = "SUPER_ADMIN"

    # ==========================================
    # MASTERS MODULE
    # ==========================================
    # Organization
    MASTER_ORG_VIEW = "MASTER_ORG_VIEW"
    MASTER_ORG_CREATE = "MASTER_ORG_CREATE"
    MASTER_ORG_UPDATE = "MASTER_ORG_UPDATE"
    MASTER_ORG_DELETE = "MASTER_ORG_DELETE"

    # Organization Bank Account
    MASTER_ORG_BANK_CREATE = "MASTER_ORG_BANK_CREATE"
    MASTER_ORG_BANK_UPDATE = "MASTER_ORG_BANK_UPDATE"
    MASTER_ORG_BANK_DELETE = "MASTER_ORG_BANK_DELETE"

    # Organization Address
    MASTER_ORG_ADDRESS_CREATE = "MASTER_ORG_ADDRESS_CREATE"
    MASTER_ORG_ADDRESS_UPDATE = "MASTER_ORG_ADDRESS_UPDATE"
    MASTER_ORG_ADDRESS_DELETE = "MASTER_ORG_ADDRESS_DELETE"

    # Unit
    MASTER_UNIT_VIEW = "MASTER_UNIT_VIEW"
    MASTER_UNIT_CREATE = "MASTER_UNIT_CREATE"
    MASTER_UNIT_UPDATE = "MASTER_UNIT_UPDATE"
    MASTER_UNIT_DELETE = "MASTER_UNIT_DELETE"

    # Department
    MASTER_DEPT_VIEW = "MASTER_DEPT_VIEW"
    MASTER_DEPT_CREATE = "MASTER_DEPT_CREATE"
    MASTER_DEPT_UPDATE = "MASTER_DEPT_UPDATE"
    MASTER_DEPT_DELETE = "MASTER_DEPT_DELETE"

    # Designation
    MASTER_DESIG_VIEW = "MASTER_DESIG_VIEW"
    MASTER_DESIG_CREATE = "MASTER_DESIG_CREATE"
    MASTER_DESIG_UPDATE = "MASTER_DESIG_UPDATE"
    MASTER_DESIG_DELETE = "MASTER_DESIG_DELETE"

    # ==========================================
    # USER MANAGEMENT MODULE
    # ==========================================
    USER_VIEW = "USER_VIEW"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_UNLOCK = "USER_UNLOCK"
    USER_RESET_PASSWORD = "USER_RESET_PASSWORD"
    USER_ROLE_ASSIGN = "USER_ROLE_ASSIGN"

    # Role Management
    ROLE_VIEW = "ROLE_VIEW"
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_UPDATE = "ROLE_UPDATE"
    ROLE_DELETE = "ROLE_DELETE"
    ROLE_PERMISSION_ASSIGN = "ROLE_PERMISSION_ASSIGN"

    # ==========================================
    # FINANCE MODULE
    # ==========================================
    # Financial Year
    FIN_FY_VIEW = "FIN_FY_VIEW"
    FIN_FY_CREATE = "FIN_FY_CREATE"
    FIN_FY_UPDATE = "FIN_FY_UPDATE"
    FIN_FY_DELETE = "FIN_FY_DELETE"
    FIN_FY_CLOSE = "FIN_FY_CLOSE"

    # Chart of Accounts (COA)
    FIN_COA_VIEW = "FIN_COA_VIEW"
    FIN_COA_CREATE = "FIN_COA_CREATE"
    FIN_COA_UPDATE = "FIN_COA_UPDATE"
    FIN_COA_DELETE = "FIN_COA_DELETE"

    # Voucher Types
    FIN_VTYPE_VIEW = "FIN_VTYPE_VIEW"
    FIN_VTYPE_CREATE = "FIN_VTYPE_CREATE"
    FIN_VTYPE_UPDATE = "FIN_VTYPE_UPDATE"
    FIN_VTYPE_DELETE = "FIN_VTYPE_DELETE"

    # Vouchers
    FIN_VOUCHER_VIEW = "FIN_VOUCHER_VIEW"
    FIN_VOUCHER_CREATE = "FIN_VOUCHER_CREATE"
    FIN_VOUCHER_UPDATE = "FIN_VOUCHER_UPDATE"
    FIN_VOUCHER_DELETE = "FIN_VOUCHER_DELETE"
    FIN_VOUCHER_APPROVE = "FIN_VOUCHER_APPROVE"
    FIN_VOUCHER_POST = "FIN_VOUCHER_POST"
    FIN_VOUCHER_CANCEL = "FIN_VOUCHER_CANCEL"

    # Reports
    FIN_REPORT_VIEW = "FIN_REPORT_VIEW"

    # ==========================================
    # AP/AR MODULE
    # ==========================================
    # Payment Terms
    APAR_TERMS_VIEW = "APAR_TERMS_VIEW"
    APAR_TERMS_CREATE = "APAR_TERMS_CREATE"
    APAR_TERMS_UPDATE = "APAR_TERMS_UPDATE"
    APAR_TERMS_DELETE = "APAR_TERMS_DELETE"

    # Vendors
    APAR_VENDOR_VIEW = "APAR_VENDOR_VIEW"
    APAR_VENDOR_CREATE = "APAR_VENDOR_CREATE"
    APAR_VENDOR_UPDATE = "APAR_VENDOR_UPDATE"
    APAR_VENDOR_DELETE = "APAR_VENDOR_DELETE"

    # Customers
    APAR_CUSTOMER_VIEW = "APAR_CUSTOMER_VIEW"
    APAR_CUSTOMER_CREATE = "APAR_CUSTOMER_CREATE"
    APAR_CUSTOMER_UPDATE = "APAR_CUSTOMER_UPDATE"
    APAR_CUSTOMER_DELETE = "APAR_CUSTOMER_DELETE"

    # Purchase Bills
    APAR_BILL_VIEW = "APAR_BILL_VIEW"
    APAR_BILL_CREATE = "APAR_BILL_CREATE"
    APAR_BILL_UPDATE = "APAR_BILL_UPDATE"
    APAR_BILL_DELETE = "APAR_BILL_DELETE"
    APAR_BILL_APPROVE = "APAR_BILL_APPROVE"

    # Sales Invoices
    APAR_INVOICE_VIEW = "APAR_INVOICE_VIEW"
    APAR_INVOICE_CREATE = "APAR_INVOICE_CREATE"
    APAR_INVOICE_UPDATE = "APAR_INVOICE_UPDATE"
    APAR_INVOICE_DELETE = "APAR_INVOICE_DELETE"
    APAR_INVOICE_APPROVE = "APAR_INVOICE_APPROVE"

    # Payments
    APAR_PAYMENT_VIEW = "APAR_PAYMENT_VIEW"
    APAR_PAYMENT_CREATE = "APAR_PAYMENT_CREATE"
    APAR_PAYMENT_UPDATE = "APAR_PAYMENT_UPDATE"
    APAR_PAYMENT_DELETE = "APAR_PAYMENT_DELETE"
    APAR_PAYMENT_APPROVE = "APAR_PAYMENT_APPROVE"

    # ==========================================
    # AUDIT & WORKFLOW MODULE
    # ==========================================
    AUDIT_LOG_VIEW = "AUDIT_LOG_VIEW"

    WORKFLOW_VIEW = "WORKFLOW_VIEW"
    WORKFLOW_CREATE = "WORKFLOW_CREATE"
    WORKFLOW_UPDATE = "WORKFLOW_UPDATE"
    WORKFLOW_DELETE = "WORKFLOW_DELETE"
    WORKFLOW_APPROVE = "WORKFLOW_APPROVE"
    WORKFLOW_CANCEL = "WORKFLOW_CANCEL"

    # ==========================================
    # APPROVAL (MAKER-CHECKER) MODULE
    # ==========================================
    APPROVAL_CONFIG_VIEW = "APPROVAL_CONFIG_VIEW"
    APPROVAL_CONFIG_CREATE = "APPROVAL_CONFIG_CREATE"
    APPROVAL_CONFIG_UPDATE = "APPROVAL_CONFIG_UPDATE"
    APPROVAL_CONFIG_DELETE = "APPROVAL_CONFIG_DELETE"
    APPROVAL_REQUEST_VIEW = "APPROVAL_REQUEST_VIEW"
    APPROVAL_REQUEST_SUBMIT = "APPROVAL_REQUEST_SUBMIT"
    APPROVAL_REQUEST_APPROVE = "APPROVAL_REQUEST_APPROVE"
    APPROVAL_REQUEST_CANCEL = "APPROVAL_REQUEST_CANCEL"
    APPROVAL_PENDING_VIEW = "APPROVAL_PENDING_VIEW"  # View own pending approvals

    # ==========================================
    # LENDING - LOS (Loan Origination System)
    # ==========================================
    # Entity/Borrower
    LOS_ENTITY_VIEW = "LOS_ENTITY_VIEW"
    LOS_ENTITY_CREATE = "LOS_ENTITY_CREATE"
    LOS_ENTITY_UPDATE = "LOS_ENTITY_UPDATE"
    LOS_ENTITY_DELETE = "LOS_ENTITY_DELETE"

    # Loan Products
    LOS_PRODUCT_VIEW = "LOS_PRODUCT_VIEW"
    LOS_PRODUCT_CREATE = "LOS_PRODUCT_CREATE"
    LOS_PRODUCT_UPDATE = "LOS_PRODUCT_UPDATE"
    LOS_PRODUCT_DELETE = "LOS_PRODUCT_DELETE"

    # Loan Applications
    LOS_APPLICATION_VIEW = "LOS_APPLICATION_VIEW"
    LOS_APPLICATION_CREATE = "LOS_APPLICATION_CREATE"
    LOS_APPLICATION_UPDATE = "LOS_APPLICATION_UPDATE"
    LOS_APPLICATION_DELETE = "LOS_APPLICATION_DELETE"

    # Appraisal
    LOS_APPRAISAL_CREATE = "LOS_APPRAISAL_CREATE"
    LOS_APPRAISAL_UPDATE = "LOS_APPRAISAL_UPDATE"

    # Sanction
    LOS_SANCTION_VIEW = "LOS_SANCTION_VIEW"
    LOS_SANCTION_CREATE = "LOS_SANCTION_CREATE"
    LOS_SANCTION_UPDATE = "LOS_SANCTION_UPDATE"
    LOS_SANCTION_APPROVE = "LOS_SANCTION_APPROVE"

    # ==========================================
    # LENDING - LMS (Loan Management System)
    # ==========================================
    # Loan Accounts
    LMS_ACCOUNT_VIEW = "LMS_ACCOUNT_VIEW"
    LMS_ACCOUNT_CREATE = "LMS_ACCOUNT_CREATE"
    LMS_ACCOUNT_UPDATE = "LMS_ACCOUNT_UPDATE"

    # Disbursements
    LMS_DISBURSEMENT_CREATE = "LMS_DISBURSEMENT_CREATE"
    LMS_DISBURSEMENT_APPROVE = "LMS_DISBURSEMENT_APPROVE"
    LMS_DISBURSEMENT_PROCESS = "LMS_DISBURSEMENT_PROCESS"

    # Schedules
    LMS_SCHEDULE_CREATE = "LMS_SCHEDULE_CREATE"

    # Receipts
    LMS_RECEIPT_CREATE = "LMS_RECEIPT_CREATE"
    LMS_RECEIPT_UPDATE = "LMS_RECEIPT_UPDATE"
    LMS_RECEIPT_ALLOCATE = "LMS_RECEIPT_ALLOCATE"

    # Accruals & Adjustments
    LMS_ACCRUAL_RUN = "LMS_ACCRUAL_RUN"
    LMS_ADJUSTMENT_CREATE = "LMS_ADJUSTMENT_CREATE"

    # Classification & Provision
    LMS_CLASSIFICATION_UPDATE = "LMS_CLASSIFICATION_UPDATE"
    LMS_PROVISION_CALCULATE = "LMS_PROVISION_CALCULATE"

    # Mandate
    LMS_MANDATE_CREATE = "LMS_MANDATE_CREATE"
    LMS_MANDATE_UPDATE = "LMS_MANDATE_UPDATE"

    # ==========================================
    # LENDING - COLLECTIONS
    # ==========================================
    COLLECTIONS_READ = "collections:read"
    COLLECTIONS_CREATE = "collections:create"
    COLLECTIONS_UPDATE = "collections:update"
    COLLECTIONS_APPROVE = "collections:approve"

    # NPA
    NPA_READ = "npa:read"
    NPA_CREATE = "npa:create"
    NPA_UPDATE = "npa:update"

    # OTS (One-Time Settlement)
    OTS_CREATE = "ots:create"
    OTS_UPDATE = "ots:update"
    OTS_APPROVE = "ots:approve"

    # Restructure
    RESTRUCTURE_CREATE = "restructure:create"
    RESTRUCTURE_UPDATE = "restructure:update"
    RESTRUCTURE_APPROVE = "restructure:approve"

    # Write-off
    WRITEOFF_CREATE = "writeoff:create"
    WRITEOFF_APPROVE = "writeoff:approve"

    # Legal
    LEGAL_READ = "legal:read"
    LEGAL_CREATE = "legal:create"
    LEGAL_UPDATE = "legal:update"

    # ==========================================
    # LENDING - TREASURY
    # ==========================================
    TREASURY_READ = "treasury:read"
    TREASURY_WRITE = "treasury:write"
    TREASURY_APPROVE = "treasury:approve"

    # ==========================================
    # FIXED ASSETS MODULE
    # ==========================================
    FA_CATEGORY_VIEW = "FA_CATEGORY_VIEW"
    FA_CATEGORY_CREATE = "FA_CATEGORY_CREATE"
    FA_CATEGORY_UPDATE = "FA_CATEGORY_UPDATE"
    FA_CATEGORY_DELETE = "FA_CATEGORY_DELETE"

    FA_ASSET_VIEW = "FA_ASSET_VIEW"
    FA_ASSET_CREATE = "FA_ASSET_CREATE"
    FA_ASSET_UPDATE = "FA_ASSET_UPDATE"
    FA_ASSET_DELETE = "FA_ASSET_DELETE"
    FA_ASSET_CAPITALIZE = "FA_ASSET_CAPITALIZE"
    FA_ASSET_DISPOSE = "FA_ASSET_DISPOSE"
    FA_ASSET_TRANSFER = "FA_ASSET_TRANSFER"
    FA_ASSET_REVALUE = "FA_ASSET_REVALUE"

    FA_DEPRECIATION_VIEW = "FA_DEPRECIATION_VIEW"
    FA_DEPRECIATION_RUN = "FA_DEPRECIATION_RUN"
    FA_DEPRECIATION_REVERSE = "FA_DEPRECIATION_REVERSE"

    FA_REPORT_VIEW = "FA_REPORT_VIEW"

    # ==========================================
    # HRIS MODULE
    # ==========================================
    HRIS_EMPLOYEE_VIEW = "HRIS_EMPLOYEE_VIEW"
    HRIS_EMPLOYEE_CREATE = "HRIS_EMPLOYEE_CREATE"
    HRIS_EMPLOYEE_UPDATE = "HRIS_EMPLOYEE_UPDATE"
    HRIS_EMPLOYEE_DELETE = "HRIS_EMPLOYEE_DELETE"

    HRIS_SHIFT_VIEW = "HRIS_SHIFT_VIEW"
    HRIS_SHIFT_CREATE = "HRIS_SHIFT_CREATE"
    HRIS_SHIFT_UPDATE = "HRIS_SHIFT_UPDATE"
    HRIS_SHIFT_DELETE = "HRIS_SHIFT_DELETE"

    HRIS_HOLIDAY_VIEW = "HRIS_HOLIDAY_VIEW"
    HRIS_HOLIDAY_CREATE = "HRIS_HOLIDAY_CREATE"
    HRIS_HOLIDAY_UPDATE = "HRIS_HOLIDAY_UPDATE"
    HRIS_HOLIDAY_DELETE = "HRIS_HOLIDAY_DELETE"

    HRIS_LEAVE_TYPE_VIEW = "HRIS_LEAVE_TYPE_VIEW"
    HRIS_LEAVE_TYPE_CREATE = "HRIS_LEAVE_TYPE_CREATE"
    HRIS_LEAVE_TYPE_UPDATE = "HRIS_LEAVE_TYPE_UPDATE"
    HRIS_LEAVE_TYPE_DELETE = "HRIS_LEAVE_TYPE_DELETE"

    HRIS_LEAVE_VIEW = "HRIS_LEAVE_VIEW"
    HRIS_LEAVE_APPLY = "HRIS_LEAVE_APPLY"
    HRIS_LEAVE_APPROVE = "HRIS_LEAVE_APPROVE"
    HRIS_LEAVE_CANCEL = "HRIS_LEAVE_CANCEL"

    HRIS_ATTENDANCE_VIEW = "HRIS_ATTENDANCE_VIEW"
    HRIS_ATTENDANCE_MARK = "HRIS_ATTENDANCE_MARK"
    HRIS_ATTENDANCE_REGULARIZE = "HRIS_ATTENDANCE_REGULARIZE"
    HRIS_ATTENDANCE_APPROVE = "HRIS_ATTENDANCE_APPROVE"

    # ==========================================
    # PAYROLL MODULE
    # ==========================================
    PAYROLL_COMPONENT_VIEW = "PAYROLL_COMPONENT_VIEW"
    PAYROLL_COMPONENT_CREATE = "PAYROLL_COMPONENT_CREATE"
    PAYROLL_COMPONENT_UPDATE = "PAYROLL_COMPONENT_UPDATE"
    PAYROLL_COMPONENT_DELETE = "PAYROLL_COMPONENT_DELETE"

    PAYROLL_STRUCTURE_VIEW = "PAYROLL_STRUCTURE_VIEW"
    PAYROLL_STRUCTURE_CREATE = "PAYROLL_STRUCTURE_CREATE"
    PAYROLL_STRUCTURE_UPDATE = "PAYROLL_STRUCTURE_UPDATE"
    PAYROLL_STRUCTURE_DELETE = "PAYROLL_STRUCTURE_DELETE"

    PAYROLL_RUN_VIEW = "PAYROLL_RUN_VIEW"
    PAYROLL_RUN_PROCESS = "PAYROLL_RUN_PROCESS"
    PAYROLL_RUN_LOCK = "PAYROLL_RUN_LOCK"
    PAYROLL_RUN_POST = "PAYROLL_RUN_POST"

    PAYROLL_PAYSLIP_VIEW = "PAYROLL_PAYSLIP_VIEW"
    PAYROLL_PAYSLIP_PUBLISH = "PAYROLL_PAYSLIP_PUBLISH"

    PAYROLL_REPORT_VIEW = "PAYROLL_REPORT_VIEW"

    # ==========================================
    # HRIS - SEPARATION MODULE
    # ==========================================
    HRIS_SEPARATION_VIEW = "HRIS_SEPARATION_VIEW"
    HRIS_SEPARATION_INITIATE = "HRIS_SEPARATION_INITIATE"
    HRIS_SEPARATION_APPROVE = "HRIS_SEPARATION_APPROVE"
    HRIS_SEPARATION_CANCEL = "HRIS_SEPARATION_CANCEL"
    HRIS_CLEARANCE_VIEW = "HRIS_CLEARANCE_VIEW"
    HRIS_CLEARANCE_UPDATE = "HRIS_CLEARANCE_UPDATE"
    HRIS_FNF_VIEW = "HRIS_FNF_VIEW"
    HRIS_FNF_CALCULATE = "HRIS_FNF_CALCULATE"
    HRIS_FNF_APPROVE = "HRIS_FNF_APPROVE"

    # ==========================================
    # HRIS - TRAINING MODULE
    # ==========================================
    HRIS_TRAINING_VIEW = "HRIS_TRAINING_VIEW"
    HRIS_TRAINING_CREATE = "HRIS_TRAINING_CREATE"
    HRIS_TRAINING_UPDATE = "HRIS_TRAINING_UPDATE"
    HRIS_TRAINING_DELETE = "HRIS_TRAINING_DELETE"
    HRIS_TRAINING_NOMINATE = "HRIS_TRAINING_NOMINATE"
    HRIS_TRAINING_APPROVE = "HRIS_TRAINING_APPROVE"
    HRIS_TRAINING_FEEDBACK = "HRIS_TRAINING_FEEDBACK"

    # ==========================================
    # HRIS - PERFORMANCE MODULE
    # ==========================================
    HRIS_APPRAISAL_VIEW = "HRIS_APPRAISAL_VIEW"
    HRIS_APPRAISAL_CREATE = "HRIS_APPRAISAL_CREATE"
    HRIS_APPRAISAL_UPDATE = "HRIS_APPRAISAL_UPDATE"
    HRIS_GOAL_VIEW = "HRIS_GOAL_VIEW"
    HRIS_GOAL_CREATE = "HRIS_GOAL_CREATE"
    HRIS_GOAL_UPDATE = "HRIS_GOAL_UPDATE"
    HRIS_GOAL_APPROVE = "HRIS_GOAL_APPROVE"
    HRIS_SELF_APPRAISAL = "HRIS_SELF_APPRAISAL"
    HRIS_MANAGER_REVIEW = "HRIS_MANAGER_REVIEW"
    HRIS_CALIBRATION = "HRIS_CALIBRATION"

    # ==========================================
    # INVENTORY MODULE
    # ==========================================
    INV_CATEGORY_VIEW = "INV_CATEGORY_VIEW"
    INV_CATEGORY_CREATE = "INV_CATEGORY_CREATE"
    INV_CATEGORY_UPDATE = "INV_CATEGORY_UPDATE"
    INV_CATEGORY_DELETE = "INV_CATEGORY_DELETE"

    INV_ITEM_VIEW = "INV_ITEM_VIEW"
    INV_ITEM_CREATE = "INV_ITEM_CREATE"
    INV_ITEM_UPDATE = "INV_ITEM_UPDATE"
    INV_ITEM_DELETE = "INV_ITEM_DELETE"

    INV_WAREHOUSE_VIEW = "INV_WAREHOUSE_VIEW"
    INV_WAREHOUSE_CREATE = "INV_WAREHOUSE_CREATE"
    INV_WAREHOUSE_UPDATE = "INV_WAREHOUSE_UPDATE"
    INV_WAREHOUSE_DELETE = "INV_WAREHOUSE_DELETE"

    INV_STOCK_VIEW = "INV_STOCK_VIEW"
    INV_STOCK_IN = "INV_STOCK_IN"
    INV_STOCK_OUT = "INV_STOCK_OUT"
    INV_STOCK_TRANSFER = "INV_STOCK_TRANSFER"
    INV_STOCK_ADJUST = "INV_STOCK_ADJUST"
    INV_STOCK_APPROVE = "INV_STOCK_APPROVE"

    INV_REPORT_VIEW = "INV_REPORT_VIEW"

    # ==========================================
    # NOTIFICATION MODULE
    # ==========================================
    NOTIF_VIEW = "NOTIF_VIEW"
    NOTIF_SEND = "NOTIF_SEND"
    NOTIF_TEMPLATE_VIEW = "NOTIF_TEMPLATE_VIEW"
    NOTIF_TEMPLATE_CREATE = "NOTIF_TEMPLATE_CREATE"
    NOTIF_TEMPLATE_UPDATE = "NOTIF_TEMPLATE_UPDATE"
    NOTIF_TEMPLATE_DELETE = "NOTIF_TEMPLATE_DELETE"
    NOTIF_SETTINGS_VIEW = "NOTIF_SETTINGS_VIEW"
    NOTIF_SETTINGS_UPDATE = "NOTIF_SETTINGS_UPDATE"
    NOTIF_LOG_VIEW = "NOTIF_LOG_VIEW"

    # ==========================================
    # DOCUMENT MANAGEMENT SYSTEM (DMS)
    # ==========================================
    DMS_FOLDER_VIEW = "DMS_FOLDER_VIEW"
    DMS_FOLDER_CREATE = "DMS_FOLDER_CREATE"
    DMS_FOLDER_UPDATE = "DMS_FOLDER_UPDATE"
    DMS_FOLDER_DELETE = "DMS_FOLDER_DELETE"

    DMS_DOCUMENT_VIEW = "DMS_DOCUMENT_VIEW"
    DMS_DOCUMENT_UPLOAD = "DMS_DOCUMENT_UPLOAD"
    DMS_DOCUMENT_UPDATE = "DMS_DOCUMENT_UPDATE"
    DMS_DOCUMENT_DELETE = "DMS_DOCUMENT_DELETE"
    DMS_DOCUMENT_DOWNLOAD = "DMS_DOCUMENT_DOWNLOAD"
    DMS_DOCUMENT_SHARE = "DMS_DOCUMENT_SHARE"

    DMS_TAG_VIEW = "DMS_TAG_VIEW"
    DMS_TAG_CREATE = "DMS_TAG_CREATE"
    DMS_TAG_UPDATE = "DMS_TAG_UPDATE"
    DMS_TAG_DELETE = "DMS_TAG_DELETE"

    # ==========================================
    # LEGAL MODULE
    # ==========================================
    LEGAL_DASHBOARD_VIEW = "LEGAL_DASHBOARD_VIEW"

    LEGAL_LAWFIRM_VIEW = "LEGAL_LAWFIRM_VIEW"
    LEGAL_LAWFIRM_CREATE = "LEGAL_LAWFIRM_CREATE"
    LEGAL_LAWFIRM_UPDATE = "LEGAL_LAWFIRM_UPDATE"
    LEGAL_LAWFIRM_DELETE = "LEGAL_LAWFIRM_DELETE"

    LEGAL_ADVOCATE_VIEW = "LEGAL_ADVOCATE_VIEW"
    LEGAL_ADVOCATE_CREATE = "LEGAL_ADVOCATE_CREATE"
    LEGAL_ADVOCATE_UPDATE = "LEGAL_ADVOCATE_UPDATE"
    LEGAL_ADVOCATE_DELETE = "LEGAL_ADVOCATE_DELETE"
    LEGAL_ADVOCATE_ASSIGN = "LEGAL_ADVOCATE_ASSIGN"

    LEGAL_CASE_VIEW = "LEGAL_CASE_VIEW"
    LEGAL_CASE_CREATE = "LEGAL_CASE_CREATE"
    LEGAL_CASE_UPDATE = "LEGAL_CASE_UPDATE"
    LEGAL_CASE_DELETE = "LEGAL_CASE_DELETE"
    LEGAL_CASE_CLOSE = "LEGAL_CASE_CLOSE"

    LEGAL_NOTICE_VIEW = "LEGAL_NOTICE_VIEW"
    LEGAL_NOTICE_CREATE = "LEGAL_NOTICE_CREATE"
    LEGAL_NOTICE_UPDATE = "LEGAL_NOTICE_UPDATE"
    LEGAL_NOTICE_DELETE = "LEGAL_NOTICE_DELETE"
    LEGAL_NOTICE_SEND = "LEGAL_NOTICE_SEND"

    LEGAL_EXPENSE_VIEW = "LEGAL_EXPENSE_VIEW"
    LEGAL_EXPENSE_CREATE = "LEGAL_EXPENSE_CREATE"
    LEGAL_EXPENSE_UPDATE = "LEGAL_EXPENSE_UPDATE"
    LEGAL_EXPENSE_APPROVE = "LEGAL_EXPENSE_APPROVE"

    LEGAL_SARFAESI_VIEW = "LEGAL_SARFAESI_VIEW"
    LEGAL_SARFAESI_INITIATE = "LEGAL_SARFAESI_INITIATE"
    LEGAL_SARFAESI_UPDATE = "LEGAL_SARFAESI_UPDATE"

    LEGAL_REPORT_VIEW = "LEGAL_REPORT_VIEW"

    # ==========================================
    # CUSTOMER PORTAL MODULE
    # ==========================================
    PORTAL_USER_VIEW = "PORTAL_USER_VIEW"
    PORTAL_USER_CREATE = "PORTAL_USER_CREATE"
    PORTAL_USER_UPDATE = "PORTAL_USER_UPDATE"
    PORTAL_USER_DELETE = "PORTAL_USER_DELETE"
    PORTAL_USER_ACTIVATE = "PORTAL_USER_ACTIVATE"

    PORTAL_PAYMENT_VIEW = "PORTAL_PAYMENT_VIEW"
    PORTAL_PAYMENT_PROCESS = "PORTAL_PAYMENT_PROCESS"
    PORTAL_PAYMENT_REFUND = "PORTAL_PAYMENT_REFUND"

    PORTAL_SERVICE_VIEW = "PORTAL_SERVICE_VIEW"
    PORTAL_SERVICE_UPDATE = "PORTAL_SERVICE_UPDATE"
    PORTAL_SERVICE_CLOSE = "PORTAL_SERVICE_CLOSE"

    PORTAL_COMMUNICATION_VIEW = "PORTAL_COMMUNICATION_VIEW"
    PORTAL_COMMUNICATION_SEND = "PORTAL_COMMUNICATION_SEND"

    PORTAL_SETTINGS_VIEW = "PORTAL_SETTINGS_VIEW"
    PORTAL_SETTINGS_UPDATE = "PORTAL_SETTINGS_UPDATE"

    # ==========================================
    # VENDOR PORTAL MODULE
    # ==========================================
    VENDOR_PORTAL_VIEW = "VENDOR_PORTAL_VIEW"
    VENDOR_PORTAL_MANAGE = "VENDOR_PORTAL_MANAGE"
    VENDOR_PO_VIEW = "VENDOR_PO_VIEW"
    VENDOR_PO_ACKNOWLEDGE = "VENDOR_PO_ACKNOWLEDGE"
    VENDOR_INVOICE_VIEW = "VENDOR_INVOICE_VIEW"
    VENDOR_INVOICE_CREATE = "VENDOR_INVOICE_CREATE"
    VENDOR_ASN_VIEW = "VENDOR_ASN_VIEW"
    VENDOR_ASN_CREATE = "VENDOR_ASN_CREATE"
    VENDOR_COMPLIANCE_VIEW = "VENDOR_COMPLIANCE_VIEW"
    VENDOR_COMPLIANCE_UPLOAD = "VENDOR_COMPLIANCE_UPLOAD"

    # ==========================================
    # ESS PORTAL MODULE
    # ==========================================
    ESS_PROFILE_VIEW = "ESS_PROFILE_VIEW"
    ESS_PROFILE_UPDATE = "ESS_PROFILE_UPDATE"
    ESS_PAYSLIP_VIEW = "ESS_PAYSLIP_VIEW"
    ESS_LEAVE_APPLY = "ESS_LEAVE_APPLY"
    ESS_LEAVE_VIEW = "ESS_LEAVE_VIEW"
    ESS_ATTENDANCE_VIEW = "ESS_ATTENDANCE_VIEW"
    ESS_REIMBURSEMENT_CREATE = "ESS_REIMBURSEMENT_CREATE"
    ESS_REIMBURSEMENT_VIEW = "ESS_REIMBURSEMENT_VIEW"
    ESS_EXPENSE_CREATE = "ESS_EXPENSE_CREATE"
    ESS_EXPENSE_VIEW = "ESS_EXPENSE_VIEW"
    ESS_TIMESHEET_CREATE = "ESS_TIMESHEET_CREATE"
    ESS_TIMESHEET_VIEW = "ESS_TIMESHEET_VIEW"
    ESS_HELPDESK_CREATE = "ESS_HELPDESK_CREATE"
    ESS_HELPDESK_VIEW = "ESS_HELPDESK_VIEW"
    ESS_IT_DECLARATION_VIEW = "ESS_IT_DECLARATION_VIEW"
    ESS_IT_DECLARATION_UPDATE = "ESS_IT_DECLARATION_UPDATE"
    ESS_TRAINING_VIEW = "ESS_TRAINING_VIEW"
    ESS_TRAINING_ENROLL = "ESS_TRAINING_ENROLL"
    ESS_GOALS_VIEW = "ESS_GOALS_VIEW"
    ESS_GOALS_UPDATE = "ESS_GOALS_UPDATE"
    ESS_APPRAISAL_VIEW = "ESS_APPRAISAL_VIEW"
    ESS_APPRAISAL_SUBMIT = "ESS_APPRAISAL_SUBMIT"

    # ==========================================
    # KYC MODULE
    # ==========================================
    KYC_CKYC_SEARCH = "KYC_CKYC_SEARCH"
    KYC_CKYC_DOWNLOAD = "KYC_CKYC_DOWNLOAD"
    KYC_CKYC_UPLOAD = "KYC_CKYC_UPLOAD"
    KYC_CKYC_VIEW = "KYC_CKYC_VIEW"

    KYC_CREDIT_PULL = "KYC_CREDIT_PULL"
    KYC_CREDIT_VIEW = "KYC_CREDIT_VIEW"

    KYC_DOC_VIEW = "KYC_DOC_VIEW"
    KYC_DOC_UPLOAD = "KYC_DOC_UPLOAD"
    KYC_DOC_VERIFY = "KYC_DOC_VERIFY"
    KYC_DOC_REJECT = "KYC_DOC_REJECT"

    # ==========================================
    # GST MODULE
    # ==========================================
    GST_RATE_VIEW = "GST_RATE_VIEW"
    GST_RATE_CREATE = "GST_RATE_CREATE"
    GST_RATE_UPDATE = "GST_RATE_UPDATE"
    GST_RATE_DELETE = "GST_RATE_DELETE"

    GST_RETURN_VIEW = "GST_RETURN_VIEW"
    GST_RETURN_FILE = "GST_RETURN_FILE"
    GST_RETURN_DOWNLOAD = "GST_RETURN_DOWNLOAD"

    GST_ITC_VIEW = "GST_ITC_VIEW"
    GST_ITC_RECONCILE = "GST_ITC_RECONCILE"

    GST_CHALLAN_VIEW = "GST_CHALLAN_VIEW"
    GST_CHALLAN_CREATE = "GST_CHALLAN_CREATE"

    # ==========================================
    # TDS MODULE
    # ==========================================
    TDS_SECTION_VIEW = "TDS_SECTION_VIEW"
    TDS_SECTION_CREATE = "TDS_SECTION_CREATE"
    TDS_SECTION_UPDATE = "TDS_SECTION_UPDATE"
    TDS_SECTION_DELETE = "TDS_SECTION_DELETE"

    TDS_RETURN_VIEW = "TDS_RETURN_VIEW"
    TDS_RETURN_GENERATE = "TDS_RETURN_GENERATE"
    TDS_RETURN_FILE = "TDS_RETURN_FILE"

    TDS_CHALLAN_VIEW = "TDS_CHALLAN_VIEW"
    TDS_CHALLAN_CREATE = "TDS_CHALLAN_CREATE"
    TDS_CHALLAN_VERIFY = "TDS_CHALLAN_VERIFY"

    TDS_CERTIFICATE_VIEW = "TDS_CERTIFICATE_VIEW"
    TDS_CERTIFICATE_GENERATE = "TDS_CERTIFICATE_GENERATE"
    TDS_CERTIFICATE_DOWNLOAD = "TDS_CERTIFICATE_DOWNLOAD"

    # ==========================================
    # COMPLIANCE MODULE
    # ==========================================
    COMPLIANCE_DASHBOARD_VIEW = "COMPLIANCE_DASHBOARD_VIEW"
    COMPLIANCE_ITEM_VIEW = "COMPLIANCE_ITEM_VIEW"
    COMPLIANCE_ITEM_CREATE = "COMPLIANCE_ITEM_CREATE"
    COMPLIANCE_ITEM_UPDATE = "COMPLIANCE_ITEM_UPDATE"
    COMPLIANCE_ITEM_DELETE = "COMPLIANCE_ITEM_DELETE"
    COMPLIANCE_INSTANCE_VIEW = "COMPLIANCE_INSTANCE_VIEW"
    COMPLIANCE_INSTANCE_UPDATE = "COMPLIANCE_INSTANCE_UPDATE"
    COMPLIANCE_INSTANCE_COMPLETE = "COMPLIANCE_INSTANCE_COMPLETE"

    # ==========================================
    # FIXED DEPOSITS MODULE
    # ==========================================
    FD_PRODUCT_VIEW = "FD_PRODUCT_VIEW"
    FD_PRODUCT_CREATE = "FD_PRODUCT_CREATE"
    FD_PRODUCT_UPDATE = "FD_PRODUCT_UPDATE"
    FD_PRODUCT_DELETE = "FD_PRODUCT_DELETE"

    FD_DEPOSIT_VIEW = "FD_DEPOSIT_VIEW"
    FD_DEPOSIT_CREATE = "FD_DEPOSIT_CREATE"
    FD_DEPOSIT_UPDATE = "FD_DEPOSIT_UPDATE"
    FD_DEPOSIT_CLOSE = "FD_DEPOSIT_CLOSE"
    FD_DEPOSIT_RENEW = "FD_DEPOSIT_RENEW"
    FD_DEPOSIT_PREMATURE = "FD_DEPOSIT_PREMATURE"

    FD_INTEREST_ACCRUE = "FD_INTEREST_ACCRUE"
    FD_INTEREST_PAYOUT = "FD_INTEREST_PAYOUT"

    FD_REPORT_VIEW = "FD_REPORT_VIEW"

    # ==========================================
    # REPORTS & ANALYTICS MODULE
    # ==========================================
    REPORT_REGULATORY_VIEW = "REPORT_REGULATORY_VIEW"
    REPORT_REGULATORY_GENERATE = "REPORT_REGULATORY_GENERATE"
    REPORT_REGULATORY_SUBMIT = "REPORT_REGULATORY_SUBMIT"

    REPORT_MIS_VIEW = "REPORT_MIS_VIEW"
    REPORT_MIS_GENERATE = "REPORT_MIS_GENERATE"
    REPORT_MIS_EXPORT = "REPORT_MIS_EXPORT"

    REPORT_SCHEDULE_VIEW = "REPORT_SCHEDULE_VIEW"
    REPORT_SCHEDULE_CREATE = "REPORT_SCHEDULE_CREATE"
    REPORT_SCHEDULE_UPDATE = "REPORT_SCHEDULE_UPDATE"
    REPORT_SCHEDULE_DELETE = "REPORT_SCHEDULE_DELETE"

    REPORT_DASHBOARD_VIEW = "REPORT_DASHBOARD_VIEW"
    REPORT_DASHBOARD_CREATE = "REPORT_DASHBOARD_CREATE"

    # ==========================================
    # PAYMENT GATEWAY MODULE
    # ==========================================
    PG_TRANSACTION_VIEW = "PG_TRANSACTION_VIEW"
    PG_TRANSACTION_INITIATE = "PG_TRANSACTION_INITIATE"
    PG_TRANSACTION_REFUND = "PG_TRANSACTION_REFUND"

    PG_MANDATE_VIEW = "PG_MANDATE_VIEW"
    PG_MANDATE_CREATE = "PG_MANDATE_CREATE"
    PG_MANDATE_UPDATE = "PG_MANDATE_UPDATE"
    PG_MANDATE_CANCEL = "PG_MANDATE_CANCEL"

    PG_NACH_BATCH_VIEW = "PG_NACH_BATCH_VIEW"
    PG_NACH_BATCH_CREATE = "PG_NACH_BATCH_CREATE"
    PG_NACH_BATCH_PROCESS = "PG_NACH_BATCH_PROCESS"

    PG_SETTINGS_VIEW = "PG_SETTINGS_VIEW"
    PG_SETTINGS_UPDATE = "PG_SETTINGS_UPDATE"


# All permissions grouped by module for UI display and role assignment
ALL_PERMISSIONS = {
    "Super Admin": [
        Permissions.SUPER_ADMIN,
    ],
    "Masters": [
        Permissions.MASTER_ORG_VIEW,
        Permissions.MASTER_ORG_CREATE,
        Permissions.MASTER_ORG_UPDATE,
        Permissions.MASTER_ORG_DELETE,
        Permissions.MASTER_ORG_BANK_CREATE,
        Permissions.MASTER_ORG_BANK_UPDATE,
        Permissions.MASTER_ORG_BANK_DELETE,
        Permissions.MASTER_ORG_ADDRESS_CREATE,
        Permissions.MASTER_ORG_ADDRESS_UPDATE,
        Permissions.MASTER_ORG_ADDRESS_DELETE,
        Permissions.MASTER_UNIT_VIEW,
        Permissions.MASTER_UNIT_CREATE,
        Permissions.MASTER_UNIT_UPDATE,
        Permissions.MASTER_UNIT_DELETE,
        Permissions.MASTER_DEPT_VIEW,
        Permissions.MASTER_DEPT_CREATE,
        Permissions.MASTER_DEPT_UPDATE,
        Permissions.MASTER_DEPT_DELETE,
        Permissions.MASTER_DESIG_VIEW,
        Permissions.MASTER_DESIG_CREATE,
        Permissions.MASTER_DESIG_UPDATE,
        Permissions.MASTER_DESIG_DELETE,
    ],
    "User Management": [
        Permissions.USER_VIEW,
        Permissions.USER_CREATE,
        Permissions.USER_UPDATE,
        Permissions.USER_DELETE,
        Permissions.USER_UNLOCK,
        Permissions.USER_RESET_PASSWORD,
        Permissions.USER_ROLE_ASSIGN,
        Permissions.ROLE_VIEW,
        Permissions.ROLE_CREATE,
        Permissions.ROLE_UPDATE,
        Permissions.ROLE_DELETE,
        Permissions.ROLE_PERMISSION_ASSIGN,
    ],
    "Finance": [
        Permissions.FIN_FY_VIEW,
        Permissions.FIN_FY_CREATE,
        Permissions.FIN_FY_UPDATE,
        Permissions.FIN_FY_DELETE,
        Permissions.FIN_FY_CLOSE,
        Permissions.FIN_COA_VIEW,
        Permissions.FIN_COA_CREATE,
        Permissions.FIN_COA_UPDATE,
        Permissions.FIN_COA_DELETE,
        Permissions.FIN_VTYPE_VIEW,
        Permissions.FIN_VTYPE_CREATE,
        Permissions.FIN_VTYPE_UPDATE,
        Permissions.FIN_VTYPE_DELETE,
        Permissions.FIN_VOUCHER_VIEW,
        Permissions.FIN_VOUCHER_CREATE,
        Permissions.FIN_VOUCHER_UPDATE,
        Permissions.FIN_VOUCHER_DELETE,
        Permissions.FIN_VOUCHER_APPROVE,
        Permissions.FIN_VOUCHER_POST,
        Permissions.FIN_VOUCHER_CANCEL,
        Permissions.FIN_REPORT_VIEW,
    ],
    "AP/AR": [
        Permissions.APAR_TERMS_VIEW,
        Permissions.APAR_TERMS_CREATE,
        Permissions.APAR_TERMS_UPDATE,
        Permissions.APAR_TERMS_DELETE,
        Permissions.APAR_VENDOR_VIEW,
        Permissions.APAR_VENDOR_CREATE,
        Permissions.APAR_VENDOR_UPDATE,
        Permissions.APAR_VENDOR_DELETE,
        Permissions.APAR_CUSTOMER_VIEW,
        Permissions.APAR_CUSTOMER_CREATE,
        Permissions.APAR_CUSTOMER_UPDATE,
        Permissions.APAR_CUSTOMER_DELETE,
        Permissions.APAR_BILL_VIEW,
        Permissions.APAR_BILL_CREATE,
        Permissions.APAR_BILL_UPDATE,
        Permissions.APAR_BILL_DELETE,
        Permissions.APAR_BILL_APPROVE,
        Permissions.APAR_INVOICE_VIEW,
        Permissions.APAR_INVOICE_CREATE,
        Permissions.APAR_INVOICE_UPDATE,
        Permissions.APAR_INVOICE_DELETE,
        Permissions.APAR_INVOICE_APPROVE,
        Permissions.APAR_PAYMENT_VIEW,
        Permissions.APAR_PAYMENT_CREATE,
        Permissions.APAR_PAYMENT_UPDATE,
        Permissions.APAR_PAYMENT_DELETE,
        Permissions.APAR_PAYMENT_APPROVE,
    ],
    "Audit & Workflow": [
        Permissions.AUDIT_LOG_VIEW,
        Permissions.WORKFLOW_VIEW,
        Permissions.WORKFLOW_CREATE,
        Permissions.WORKFLOW_UPDATE,
        Permissions.WORKFLOW_DELETE,
        Permissions.WORKFLOW_APPROVE,
        Permissions.WORKFLOW_CANCEL,
    ],
    "Approval (Maker-Checker)": [
        Permissions.APPROVAL_CONFIG_VIEW,
        Permissions.APPROVAL_CONFIG_CREATE,
        Permissions.APPROVAL_CONFIG_UPDATE,
        Permissions.APPROVAL_CONFIG_DELETE,
        Permissions.APPROVAL_REQUEST_VIEW,
        Permissions.APPROVAL_REQUEST_SUBMIT,
        Permissions.APPROVAL_REQUEST_APPROVE,
        Permissions.APPROVAL_REQUEST_CANCEL,
        Permissions.APPROVAL_PENDING_VIEW,
    ],
    "LOS (Origination)": [
        Permissions.LOS_ENTITY_VIEW,
        Permissions.LOS_ENTITY_CREATE,
        Permissions.LOS_ENTITY_UPDATE,
        Permissions.LOS_ENTITY_DELETE,
        Permissions.LOS_PRODUCT_VIEW,
        Permissions.LOS_PRODUCT_CREATE,
        Permissions.LOS_PRODUCT_UPDATE,
        Permissions.LOS_PRODUCT_DELETE,
        Permissions.LOS_APPLICATION_VIEW,
        Permissions.LOS_APPLICATION_CREATE,
        Permissions.LOS_APPLICATION_UPDATE,
        Permissions.LOS_APPLICATION_DELETE,
        Permissions.LOS_APPRAISAL_CREATE,
        Permissions.LOS_APPRAISAL_UPDATE,
        Permissions.LOS_SANCTION_VIEW,
        Permissions.LOS_SANCTION_CREATE,
        Permissions.LOS_SANCTION_UPDATE,
        Permissions.LOS_SANCTION_APPROVE,
    ],
    "LMS (Loan Management)": [
        Permissions.LMS_ACCOUNT_VIEW,
        Permissions.LMS_ACCOUNT_CREATE,
        Permissions.LMS_ACCOUNT_UPDATE,
        Permissions.LMS_DISBURSEMENT_CREATE,
        Permissions.LMS_DISBURSEMENT_APPROVE,
        Permissions.LMS_DISBURSEMENT_PROCESS,
        Permissions.LMS_SCHEDULE_CREATE,
        Permissions.LMS_RECEIPT_CREATE,
        Permissions.LMS_RECEIPT_UPDATE,
        Permissions.LMS_RECEIPT_ALLOCATE,
        Permissions.LMS_ACCRUAL_RUN,
        Permissions.LMS_ADJUSTMENT_CREATE,
        Permissions.LMS_CLASSIFICATION_UPDATE,
        Permissions.LMS_PROVISION_CALCULATE,
        Permissions.LMS_MANDATE_CREATE,
        Permissions.LMS_MANDATE_UPDATE,
    ],
    "Collections": [
        Permissions.COLLECTIONS_READ,
        Permissions.COLLECTIONS_CREATE,
        Permissions.COLLECTIONS_UPDATE,
        Permissions.COLLECTIONS_APPROVE,
        Permissions.NPA_READ,
        Permissions.NPA_CREATE,
        Permissions.NPA_UPDATE,
        Permissions.OTS_CREATE,
        Permissions.OTS_UPDATE,
        Permissions.OTS_APPROVE,
        Permissions.RESTRUCTURE_CREATE,
        Permissions.RESTRUCTURE_UPDATE,
        Permissions.RESTRUCTURE_APPROVE,
        Permissions.WRITEOFF_CREATE,
        Permissions.WRITEOFF_APPROVE,
        Permissions.LEGAL_READ,
        Permissions.LEGAL_CREATE,
        Permissions.LEGAL_UPDATE,
    ],
    "Treasury": [
        Permissions.TREASURY_READ,
        Permissions.TREASURY_WRITE,
        Permissions.TREASURY_APPROVE,
    ],
    "Fixed Assets": [
        Permissions.FA_CATEGORY_VIEW,
        Permissions.FA_CATEGORY_CREATE,
        Permissions.FA_CATEGORY_UPDATE,
        Permissions.FA_CATEGORY_DELETE,
        Permissions.FA_ASSET_VIEW,
        Permissions.FA_ASSET_CREATE,
        Permissions.FA_ASSET_UPDATE,
        Permissions.FA_ASSET_DELETE,
        Permissions.FA_ASSET_CAPITALIZE,
        Permissions.FA_ASSET_DISPOSE,
        Permissions.FA_ASSET_TRANSFER,
        Permissions.FA_ASSET_REVALUE,
        Permissions.FA_DEPRECIATION_VIEW,
        Permissions.FA_DEPRECIATION_RUN,
        Permissions.FA_DEPRECIATION_REVERSE,
        Permissions.FA_REPORT_VIEW,
    ],
    "HRIS": [
        Permissions.HRIS_EMPLOYEE_VIEW,
        Permissions.HRIS_EMPLOYEE_CREATE,
        Permissions.HRIS_EMPLOYEE_UPDATE,
        Permissions.HRIS_EMPLOYEE_DELETE,
        Permissions.HRIS_SHIFT_VIEW,
        Permissions.HRIS_SHIFT_CREATE,
        Permissions.HRIS_SHIFT_UPDATE,
        Permissions.HRIS_SHIFT_DELETE,
        Permissions.HRIS_HOLIDAY_VIEW,
        Permissions.HRIS_HOLIDAY_CREATE,
        Permissions.HRIS_HOLIDAY_UPDATE,
        Permissions.HRIS_HOLIDAY_DELETE,
        Permissions.HRIS_LEAVE_TYPE_VIEW,
        Permissions.HRIS_LEAVE_TYPE_CREATE,
        Permissions.HRIS_LEAVE_TYPE_UPDATE,
        Permissions.HRIS_LEAVE_TYPE_DELETE,
        Permissions.HRIS_LEAVE_VIEW,
        Permissions.HRIS_LEAVE_APPLY,
        Permissions.HRIS_LEAVE_APPROVE,
        Permissions.HRIS_LEAVE_CANCEL,
        Permissions.HRIS_ATTENDANCE_VIEW,
        Permissions.HRIS_ATTENDANCE_MARK,
        Permissions.HRIS_ATTENDANCE_REGULARIZE,
        Permissions.HRIS_ATTENDANCE_APPROVE,
    ],
    "Payroll": [
        Permissions.PAYROLL_COMPONENT_VIEW,
        Permissions.PAYROLL_COMPONENT_CREATE,
        Permissions.PAYROLL_COMPONENT_UPDATE,
        Permissions.PAYROLL_COMPONENT_DELETE,
        Permissions.PAYROLL_STRUCTURE_VIEW,
        Permissions.PAYROLL_STRUCTURE_CREATE,
        Permissions.PAYROLL_STRUCTURE_UPDATE,
        Permissions.PAYROLL_STRUCTURE_DELETE,
        Permissions.PAYROLL_RUN_VIEW,
        Permissions.PAYROLL_RUN_PROCESS,
        Permissions.PAYROLL_RUN_LOCK,
        Permissions.PAYROLL_RUN_POST,
        Permissions.PAYROLL_PAYSLIP_VIEW,
        Permissions.PAYROLL_PAYSLIP_PUBLISH,
        Permissions.PAYROLL_REPORT_VIEW,
    ],
    "HRIS - Separation": [
        Permissions.HRIS_SEPARATION_VIEW,
        Permissions.HRIS_SEPARATION_INITIATE,
        Permissions.HRIS_SEPARATION_APPROVE,
        Permissions.HRIS_SEPARATION_CANCEL,
        Permissions.HRIS_CLEARANCE_VIEW,
        Permissions.HRIS_CLEARANCE_UPDATE,
        Permissions.HRIS_FNF_VIEW,
        Permissions.HRIS_FNF_CALCULATE,
        Permissions.HRIS_FNF_APPROVE,
    ],
    "HRIS - Training": [
        Permissions.HRIS_TRAINING_VIEW,
        Permissions.HRIS_TRAINING_CREATE,
        Permissions.HRIS_TRAINING_UPDATE,
        Permissions.HRIS_TRAINING_DELETE,
        Permissions.HRIS_TRAINING_NOMINATE,
        Permissions.HRIS_TRAINING_APPROVE,
        Permissions.HRIS_TRAINING_FEEDBACK,
    ],
    "HRIS - Performance": [
        Permissions.HRIS_APPRAISAL_VIEW,
        Permissions.HRIS_APPRAISAL_CREATE,
        Permissions.HRIS_APPRAISAL_UPDATE,
        Permissions.HRIS_GOAL_VIEW,
        Permissions.HRIS_GOAL_CREATE,
        Permissions.HRIS_GOAL_UPDATE,
        Permissions.HRIS_GOAL_APPROVE,
        Permissions.HRIS_SELF_APPRAISAL,
        Permissions.HRIS_MANAGER_REVIEW,
        Permissions.HRIS_CALIBRATION,
    ],
    "Inventory": [
        Permissions.INV_CATEGORY_VIEW,
        Permissions.INV_CATEGORY_CREATE,
        Permissions.INV_CATEGORY_UPDATE,
        Permissions.INV_CATEGORY_DELETE,
        Permissions.INV_ITEM_VIEW,
        Permissions.INV_ITEM_CREATE,
        Permissions.INV_ITEM_UPDATE,
        Permissions.INV_ITEM_DELETE,
        Permissions.INV_WAREHOUSE_VIEW,
        Permissions.INV_WAREHOUSE_CREATE,
        Permissions.INV_WAREHOUSE_UPDATE,
        Permissions.INV_WAREHOUSE_DELETE,
        Permissions.INV_STOCK_VIEW,
        Permissions.INV_STOCK_IN,
        Permissions.INV_STOCK_OUT,
        Permissions.INV_STOCK_TRANSFER,
        Permissions.INV_STOCK_ADJUST,
        Permissions.INV_STOCK_APPROVE,
        Permissions.INV_REPORT_VIEW,
    ],
    "Notification": [
        Permissions.NOTIF_VIEW,
        Permissions.NOTIF_SEND,
        Permissions.NOTIF_TEMPLATE_VIEW,
        Permissions.NOTIF_TEMPLATE_CREATE,
        Permissions.NOTIF_TEMPLATE_UPDATE,
        Permissions.NOTIF_TEMPLATE_DELETE,
        Permissions.NOTIF_SETTINGS_VIEW,
        Permissions.NOTIF_SETTINGS_UPDATE,
        Permissions.NOTIF_LOG_VIEW,
    ],
    "Document Management": [
        Permissions.DMS_FOLDER_VIEW,
        Permissions.DMS_FOLDER_CREATE,
        Permissions.DMS_FOLDER_UPDATE,
        Permissions.DMS_FOLDER_DELETE,
        Permissions.DMS_DOCUMENT_VIEW,
        Permissions.DMS_DOCUMENT_UPLOAD,
        Permissions.DMS_DOCUMENT_UPDATE,
        Permissions.DMS_DOCUMENT_DELETE,
        Permissions.DMS_DOCUMENT_DOWNLOAD,
        Permissions.DMS_DOCUMENT_SHARE,
        Permissions.DMS_TAG_VIEW,
        Permissions.DMS_TAG_CREATE,
        Permissions.DMS_TAG_UPDATE,
        Permissions.DMS_TAG_DELETE,
    ],
    "Legal": [
        Permissions.LEGAL_DASHBOARD_VIEW,
        Permissions.LEGAL_LAWFIRM_VIEW,
        Permissions.LEGAL_LAWFIRM_CREATE,
        Permissions.LEGAL_LAWFIRM_UPDATE,
        Permissions.LEGAL_LAWFIRM_DELETE,
        Permissions.LEGAL_ADVOCATE_VIEW,
        Permissions.LEGAL_ADVOCATE_CREATE,
        Permissions.LEGAL_ADVOCATE_UPDATE,
        Permissions.LEGAL_ADVOCATE_DELETE,
        Permissions.LEGAL_ADVOCATE_ASSIGN,
        Permissions.LEGAL_CASE_VIEW,
        Permissions.LEGAL_CASE_CREATE,
        Permissions.LEGAL_CASE_UPDATE,
        Permissions.LEGAL_CASE_DELETE,
        Permissions.LEGAL_CASE_CLOSE,
        Permissions.LEGAL_NOTICE_VIEW,
        Permissions.LEGAL_NOTICE_CREATE,
        Permissions.LEGAL_NOTICE_UPDATE,
        Permissions.LEGAL_NOTICE_DELETE,
        Permissions.LEGAL_NOTICE_SEND,
        Permissions.LEGAL_EXPENSE_VIEW,
        Permissions.LEGAL_EXPENSE_CREATE,
        Permissions.LEGAL_EXPENSE_UPDATE,
        Permissions.LEGAL_EXPENSE_APPROVE,
        Permissions.LEGAL_SARFAESI_VIEW,
        Permissions.LEGAL_SARFAESI_INITIATE,
        Permissions.LEGAL_SARFAESI_UPDATE,
        Permissions.LEGAL_REPORT_VIEW,
    ],
    "Customer Portal": [
        Permissions.PORTAL_USER_VIEW,
        Permissions.PORTAL_USER_CREATE,
        Permissions.PORTAL_USER_UPDATE,
        Permissions.PORTAL_USER_DELETE,
        Permissions.PORTAL_USER_ACTIVATE,
        Permissions.PORTAL_PAYMENT_VIEW,
        Permissions.PORTAL_PAYMENT_PROCESS,
        Permissions.PORTAL_PAYMENT_REFUND,
        Permissions.PORTAL_SERVICE_VIEW,
        Permissions.PORTAL_SERVICE_UPDATE,
        Permissions.PORTAL_SERVICE_CLOSE,
        Permissions.PORTAL_COMMUNICATION_VIEW,
        Permissions.PORTAL_COMMUNICATION_SEND,
        Permissions.PORTAL_SETTINGS_VIEW,
        Permissions.PORTAL_SETTINGS_UPDATE,
    ],
    "Vendor Portal": [
        Permissions.VENDOR_PORTAL_VIEW,
        Permissions.VENDOR_PORTAL_MANAGE,
        Permissions.VENDOR_PO_VIEW,
        Permissions.VENDOR_PO_ACKNOWLEDGE,
        Permissions.VENDOR_INVOICE_VIEW,
        Permissions.VENDOR_INVOICE_CREATE,
        Permissions.VENDOR_ASN_VIEW,
        Permissions.VENDOR_ASN_CREATE,
        Permissions.VENDOR_COMPLIANCE_VIEW,
        Permissions.VENDOR_COMPLIANCE_UPLOAD,
    ],
    "ESS Portal": [
        Permissions.ESS_PROFILE_VIEW,
        Permissions.ESS_PROFILE_UPDATE,
        Permissions.ESS_PAYSLIP_VIEW,
        Permissions.ESS_LEAVE_APPLY,
        Permissions.ESS_LEAVE_VIEW,
        Permissions.ESS_ATTENDANCE_VIEW,
        Permissions.ESS_REIMBURSEMENT_CREATE,
        Permissions.ESS_REIMBURSEMENT_VIEW,
        Permissions.ESS_EXPENSE_CREATE,
        Permissions.ESS_EXPENSE_VIEW,
        Permissions.ESS_TIMESHEET_CREATE,
        Permissions.ESS_TIMESHEET_VIEW,
        Permissions.ESS_HELPDESK_CREATE,
        Permissions.ESS_HELPDESK_VIEW,
        Permissions.ESS_IT_DECLARATION_VIEW,
        Permissions.ESS_IT_DECLARATION_UPDATE,
        Permissions.ESS_TRAINING_VIEW,
        Permissions.ESS_TRAINING_ENROLL,
        Permissions.ESS_GOALS_VIEW,
        Permissions.ESS_GOALS_UPDATE,
        Permissions.ESS_APPRAISAL_VIEW,
        Permissions.ESS_APPRAISAL_SUBMIT,
    ],
    "KYC": [
        Permissions.KYC_CKYC_SEARCH,
        Permissions.KYC_CKYC_DOWNLOAD,
        Permissions.KYC_CKYC_UPLOAD,
        Permissions.KYC_CKYC_VIEW,
        Permissions.KYC_CREDIT_PULL,
        Permissions.KYC_CREDIT_VIEW,
        Permissions.KYC_DOC_VIEW,
        Permissions.KYC_DOC_UPLOAD,
        Permissions.KYC_DOC_VERIFY,
        Permissions.KYC_DOC_REJECT,
    ],
    "GST": [
        Permissions.GST_RATE_VIEW,
        Permissions.GST_RATE_CREATE,
        Permissions.GST_RATE_UPDATE,
        Permissions.GST_RATE_DELETE,
        Permissions.GST_RETURN_VIEW,
        Permissions.GST_RETURN_FILE,
        Permissions.GST_RETURN_DOWNLOAD,
        Permissions.GST_ITC_VIEW,
        Permissions.GST_ITC_RECONCILE,
        Permissions.GST_CHALLAN_VIEW,
        Permissions.GST_CHALLAN_CREATE,
    ],
    "TDS": [
        Permissions.TDS_SECTION_VIEW,
        Permissions.TDS_SECTION_CREATE,
        Permissions.TDS_SECTION_UPDATE,
        Permissions.TDS_SECTION_DELETE,
        Permissions.TDS_RETURN_VIEW,
        Permissions.TDS_RETURN_GENERATE,
        Permissions.TDS_RETURN_FILE,
        Permissions.TDS_CHALLAN_VIEW,
        Permissions.TDS_CHALLAN_CREATE,
        Permissions.TDS_CHALLAN_VERIFY,
        Permissions.TDS_CERTIFICATE_VIEW,
        Permissions.TDS_CERTIFICATE_GENERATE,
        Permissions.TDS_CERTIFICATE_DOWNLOAD,
    ],
    "Compliance": [
        Permissions.COMPLIANCE_DASHBOARD_VIEW,
        Permissions.COMPLIANCE_ITEM_VIEW,
        Permissions.COMPLIANCE_ITEM_CREATE,
        Permissions.COMPLIANCE_ITEM_UPDATE,
        Permissions.COMPLIANCE_ITEM_DELETE,
        Permissions.COMPLIANCE_INSTANCE_VIEW,
        Permissions.COMPLIANCE_INSTANCE_UPDATE,
        Permissions.COMPLIANCE_INSTANCE_COMPLETE,
    ],
    "Fixed Deposits": [
        Permissions.FD_PRODUCT_VIEW,
        Permissions.FD_PRODUCT_CREATE,
        Permissions.FD_PRODUCT_UPDATE,
        Permissions.FD_PRODUCT_DELETE,
        Permissions.FD_DEPOSIT_VIEW,
        Permissions.FD_DEPOSIT_CREATE,
        Permissions.FD_DEPOSIT_UPDATE,
        Permissions.FD_DEPOSIT_CLOSE,
        Permissions.FD_DEPOSIT_RENEW,
        Permissions.FD_DEPOSIT_PREMATURE,
        Permissions.FD_INTEREST_ACCRUE,
        Permissions.FD_INTEREST_PAYOUT,
        Permissions.FD_REPORT_VIEW,
    ],
    "Reports & Analytics": [
        Permissions.REPORT_REGULATORY_VIEW,
        Permissions.REPORT_REGULATORY_GENERATE,
        Permissions.REPORT_REGULATORY_SUBMIT,
        Permissions.REPORT_MIS_VIEW,
        Permissions.REPORT_MIS_GENERATE,
        Permissions.REPORT_MIS_EXPORT,
        Permissions.REPORT_SCHEDULE_VIEW,
        Permissions.REPORT_SCHEDULE_CREATE,
        Permissions.REPORT_SCHEDULE_UPDATE,
        Permissions.REPORT_SCHEDULE_DELETE,
        Permissions.REPORT_DASHBOARD_VIEW,
        Permissions.REPORT_DASHBOARD_CREATE,
    ],
    "Payment Gateway": [
        Permissions.PG_TRANSACTION_VIEW,
        Permissions.PG_TRANSACTION_INITIATE,
        Permissions.PG_TRANSACTION_REFUND,
        Permissions.PG_MANDATE_VIEW,
        Permissions.PG_MANDATE_CREATE,
        Permissions.PG_MANDATE_UPDATE,
        Permissions.PG_MANDATE_CANCEL,
        Permissions.PG_NACH_BATCH_VIEW,
        Permissions.PG_NACH_BATCH_CREATE,
        Permissions.PG_NACH_BATCH_PROCESS,
        Permissions.PG_SETTINGS_VIEW,
        Permissions.PG_SETTINGS_UPDATE,
    ],
}
