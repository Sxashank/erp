/**
 * Lending Module TypeScript Types
 * Enterprise NBFC Lending Platform
 */

// ============== ENUMS ==============

export type EntityType = 'CORPORATE' | 'INDIVIDUAL' | 'LLP' | 'PARTNERSHIP' | 'TRUST' | 'HUF';
export type EntityStatus = 'PROSPECT' | 'ACTIVE' | 'INACTIVE' | 'BLACKLISTED';
export type RiskCategory = 'LOW' | 'MEDIUM' | 'HIGH';
export type CreditRating = 'AAA' | 'AA' | 'A' | 'BBB' | 'BB' | 'B' | 'C' | 'D';

export type ApplicationStage = 'APPLICATION' | 'APPRAISAL' | 'SANCTION' | 'POST_SANCTION' | 'DISBURSED';
export type ApplicationStatus = 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'SANCTIONED' | 'REJECTED' | 'WITHDRAWN';

export type InterestType = 'FIXED' | 'FLOATING';
export type RepaymentFrequency = 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY' | 'BULLET';
export type RepaymentMode = 'EMI' | 'STRUCTURED' | 'BULLET' | 'BALLOON' | 'STEP_UP' | 'STEP_DOWN';
export type DayCountConvention = 'ACT_365' | 'ACT_360' | 'THIRTY_360';

export type AssetClassification =
  | 'STANDARD' | 'SMA_0' | 'SMA_1' | 'SMA_2'
  | 'SUB_STANDARD' | 'DOUBTFUL_1' | 'DOUBTFUL_2' | 'DOUBTFUL_3' | 'LOSS';

export type LoanAccountStatus = 'ACTIVE' | 'CLOSED' | 'NPA' | 'WRITTEN_OFF';
export type DisbursementStatus = 'PENDING' | 'APPROVED' | 'PROCESSED' | 'REJECTED';
export type ReceiptMode = 'CASH' | 'CHEQUE' | 'NEFT' | 'RTGS' | 'IMPS' | 'UPI' | 'NACH' | 'OTHER';
export type ReceiptStatus = 'PENDING' | 'ALLOCATED' | 'PARTIAL' | 'REVERSED';

export type OTSStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'SETTLED' | 'CANCELLED';
export type LegalCaseType = 'SARFAESI' | 'DRT' | 'NCLT' | 'CIVIL' | 'CRIMINAL' | 'ARBITRATION';
export type LegalCaseStatus = 'FILED' | 'PENDING' | 'HEARING' | 'DISPOSED' | 'APPEALED' | 'CLOSED';

export type LenderType = 'BANK' | 'DFI' | 'NCD' | 'CP' | 'ECB' | 'SUBORDINATE_DEBT';
export type BorrowingStatus = 'ACTIVE' | 'CLOSED' | 'PREPAID';

// ============== ENTITY/BORROWER ==============

export interface Entity {
  entity_id: string;
  organization_id: string;
  entity_code: string;
  entity_type: EntityType;
  legal_name: string;
  trade_name?: string;
  cin?: string;
  pan: string;
  gstin?: string;
  tan?: string;
  ckyc_number?: string;
  constitution_date?: string;
  date_of_incorporation?: string;
  internal_rating?: CreditRating;
  risk_category: RiskCategory;
  relationship_manager_id?: string;
  relationship_manager_name?: string;
  status: EntityStatus;
  remarks?: string;
  created_at: string;
  updated_at: string;

  // Related data
  contacts?: EntityContact[];
  addresses?: EntityAddress[];
  bank_accounts?: EntityBankAccount[];
  relations?: EntityRelation[];
  financials?: EntityFinancial[];
  kyc_documents?: EntityKYCDocument[];
}

export interface EntityContact {
  contact_id: string;
  entity_id: string;
  contact_type: 'DIRECTOR' | 'PROMOTER' | 'AUTHORIZED_SIGNATORY' | 'KEY_PERSON' | 'GUARANTOR';
  name: string;
  designation?: string;
  din?: string;
  pan?: string;
  phone?: string;
  mobile?: string;
  email?: string;
  is_primary: boolean;
  created_at: string;
}

export interface EntityAddress {
  address_id: string;
  entity_id: string;
  address_type: 'REGISTERED' | 'CORRESPONDENCE' | 'PLANT' | 'WAREHOUSE' | 'BRANCH';
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  is_primary: boolean;
}

export interface EntityBankAccount {
  bank_account_id: string;
  entity_id: string;
  bank_name: string;
  branch_name: string;
  account_number: string;
  ifsc_code: string;
  account_type: 'CURRENT' | 'SAVINGS' | 'CC' | 'OD';
  is_primary: boolean;
  is_verified: boolean;
  account_holder_name?: string;
}

export interface EntityRelation {
  relation_id: string;
  entity_id: string;
  related_entity_id?: string;
  relation_type: 'PROMOTER' | 'GUARANTOR' | 'GROUP_COMPANY' | 'SUBSIDIARY' | 'ASSOCIATE';
  name: string;
  pan?: string;
  share_percentage?: number;
  remarks?: string;
}

export interface EntityFinancial {
  financial_id: string;
  entity_id: string;
  financial_year: string;
  audited: boolean;

  // Balance Sheet
  total_assets?: number;
  fixed_assets?: number;
  current_assets?: number;
  total_liabilities?: number;
  net_worth?: number;
  long_term_debt?: number;
  short_term_debt?: number;

  // P&L
  revenue?: number;
  operating_profit?: number;
  profit_before_tax?: number;
  profit_after_tax?: number;
  ebitda?: number;
  net_profit?: number;
  total_debt?: number;
  depreciation?: number;
  interest_expense?: number;

  // Additional
  pbt?: number;
  tax?: number;
  current_liabilities?: number;

  // Ratios
  current_ratio?: number;
  debt_equity_ratio?: number;
  dscr?: number;
  interest_coverage?: number;

  created_at: string;
}

export interface EntityKYCDocument {
  kyc_document_id: string;
  entity_id: string;
  document_type: string;
  document_number?: string;
  issue_date?: string;
  expiry_date?: string;
  file_path?: string;
  file_name?: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  verified_by?: string;
  verified_at?: string;
  remarks?: string;
  uploaded_at?: string;
}

// ============== LOAN PRODUCT ==============

export interface LoanProduct {
  product_id: string;
  organization_id: string;
  product_code: string;
  product_name: string;
  product_category: 'TERM_LOAN' | 'WORKING_CAPITAL' | 'PROJECT_FINANCE' | 'LAP' | 'VEHICLE' | 'EQUIPMENT';

  // Limits
  min_amount: number;
  max_amount: number;
  min_tenure_months: number;
  max_tenure_months: number;

  // Interest
  interest_type: InterestType;
  base_rate_type?: string;
  min_spread_bps?: number;
  max_spread_bps?: number;
  default_spread_bps?: number;

  // Repayment
  repayment_mode: RepaymentMode;
  repayment_frequency: RepaymentFrequency;
  day_count_convention: DayCountConvention;

  // Other
  moratorium_allowed: boolean;
  max_moratorium_months?: number;
  prepayment_allowed: boolean;
  prepayment_charges_percent?: number;

  is_active: boolean;
  created_at: string;
  updated_at: string;

  // Related
  fees?: ProductFee[];
  checklist?: DocumentChecklist[];
}

export interface ProductFee {
  product_fee_id: string;
  product_id: string;
  fee_type: 'PROCESSING' | 'DOCUMENTATION' | 'PREPAYMENT' | 'FORECLOSURE' | 'LATE_PAYMENT' | 'BOUNCE' | 'OTHER';
  fee_name: string;
  calculation_type: 'PERCENTAGE' | 'FLAT' | 'SLAB';
  percentage_value?: number;
  flat_value?: number;
  min_value?: number;
  max_value?: number;
  is_gst_applicable: boolean;
}

export interface DocumentChecklist {
  checklist_id: string;
  product_id: string;
  document_name: string;
  document_category: 'KYC' | 'FINANCIAL' | 'LEGAL' | 'SECURITY' | 'OTHER';
  is_mandatory: boolean;
  entity_type_applicable: EntityType[];
}

// ============== LOAN APPLICATION ==============

export interface LoanApplication {
  application_id: string;
  organization_id: string;
  application_number: string;
  entity_id: string;
  entity_name?: string;
  product_id: string;
  product_name?: string;

  // Loan Details
  requested_amount: number;
  approved_amount?: number;
  requested_tenure_months: number;
  approved_tenure_months?: number;
  purpose: string;

  // Project Details (for Project Finance)
  project_name?: string;
  project_cost?: number;
  promoter_contribution?: number;
  bank_finance?: number;
  project_start_date?: string;
  project_end_date?: string;

  // Status
  stage: ApplicationStage;
  status: ApplicationStatus;

  // Interest
  interest_type?: InterestType;
  proposed_rate?: number;
  moratorium_months?: number;
  repayment_frequency?: RepaymentFrequency;

  // Workflow
  workflow_instance_id?: string;
  current_approver?: string;

  // Timestamps
  application_date: string;
  submitted_at?: string;
  sanctioned_at?: string;
  created_at: string;
  updated_at: string;

  // Related
  documents?: ApplicationDocument[];
  fees?: ApplicationFee[];
  securities?: LoanSecurity[];
  milestones?: ProjectMilestone[];
}

export interface ApplicationDocument {
  document_id: string;
  application_id: string;
  checklist_id?: string;
  document_name: string;
  file_path?: string;
  file_name?: string;
  uploaded_at?: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  remarks?: string;
}

export interface ApplicationFee {
  fee_id: string;
  application_id: string;
  fee_type: string;
  fee_name: string;
  calculated_amount: number;
  gst_amount: number;
  total_amount: number;
  paid_amount: number;
  status: 'PENDING' | 'PARTIAL' | 'PAID' | 'WAIVED';
}

export interface LoanSecurity {
  security_id: string;
  application_id?: string;
  sanction_id?: string;
  loan_account_id?: string;

  security_type: 'PRIMARY' | 'COLLATERAL';
  nature: 'PROPERTY' | 'FIXED_DEPOSIT' | 'RECEIVABLES' | 'INVENTORY' | 'EQUIPMENT' | 'SHARES' | 'GUARANTEE' | 'OTHER';
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
  milestone_id: string;
  application_id: string;
  milestone_name: string;
  milestone_sequence: number;
  description?: string;
  expected_completion_date?: string;
  actual_completion_date?: string;
  disbursement_percent: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'DELAYED';
}

// ============== LOAN SANCTION ==============

export interface LoanSanction {
  sanction_id: string;
  organization_id: string;
  sanction_number: string;
  application_id: string;
  entity_id: string;
  entity_name?: string;
  product_id: string;
  product_name?: string;

  // Sanctioned Terms
  sanctioned_amount: number;
  tenure_months: number;
  moratorium_months: number;

  // Interest
  interest_type: InterestType;
  base_rate_id?: string;
  base_rate_name?: string;
  spread_bps: number;
  effective_rate: number;
  rate_reset_frequency?: RepaymentFrequency;

  // Repayment
  repayment_mode: RepaymentMode;
  repayment_frequency: RepaymentFrequency;
  day_count_convention: DayCountConvention;
  repayment_start_date: string;
  maturity_date: string;

  // Status
  sanction_date: string;
  validity_date: string;
  status: 'DRAFT' | 'PENDING_ACCEPTANCE' | 'ACCEPTED' | 'EXPIRED' | 'CANCELLED';
  accepted_at?: string;

  // Workflow
  sanctioned_by?: string;
  approval_authority?: string;

  created_at: string;
  updated_at: string;

  // Related
  conditions?: SanctionCondition[];
  securities?: LoanSecurity[];
}

export interface SanctionCondition {
  condition_id: string;
  sanction_id: string;
  condition_type: 'PRE_DISBURSEMENT' | 'POST_DISBURSEMENT' | 'GENERAL';
  condition_text: string;
  due_date?: string;
  is_mandatory: boolean;
  status: 'PENDING' | 'COMPLIED' | 'WAIVED' | 'OVERDUE';
  complied_at?: string;
  remarks?: string;
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
  entity_type?: EntityType;
  status?: EntityStatus;
  risk_category?: RiskCategory;
  relationship_manager_id?: string;
  page?: number;
  page_size?: number;
}

export interface ApplicationFilters {
  search?: string;
  entity_id?: string;
  product_id?: string;
  stage?: ApplicationStage;
  status?: ApplicationStatus;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface LoanAccountFilters {
  search?: string;
  entity_id?: string;
  product_id?: string;
  asset_classification?: AssetClassification;
  status?: LoanAccountStatus;
  branch_id?: string;
  dpd_from?: number;
  dpd_to?: number;
  page?: number;
  page_size?: number;
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
  loan_account_id?: string;
  entity_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
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
  entity_id?: string;
  application_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
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
  entity_type: EntityType;
  legal_name: string;
  trade_name?: string;
  cin?: string;
  pan: string;
  gstin?: string;
  tan?: string;
  constitution_date?: string;
  risk_category?: RiskCategory;
  relationship_manager_id?: string;
  remarks?: string;
}

export interface CreateApplicationRequest {
  entity_id: string;
  product_id: string;
  requested_amount: number;
  requested_tenure_months: number;
  purpose: string;
  project_name?: string;
  project_cost?: number;
  promoter_contribution?: number;
  interest_type?: InterestType;
  proposed_rate?: number;
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
