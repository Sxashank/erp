"""Lending module repositories package."""

from app.repositories.lending.entity_repo import (
    EntityRepository,
    EntityContactRepository,
    EntityAddressRepository,
    EntityBankAccountRepository,
    EntityRelationRepository,
    EntityFinancialRepository,
)
from app.repositories.lending.kyc_repo import (
    KYCDocumentTypeRepository,
    EntityKYCDocumentRepository,
    CKYCTransactionRepository,
    BureauPullRepository,
    BureauReportRepository,
)
from app.repositories.lending.rating_repo import (
    RiskCategoryRepository,
    RiskParameterRepository,
    RatingMatrixRepository,
    EntityRatingRepository,
    RatingScoreDetailRepository,
)
from app.repositories.lending.product_repo import (
    LoanProductRepository,
    InterestRateRepository,
    FeeMasterRepository,
    ProductFeeRepository,
    DocumentChecklistRepository,
)
from app.repositories.lending.application_repo import (
    LoanApplicationRepository,
    ApplicationDocumentRepository,
    ApplicationFeeRepository,
    TechnicalAppraisalRepository,
    FinancialAnalysisRepository,
    ProjectMilestoneRepository,
)
from app.repositories.lending.sanction_repo import (
    LoanSanctionRepository,
    SanctionConditionRepository,
    LoanSecurityRepository,
)

# Phase 2: Loan Account Repositories
from app.repositories.lending.loan_account_repo import (
    LoanAccountRepository,
    DisbursementRepository,
    RepaymentScheduleRepository,
    ScheduleInstallmentRepository,
    LoanAccrualRepository,
    LoanReceiptRepository,
    ReceiptAllocationRepository,
    LoanMandateRepository,
    AssetClassificationHistoryRepository,
    LoanProvisionRepository,
    LoanAdjustmentRepository,
)

# Phase 3: NPA & Collections Repositories
from app.repositories.lending.collections_repo import (
    CollectionFollowUpRepository,
    DemandNoticeRepository,
    NPARecordRepository,
    PenalInterestRepository,
    PenalWaiverRepository,
    OTSProposalRepository,
    OTSPaymentScheduleRepository,
    LoanRestructureRepository,
    LegalCaseRepository,
    LegalHearingRepository,
    PropertyAuctionRepository,
    WriteOffRecordRepository,
)

# Phase 4: Treasury & ALM Repositories
from app.repositories.lending.treasury_repo import (
    LenderRepository,
    BorrowingRepository,
    BorrowingTrancheRepository,
    BorrowingScheduleRepository,
    BorrowingPaymentRepository,
    BorrowingCovenantRepository,
    ALMPositionRepository,
    ALMAssetRepository,
    ALMLiabilityRepository,
    IRSAnalysisRepository,
    ExposureLimitRepository,
    ExposureTrackingRepository,
)


__all__ = [
    # Entity
    "EntityRepository",
    "EntityContactRepository",
    "EntityAddressRepository",
    "EntityBankAccountRepository",
    "EntityRelationRepository",
    "EntityFinancialRepository",
    # KYC
    "KYCDocumentTypeRepository",
    "EntityKYCDocumentRepository",
    "CKYCTransactionRepository",
    "BureauPullRepository",
    "BureauReportRepository",
    # Rating
    "RiskCategoryRepository",
    "RiskParameterRepository",
    "RatingMatrixRepository",
    "EntityRatingRepository",
    "RatingScoreDetailRepository",
    # Product
    "LoanProductRepository",
    "InterestRateRepository",
    "FeeMasterRepository",
    "ProductFeeRepository",
    "DocumentChecklistRepository",
    # Application
    "LoanApplicationRepository",
    "ApplicationDocumentRepository",
    "ApplicationFeeRepository",
    "TechnicalAppraisalRepository",
    "FinancialAnalysisRepository",
    "ProjectMilestoneRepository",
    # Sanction
    "LoanSanctionRepository",
    "SanctionConditionRepository",
    "LoanSecurityRepository",
    # Phase 2: Loan Account
    "LoanAccountRepository",
    "DisbursementRepository",
    "RepaymentScheduleRepository",
    "ScheduleInstallmentRepository",
    "LoanAccrualRepository",
    "LoanReceiptRepository",
    "ReceiptAllocationRepository",
    "LoanMandateRepository",
    "AssetClassificationHistoryRepository",
    "LoanProvisionRepository",
    "LoanAdjustmentRepository",
    # Phase 3: NPA & Collections
    "CollectionFollowUpRepository",
    "DemandNoticeRepository",
    "NPARecordRepository",
    "PenalInterestRepository",
    "PenalWaiverRepository",
    "OTSProposalRepository",
    "OTSPaymentScheduleRepository",
    "LoanRestructureRepository",
    "LegalCaseRepository",
    "LegalHearingRepository",
    "PropertyAuctionRepository",
    "WriteOffRecordRepository",
    # Phase 4: Treasury & ALM
    "LenderRepository",
    "BorrowingRepository",
    "BorrowingTrancheRepository",
    "BorrowingScheduleRepository",
    "BorrowingPaymentRepository",
    "BorrowingCovenantRepository",
    "ALMPositionRepository",
    "ALMAssetRepository",
    "ALMLiabilityRepository",
    "IRSAnalysisRepository",
    "ExposureLimitRepository",
    "ExposureTrackingRepository",
]
