"""Lending module models package."""

# Enums
from app.models.lending.enums import (
    # Entity/Borrower Enums
    EntityType,
    EntityStatus,
    ContactType,
    AddressType,
    RelationType,
    RiskCategory,
    IndustrySector,
    # KYC Enums
    KYCDocCategory,
    KYCVerificationStatus,
    KYCVerificationMethod,
    CKYCTransactionType,
    BureauType,
    BureauPullStatus,
    # Credit Rating Enums
    RatingGrade,
    RatingType,
    RatingStatus,
    RiskCategoryType,
    # Loan Product Enums
    ProductCategory,
    InterestType,
    RateResetFrequency,
    RepaymentFrequency,
    RepaymentMode,
    DayCountConvention,
    FeeType,
    FeeCalculationType,
    FeeCollectionStage,
    # Document Checklist Enums
    DocumentCategory,
    DocumentStage,
    # Application Enums
    ApplicationStage,
    ApplicationStatus,
    AppraisalType,
    TechnicalFeasibility,
    AppraisalRecommendation,
    MilestoneStatus,
    # Sanction Enums
    SanctionStatus,
    ConditionType,
    ConditionCategory,
    ConditionComplianceStatus,
    # Security/Collateral Enums
    SecurityCategory,
    SecurityType,
    ChargeType,
    SecurityStatus,
)

# Entity/Borrower Models
from app.models.lending.entity import (
    Entity,
    EntityContact,
    EntityAddress,
    EntityBankAccount,
    EntityRelation,
    EntityFinancial,
)

# KYC Models
from app.models.lending.kyc import (
    KYCDocumentType,
    EntityKYCDocument,
    CKYCTransaction,
    BureauPull,
    BureauReport,
)

# Credit Rating Models
from app.models.lending.rating import (
    RiskCategory as RiskCategoryModel,
    RiskParameter,
    RatingMatrix,
    EntityRating,
    RatingScoreDetail,
)

# Loan Product Models
from app.models.lending.product import (
    LoanProduct,
    InterestRate,
    InterestRateHistory,
    FeeMaster,
    ProductFee,
    DocumentChecklist,
)

# Application Models
from app.models.lending.application import (
    LoanApplication,
    ApplicationDocument,
    ApplicationFee,
    TechnicalAppraisal,
    FinancialAnalysis,
    ProjectMilestone,
)

# Sanction Models
from app.models.lending.sanction import (
    LoanSanction,
    SanctionCondition,
    LoanSecurity,
)

# Phase 2: Loan Accounting Models
from app.models.lending.loan_account import (
    LoanAccount,
    Disbursement,
    RepaymentSchedule,
    ScheduleInstallment,
    LoanAccrual,
    LoanReceipt,
    ReceiptAllocation,
    LoanMandate,
    AssetClassificationHistory,
    LoanProvision,
    LoanAdjustment,
)

# Phase 2: Loan Accounting Enums
from app.models.lending.enums import (
    LoanAccountStatus,
    DisbursementStatus,
    DisbursementMode,
    ScheduleType,
    InstallmentType,
    InstallmentStatus,
    AccrualCategory,
    AccrualStatus,
    AssetClassification,
    ReceiptType,
    ReceiptStatus,
    ReceiptMode,
    AllocationPriority,
    AllocationComponent,
    AdjustmentType,
    WaiverType,
    ProvisioningCategory,
    MandateStatus,
    GLEntryType,
)

# Phase 3: NPA & Collections Models
from app.models.lending.collections import (
    CollectionFollowUp,
    DemandNotice,
    NPARecord,
    PenalInterest,
    PenalWaiver,
    OTSProposal,
    OTSPaymentSchedule,
    LoanRestructure,
    LegalCase,
    LegalHearing,
    PropertyAuction,
    WriteOffRecord,
)

# Phase 3: NPA & Collections Enums
from app.models.lending.enums import (
    CollectionStage,
    FollowUpType,
    FollowUpStatus,
    FollowUpOutcome,
    DemandNoticeType,
    NPAStatus,
    OTSStatus,
    OTSPaymentMode,
    RestructureType,
    RestructureStatus,
    LegalForumType,
    LegalCaseType,
    LegalCaseStatus,
    SARFAESIStage,
    AuctionStatus,
    WriteOffType,
    WriteOffStatus,
)

# Phase 4: Treasury & ALM Models
from app.models.lending.treasury import (
    Lender,
    Borrowing,
    BorrowingTranche,
    BorrowingSchedule,
    BorrowingPayment,
    BorrowingCovenant,
    ALMPosition,
    ALMAsset,
    ALMLiability,
    IRSAnalysis,
    ExposureLimit,
    ExposureTracking,
)

# Phase 4: Treasury & ALM Enums
from app.models.lending.enums import (
    LenderType,
    LenderStatus,
    BorrowingType,
    BorrowingStatus,
    BorrowingSecurityType,
    DrawdownStatus,
    BorrowingRateType,
    BorrowingPaymentType,
    ALMBucket,
    ALMCategory,
    ALMAssetType,
    ALMLiabilityType,
    IRSShockType,
    ExposureLimitType,
    ExposureStatus,
    LiquidityRatioType,
    CovenantType,
    CovenantStatus,
)

# Phase 5: NACH/eNACH Integration Models
from app.models.lending.nach_batch import (
    NachBatch,
    NachTransaction,
    NachMandateLog,
)

# Phase 5: NACH/eNACH Integration Enums
from app.models.lending.enums import (
    NachBatchStatus,
    NachTransactionStatus,
    NachReturnCode,
    NachFileFormat,
)

# Phase 6: Account Aggregator Integration Models
from app.models.lending.aa_consent import (
    AAConsent,
    AAFetchSession,
    AABankAccount,
    AABankTransaction,
    AAConsentLog,
)

# Phase 6: Account Aggregator Integration Enums
from app.models.lending.enums import (
    AAProvider,
    AAConsentStatus,
    AAConsentPurpose,
    AAConsentMode,
    AAFetchFrequency,
    AAFIType,
    AAFetchSessionStatus,
    AADataStatus,
    AANotificationType,
)

# Phase 7: Credit Bureau Integration Models
from app.models.lending.credit_pull import (
    CreditPull,
    CreditAccount,
    CreditEnquiry,
    CreditBureau,
    CreditPullType,
    CreditPullStatus,
    CreditAccountType,
    CreditAccountStatus,
    AccountOwnership,
)

# Aliases for backward compatibility
LoanSchedule = RepaymentSchedule
NPAClassification = NPARecord
NPAProvision = LoanProvision
NPAHistory = AssetClassificationHistory


__all__ = [
    # Entity/Borrower Enums
    "EntityType",
    "EntityStatus",
    "ContactType",
    "AddressType",
    "RelationType",
    "RiskCategory",
    "IndustrySector",
    # KYC Enums
    "KYCDocCategory",
    "KYCVerificationStatus",
    "KYCVerificationMethod",
    "CKYCTransactionType",
    "BureauType",
    "BureauPullStatus",
    # Credit Rating Enums
    "RatingGrade",
    "RatingType",
    "RatingStatus",
    "RiskCategoryType",
    # Loan Product Enums
    "ProductCategory",
    "InterestType",
    "RateResetFrequency",
    "RepaymentFrequency",
    "RepaymentMode",
    "DayCountConvention",
    "FeeType",
    "FeeCalculationType",
    "FeeCollectionStage",
    # Document Checklist Enums
    "DocumentCategory",
    "DocumentStage",
    # Application Enums
    "ApplicationStage",
    "ApplicationStatus",
    "AppraisalType",
    "TechnicalFeasibility",
    "AppraisalRecommendation",
    "MilestoneStatus",
    # Sanction Enums
    "SanctionStatus",
    "ConditionType",
    "ConditionCategory",
    "ConditionComplianceStatus",
    # Security/Collateral Enums
    "SecurityCategory",
    "SecurityType",
    "ChargeType",
    "SecurityStatus",
    # Entity/Borrower Models
    "Entity",
    "EntityContact",
    "EntityAddress",
    "EntityBankAccount",
    "EntityRelation",
    "EntityFinancial",
    # KYC Models
    "KYCDocumentType",
    "EntityKYCDocument",
    "CKYCTransaction",
    "BureauPull",
    "BureauReport",
    # Credit Rating Models
    "RiskCategoryModel",
    "RiskParameter",
    "RatingMatrix",
    "EntityRating",
    "RatingScoreDetail",
    # Loan Product Models
    "LoanProduct",
    "InterestRate",
    "InterestRateHistory",
    "FeeMaster",
    "ProductFee",
    "DocumentChecklist",
    # Application Models
    "LoanApplication",
    "ApplicationDocument",
    "ApplicationFee",
    "TechnicalAppraisal",
    "FinancialAnalysis",
    "ProjectMilestone",
    # Sanction Models
    "LoanSanction",
    "SanctionCondition",
    "LoanSecurity",
    # Phase 2: Loan Accounting Models
    "LoanAccount",
    "Disbursement",
    "RepaymentSchedule",
    "ScheduleInstallment",
    "LoanAccrual",
    "LoanReceipt",
    "ReceiptAllocation",
    "LoanMandate",
    "AssetClassificationHistory",
    "LoanProvision",
    "LoanAdjustment",
    # Phase 2: Loan Accounting Enums
    "LoanAccountStatus",
    "DisbursementStatus",
    "DisbursementMode",
    "ScheduleType",
    "InstallmentType",
    "InstallmentStatus",
    "AccrualCategory",
    "AccrualStatus",
    "AssetClassification",
    "ReceiptType",
    "ReceiptStatus",
    "ReceiptMode",
    "AllocationPriority",
    "AllocationComponent",
    "AdjustmentType",
    "WaiverType",
    "ProvisioningCategory",
    "MandateStatus",
    "GLEntryType",
    # Phase 3: NPA & Collections Models
    "CollectionFollowUp",
    "DemandNotice",
    "NPARecord",
    "PenalInterest",
    "PenalWaiver",
    "OTSProposal",
    "OTSPaymentSchedule",
    "LoanRestructure",
    "LegalCase",
    "LegalHearing",
    "PropertyAuction",
    "WriteOffRecord",
    # Phase 3: NPA & Collections Enums
    "CollectionStage",
    "FollowUpType",
    "FollowUpStatus",
    "FollowUpOutcome",
    "DemandNoticeType",
    "NPAStatus",
    "OTSStatus",
    "OTSPaymentMode",
    "RestructureType",
    "RestructureStatus",
    "LegalForumType",
    "LegalCaseType",
    "LegalCaseStatus",
    "SARFAESIStage",
    "AuctionStatus",
    "WriteOffType",
    "WriteOffStatus",
    # Phase 4: Treasury & ALM Models
    "Lender",
    "Borrowing",
    "BorrowingTranche",
    "BorrowingSchedule",
    "BorrowingPayment",
    "BorrowingCovenant",
    "ALMPosition",
    "ALMAsset",
    "ALMLiability",
    "IRSAnalysis",
    "ExposureLimit",
    "ExposureTracking",
    # Phase 4: Treasury & ALM Enums
    "LenderType",
    "LenderStatus",
    "BorrowingType",
    "BorrowingStatus",
    "BorrowingSecurityType",
    "DrawdownStatus",
    "BorrowingRateType",
    "BorrowingPaymentType",
    "ALMBucket",
    "ALMCategory",
    "ALMAssetType",
    "ALMLiabilityType",
    "IRSShockType",
    "ExposureLimitType",
    "ExposureStatus",
    "LiquidityRatioType",
    "CovenantType",
    "CovenantStatus",
    # Phase 5: NACH/eNACH Integration Models
    "NachBatch",
    "NachTransaction",
    "NachMandateLog",
    # Phase 5: NACH/eNACH Integration Enums
    "NachBatchStatus",
    "NachTransactionStatus",
    "NachReturnCode",
    "NachFileFormat",
    # Phase 6: Account Aggregator Integration Models
    "AAConsent",
    "AAFetchSession",
    "AABankAccount",
    "AABankTransaction",
    "AAConsentLog",
    # Phase 6: Account Aggregator Integration Enums
    "AAProvider",
    "AAConsentStatus",
    "AAConsentPurpose",
    "AAConsentMode",
    "AAFetchFrequency",
    "AAFIType",
    "AAFetchSessionStatus",
    "AADataStatus",
    "AANotificationType",
    # Phase 7: Credit Bureau Integration Models
    "CreditPull",
    "CreditAccount",
    "CreditEnquiry",
    # Phase 7: Credit Bureau Integration Enums
    "CreditBureau",
    "CreditPullType",
    "CreditPullStatus",
    "CreditAccountType",
    "CreditAccountStatus",
    "AccountOwnership",
    # Aliases
    "LoanSchedule",
    "NPAClassification",
    "NPAProvision",
    "NPAHistory",
]
