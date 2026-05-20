"""Lending module models package."""

# Enums
# Phase 6: Account Aggregator Integration Models
from app.models.lending.aa_consent import (
    AABankAccount,
    AABankTransaction,
    AAConsent,
    AAConsentLog,
    AAFetchSession,
)

# Application Models
from app.models.lending.application import (
    ApplicationDocument,
    ApplicationFee,
    FinancialAnalysis,
    LoanApplication,
    ProjectMilestone,
    TechnicalAppraisal,
)

# Approval Checklist Models + Enums
from app.models.lending.checklist import (
    ApprovalChecklistTemplate,
    ApprovalChecklistTemplateItem,
    LoanChecklist,
    LoanChecklistItem,
)

# Phase 3: NPA & Collections Models
from app.models.lending.collections import (
    CollectionFollowUp,
    DemandNotice,
    LegalCase,
    LegalHearing,
    LoanRestructure,
    NPARecord,
    OTSPaymentSchedule,
    OTSProposal,
    PenalInterest,
    PenalWaiver,
    PropertyAuction,
    WriteOffRecord,
)

# Phase 7: Credit Bureau Integration Models
from app.models.lending.credit_pull import (
    AccountOwnership,
    CreditAccount,
    CreditAccountStatus,
    CreditAccountType,
    CreditBureau,
    CreditEnquiry,
    CreditPull,
    CreditPullStatus,
    CreditPullType,
)

# Entity/Borrower Models
from app.models.lending.entity import (
    Entity,
    EntityAddress,
    EntityBankAccount,
    EntityContact,
    EntityFinancial,
    EntityRelation,
)

# Phase 2: Loan Accounting Enums
# Phase 3: NPA & Collections Enums
# Phase 4: Treasury & ALM Enums
# Treasury Investment Enums
# Phase 5: NACH/eNACH Integration Enums
# Phase 6: Account Aggregator Integration Enums
# IIF Enums
from app.models.lending.enums import (
    AAConsentMode,
    AAConsentPurpose,
    AAConsentStatus,
    AADataStatus,
    AAFetchFrequency,
    AAFetchSessionStatus,
    AAFIType,
    AANotificationType,
    AAProvider,
    AccrualCategory,
    AccrualStatus,
    AddressType,
    AdjustmentType,
    AllocationComponent,
    AllocationPriority,
    ALMAssetType,
    ALMBucket,
    ALMCategory,
    ALMLiabilityType,
    # Application Enums
    ApplicationStage,
    ApplicationStatus,
    AppraisalRecommendation,
    AppraisalType,
    AssetClassification,
    AuctionStatus,
    BorrowingPaymentType,
    BorrowingRateType,
    BorrowingSecurityType,
    BorrowingStatus,
    BorrowingType,
    BureauPullStatus,
    BureauType,
    ChargeType,
    ChecklistAppliesTo,
    ChecklistItemCategory,
    ChecklistItemStatus,
    CKYCTransactionType,
    ClaimFrequency,
    CollectionStage,
    ConditionCategory,
    ConditionComplianceStatus,
    ConditionType,
    ContactType,
    CouponFrequency,
    CovenantStatus,
    CovenantType,
    DayCountConvention,
    DemandNoticeType,
    DisbursementMode,
    DisbursementStatus,
    # Document Checklist Enums
    DocumentCategory,
    DocumentStage,
    DrawdownStatus,
    EntityStatus,
    # Entity/Borrower Enums
    EntityType,
    ExposureLimitType,
    ExposureStatus,
    FeeCalculationType,
    FeeCollectionStage,
    FeeType,
    FollowUpOutcome,
    FollowUpStatus,
    FollowUpType,
    GLEntryType,
    IIFLoanType,
    IndustrySector,
    InstallmentStatus,
    InstallmentType,
    InterestType,
    InvestmentCategory,
    InvestmentStatus,
    InvestmentType,
    IRSShockType,
    # KYC Enums
    KYCDocCategory,
    KYCVerificationMethod,
    KYCVerificationStatus,
    LegalCaseStatus,
    LegalCaseType,
    LegalForumType,
    LenderStatus,
    LenderType,
    LiquidityRatioType,
    LoanAccountStatus,
    MandateStatus,
    MilestoneStatus,
    NachBatchStatus,
    NachFileFormat,
    NachReturnCode,
    NachTransactionStatus,
    NPAStatus,
    OTSPaymentMode,
    OTSStatus,
    # Loan Product Enums
    ProductCategory,
    ProvisioningCategory,
    RateResetFrequency,
    # Credit Rating Enums
    RatingGrade,
    RatingStatus,
    RatingType,
    ReceiptMode,
    ReceiptStatus,
    ReceiptType,
    RelationType,
    RepaymentFrequency,
    RepaymentMode,
    RestructureStatus,
    RestructureType,
    RiskCategory,
    RiskCategoryType,
    # Sanction Enums
    SanctionStatus,
    SARFAESIStage,
    ScheduleType,
    # Security/Collateral Enums
    SecurityCategory,
    SecurityStatus,
    SecurityType,
    SubventionClaimStatus,
    SubventionEnrollmentStatus,
    TechnicalFeasibility,
    WaiverType,
    WriteOffStatus,
    WriteOffType,
)

# Interest Incentivization Fund (IIF) Models
from app.models.lending.iif import (
    ApplicationFundingSource,
    ApplicationLenderLoan,
    ApplicationUtilization,
    FundUtilizationCategory,
    LoanSubventionEnrollment,
    SubventionClaim,
    SubventionFundTransaction,
    SubventionScheme,
)

# KYC Models
from app.models.lending.kyc import (
    BureauPull,
    BureauReport,
    CKYCTransaction,
    EntityKYCDocument,
    KYCDocumentType,
)

# Phase 2: Loan Accounting Models
from app.models.lending.loan_account import (
    AssetClassificationHistory,
    Disbursement,
    LoanAccount,
    LoanAccrual,
    LoanAdjustment,
    LoanMandate,
    LoanProvision,
    LoanReceipt,
    LoanReceiptBankStatementMatch,
    ReceiptAllocation,
    RepaymentSchedule,
    ScheduleInstallment,
)

# Phase 5: NACH/eNACH Integration Models
from app.models.lending.nach_batch import (
    NachBatch,
    NachMandateLog,
    NachTransaction,
)

# Loan Product Models
from app.models.lending.product import (
    DocumentChecklist,
    FeeMaster,
    InterestRate,
    InterestRateHistory,
    LoanProduct,
    ProductFee,
)
from app.models.lending.rating import (
    EntityRating,
    RatingMatrix,
    RatingScoreDetail,
    RiskParameter,
)

# Credit Rating Models
from app.models.lending.rating import (
    RiskCategory as RiskCategoryModel,
)

# Sanction Models
from app.models.lending.sanction import (
    LoanSanction,
    LoanSecurity,
    SanctionCondition,
)

# Phase 4: Treasury & ALM Models
from app.models.lending.treasury import (
    ALMAsset,
    ALMLiability,
    ALMPosition,
    Borrowing,
    BorrowingCovenant,
    BorrowingPayment,
    BorrowingSchedule,
    BorrowingTranche,
    ExposureLimit,
    ExposureTracking,
    FundDeployment,
    IRSAnalysis,
    Lender,
)

# Treasury Investment Portfolio
from app.models.lending.treasury_investment import TreasuryInvestment

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
    "LoanReceiptBankStatementMatch",
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
    "FundDeployment",
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
    # Treasury Investment Portfolio
    "TreasuryInvestment",
    "InvestmentType",
    "InvestmentCategory",
    "CouponFrequency",
    "InvestmentStatus",
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
    # IIF Models
    "SubventionScheme",
    "FundUtilizationCategory",
    "ApplicationUtilization",
    "ApplicationFundingSource",
    "ApplicationLenderLoan",
    "LoanSubventionEnrollment",
    "SubventionClaim",
    "SubventionFundTransaction",
    # IIF Enums
    "IIFLoanType",
    "ClaimFrequency",
    "SubventionEnrollmentStatus",
    "SubventionClaimStatus",
    # Approval Checklist Models
    "ApprovalChecklistTemplate",
    "ApprovalChecklistTemplateItem",
    "LoanChecklist",
    "LoanChecklistItem",
    # Approval Checklist Enums
    "ChecklistItemCategory",
    "ChecklistItemStatus",
    "ChecklistAppliesTo",
    # Aliases
    "LoanSchedule",
    "NPAClassification",
    "NPAProvision",
    "NPAHistory",
]
