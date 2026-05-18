"""Enums for the lending module."""

from enum import Enum

# ============================================================================
# Entity/Borrower Enums
# ============================================================================


class EntityType(str, Enum):
    """Type of borrower entity."""

    CORPORATE = "CORPORATE"
    INDIVIDUAL = "INDIVIDUAL"
    LLP = "LLP"
    PARTNERSHIP = "PARTNERSHIP"
    TRUST = "TRUST"
    HUF = "HUF"
    SOCIETY = "SOCIETY"
    PROPRIETORSHIP = "PROPRIETORSHIP"


class EntityStatus(str, Enum):
    """Status of borrower entity."""

    PROSPECT = "PROSPECT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"
    SUSPENDED = "SUSPENDED"


class ContactType(str, Enum):
    """Type of entity contact."""

    DIRECTOR = "DIRECTOR"
    PROMOTER = "PROMOTER"
    AUTHORIZED_SIGNATORY = "AUTHORIZED_SIGNATORY"
    KEY_MANAGERIAL_PERSON = "KEY_MANAGERIAL_PERSON"
    CFO = "CFO"
    CEO = "CEO"
    COMPANY_SECRETARY = "COMPANY_SECRETARY"
    PARTNER = "PARTNER"
    PROPRIETOR = "PROPRIETOR"
    TRUSTEE = "TRUSTEE"
    GUARANTOR = "GUARANTOR"


class AddressType(str, Enum):
    """Type of address."""

    REGISTERED = "REGISTERED"
    CORRESPONDENCE = "CORRESPONDENCE"
    PLANT = "PLANT"
    WAREHOUSE = "WAREHOUSE"
    BRANCH = "BRANCH"
    PROJECT_SITE = "PROJECT_SITE"


class RelationType(str, Enum):
    """Type of entity relationship."""

    PARENT = "PARENT"
    SUBSIDIARY = "SUBSIDIARY"
    ASSOCIATE = "ASSOCIATE"
    GROUP_COMPANY = "GROUP_COMPANY"
    HOLDING = "HOLDING"
    JOINT_VENTURE = "JOINT_VENTURE"
    PROMOTER = "PROMOTER"
    GUARANTOR = "GUARANTOR"


class RiskCategory(str, Enum):
    """Risk category for entity."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class IndustrySector(str, Enum):
    """Industry sector classification."""

    MANUFACTURING = "MANUFACTURING"
    SERVICES = "SERVICES"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    REAL_ESTATE = "REAL_ESTATE"
    TRADING = "TRADING"
    AGRICULTURE = "AGRICULTURE"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    IT_ITES = "IT_ITES"
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    RETAIL = "RETAIL"
    HOSPITALITY = "HOSPITALITY"
    TRANSPORT = "TRANSPORT"
    POWER = "POWER"
    TELECOM = "TELECOM"
    OTHERS = "OTHERS"


# ============================================================================
# KYC Enums
# ============================================================================


class KYCDocCategory(str, Enum):
    """Category of KYC document."""

    IDENTITY = "IDENTITY"
    ADDRESS = "ADDRESS"
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    BUSINESS = "BUSINESS"
    TAX = "TAX"
    BANK = "BANK"


class KYCVerificationStatus(str, Enum):
    """Verification status of KYC document."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    RESUBMISSION_REQUIRED = "RESUBMISSION_REQUIRED"


class KYCVerificationMethod(str, Enum):
    """Method of KYC verification."""

    MANUAL = "MANUAL"
    API = "API"
    PHYSICAL = "PHYSICAL"
    VIDEO_KYC = "VIDEO_KYC"
    AADHAAR_OTP = "AADHAAR_OTP"
    CKYC = "CKYC"


class CKYCTransactionType(str, Enum):
    """Type of CKYC transaction."""

    SEARCH = "SEARCH"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    UPDATE = "UPDATE"


class BureauType(str, Enum):
    """Credit bureau type."""

    CIBIL = "CIBIL"
    EXPERIAN = "EXPERIAN"
    EQUIFAX = "EQUIFAX"
    CRIF_HIGH_MARK = "CRIF_HIGH_MARK"


class BureauPullStatus(str, Enum):
    """Status of bureau pull."""

    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    NO_HIT = "NO_HIT"


# ============================================================================
# Credit Rating Enums
# ============================================================================


class RatingGrade(str, Enum):
    """Internal credit rating grade."""

    AAA = "AAA"
    AA_PLUS = "AA+"
    AA = "AA"
    AA_MINUS = "AA-"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB_PLUS = "BBB+"
    BBB = "BBB"
    BBB_MINUS = "BBB-"
    BB_PLUS = "BB+"
    BB = "BB"
    BB_MINUS = "BB-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C = "C"
    D = "D"


class RatingType(str, Enum):
    """Type of rating."""

    INITIAL = "INITIAL"
    REVIEW = "REVIEW"
    ANNUAL = "ANNUAL"
    EVENT_BASED = "EVENT_BASED"


class RatingStatus(str, Enum):
    """Status of rating."""

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RiskCategoryType(str, Enum):
    """Type of risk category for scoring."""

    SPONSOR = "SPONSOR"
    PROJECT = "PROJECT"
    FINANCIAL = "FINANCIAL"
    INDUSTRY = "INDUSTRY"
    SECURITY = "SECURITY"
    MANAGEMENT = "MANAGEMENT"
    CONDUCT = "CONDUCT"


# ============================================================================
# Loan Product Enums
# ============================================================================


class ProductCategory(str, Enum):
    """Category of loan product."""

    TERM_LOAN = "TERM_LOAN"
    PROJECT_FINANCE = "PROJECT_FINANCE"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    DEMAND_LOAN = "DEMAND_LOAN"
    OVERDRAFT = "OVERDRAFT"
    CASH_CREDIT = "CASH_CREDIT"
    LETTER_OF_CREDIT = "LETTER_OF_CREDIT"
    BANK_GUARANTEE = "BANK_GUARANTEE"
    BILL_DISCOUNTING = "BILL_DISCOUNTING"


class InterestType(str, Enum):
    """Type of interest."""

    FIXED = "FIXED"
    FLOATING = "FLOATING"


class RateResetFrequency(str, Enum):
    """Frequency of rate reset for floating loans."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class RepaymentFrequency(str, Enum):
    """Frequency of repayment."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"
    BULLET = "BULLET"


class RepaymentMode(str, Enum):
    """Mode of repayment schedule."""

    EMI = "EMI"
    STRUCTURED = "STRUCTURED"
    BULLET = "BULLET"
    BALLOON = "BALLOON"
    STEP_UP = "STEP_UP"
    STEP_DOWN = "STEP_DOWN"


class DayCountConvention(str, Enum):
    """Day count convention for interest calculation."""

    ACT_365 = "ACT_365"
    ACT_360 = "ACT_360"
    THIRTY_360 = "30_360"


class FeeType(str, Enum):
    """Type of fee."""

    PROCESSING = "PROCESSING"
    UPFRONT = "UPFRONT"
    COMMITMENT = "COMMITMENT"
    PREPAYMENT = "PREPAYMENT"
    FORECLOSURE = "FORECLOSURE"
    DOCUMENTATION = "DOCUMENTATION"
    VALUATION = "VALUATION"
    LEGAL = "LEGAL"
    TECHNICAL = "TECHNICAL"
    INSURANCE = "INSURANCE"
    STAMP_DUTY = "STAMP_DUTY"
    ROC_CHARGES = "ROC_CHARGES"
    CERSAI_CHARGES = "CERSAI_CHARGES"


class FeeCalculationType(str, Enum):
    """Type of fee calculation."""

    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"
    SLAB = "SLAB"


class FeeCollectionStage(str, Enum):
    """Stage at which fee is collected."""

    APPLICATION = "APPLICATION"
    SANCTION = "SANCTION"
    DISBURSEMENT = "DISBURSEMENT"
    PREPAYMENT = "PREPAYMENT"
    CLOSURE = "CLOSURE"


# ============================================================================
# Document Checklist Enums
# ============================================================================


class DocumentCategory(str, Enum):
    """Category of document in checklist."""

    KYC = "KYC"
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    PROJECT = "PROJECT"
    SECURITY = "SECURITY"
    INSURANCE = "INSURANCE"
    REGULATORY = "REGULATORY"


class DocumentStage(str, Enum):
    """Stage at which document is required."""

    APPLICATION = "APPLICATION"
    APPRAISAL = "APPRAISAL"
    SANCTION = "SANCTION"
    PRE_DISBURSEMENT = "PRE_DISBURSEMENT"
    POST_DISBURSEMENT = "POST_DISBURSEMENT"
    ONGOING = "ONGOING"


# ============================================================================
# Application Enums
# ============================================================================


class ApplicationStage(str, Enum):
    """Stage of loan application."""

    LEAD = "LEAD"
    APPLICATION = "APPLICATION"
    APPRAISAL = "APPRAISAL"
    SANCTION = "SANCTION"
    POST_SANCTION = "POST_SANCTION"
    DISBURSED = "DISBURSED"
    CLOSED = "CLOSED"


class ApplicationStatus(str, Enum):
    """Status of loan application."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUIRED = "ADDITIONAL_INFO_REQUIRED"
    SANCTIONED = "SANCTIONED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class AppraisalType(str, Enum):
    """Type of appraisal."""

    TECHNICAL = "TECHNICAL"
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    MARKET = "MARKET"


class TechnicalFeasibility(str, Enum):
    """Technical feasibility assessment."""

    FEASIBLE = "FEASIBLE"
    CONDITIONAL = "CONDITIONAL"
    NOT_FEASIBLE = "NOT_FEASIBLE"


class AppraisalRecommendation(str, Enum):
    """Appraisal recommendation."""

    PROCEED = "PROCEED"
    PROCEED_WITH_CONDITIONS = "PROCEED_WITH_CONDITIONS"
    REJECT = "REJECT"
    HOLD = "HOLD"


class MilestoneStatus(str, Enum):
    """Status of project milestone."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    WAIVED = "WAIVED"


# ============================================================================
# Sanction Enums
# ============================================================================


class SanctionStatus(str, Enum):
    """Status of sanction."""

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class ConditionType(str, Enum):
    """Type of sanction condition."""

    PRE_DISBURSEMENT = "PRE_DISBURSEMENT"
    POST_DISBURSEMENT = "POST_DISBURSEMENT"
    ONGOING = "ONGOING"
    EVENT_BASED = "EVENT_BASED"


class ConditionCategory(str, Enum):
    """Category of sanction condition."""

    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    SECURITY = "SECURITY"
    REGULATORY = "REGULATORY"
    OPERATIONAL = "OPERATIONAL"
    PROJECT = "PROJECT"


class ConditionComplianceStatus(str, Enum):
    """Compliance status of condition."""

    PENDING = "PENDING"
    COMPLIED = "COMPLIED"
    WAIVED = "WAIVED"
    DEFERRED = "DEFERRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ============================================================================
# Security/Collateral Enums
# ============================================================================


class SecurityCategory(str, Enum):
    """Category of security."""

    PRIMARY = "PRIMARY"
    COLLATERAL = "COLLATERAL"
    GUARANTEE = "GUARANTEE"


class SecurityType(str, Enum):
    """Type of security."""

    IMMOVABLE_PROPERTY = "IMMOVABLE_PROPERTY"
    MOVABLE_PROPERTY = "MOVABLE_PROPERTY"
    PLANT_MACHINERY = "PLANT_MACHINERY"
    INVENTORY = "INVENTORY"
    RECEIVABLES = "RECEIVABLES"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    SHARES = "SHARES"
    DEBENTURES = "DEBENTURES"
    GOVERNMENT_SECURITIES = "GOVERNMENT_SECURITIES"
    VEHICLE = "VEHICLE"
    GOLD = "GOLD"
    PERSONAL_GUARANTEE = "PERSONAL_GUARANTEE"
    CORPORATE_GUARANTEE = "CORPORATE_GUARANTEE"
    BANK_GUARANTEE = "BANK_GUARANTEE"


class ChargeType(str, Enum):
    """Type of charge on security."""

    FIRST = "FIRST"
    SECOND = "SECOND"
    PARI_PASSU = "PARI_PASSU"
    SUBSERVIENT = "SUBSERVIENT"


class SecurityStatus(str, Enum):
    """Status of security."""

    PROPOSED = "PROPOSED"
    CREATED = "CREATED"
    REGISTERED = "REGISTERED"
    RELEASED = "RELEASED"
    SUBSTITUTED = "SUBSTITUTED"


# ============================================================================
# Phase 2: Loan Accounting Enums
# ============================================================================


class LoanAccountStatus(str, Enum):
    """Status of loan account."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"
    WRITTEN_OFF = "WRITTEN_OFF"
    RECALLED = "RECALLED"


class DisbursementStatus(str, Enum):
    """Status of disbursement."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class DisbursementMode(str, Enum):
    """Mode of disbursement."""

    RTGS = "RTGS"
    NEFT = "NEFT"
    IMPS = "IMPS"
    CHEQUE = "CHEQUE"
    DD = "DD"
    DIRECT_CREDIT = "DIRECT_CREDIT"
    ESCROW = "ESCROW"


class ScheduleType(str, Enum):
    """Type of repayment schedule."""

    ORIGINAL = "ORIGINAL"
    RESCHEDULED = "RESCHEDULED"
    RESTRUCTURED = "RESTRUCTURED"
    REVISED = "REVISED"


class InstallmentType(str, Enum):
    """Type of installment component."""

    PRINCIPAL = "PRINCIPAL"
    INTEREST = "INTEREST"
    EMI = "EMI"
    MORATORIUM_INTEREST = "MORATORIUM_INTEREST"
    PENAL_INTEREST = "PENAL_INTEREST"


class InstallmentStatus(str, Enum):
    """Status of installment."""

    NOT_DUE = "NOT_DUE"
    DUE = "DUE"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    WAIVED = "WAIVED"
    WRITTEN_OFF = "WRITTEN_OFF"


class AccrualCategory(str, Enum):
    """Category of accrual."""

    INTEREST = "INTEREST"
    PENAL_INTEREST = "PENAL_INTEREST"
    FEE = "FEE"
    COMMITMENT_FEE = "COMMITMENT_FEE"


class AccrualStatus(str, Enum):
    """Status of accrual."""

    ACCRUED = "ACCRUED"
    REVERSED = "REVERSED"
    SUSPENDED = "SUSPENDED"
    WRITTEN_OFF = "WRITTEN_OFF"


class AssetClassification(str, Enum):
    """RBI asset classification."""

    STANDARD = "STANDARD"
    SMA_0 = "SMA_0"  # 1-30 days
    SMA_1 = "SMA_1"  # 31-60 days
    SMA_2 = "SMA_2"  # 61-90 days
    NPA = "NPA"  # Substandard
    SUBSTANDARD = "SUBSTANDARD"  # < 12 months NPA
    DOUBTFUL_1 = "DOUBTFUL_1"  # 12-24 months NPA
    DOUBTFUL_2 = "DOUBTFUL_2"  # 24-36 months NPA
    DOUBTFUL_3 = "DOUBTFUL_3"  # > 36 months NPA
    LOSS = "LOSS"


class ReceiptType(str, Enum):
    """Type of loan receipt."""

    REGULAR = "REGULAR"
    PREPAYMENT = "PREPAYMENT"
    FORECLOSURE = "FORECLOSURE"
    SUBVENTION = "SUBVENTION"
    INSURANCE_CLAIM = "INSURANCE_CLAIM"
    LEGAL_RECOVERY = "LEGAL_RECOVERY"
    OTS_SETTLEMENT = "OTS_SETTLEMENT"
    WRITE_BACK = "WRITE_BACK"


class ReceiptStatus(str, Enum):
    """Status of receipt."""

    PENDING = "PENDING"
    ALLOCATED = "ALLOCATED"
    REVERSED = "REVERSED"
    BOUNCED = "BOUNCED"


class ReceiptMode(str, Enum):
    """Mode of receipt."""

    CASH = "CASH"
    CHEQUE = "CHEQUE"
    DD = "DD"
    RTGS = "RTGS"
    NEFT = "NEFT"
    IMPS = "IMPS"
    UPI = "UPI"
    NACH = "NACH"
    AUTO_DEBIT = "AUTO_DEBIT"
    ADJUSTMENT = "ADJUSTMENT"


class AllocationPriority(str, Enum):
    """Priority for receipt allocation."""

    FIFO = "FIFO"  # First In First Out
    LIFO = "LIFO"  # Last In First Out
    PROPORTIONATE = "PROPORTIONATE"
    CUSTOM = "CUSTOM"


class AllocationComponent(str, Enum):
    """Component for receipt allocation."""

    CHARGES = "CHARGES"
    PENAL_INTEREST = "PENAL_INTEREST"
    INTEREST = "INTEREST"
    PRINCIPAL = "PRINCIPAL"
    EMI = "EMI"


class AdjustmentType(str, Enum):
    """Type of loan adjustment."""

    RATE_CHANGE = "RATE_CHANGE"
    TENURE_CHANGE = "TENURE_CHANGE"
    EMI_CHANGE = "EMI_CHANGE"
    MORATORIUM = "MORATORIUM"
    RESCHEDULE = "RESCHEDULE"
    RESTRUCTURE = "RESTRUCTURE"
    WRITE_OFF = "WRITE_OFF"
    WAIVER = "WAIVER"


class WaiverType(str, Enum):
    """Type of waiver."""

    INTEREST = "INTEREST"
    PENAL_INTEREST = "PENAL_INTEREST"
    CHARGES = "CHARGES"
    PRINCIPAL = "PRINCIPAL"
    FULL = "FULL"


class ProvisioningCategory(str, Enum):
    """RBI provisioning category."""

    STANDARD = "STANDARD"  # 0.40%
    SUBSTANDARD_SECURED = "SUBSTANDARD_SECURED"  # 15%
    SUBSTANDARD_UNSECURED = "SUBSTANDARD_UNSECURED"  # 25%
    DOUBTFUL_1 = "DOUBTFUL_1"  # 25%
    DOUBTFUL_2 = "DOUBTFUL_2"  # 40%
    DOUBTFUL_3 = "DOUBTFUL_3"  # 100%
    LOSS = "LOSS"  # 100%


class MandateStatus(str, Enum):
    """Status of NACH/eMandate."""

    INITIATED = "INITIATED"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class GLEntryType(str, Enum):
    """Type of GL entry for loan accounting."""

    DISBURSEMENT = "DISBURSEMENT"
    ACCRUAL = "ACCRUAL"
    RECEIPT = "RECEIPT"
    REVERSAL = "REVERSAL"
    PROVISIONING = "PROVISIONING"
    WRITE_OFF = "WRITE_OFF"
    WRITE_BACK = "WRITE_BACK"
    ADJUSTMENT = "ADJUSTMENT"


# ============================================================================
# Phase 3: NPA & Collections Enums
# ============================================================================


class CollectionStage(str, Enum):
    """Stage of collection follow-up."""

    NORMAL = "NORMAL"
    SOFT_COLLECTION = "SOFT_COLLECTION"  # 1-30 DPD
    HARD_COLLECTION = "HARD_COLLECTION"  # 31-90 DPD
    RECOVERY = "RECOVERY"  # > 90 DPD
    LEGAL = "LEGAL"
    WRITE_OFF = "WRITE_OFF"


class FollowUpType(str, Enum):
    """Type of collection follow-up."""

    SMS = "SMS"
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"
    FIELD_VISIT = "FIELD_VISIT"
    DEMAND_NOTICE = "DEMAND_NOTICE"
    LEGAL_NOTICE = "LEGAL_NOTICE"
    RECALL_NOTICE = "RECALL_NOTICE"


class FollowUpStatus(str, Enum):
    """Status of follow-up activity."""

    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NO_RESPONSE = "NO_RESPONSE"
    PTP_RECEIVED = "PTP_RECEIVED"  # Promise to Pay


class FollowUpOutcome(str, Enum):
    """Outcome of collection follow-up."""

    CONTACTED = "CONTACTED"
    NOT_CONTACTABLE = "NOT_CONTACTABLE"
    PROMISE_TO_PAY = "PROMISE_TO_PAY"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"
    DISPUTE = "DISPUTE"
    REFUSED = "REFUSED"
    BROKEN_PTP = "BROKEN_PTP"
    SETTLEMENT_REQUESTED = "SETTLEMENT_REQUESTED"


class DemandNoticeType(str, Enum):
    """Type of demand notice."""

    REMINDER = "REMINDER"
    DEMAND = "DEMAND"
    FINAL_DEMAND = "FINAL_DEMAND"
    RECALL = "RECALL"
    SARFAESI_13_2 = "SARFAESI_13_2"  # Demand notice under SARFAESI
    SARFAESI_13_4 = "SARFAESI_13_4"  # Possession notice


class NPAStatus(str, Enum):
    """Status of NPA account."""

    SMA = "SMA"  # Special Mention Account
    NPA = "NPA"
    UPGRADED = "UPGRADED"  # Back to standard
    RECOVERED = "RECOVERED"
    WRITTEN_OFF = "WRITTEN_OFF"
    SETTLED = "SETTLED"


class OTSStatus(str, Enum):
    """Status of One-Time Settlement."""

    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    NEGOTIATION = "NEGOTIATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"  # Borrower accepted
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class OTSPaymentMode(str, Enum):
    """Payment mode for OTS."""

    LUMP_SUM = "LUMP_SUM"
    INSTALLMENTS = "INSTALLMENTS"
    HYBRID = "HYBRID"  # Upfront + installments


class RestructureType(str, Enum):
    """Type of loan restructuring."""

    TENURE_EXTENSION = "TENURE_EXTENSION"
    EMI_REDUCTION = "EMI_REDUCTION"
    MORATORIUM = "MORATORIUM"
    RATE_REDUCTION = "RATE_REDUCTION"
    PRINCIPAL_HAIRCUT = "PRINCIPAL_HAIRCUT"
    INTEREST_WAIVER = "INTEREST_WAIVER"
    COMPREHENSIVE = "COMPREHENSIVE"  # Multiple changes
    COVID_RESTRUCTURE = "COVID_RESTRUCTURE"


class RestructureStatus(str, Enum):
    """Status of restructuring."""

    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    CANCELLED = "CANCELLED"


class LegalForumType(str, Enum):
    """Legal forum type."""

    DRT = "DRT"  # Debt Recovery Tribunal
    NCLT = "NCLT"  # National Company Law Tribunal
    CIVIL_COURT = "CIVIL_COURT"
    HIGH_COURT = "HIGH_COURT"
    ARBITRATION = "ARBITRATION"
    LOK_ADALAT = "LOK_ADALAT"


class LegalCaseType(str, Enum):
    """Type of legal case."""

    SARFAESI = "SARFAESI"  # Securitisation Act
    DRT_APPLICATION = "DRT_APPLICATION"
    RECOVERY_SUIT = "RECOVERY_SUIT"
    WINDING_UP = "WINDING_UP"
    IBC = "IBC"  # Insolvency and Bankruptcy Code
    ARBITRATION = "ARBITRATION"
    EXECUTION = "EXECUTION"
    APPEAL = "APPEAL"


class LegalCaseStatus(str, Enum):
    """Status of legal case."""

    DRAFT = "DRAFT"
    NOTICE_ISSUED = "NOTICE_ISSUED"
    FILED = "FILED"
    PENDING = "PENDING"
    INTERIM_ORDER = "INTERIM_ORDER"
    DECREE_OBTAINED = "DECREE_OBTAINED"
    EXECUTION = "EXECUTION"
    SETTLED = "SETTLED"
    DISMISSED = "DISMISSED"
    WITHDRAWN = "WITHDRAWN"
    APPEALED = "APPEALED"
    CLOSED = "CLOSED"


class SARFAESIStage(str, Enum):
    """Stages under SARFAESI Act."""

    DEMAND_13_2 = "DEMAND_13_2"  # Demand notice
    OBJECTION_PERIOD = "OBJECTION_PERIOD"  # 60 days wait
    POSSESSION_13_4 = "POSSESSION_13_4"  # Possession notice
    PHYSICAL_POSSESSION = "PHYSICAL_POSSESSION"
    SYMBOLIC_POSSESSION = "SYMBOLIC_POSSESSION"
    SALE_NOTICE = "SALE_NOTICE"
    AUCTION = "AUCTION"
    SALE_COMPLETED = "SALE_COMPLETED"


class AuctionStatus(str, Enum):
    """Status of property auction."""

    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    BID_RECEIVED = "BID_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NO_BIDDERS = "NO_BIDDERS"


class WriteOffType(str, Enum):
    """Type of write-off."""

    TECHNICAL = "TECHNICAL"  # For provisioning
    PRUDENTIAL = "PRUDENTIAL"  # Full write-off
    PARTIAL = "PARTIAL"


class WriteOffStatus(str, Enum):
    """Status of write-off."""

    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EFFECTED = "EFFECTED"
    WRITTEN_BACK = "WRITTEN_BACK"


# ============================================================================
# Phase 4: Treasury & ALM Enums
# ============================================================================


class LenderType(str, Enum):
    """Type of lender/source of borrowing."""

    BANK = "BANK"
    NBFC = "NBFC"
    DFI = "DFI"  # Development Financial Institution
    MUTUAL_FUND = "MUTUAL_FUND"
    INSURANCE_COMPANY = "INSURANCE_COMPANY"
    PENSION_FUND = "PENSION_FUND"
    FII = "FII"  # Foreign Institutional Investor
    NCD = "NCD"  # Non-Convertible Debentures
    COMMERCIAL_PAPER = "COMMERCIAL_PAPER"
    SUBORDINATED_DEBT = "SUBORDINATED_DEBT"
    TIER_2_CAPITAL = "TIER_2_CAPITAL"
    ECB = "ECB"  # External Commercial Borrowing
    RELATED_PARTY = "RELATED_PARTY"


class LenderStatus(str, Enum):
    """Status of lender."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"


class BorrowingType(str, Enum):
    """Type of borrowing facility."""

    TERM_LOAN = "TERM_LOAN"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    CASH_CREDIT = "CASH_CREDIT"
    OVERDRAFT = "OVERDRAFT"
    NCD = "NCD"
    SUBORDINATED_DEBT = "SUBORDINATED_DEBT"
    COMMERCIAL_PAPER = "COMMERCIAL_PAPER"
    REFINANCE = "REFINANCE"
    SECURITIZATION = "SECURITIZATION"
    DIRECT_ASSIGNMENT = "DIRECT_ASSIGNMENT"
    CO_LENDING = "CO_LENDING"
    ECB = "ECB"


class BorrowingStatus(str, Enum):
    """Status of borrowing facility."""

    PROPOSED = "PROPOSED"
    SANCTIONED = "SANCTIONED"
    DOCUMENTATION = "DOCUMENTATION"
    ACTIVE = "ACTIVE"
    FULLY_DRAWN = "FULLY_DRAWN"
    REPAYING = "REPAYING"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    PREPAID = "PREPAID"


class BorrowingSecurityType(str, Enum):
    """Security type for borrowing."""

    UNSECURED = "UNSECURED"
    HYPOTHECATION = "HYPOTHECATION"
    PLEDGE = "PLEDGE"
    MORTGAGE = "MORTGAGE"
    ASSIGNMENT = "ASSIGNMENT"
    GUARANTEE = "GUARANTEE"


class DrawdownStatus(str, Enum):
    """Status of borrowing drawdown/tranche."""

    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    DISBURSED = "DISBURSED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class BorrowingRateType(str, Enum):
    """Interest rate type for borrowing."""

    FIXED = "FIXED"
    FLOATING = "FLOATING"
    MCLR_LINKED = "MCLR_LINKED"
    REPO_LINKED = "REPO_LINKED"
    TBILL_LINKED = "TBILL_LINKED"


class BorrowingPaymentType(str, Enum):
    """Type of borrowing payment."""

    INTEREST = "INTEREST"
    PRINCIPAL = "PRINCIPAL"
    PREPAYMENT = "PREPAYMENT"
    COMMITMENT_FEE = "COMMITMENT_FEE"
    OTHER_CHARGES = "OTHER_CHARGES"


class ALMBucket(str, Enum):
    """RBI ALM time buckets."""

    DAY_1 = "DAY_1"
    DAYS_2_7 = "DAYS_2_7"
    DAYS_8_14 = "DAYS_8_14"
    DAYS_15_28 = "DAYS_15_28"
    DAYS_29_3M = "DAYS_29_3M"  # 29 days to 3 months
    MONTHS_3_6 = "MONTHS_3_6"
    MONTHS_6_12 = "MONTHS_6_12"
    YEARS_1_3 = "YEARS_1_3"
    YEARS_3_5 = "YEARS_3_5"
    OVER_5_YEARS = "OVER_5_YEARS"


class ALMCategory(str, Enum):
    """Category for ALM classification."""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    OFF_BALANCE_SHEET = "OFF_BALANCE_SHEET"


class ALMAssetType(str, Enum):
    """Type of asset for ALM."""

    CASH = "CASH"
    BANK_BALANCE = "BANK_BALANCE"
    INVESTMENTS_HTM = "INVESTMENTS_HTM"  # Held to Maturity
    INVESTMENTS_AFS = "INVESTMENTS_AFS"  # Available for Sale
    INVESTMENTS_HFT = "INVESTMENTS_HFT"  # Held for Trading
    LOANS_STANDARD = "LOANS_STANDARD"
    LOANS_NPA = "LOANS_NPA"
    FIXED_ASSETS = "FIXED_ASSETS"
    OTHER_ASSETS = "OTHER_ASSETS"


class ALMLiabilityType(str, Enum):
    """Type of liability for ALM."""

    BORROWINGS_BANK = "BORROWINGS_BANK"
    BORROWINGS_NCD = "BORROWINGS_NCD"
    BORROWINGS_CP = "BORROWINGS_CP"
    BORROWINGS_SUBORDINATED = "BORROWINGS_SUBORDINATED"
    DEPOSITS = "DEPOSITS"
    OTHER_LIABILITIES = "OTHER_LIABILITIES"
    EQUITY = "EQUITY"


class IRSShockType(str, Enum):
    """Interest rate sensitivity shock scenarios."""

    PARALLEL_UP_100 = "PARALLEL_UP_100"  # +100 bps
    PARALLEL_UP_200 = "PARALLEL_UP_200"  # +200 bps
    PARALLEL_DOWN_100 = "PARALLEL_DOWN_100"  # -100 bps
    PARALLEL_DOWN_200 = "PARALLEL_DOWN_200"  # -200 bps
    STEEPENER = "STEEPENER"  # Short rates down, long rates up
    FLATTENER = "FLATTENER"  # Short rates up, long rates down


class ExposureLimitType(str, Enum):
    """Type of exposure limit."""

    SINGLE_BORROWER = "SINGLE_BORROWER"
    GROUP_BORROWER = "GROUP_BORROWER"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    GEOGRAPHY = "GEOGRAPHY"
    RATING = "RATING"
    PRODUCT = "PRODUCT"
    LENDER = "LENDER"
    UNSECURED = "UNSECURED"
    RELATED_PARTY = "RELATED_PARTY"


class ExposureStatus(str, Enum):
    """Status of exposure against limit."""

    WITHIN_LIMIT = "WITHIN_LIMIT"
    NEAR_LIMIT = "NEAR_LIMIT"  # > 80%
    BREACH = "BREACH"
    EXCEPTION_APPROVED = "EXCEPTION_APPROVED"


class LiquidityRatioType(str, Enum):
    """Type of liquidity ratio."""

    LCR = "LCR"  # Liquidity Coverage Ratio
    NSFR = "NSFR"  # Net Stable Funding Ratio
    CUMULATIVE_GAP = "CUMULATIVE_GAP"
    STRUCTURAL_LIQUIDITY = "STRUCTURAL_LIQUIDITY"


class CovenantType(str, Enum):
    """Type of financial covenant."""

    CRAR = "CRAR"  # Capital to Risk-Weighted Assets
    NPA_RATIO = "NPA_RATIO"
    PROVISION_COVERAGE = "PROVISION_COVERAGE"
    LEVERAGE_RATIO = "LEVERAGE_RATIO"
    INTEREST_COVERAGE = "INTEREST_COVERAGE"
    ASSET_LIABILITY_MISMATCH = "ASSET_LIABILITY_MISMATCH"
    CONCENTRATION_LIMIT = "CONCENTRATION_LIMIT"


class CovenantStatus(str, Enum):
    """Status of covenant compliance."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    WAIVER_OBTAINED = "WAIVER_OBTAINED"
    CURE_PERIOD = "CURE_PERIOD"


# ============================================================================
# Phase 5: NACH/eNACH Integration Enums
# ============================================================================


class NachBatchStatus(str, Enum):
    """Status of NACH batch."""

    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    FILE_GENERATED = "FILE_GENERATED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NachTransactionStatus(str, Enum):
    """Status of individual NACH transaction."""

    PENDING = "PENDING"
    INCLUDED = "INCLUDED"  # Included in batch
    SUBMITTED = "SUBMITTED"
    SUCCESS = "SUCCESS"
    BOUNCED = "BOUNCED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"


class NachReturnCode(str, Enum):
    """NPCI NACH return codes."""

    SUCCESS = "00"  # Transaction successful
    INSUFFICIENT_FUNDS = "01"  # Insufficient funds
    ACCOUNT_CLOSED = "02"  # Account closed
    ACCOUNT_BLOCKED = "03"  # Account blocked/frozen
    NO_SUCH_ACCOUNT = "04"  # No such account
    MANDATE_NOT_FOUND = "05"  # Mandate not found
    MANDATE_CANCELLED = "06"  # Mandate cancelled
    MANDATE_EXPIRED = "07"  # Mandate expired
    MANDATE_SUSPENDED = "08"  # Mandate suspended
    AMOUNT_EXCEEDS_LIMIT = "09"  # Amount exceeds mandate limit
    DUPLICATE_TRANSACTION = "10"  # Duplicate transaction
    INVALID_ACCOUNT = "11"  # Invalid account number
    INVALID_IFSC = "12"  # Invalid IFSC code
    BANK_REJECTED = "13"  # Bank rejected
    TECHNICAL_ERROR = "14"  # Technical error
    TIMEOUT = "15"  # Transaction timeout
    OTHER = "99"  # Other reasons


class NachFileFormat(str, Enum):
    """NACH file format types."""

    ACH_DEBIT = "ACH_DEBIT"
    ACH_CREDIT = "ACH_CREDIT"
    MANDATE_REGISTER = "MANDATE_REGISTER"
    MANDATE_MODIFY = "MANDATE_MODIFY"
    MANDATE_CANCEL = "MANDATE_CANCEL"


# ============================================================================
# Phase 6: Account Aggregator Integration Enums
# ============================================================================


class AAProvider(str, Enum):
    """Account Aggregator providers."""

    FINVU = "FINVU"
    ONEMONEY = "ONEMONEY"
    SETU = "SETU"
    NADL = "NADL"  # NSDL AA
    CAMS_FINSERV = "CAMS_FINSERV"
    PERFIOS = "PERFIOS"


class AAConsentStatus(str, Enum):
    """Status of AA consent."""

    PENDING = "PENDING"  # Consent request created, waiting for user
    APPROVED = "APPROVED"  # User approved consent
    REJECTED = "REJECTED"  # User rejected consent
    ACTIVE = "ACTIVE"  # Consent is active and can be used
    PAUSED = "PAUSED"  # Consent temporarily paused
    REVOKED = "REVOKED"  # User revoked consent
    EXPIRED = "EXPIRED"  # Consent validity expired
    FAILED = "FAILED"  # Consent request failed


class AAConsentPurpose(str, Enum):
    """Purpose of AA consent."""

    WEALTH_MANAGEMENT = "WEALTH_MANAGEMENT"
    UNDERWRITING = "UNDERWRITING"
    MONITORING = "MONITORING"
    BANK_STATEMENT_ANALYSIS = "BANK_STATEMENT_ANALYSIS"
    INCOME_VERIFICATION = "INCOME_VERIFICATION"
    ACCOUNT_AGGREGATION = "ACCOUNT_AGGREGATION"
    TAX_FILING = "TAX_FILING"


class AAConsentMode(str, Enum):
    """Mode of consent - frequency of data fetch."""

    VIEW = "VIEW"  # One-time view
    STORE = "STORE"  # Store data
    QUERY = "QUERY"  # Query data
    STREAM = "STREAM"  # Stream data


class AAFetchFrequency(str, Enum):
    """Frequency of data fetch under consent."""

    ONETIME = "ONETIME"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    AS_AVAILABLE = "AS_AVAILABLE"


class AAFIType(str, Enum):
    """Financial Information types under AA framework."""

    DEPOSIT = "DEPOSIT"
    TERM_DEPOSIT = "TERM_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    SIP = "SIP"
    CP = "CP"  # Commercial Paper
    GOVT_SECURITIES = "GOVT_SECURITIES"
    EQUITIES = "EQUITIES"
    BONDS = "BONDS"
    DEBENTURES = "DEBENTURES"
    MUTUAL_FUNDS = "MUTUAL_FUNDS"
    ETF = "ETF"
    IDR = "IDR"
    CIS = "CIS"
    AIF = "AIF"
    INSURANCE_POLICIES = "INSURANCE_POLICIES"
    NPS = "NPS"
    INVIT = "INVIT"
    REIT = "REIT"
    GSTR1_3B = "GSTR1_3B"
    EPF = "EPF"
    PPF = "PPF"


class AAFetchSessionStatus(str, Enum):
    """Status of AA data fetch session."""

    INITIATED = "INITIATED"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    TIMEOUT = "TIMEOUT"


class AADataStatus(str, Enum):
    """Status of fetched AA data."""

    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"
    IMPORTED = "IMPORTED"  # Imported into system
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class AANotificationType(str, Enum):
    """Type of AA notification/webhook."""

    CONSENT_STATUS_UPDATE = "CONSENT_STATUS_UPDATE"
    FI_NOTIFICATION = "FI_NOTIFICATION"
    ACCOUNT_LINKED = "ACCOUNT_LINKED"
    ACCOUNT_UNLINKED = "ACCOUNT_UNLINKED"
    SESSION_STATUS = "SESSION_STATUS"


# ============================================================================
# Treasury Investment Enums
# ============================================================================
# Distinct from the ALMAssetType.INVESTMENTS_* bucket values — those are for
# liability/asset classification in ALM reporting, while these are for the
# treasury investment portfolio (trs_investment).


class InvestmentType(str, Enum):
    """Type of treasury investment instrument."""

    GSEC = "GSEC"  # Government Securities
    SDL = "SDL"  # State Development Loan
    TBILL = "TBILL"  # Treasury Bill
    CORP_BOND = "CORP_BOND"  # Corporate Bond
    NCD = "NCD"  # Non-Convertible Debenture
    CP = "CP"  # Commercial Paper
    CD = "CD"  # Certificate of Deposit
    MUTUAL_FUND = "MUTUAL_FUND"


class InvestmentCategory(str, Enum):
    """RBI investment classification category."""

    HTM = "HTM"  # Held to Maturity
    AFS = "AFS"  # Available for Sale
    HFT = "HFT"  # Held for Trading


class CouponFrequency(str, Enum):
    """Coupon payment frequency for fixed-income investments."""

    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    ZERO = "ZERO"  # Zero-coupon (discount instruments like T-Bills)


class InvestmentStatus(str, Enum):
    """Lifecycle status of an investment holding."""

    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    SOLD = "SOLD"


# ============================================================================
# IIF / Subvention (Interest Incentivization Fund — Maritime Development Fund)
# ============================================================================


class IIFLoanType(str, Enum):
    """Eligible loan types under the IIF subvention scheme.

    Per scheme clause 6.2.iii: term loans (CAPEX) for new shipyards /
    expansion and working capital for ship-building.
    """

    TERM_LOAN_CAPEX = "TERM_LOAN_CAPEX"
    WORKING_CAPITAL = "WORKING_CAPITAL"


class ClaimFrequency(str, Enum):
    """Subvention claim frequency.

    Per scheme clause 9.2.ii, IIF credits to the loan account quarterly
    even when EMIs are monthly. Half-yearly / annual remain notifiable
    variants — enum is intentionally permissive.
    """

    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class SubventionEnrollmentStatus(str, Enum):
    """Lifecycle of a loan-account ↔ subvention-scheme enrollment."""

    PENDING_APPROVAL = "PENDING_APPROVAL"
    ENROLLED = "ENROLLED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class SubventionClaimStatus(str, Enum):
    """Lifecycle of a single quarterly / period claim."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    RELEASE_IN_PROGRESS = "RELEASE_IN_PROGRESS"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


# ============================================================================
# Approval Checklist (loan-application gating checklist)
# ============================================================================


class ChecklistItemCategory(str, Enum):
    """Category of a checklist item — drives the FE grouping."""

    DOCUMENT = "DOCUMENT"
    KYC = "KYC"
    COMPLIANCE = "COMPLIANCE"
    COVENANT = "COVENANT"
    LEGAL = "LEGAL"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


class ChecklistItemStatus(str, Enum):
    """Per-item completion status on a loan checklist."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    MET = "MET"
    WAIVED = "WAIVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ChecklistAppliesTo(str, Enum):
    """Entity type a checklist template targets.

    Kept as a string column on the template table so future variants
    (DISBURSEMENT / OTS / RESTRUCTURE) extend without a migration.
    """

    LOAN_APPLICATION = "LOAN_APPLICATION"
