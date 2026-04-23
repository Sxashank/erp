/**
 * Legal Module TypeScript Types
 */

// ==================== Law Firm & Advocate Types ====================

export interface LawFirm {
  id: string;
  name: string;
  registration_number?: string;
  bar_council_id?: string;
  pan?: string;
  gstin?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  fee_structure?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Advocate {
  id: string;
  law_firm_id?: string;
  law_firm_name?: string;
  name: string;
  enrollment_number: string;
  bar_council_state: string;
  specializations: string[];
  experience_years?: number;
  mobile?: string;
  email?: string;
  fee_structure?: string;
  is_empanelled: boolean;
  is_active: boolean;
  cases_handled: number;
  success_rate?: number;
  created_at: string;
}

export interface AdvocateAssignment {
  id: string;
  advocate_id: string;
  advocate_name: string;
  legal_case_id: string;
  case_number: string;
  role: 'LEAD' | 'ASSOCIATE';
  assigned_date: string;
  fee_amount?: number;
  fee_type?: 'FIXED' | 'PER_HEARING' | 'SUCCESS_FEE';
  status: 'ACTIVE' | 'COMPLETED' | 'WITHDRAWN';
}

// ==================== Legal Notice Types ====================

export type NoticeType =
  | 'SECTION_13_2_SARFAESI'
  | 'SECTION_13_4_POSSESSION'
  | 'AUCTION_NOTICE'
  | 'SECTION_138_NI_ACT'
  | 'DRT_NOTICE'
  | 'ARBITRATION_NOTICE'
  | 'DEMAND_NOTICE'
  | 'LEGAL_NOTICE';

export interface LegalNotice {
  id: string;
  notice_number: string;
  loan_account_id: string;
  loan_account_number: string;
  borrower_name: string;
  notice_type: NoticeType;
  notice_date: string;
  amount_demanded: number;
  statutory_period_days: number;
  response_due_date: string;
  delivery_method: 'RPAD' | 'SPEED_POST' | 'EMAIL' | 'HAND_DELIVERY';
  tracking_number?: string;
  dispatch_date?: string;
  delivery_date?: string;
  pod_document_id?: string;
  status: 'DRAFT' | 'DISPATCHED' | 'DELIVERED' | 'RETURNED' | 'RESPONDED' | 'EXPIRED';
  response_received?: string;
  response_date?: string;
  created_at: string;
}

export interface NoticeTemplate {
  id: string;
  name: string;
  notice_type: NoticeType;
  content_template: string;
  statutory_period_days: number;
  is_active: boolean;
}

// ==================== Legal Case Types ====================

export type LegalForumType =
  | 'DRT'
  | 'DRAT'
  | 'NCLT'
  | 'NCLAT'
  | 'CIVIL_COURT'
  | 'HIGH_COURT'
  | 'SUPREME_COURT'
  | 'ARBITRATION'
  | 'LOK_ADALAT';

export type LegalCaseType =
  | 'SARFAESI'
  | 'DRT_APPLICATION'
  | 'DRT_APPEAL'
  | 'RECOVERY_SUIT'
  | 'EXECUTION_PETITION'
  | 'IBC'
  | 'ARBITRATION'
  | 'LOK_ADALAT'
  | 'SECTION_138';

export type SARFAESIStage =
  | 'DEMAND_13_2'
  | 'OBJECTION_RECEIVED'
  | 'POSSESSION_13_4'
  | 'AUCTION_NOTICE'
  | 'AUCTION_SCHEDULED'
  | 'AUCTION_COMPLETED'
  | 'SALE_CONFIRMED'
  | 'AMOUNT_RECOVERED';

export interface LegalCase {
  id: string;
  case_number: string;
  loan_account_id: string;
  loan_account_number: string;
  borrower_name: string;
  case_type: LegalCaseType;
  forum_type: LegalForumType;
  court_name?: string;
  court_location?: string;
  filing_date?: string;
  claim_amount: number;
  current_status: string;
  sarfaesi_stage?: SARFAESIStage;
  next_hearing_date?: string;
  assigned_advocate_id?: string;
  assigned_advocate_name?: string;
  remarks?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LegalHearing {
  id: string;
  legal_case_id: string;
  case_number: string;
  hearing_date: string;
  hearing_time?: string;
  court_name: string;
  purpose: string;
  advocate_id?: string;
  advocate_name?: string;
  outcome?: string;
  next_date?: string;
  remarks?: string;
  order_document_id?: string;
  status: 'SCHEDULED' | 'COMPLETED' | 'ADJOURNED' | 'CANCELLED';
}

export interface PropertyAuction {
  id: string;
  legal_case_id: string;
  case_number: string;
  loan_account_id: string;
  property_description: string;
  property_address: string;
  reserve_price: number;
  earnest_money_deposit: number;
  auction_date: string;
  auction_time?: string;
  auction_location: string;
  publication_details?: string;
  bidder_count: number;
  highest_bid?: number;
  successful_bidder_name?: string;
  sale_confirmation_date?: string;
  sale_deed_date?: string;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'RESCHEDULED';
}

// ==================== Legal Expense Types ====================

export type ExpenseCategory =
  | 'COURT_FEE'
  | 'ADVOCATE_FEE'
  | 'VALUATION_FEE'
  | 'PUBLICATION_FEE'
  | 'TRAVEL_EXPENSE'
  | 'DOCUMENTATION'
  | 'STAMP_DUTY'
  | 'OTHER';

export interface LegalExpense {
  id: string;
  expense_number: string;
  legal_case_id?: string;
  case_number?: string;
  loan_account_id: string;
  loan_account_number: string;
  category: ExpenseCategory;
  description: string;
  amount: number;
  gst_amount?: number;
  total_amount: number;
  expense_date: string;
  payee_name: string;
  payee_type: 'ADVOCATE' | 'COURT' | 'VENDOR' | 'OTHER';
  reference_number?: string;
  is_tds_applicable: boolean;
  tds_amount?: number;
  voucher_id?: string;
  status: 'PENDING' | 'APPROVED' | 'PAID' | 'REJECTED';
  recovery_status?: 'PENDING' | 'PARTIAL' | 'RECOVERED' | 'WRITTEN_OFF';
  recovered_amount?: number;
  created_at: string;
}

// ==================== Statutory Period Types ====================

export interface StatutoryPeriod {
  id: string;
  provision_name: string;
  act_name: string;
  period_days: number;
  period_type: 'NOTICE_PERIOD' | 'LIMITATION' | 'APPEAL' | 'EXECUTION';
  description: string;
  consequence_on_expiry: string;
}

export interface PeriodTracking {
  id: string;
  loan_account_id: string;
  loan_account_number: string;
  statutory_period_id: string;
  provision_name: string;
  start_date: string;
  end_date: string;
  days_remaining: number;
  status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'COMPLETED';
  action_taken?: string;
}

// ==================== Dashboard & Analytics Types ====================

export interface LegalDashboard {
  summary: {
    total_cases: number;
    active_cases: number;
    cases_by_forum: Record<string, number>;
    cases_by_type: Record<string, number>;
    sarfaesi_by_stage: Record<string, number>;
    total_claim_amount: number;
    total_recovered: number;
  };
  upcoming_hearings: LegalHearing[];
  upcoming_auctions: PropertyAuction[];
  expiring_periods: PeriodTracking[];
  recent_cases: LegalCase[];
  expense_summary: {
    total_expenses: number;
    pending_approval: number;
    pending_recovery: number;
    recovered: number;
  };
}

export interface LegalAnalytics {
  recovery_efficiency: {
    total_cases: number;
    resolved_cases: number;
    resolution_rate: number;
    avg_resolution_days: number;
    amount_claimed: number;
    amount_recovered: number;
    recovery_rate: number;
  };
  forum_analysis: {
    forum: string;
    cases: number;
    resolved: number;
    avg_duration_days: number;
    recovery_rate: number;
  }[];
  monthly_trend: {
    month: string;
    new_cases: number;
    resolved_cases: number;
    recovery_amount: number;
  }[];
  expense_analysis: {
    category: string;
    total_amount: number;
    recovered_amount: number;
    recovery_rate: number;
  }[];
}

// ==================== Court Types ====================

export interface Court {
  id: string;
  name: string;
  forum_type: LegalForumType;
  city: string;
  state: string;
  address?: string;
  jurisdiction?: string;
  is_active: boolean;
}

export interface CourtFeeSlab {
  id: string;
  court_id: string;
  court_name: string;
  min_claim_amount: number;
  max_claim_amount?: number;
  fee_type: 'FIXED' | 'PERCENTAGE' | 'SLAB';
  fee_amount?: number;
  fee_percentage?: number;
  is_active: boolean;
}
