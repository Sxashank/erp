/**
 * Enhanced Lending Module Types
 * NPA, Schedule, Receipt, Disbursement, Collateral
 */

// ============== NPA Types ==============

export type NPAClassification =
  | 'STANDARD'
  | 'SMA_0'
  | 'SMA_1'
  | 'SMA_2'
  | 'SUBSTANDARD'
  | 'DOUBTFUL_1'
  | 'DOUBTFUL_2'
  | 'DOUBTFUL_3'
  | 'LOSS';

export interface NPAClassificationResult {
  loan_account_id: string;
  dpd: number;
  classification: NPAClassification;
  previous_classification?: NPAClassification;
  classified_at: string;
}

export interface ProvisionCalculation {
  loan_account_id: string;
  classification: NPAClassification;
  principal_outstanding: number;
  security_value: number;
  unsecured_portion: number;
  provision_rate: number;
  provision_amount: number;
  provision_held: number;
  provision_movement: number;
}

export interface NPASummary {
  as_of_date: string;
  total_loans: number;
  standard_loans: {
    count: number;
    amount: number;
    percentage: number;
  };
  npa_loans: {
    count: number;
    amount: number;
    percentage: number;
    gross_npa_ratio: number;
    net_npa_ratio: number;
  };
  npa_ratio: number;
}

export interface NPAMovement {
  from_date: string;
  to_date: string;
  opening: Record<string, { count: number; amount: number }>;
  additions: Record<string, { count: number; amount: number }>;
  reductions: Record<string, { count: number; amount: number }>;
  closing: Record<string, { count: number; amount: number }>;
}

// ============== Schedule Types ==============

export type CalculationMethod = 'flat' | 'reducing_balance' | 'emi' | 'rule_of_78';

export interface ScheduleEntry {
  id?: string;
  installment_number: number;
  due_date: string;
  principal_amount: number;
  interest_amount: number;
  total_amount: number;
  opening_balance: number;
  closing_balance: number;
  is_moratorium: boolean;
  is_paid: boolean;
  is_partial: boolean;
  principal_paid?: number;
  interest_paid?: number;
}

export interface LoanSchedule {
  loan_account_id: string;
  total_installments: number;
  total_principal: number;
  total_interest: number;
  total_amount: number;
  entries: ScheduleEntry[];
}

export interface EMICalculation {
  emi: number;
  total_interest: number;
  total_payment: number;
  principal: number;
  annual_rate: number;
  tenure_months: number;
}

export interface ScheduleGenerateParams {
  loan_account_id: string;
  principal: number;
  interest_rate: number;
  tenure_months: number;
  disbursement_date: string;
  emi_day?: number;
  calculation_method?: CalculationMethod;
  moratorium_months?: number;
}

export interface RescheduleParams {
  loan_account_id: string;
  new_tenure?: number;
  new_rate?: number;
  new_emi?: number;
  effective_date?: string;
  reason: string;
}

// ============== Receipt Types ==============

export type ReceiptType = 'REGULAR' | 'PREPAYMENT' | 'FORECLOSURE' | 'PARTIAL_PREPAYMENT' | 'BOUNCE_RECOVERY' | 'WRITE_OFF_RECOVERY';
export type ReceiptMode = 'CASH' | 'CHEQUE' | 'DD' | 'NEFT' | 'RTGS' | 'IMPS' | 'UPI' | 'NACH' | 'OTHER';
export type ReceiptStatus = 'PENDING' | 'ALLOCATED' | 'REVERSED' | 'BOUNCED';
export type AllocationMethod = 'fifo' | 'proportional' | 'specific';

export interface Receipt {
  id: string;
  receipt_number: string;
  loan_account_id: string;
  receipt_amount: number;
  receipt_date: string;
  value_date: string;
  receipt_type: ReceiptType;
  receipt_mode: ReceiptMode;
  status: ReceiptStatus;
  instrument_number?: string;
  instrument_date?: string;
  instrument_bank?: string;
  allocated_amount: number;
  unallocated_amount: number;
  principal_allocated: number;
  interest_allocated: number;
  penal_interest_allocated: number;
  charges_allocated: number;
  bounced: boolean;
  bounce_reason?: string;
  bounce_charges?: number;
  remarks?: string;
}

export interface ReceiptAllocation {
  id: string;
  receipt_id: string;
  installment_id?: string;
  component: 'CHARGES' | 'PENAL_INTEREST' | 'INTEREST' | 'PRINCIPAL';
  amount: number;
  sequence: number;
}

export interface ReceiptCreateParams {
  loan_account_id: string;
  receipt_amount: number;
  receipt_date: string;
  value_date?: string;
  receipt_type?: ReceiptType;
  receipt_mode: ReceiptMode;
  instrument_number?: string;
  instrument_date?: string;
  instrument_bank?: string;
  mandate_id?: string;
  remarks?: string;
}

export interface BulkReceiptItem {
  loan_account_number: string;
  receipt_amount: number;
  receipt_date: string;
  receipt_mode: ReceiptMode;
  instrument_number?: string;
  remarks?: string;
}

export interface BulkReceiptResult {
  total_count: number;
  success_count: number;
  failed_count: number;
  total_amount: number;
  failures: { index: number; error: string; data: BulkReceiptItem }[];
}

// ============== Disbursement Types ==============

export type DisbursementMode = 'RTGS' | 'NEFT' | 'IMPS' | 'CHEQUE' | 'DD' | 'INTERNAL_TRANSFER';
export type DisbursementStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'DISBURSED' | 'CANCELLED' | 'REVERSED';

export interface Disbursement {
  id: string;
  disbursement_reference: string;
  loan_account_id: string;
  disbursement_number: number;
  requested_amount: number;
  approved_amount?: number;
  disbursed_amount?: number;
  disbursement_charges: number;
  net_disbursement?: number;
  status: DisbursementStatus;
  disbursement_mode: DisbursementMode;
  beneficiary_name: string;
  beneficiary_account_number: string;
  beneficiary_ifsc: string;
  beneficiary_bank?: string;
  utr_number?: string;
  cheque_number?: string;
  request_date: string;
  scheduled_date?: string;
  approval_date?: string;
  disbursement_date?: string;
  value_date?: string;
  conditions_verified: boolean;
  purpose?: string;
  rejection_reason?: string;
  remarks?: string;
}

export interface DisbursementCreateParams {
  loan_account_id: string;
  requested_amount: number;
  beneficiary_name: string;
  beneficiary_account: string;
  beneficiary_ifsc: string;
  disbursement_mode?: DisbursementMode;
  scheduled_date?: string;
  purpose?: string;
  beneficiary_bank?: string;
  bank_account_id?: string;
  milestone_id?: string;
}

export interface DisbursementProcessParams {
  disbursement_id: string;
  disbursed_amount: number;
  disbursement_date?: string;
  value_date?: string;
  utr_number?: string;
  cheque_number?: string;
  disbursement_charges?: number;
}

export interface TrancheItem {
  amount: number;
  beneficiary_name: string;
  beneficiary_account: string;
  beneficiary_ifsc: string;
  mode?: DisbursementMode;
  scheduled_date?: string;
  purpose?: string;
  beneficiary_bank?: string;
  milestone_id?: string;
}

export interface DisbursementSummary {
  from_date: string;
  to_date: string;
  disbursed: {
    count: number;
    amount: number;
  };
  by_mode: Record<string, { count: number; amount: number }>;
  pending_count: number;
  approved: {
    count: number;
    amount: number;
  };
}

// ============== Collateral Types ==============

export type SecurityCategory = 'PRIMARY' | 'COLLATERAL' | 'GUARANTEE';
export type SecurityType =
  | 'IMMOVABLE_PROPERTY'
  | 'MOVABLE_ASSET'
  | 'SHARES'
  | 'DEBENTURES'
  | 'BONDS'
  | 'FIXED_DEPOSIT'
  | 'GOLD'
  | 'INVENTORY'
  | 'RECEIVABLES'
  | 'PLANT_MACHINERY'
  | 'VEHICLE'
  | 'PERSONAL_GUARANTEE'
  | 'CORPORATE_GUARANTEE'
  | 'BANK_GUARANTEE'
  | 'OTHER';
export type ChargeType = 'FIRST' | 'SECOND' | 'PARI_PASSU' | 'SUBSERVIENT';
export type SecurityStatus = 'PENDING' | 'ACTIVE' | 'RELEASED' | 'SUBSTITUTED';

export interface Collateral {
  id: string;
  sanction_id: string;
  security_number: number;
  security_code?: string;
  security_category: SecurityCategory;
  security_type: SecurityType;
  charge_type: ChargeType;
  description: string;
  detailed_description?: string;
  acceptable_value: number;
  margin_percentage: number;
  net_value: number;
  market_value?: number;
  forced_sale_value?: number;
  declared_value?: number;
  valuation_date?: string;
  valuer_name?: string;
  valuer_firm?: string;
  next_valuation_date?: string;
  status: SecurityStatus;
  // Property details
  property_address?: string;
  property_area_sqft?: number;
  survey_number?: string;
  property_type?: string;
  // Owner details
  owner_name?: string;
  owner_relationship?: string;
  is_third_party: boolean;
  // Encumbrance
  has_existing_charge: boolean;
  existing_charge_holder?: string;
  existing_charge_amount?: number;
  // Charge creation
  charge_created: boolean;
  charge_creation_date?: string;
  charge_id?: string;
  cersai_registration_date?: string;
  cersai_transaction_id?: string;
}

export interface PropertyDetails {
  address?: string;
  area_sqft?: number;
  survey_number?: string;
  type?: string;
  detailed_description?: string;
}

export interface OwnerDetails {
  name?: string;
  relationship?: string;
  is_third_party?: boolean;
  entity_id?: string;
}

export interface ValuationDetails {
  declared_value?: number;
  market_value?: number;
  forced_sale_value?: number;
  valuation_date?: string;
  valuer_name?: string;
  valuer_firm?: string;
  report_path?: string;
}

export interface CollateralCreateParams {
  sanction_id: string;
  security_category: SecurityCategory;
  security_type: SecurityType;
  description: string;
  acceptable_value: number;
  margin_percentage?: number;
  charge_type?: ChargeType;
  property_details?: PropertyDetails;
  owner_details?: OwnerDetails;
  valuation_details?: ValuationDetails;
}

export interface SecurityCoverage {
  sanction_id: string;
  loan_amount: number;
  securities: {
    id: string;
    category: SecurityCategory;
    type: SecurityType;
    description: string;
    acceptable_value: number;
    margin: number;
    net_value: number;
    status: SecurityStatus;
  }[];
  category_totals: Record<string, { count: number; acceptable_value: number; net_value: number }>;
  total_acceptable_value: number;
  total_net_value: number;
  coverage_ratio: number;
  is_fully_secured: boolean;
}

export interface CollateralSummary {
  total_securities: number;
  total_acceptable_value: number;
  total_net_value: number;
  by_type: Record<string, { count: number; acceptable_value: number; net_value: number }>;
  by_category: Record<string, { count: number; acceptable_value: number; net_value: number }>;
  pending_valuation_count: number;
  as_of_date: string;
}
