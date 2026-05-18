/**
 * Lending Module TypeScript Types
 * Enterprise NBFC Lending Platform
 */

// ============== ENUMS ==============

export type EntityType = 'CORPORATE' | 'INDIVIDUAL' | 'LLP' | 'PARTNERSHIP' | 'TRUST' | 'HUF';
export type EntityStatus = 'PROSPECT' | 'ACTIVE' | 'INACTIVE' | 'BLACKLISTED';
export type RiskCategory = 'LOW' | 'MEDIUM' | 'HIGH';
export type CreditRating = 'AAA' | 'AA' | 'A' | 'BBB' | 'BB' | 'B' | 'C' | 'D';

export type ApplicationStage =
  | 'LEAD'
  | 'APPLICATION'
  | 'APPRAISAL'
  | 'SANCTION'
  | 'POST_SANCTION'
  | 'DISBURSED'
  | 'CLOSED';
export type ApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'SANCTIONED'
  | 'REJECTED'
  | 'WITHDRAWN';

export type InterestType = 'FIXED' | 'FLOATING';
export type RepaymentFrequency = 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY' | 'BULLET';
export type RepaymentMode = 'EMI' | 'STRUCTURED' | 'BULLET' | 'BALLOON' | 'STEP_UP' | 'STEP_DOWN';
export type DayCountConvention = 'ACT_365' | 'ACT_360' | 'THIRTY_360';

export type AssetClassification =
  | 'STANDARD'
  | 'SMA_0'
  | 'SMA_1'
  | 'SMA_2'
  | 'NPA'
  | 'SUBSTANDARD'
  | 'SUB_STANDARD'
  | 'DOUBTFUL'
  | 'DOUBTFUL_1'
  | 'DOUBTFUL_2'
  | 'DOUBTFUL_3'
  | 'LOSS';

export type LoanAccountStatus =
  | 'CREATED'
  | 'ACTIVE'
  | 'DORMANT'
  | 'FROZEN'
  | 'CLOSED'
  | 'WRITTEN_OFF'
  | 'RECALLED';
export type DisbursementStatus = 'PENDING' | 'APPROVED' | 'PROCESSED' | 'REJECTED';
export type ReceiptMode = 'CASH' | 'CHEQUE' | 'NEFT' | 'RTGS' | 'IMPS' | 'UPI' | 'NACH' | 'OTHER';
export type ReceiptStatus = 'PENDING' | 'ALLOCATED' | 'PARTIAL' | 'REVERSED';

export type OTSStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'SETTLED' | 'CANCELLED';
export type LegalCaseType = 'SARFAESI' | 'DRT' | 'NCLT' | 'CIVIL' | 'CRIMINAL' | 'ARBITRATION';
export type LegalCaseStatus = 'FILED' | 'PENDING' | 'HEARING' | 'DISPOSED' | 'APPEALED' | 'CLOSED';

export type LenderType =
  | 'BANK'
  | 'DFI'
  | 'MF'
  | 'NCD'
  | 'CP'
  | 'ECB'
  | 'SECURITIZATION'
  | 'SUBORDINATED_DEBT'
  | 'OTHER';
export type BorrowingStatus = 'ACTIVE' | 'CLOSED' | 'PREPAID';

// ============== ENTITY/BORROWER ==============

export interface Entity {
  id: string;
  organizationId: string;
  entityCode: string;
  entityType: EntityType;
  legalName: string;
  tradeName?: string;
  cin?: string;
  pan: string;
  gstin?: string;
  tan?: string;
  ckycNumber?: string;
  constitutionDate?: string;
  dateOfIncorporation?: string;
  internalRating?: CreditRating;
  riskCategory: RiskCategory;
  relationshipManagerId?: string;
  relationshipManagerName?: string;
  status: EntityStatus;
  remarks?: string;
  createdAt: string;
  updatedAt: string;

  // Related data
  contacts?: EntityContact[];
  addresses?: EntityAddress[];
  bankAccounts?: EntityBankAccount[];
  relations?: EntityRelation[];
  financials?: EntityFinancial[];
  kycDocuments?: EntityKYCDocument[];
}

export interface EntityContact {
  id: string;
  entityId: string;
  contactType:
    | 'DIRECTOR'
    | 'PROMOTER'
    | 'AUTHORIZED_SIGNATORY'
    | 'KEY_MANAGERIAL_PERSON'
    | 'GUARANTOR';
  name: string;
  designation?: string;
  din?: string;
  pan?: string;
  phone?: string;
  mobile?: string;
  email?: string;
  isPrimary: boolean;
  createdAt: string;
}

export interface EntityAddress {
  id: string;
  entityId: string;
  addressType: 'REGISTERED' | 'CORRESPONDENCE' | 'PLANT' | 'WAREHOUSE' | 'BRANCH' | 'PROJECT_SITE';
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  stateCode?: string;
  pincode: string;
  country: string;
  isVerified?: boolean;
  isPrimary?: boolean;
}

export interface EntityBankAccount {
  id: string;
  entityId: string;
  bankName: string;
  branchName?: string;
  accountNumber: string;
  ifscCode: string;
  accountType: 'CURRENT' | 'SAVINGS' | 'CC' | 'OD';
  isPrimary: boolean;
  isVerified: boolean;
  accountHolderName?: string;
}

export interface EntityRelation {
  id: string;
  entityId: string;
  relatedEntityId?: string;
  relationType: 'PROMOTER' | 'GUARANTOR' | 'GROUP_COMPANY' | 'SUBSIDIARY' | 'ASSOCIATE';
  name: string;
  pan?: string;
  sharePercentage?: number;
  remarks?: string;
}

export interface EntityFinancial {
  id: string;
  entityId: string;
  financialYear: string;
  isAudited: boolean;
  auditStatus?: string;

  // Balance Sheet
  totalAssets?: number;
  fixedAssets?: number;
  currentAssets?: number;
  totalLiabilities?: number;
  netWorth?: number;
  longTermDebt?: number;
  shortTermDebt?: number;

  // P&L
  revenue?: number;
  operatingProfit?: number;
  profitBeforeTax?: number;
  profitAfterTax?: number;
  ebitda?: number;
  netProfit?: number;
  totalDebt?: number;
  depreciation?: number;
  interestExpense?: number;
  taxExpense?: number;

  // Additional
  currentLiabilities?: number;

  // Ratios
  currentRatio?: number;
  debtEquityRatio?: number;
  dscr?: number;
  interestCoverage?: number;

  createdAt: string;
}

export interface EntityKYCDocument {
  id: string;
  entityId: string;
  documentTypeId: string;
  documentName?: string;
  documentNumber?: string;
  issueDate?: string;
  expiryDate?: string;
  filePath?: string;
  fileName?: string;
  verificationStatus: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'EXPIRED' | 'RESUBMISSION_REQUIRED';
  verifiedBy?: string;
  verifiedAt?: string;
  remarks?: string;
  createdAt?: string;
}

// ============== LOAN PRODUCT ==============

export interface LoanProduct {
  id: string;
  organizationId: string;
  code: string;
  name: string;
  category: 'TERM_LOAN' | 'WORKING_CAPITAL' | 'PROJECT_FINANCE' | 'LAP' | 'VEHICLE' | 'EQUIPMENT';
  subCategory?: string | null;

  // Limits
  minAmount: number | string;
  maxAmount: number | string;
  minTenureMonths: number;
  maxTenureMonths: number;
  defaultTenureMonths?: number | null;

  // Interest
  interestType: InterestType;
  baseRateId?: string | null;
  minSpreadBps?: number;
  maxSpreadBps?: number;
  defaultSpreadBps?: number;

  // Repayment
  defaultRepaymentMode: RepaymentMode;
  defaultRepaymentFrequency: RepaymentFrequency;
  dayCountConvention: DayCountConvention;

  // Other
  allowsMoratorium: boolean;
  maxMoratoriumMonths?: number | null;
  allowsPrepayment: boolean;
  prepaymentLockInMonths?: number | null;

  isActive: boolean;
  createdAt: string;
  updatedAt?: string | null;

  // Related
  fees?: ProductFee[];
  checklist?: DocumentChecklist[];
}

export interface ProductFee {
  id: string;
  productId: string;
  feeMasterId: string;
  isMandatory: boolean;
  isWaivable: boolean;
  maxWaiverPercentage: number | string;
  overrideCalculationType?: 'PERCENTAGE' | 'FLAT' | 'SLAB' | null;
  overrideRate?: number | string | null;
  overrideAmount?: number | string | null;
  overrideMinAmount?: number | string | null;
  overrideMaxAmount?: number | string | null;
  displayOrder: number;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

export interface DocumentChecklist {
  id: string;
  productId: string;
  code: string;
  name: string;
  description?: string | null;
  category: 'KYC' | 'FINANCIAL' | 'LEGAL' | 'SECURITY' | 'OTHER';
  requiredAtStage: string;
  isMandatory: boolean;
  isMandatoryForDisbursement: boolean;
  applicableEntityTypes?: EntityType[] | null;
  applicableConditions?: Record<string, unknown> | null;
  hasExpiry: boolean;
  validityMonths?: number | null;
  renewalAlertDays?: number | null;
  allowedFileTypes: string[];
  maxFileSizeMb: number;
  minFileCount: number;
  maxFileCount: number;
  requiresVerification: boolean;
  verificationInstructions?: string | null;
  sampleDocumentPath?: string | null;
  helpText?: string | null;
  displayOrder: number;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

// ============== LOAN APPLICATION ==============

export interface LoanApplication {
  id: string;
  organizationId: string;
  applicationNumber: string;
  entityId: string;
  entityName?: string | null;
  productId: string;
  productName?: string | null;

  // Loan Details
  requestedAmount: number | string;
  approvedAmount?: number | string | null;
  requestedTenureMonths: number;
  approvedTenureMonths?: number | null;
  purpose: string;
  detailedPurpose?: string | null;

  // Project Details (for Project Finance)
  isProjectFinance?: boolean;
  projectName?: string | null;
  projectCost?: number | string | null;
  promoterContribution?: number | string | null;
  promoterContributionPct?: number | string | null;
  bankFinance?: number | string | null;
  otherFinance?: number | string | null;
  projectLocation?: string | null;
  projectStartDate?: string | null;
  projectCompletionDate?: string | null;

  // Status
  stage: ApplicationStage;
  status: ApplicationStatus;

  // Interest
  preferredInterestType?: InterestType;
  proposedRate?: number | string | null;
  requestedMoratoriumMonths?: number;
  preferredRepaymentFrequency?: RepaymentFrequency;
  preferredRepaymentMode?: RepaymentMode;

  // Workflow
  workflowInstanceId?: string | null;
  currentApprover?: string | null;

  // Timestamps
  applicationDate?: string;
  submittedAt?: string | null;
  sanctionedAt?: string | null;
  createdAt: string;
  updatedAt?: string | null;

  // Related
  documents?: ApplicationDocument[];
  fees?: ApplicationFee[];
  securities?: LoanSecurity[];
  milestones?: ProjectMilestone[];
}

export interface ApplicationDocument {
  id: string;
  applicationId: string;
  checklistItemId?: string | null;
  documentCode: string;
  documentName: string;
  documentDescription?: string | null;
  fileName: string;
  dmsDocumentId?: string | null;
  filePath: string;
  fileSizeBytes?: number | null;
  fileMimeType?: string | null;
  fileHash?: string | null;
  documentDate?: string | null;
  expiryDate?: string | null;
  uploadDate?: string | null;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'WAIVED';
  isMandatory: boolean;
  isWaived: boolean;
  waiverReason?: string | null;
  waiverApprovedBy?: string | null;
  verifiedById?: string | null;
  verifiedAt?: string | null;
  verificationRemarks?: string | null;
  rejectionReason?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

export interface ApplicationFee {
  id: string;
  applicationId: string;
  feeMasterId: string;
  feeCode: string;
  feeName: string;
  calculatedAmount: number | string;
  approvedAmount: number | string;
  waiverAmount: number | string;
  waiverPercentage: number | string;
  cgstAmount: number | string;
  sgstAmount: number | string;
  igstAmount: number | string;
  totalAmount: number | string;
  status: 'PENDING' | 'COLLECTED' | 'WAIVED' | 'DEDUCTED' | 'REFUNDED';
  collectionMode?: string | null;
  collectionDate?: string | null;
  collectionReference?: string | null;
  waiverApprovedBy?: string | null;
  waiverReason?: string | null;
  deductedFromDisbursement: boolean;
  disbursementId?: string | null;
  invoiceNumber?: string | null;
  invoiceDate?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

export interface LoanSecurity {
  security_id: string;
  application_id?: string;
  sanction_id?: string;
  loan_account_id?: string;

  security_type: 'PRIMARY' | 'COLLATERAL';
  nature:
    | 'PROPERTY'
    | 'FIXED_DEPOSIT'
    | 'RECEIVABLES'
    | 'INVENTORY'
    | 'EQUIPMENT'
    | 'SHARES'
    | 'GUARANTEE'
    | 'OTHER';
  description: string;

  // Valuation
  declared_value?: number;
  assessed_value?: number;
  forced_sale_value?: number;
  margin_percent?: number;
  realizable_value?: number;

  // Property specific
  property_type?: string;
  property_address?: string;
  survey_number?: string;
  area_sqft?: number;

  // Documentation
  document_type?: string;
  document_number?: string;
  document_date?: string;

  charge_type?: 'EXCLUSIVE' | 'PARI_PASSU' | 'SECOND';
  charge_registered: boolean;
  cersai_registration_number?: string;

  created_at: string;
}

export interface ProjectMilestone {
  id: string;
  applicationId: string;
  milestoneNumber: number;
  milestoneName: string;
  milestoneDescription?: string | null;
  expectedDate: string;
  actualDate?: string | null;
  delayDays?: number | null;
  disbursementPercentage: number | string;
  disbursementAmount?: number | string | null;
  cumulativeDisbursementPct?: number | string | null;
  equityContributionRequired?: number | string | null;
  equityContributionVerified: boolean;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'DELAYED' | 'WAIVED';
  verificationCriteria?: string | null;
  verificationDocuments?: Record<string, unknown>[] | null;
  verifiedById?: string | null;
  verifiedAt?: string | null;
  verificationRemarks?: string | null;
  remarks?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

// ============== LOAN SANCTION ==============

export interface LoanSanction {
  id: string;
  organizationId: string;
  sanctionNumber: string;
  applicationId: string;
  entityId: string;
  entityName?: string | null;
  productId: string;
  productName?: string | null;
  requestedAmount: number | string;

  // Sanctioned Terms
  sanctionedAmount: number | string;
  tenureMonths: number;
  moratoriumMonths: number;
  moratoriumType?: string | null;

  // Interest
  interestType: InterestType;
  baseRateId?: string | null;
  baseRateAtSanction?: number | string | null;
  baseRateName?: string | null;
  spreadBps: number;
  effectiveRate: number | string;
  rateResetFrequency?: string | null;
  firstRateResetDate?: string | null;
  penalInterestRate: number | string;

  // Repayment
  repaymentMode: RepaymentMode;
  repaymentFrequency: RepaymentFrequency;
  dayCountConvention: DayCountConvention;
  repaymentStartDate?: string | null;
  maturityDate?: string | null;

  // Disbursement and validity
  disbursementType: string;
  maxTranches: number;
  sanctionDate: string;
  validityDate: string;
  firstDisbursementDeadline?: string | null;
  sanctionLetterPath?: string | null;
  agreementDraftPath?: string | null;

  // Workflow and status
  status: SanctionStatus;
  workflowInstanceId?: string | null;
  approvedById?: string | null;
  approvedAt?: string | null;
  approvalAuthority?: string | null;
  approvalReference?: string | null;
  acceptedAt?: string | null;

  // Prepayment terms
  allowsPrepayment: boolean;
  prepaymentLockInMonths: number;
  prepaymentPenaltyRate: number | string;
  allowsForeclosure: boolean;
  foreclosurePenaltyRate: number | string;

  specialTerms?: string | null;
  remarks?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;

  // Related
  conditions?: SanctionCondition[];
  securities?: SanctionSecurity[];
}

export type SanctionStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ACTIVE'
  | 'ACCEPTED'
  | 'EXPIRED'
  | 'CANCELLED'
  | 'SUPERSEDED';

export interface SanctionCondition {
  id: string;
  sanctionId: string;
  conditionNumber?: number | null;
  conditionCode?: string | null;
  conditionType: 'PRE_DISBURSEMENT' | 'POST_DISBURSEMENT' | 'ONGOING' | 'EVENT_BASED';
  category: 'LEGAL' | 'FINANCIAL' | 'SECURITY' | 'REGULATORY' | 'OPERATIONAL' | 'PROJECT';
  description: string;
  detailedRequirement?: string | null;
  dueDate?: string | null;
  isTimeBound: boolean;
  daysFromDisbursement?: number | null;
  frequency?: string | null;
  nextComplianceDate?: string | null;
  isMandatory: boolean;
  blocksDisbursement: boolean;
  isWaivable: boolean;
  waiverAuthority?: string | null;
  complianceStatus: 'PENDING' | 'COMPLIED' | 'WAIVED' | 'DEFERRED' | 'NOT_APPLICABLE';
  complianceDate?: string | null;
  complianceRemarks?: string | null;
  complianceVerifiedBy?: string | null;
  waiverDate?: string | null;
  waiverReason?: string | null;
  waiverApprovedBy?: string | null;
  deferralDate?: string | null;
  deferralReason?: string | null;
  deferralApprovedBy?: string | null;
  requiredDocuments?: Record<string, unknown>[] | null;
  uploadedDocuments?: Record<string, unknown>[] | null;
  displayOrder: number;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

export interface SanctionSecurity {
  id: string;
  sanctionId: string;
  securityNumber?: number | null;
  securityCode?: string | null;
  securityCategory: 'PRIMARY' | 'COLLATERAL' | 'GUARANTEE';
  securityType: string;
  chargeType: string;
  description: string;
  detailedDescription?: string | null;
  propertyAddress?: string | null;
  propertyAreaSqft?: number | string | null;
  surveyNumber?: string | null;
  propertyType?: string | null;
  ownerName?: string | null;
  ownerRelationship?: string | null;
  isThirdParty: boolean;
  thirdPartyEntityId?: string | null;
  declaredValue?: number | string | null;
  marketValue?: number | string | null;
  forcedSaleValue?: number | string | null;
  acceptableValue: number | string;
  marginPercentage: number | string;
  netValue: number | string;
  valuationDate?: string | null;
  valuerName?: string | null;
  valuerFirm?: string | null;
  valuationReportPath?: string | null;
  nextValuationDate?: string | null;
  status: string;
  cersaiId?: string | null;
  cersaiRegistrationDate?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
}

// ============== LOAN ACCOUNT ==============

export interface LoanAccount {
  loan_account_id: string;
  organization_id: string;
  loan_account_number: string;
  sanction_id: string;
  entity_id: string;
  entity_name?: string;
  product_id: string;
  product_name?: string;

  // Amounts
  sanctioned_amount: number;
  disbursed_amount: number;
  principal_outstanding: number;
  interest_outstanding: number;
  penal_outstanding: number;
  charges_outstanding: number;
  total_outstanding: number;

  // Interest
  interest_type: InterestType;
  base_rate_id?: string;
  base_rate_name?: string;
  current_base_rate?: number;
  spread_bps: number;
  effective_rate: number;
  day_count_convention: DayCountConvention;

  // Tenure
  tenure_months: number;
  moratorium_months: number;
  disbursement_date?: string;
  first_emi_date?: string;
  maturity_date: string;
  repayment_frequency: RepaymentFrequency;

  // Classification
  dpd: number;
  asset_classification: AssetClassification;
  npa_date?: string;
  provision_rate: number;
  provision_amount: number;

  status: LoanAccountStatus;
  closed_at?: string;

  created_at: string;
  updated_at: string;
}

export interface RepaymentSchedule {
  schedule_id: string;
  loan_account_id: string;
  installment_number: number;
  due_date: string;

  principal_amount: number;
  interest_amount: number;
  total_emi: number;

  principal_paid: number;
  interest_paid: number;
  total_paid: number;

  opening_balance: number;
  closing_balance: number;

  status: 'PENDING' | 'PARTIAL' | 'PAID' | 'OVERDUE';
  paid_date?: string;
}

export interface Disbursement {
  disbursement_id: string;
  loan_account_id: string;
  disbursement_number: string;
  tranche_number: number;

  amount: number;
  disbursement_date: string;
  value_date: string;

  // Payment Details
  beneficiary_name: string;
  beneficiary_account: string;
  beneficiary_bank: string;
  beneficiary_ifsc: string;
  payment_mode: 'NEFT' | 'RTGS' | 'IMPS' | 'CHEQUE';
  payment_reference?: string;

  status: DisbursementStatus;
  approved_by?: string;
  approved_at?: string;
  processed_by?: string;
  processed_at?: string;

  remarks?: string;
  created_at: string;
}

// ============== RECEIPTS & COLLECTIONS ==============

export interface Receipt {
  receipt_id: string;
  organization_id: string;
  receipt_number: string;
  loan_account_id: string;
  loan_account_number?: string;
  entity_id: string;
  entity_name?: string;

  receipt_date: string;
  value_date: string;
  amount: number;

  receipt_mode: ReceiptMode;
  instrument_number?: string;
  instrument_date?: string;
  bank_name?: string;

  // Allocation
  allocated_principal: number;
  allocated_interest: number;
  allocated_penal: number;
  allocated_charges: number;
  unallocated_amount: number;

  status: ReceiptStatus;

  remarks?: string;
  created_by: string;
  created_at: string;

  allocations?: ReceiptAllocation[];
}

export interface ReceiptAllocation {
  allocation_id: string;
  receipt_id: string;
  allocation_type: 'PRINCIPAL' | 'INTEREST' | 'PENAL' | 'CHARGES' | 'ON_ACCOUNT';
  schedule_id?: string;
  amount: number;
  allocation_date: string;
}

export interface CollectionFollowUp {
  followup_id: string;
  loan_account_id: string;
  loan_account_number?: string;
  entity_name?: string;

  followup_date: string;
  followup_type: 'CALL' | 'VISIT' | 'EMAIL' | 'SMS' | 'NOTICE' | 'OTHER';
  contact_person?: string;
  contact_number?: string;

  outcome: 'PTP' | 'BROKEN_PTP' | 'NOT_REACHABLE' | 'DISPUTED' | 'PAID' | 'OTHER';
  ptp_date?: string;
  ptp_amount?: number;

  remarks: string;
  next_followup_date?: string;

  created_by: string;
  created_at: string;
}

// ============== NPA & OTS ==============

export interface NPARecord {
  npa_id: string;
  loan_account_id: string;
  loan_account_number?: string;
  entity_name?: string;

  npa_date: string;
  classification_at_npa: AssetClassification;
  current_classification: AssetClassification;

  principal_at_npa: number;
  interest_at_npa: number;
  total_at_npa: number;

  current_outstanding: number;
  provision_rate: number;
  provision_amount: number;

  recovery_amount: number;
  last_recovery_date?: string;

  status: 'ACTIVE' | 'UPGRADED' | 'SETTLED' | 'WRITTEN_OFF';
  upgraded_at?: string;

  created_at: string;
  updated_at: string;
}

export interface OTSProposal {
  ots_id: string;
  organization_id: string;
  ots_number: string;
  loan_account_id: string;
  loan_account_number?: string;
  entity_id: string;
  entity_name?: string;

  // Outstanding at OTS
  principal_outstanding: number;
  interest_outstanding: number;
  penal_outstanding: number;
  total_outstanding: number;

  // Settlement Terms
  settlement_amount: number;
  discount_amount: number;
  discount_percent: number;

  payment_mode: 'LUMPSUM' | 'STRUCTURED';
  settlement_period_days: number;
  settlement_start_date: string;
  settlement_end_date: string;

  // Status
  status: OTSStatus;
  submitted_at?: string;
  approved_by?: string;
  approved_at?: string;

  conditions?: string;
  remarks?: string;

  created_by: string;
  created_at: string;
  updated_at: string;

  payment_schedule?: OTSPaymentSchedule[];
}

export interface OTSPaymentSchedule {
  schedule_id: string;
  ots_id: string;
  installment_number: number;
  due_date: string;
  amount: number;
  paid_amount: number;
  status: 'PENDING' | 'PAID' | 'OVERDUE';
  paid_date?: string;
}

export interface LegalCase {
  legal_case_id: string;
  loan_account_id: string;
  loan_account_number?: string;
  entity_name?: string;

  case_type: LegalCaseType;
  case_number?: string;
  court_name: string;
  filing_date: string;

  claim_amount: number;

  lawyer_name?: string;
  lawyer_contact?: string;

  status: LegalCaseStatus;
  next_hearing_date?: string;

  remarks?: string;
  created_at: string;
  updated_at: string;

  hearings?: LegalHearing[];
}

export interface LegalHearing {
  hearing_id: string;
  legal_case_id: string;
  hearing_date: string;
  hearing_type: 'REGULAR' | 'ARGUMENT' | 'EVIDENCE' | 'FINAL' | 'EX_PARTE';
  outcome?: string;
  next_hearing_date?: string;
  remarks?: string;
  created_at: string;
}

// ============== TREASURY & ALM ==============

export interface Lender {
  lender_id: string;
  organization_id: string;
  lender_code: string;
  lender_name: string;
  lender_type: LenderType;

  contact_person?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;

  pan?: string;
  cin?: string;
  gstin?: string;
  rbi_registration?: string;
  registered_address?: string;

  bank_name?: string;
  bank_branch?: string;
  bank_account_number?: string;
  bank_ifsc?: string;

  external_rating?: string;
  rating_agency?: string;
  rating_date?: string;

  total_sanction_limit?: number;
  remarks?: string;

  is_active: boolean;
  created_at: string;
}

export interface LenderListItem {
  id: string;
  lenderCode: string;
  lenderName: string;
  lenderType: LenderType;
  status: string;
  externalRating: string | null;
  ratingAgency: string | null;
  totalSanctionLimit: string | null;
  availableLimit: string | null;
  contactPerson: string | null;
  contactEmail: string | null;
  contactPhone: string | null;
  pan: string | null;
  rbiRegistration: string | null;
}

export interface Borrowing {
  borrowing_id: string;
  organization_id: string;
  borrowing_number: string;
  lender_id: string;
  lender_name?: string;

  facility_type: LenderType;
  facility_name: string;

  sanctioned_amount: number;
  drawn_amount: number;
  outstanding_amount: number;

  interest_type: InterestType;
  base_rate_type?: string;
  spread_bps: number;
  effective_rate: number;

  sanction_date: string;
  first_drawdown_date?: string;
  maturity_date: string;

  repayment_frequency: RepaymentFrequency;

  status: BorrowingStatus;

  security_details?: string;
  covenants?: string;

  sanction_reference?: string;
  currency?: string;
  base_rate_value?: number;
  rate_reset_frequency?: string;
  day_count_convention?: string;
  interest_payment_frequency?: string;
  principal_payment_frequency?: string;
  tenure_months?: number;
  moratorium_months?: number;
  first_interest_date?: string;
  first_principal_date?: string;
  security_type?: string;
  security_description?: string;
  security_cover_required?: number;
  processing_fee_percent?: number;
  commitment_fee_percent?: number;
  prepayment_penalty_percent?: number;
  remarks?: string;

  created_at: string;
  updated_at: string;
}

export interface ALMPosition {
  position_id: string;
  organization_id: string;
  position_date: string;

  bucket_name: string;
  bucket_days_from: number;
  bucket_days_to: number;

  total_assets: number;
  total_liabilities: number;
  gap: number;
  cumulative_gap: number;
  gap_percent: number;

  created_at: string;
}

// ============== REPORTS & DASHBOARD ==============

export interface LendingKPIs {
  // Portfolio
  total_aum: number;
  aum_growth_mom: number;
  active_accounts: number;

  // Origination
  applications_pending: number;
  sanctioned_mtd: number;
  avg_tat_days: number;

  // Collections
  collection_efficiency: number;
  overdue_amount: number;

  // NPA
  gross_npa_percent: number;
  net_npa_percent: number;
  provision_coverage: number;

  // Treasury
  total_borrowings: number;
  alm_gap_30_days: number;
}

// ============== FORM/FILTER TYPES ==============

export interface EntityFilters {
  search?: string;
  entityType?: EntityType;
  status?: EntityStatus;
  riskCategory?: RiskCategory;
  relationshipManagerId?: string;
  page?: number;
  pageSize?: number;
}

export interface ApplicationFilters {
  search?: string;
  entityId?: string;
  productId?: string;
  stage?: ApplicationStage;
  status?: ApplicationStatus;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface LoanAccountFilters {
  search?: string;
  entityId?: string;
  productId?: string;
  status?: LoanAccountStatus;
  assetClassification?: AssetClassification;
  dpdFrom?: number;
  dpdTo?: number;
  page?: number;
  pageSize?: number;
}

export interface CollectionFilters {
  search?: string;
  loan_account_id?: string;
  entity_id?: string;
  assigned_to?: string;
  followup_type?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface NPAFilters {
  search?: string;
  entity_id?: string;
  classification?: string;
  branch_id?: string;
  dpd_from?: number;
  dpd_to?: number;
  page?: number;
  page_size?: number;
}

export interface OTSFilters {
  search?: string;
  loan_account_id?: string;
  entity_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface LegalCaseFilters {
  search?: string;
  loan_account_id?: string;
  entity_id?: string;
  case_type?: string;
  status?: string;
  court_name?: string;
  page?: number;
  page_size?: number;
}

export interface DisbursementFilters {
  search?: string;
  loanAccountId?: string;
  entityId?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface ReceiptFilters {
  search?: string;
  loan_account_id?: string;
  entity_id?: string;
  receipt_mode?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface SanctionFilters {
  search?: string;
  entityId?: string;
  applicationId?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface LenderFilters {
  search?: string;
  lender_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface BorrowingFilters {
  search?: string;
  lender_id?: string;
  facility_type?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============== API REQUEST TYPES ==============

export interface CreateEntityRequest {
  entityType: EntityType;
  legalName: string;
  tradeName?: string;
  cin?: string;
  pan: string;
  gstin?: string;
  tan?: string;
  constitutionDate?: string;
  riskCategory?: RiskCategory;
  relationshipManagerId?: string;
  remarks?: string;
}

export interface CreateApplicationRequest {
  entityId: string;
  productId: string;
  requestedAmount: number;
  requestedTenureMonths: number;
  purpose: string;
  detailedPurpose?: string;
  isProjectFinance?: boolean;
  projectName?: string;
  projectCost?: number;
  promoterContribution?: number;
  promoterContributionPct?: number;
  bankFinance?: number;
  otherFinance?: number;
  projectLocation?: string;
  projectStartDate?: string;
  projectCompletionDate?: string;
  preferredInterestType?: InterestType;
  proposedRate?: number;
  requestedMoratoriumMonths?: number;
  preferredRepaymentFrequency?: RepaymentFrequency;
  preferredRepaymentMode?: RepaymentMode;
  remarks?: string;
}

export interface CreateReceiptRequest {
  loan_account_id: string;
  receipt_date: string;
  value_date: string;
  amount: number;
  receipt_mode: ReceiptMode;
  instrument_number?: string;
  instrument_date?: string;
  bank_name?: string;
  remarks?: string;
}
