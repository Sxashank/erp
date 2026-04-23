/**
 * ESS Portal TypeScript Types
 */

// ==================== Enums ====================

export type ESSUserStatus = 'ACTIVE' | 'INACTIVE' | 'LOCKED' | 'SUSPENDED';

export type ClaimStatus = 'DRAFT' | 'SUBMITTED' | 'PENDING_APPROVAL' | 'APPROVED' | 'PARTIALLY_APPROVED' | 'REJECTED' | 'PAID' | 'CANCELLED';

export type ClaimType = 'MEDICAL' | 'TRAVEL' | 'CONVEYANCE' | 'FOOD' | 'COMMUNICATION' | 'BOOKS' | 'TRAINING' | 'WFH' | 'RELOCATION' | 'CLIENT' | 'MISC';

export type TicketCategory = 'HR' | 'IT' | 'ADMIN' | 'FINANCE';

export type TicketPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'PENDING_INFO' | 'RESOLVED' | 'CLOSED' | 'REOPENED';

export type ITDeclarationStatus = 'DRAFT' | 'SUBMITTED' | 'VERIFIED' | 'APPROVED' | 'REJECTED';

export type TaxRegime = 'OLD' | 'NEW';

export type RegularizationType = 'FORGOT_PUNCH' | 'SYSTEM_ERROR' | 'ON_DUTY' | 'WORK_FROM_HOME' | 'OTHER';

export type ProfileUpdateType = 'PERSONAL' | 'CONTACT' | 'ADDRESS' | 'BANK' | 'EMERGENCY_CONTACT' | 'EDUCATION' | 'CERTIFICATION';

// ==================== Auth Types ====================

export interface ESSUser {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  mobile: string;
  email?: string;
  is_mobile_verified: boolean;
  is_email_verified: boolean;
  preferred_language: string;
  status: ESSUserStatus;
  last_login?: string;
}

export interface ESSSession {
  id: string;
  device_type?: string;
  device_name?: string;
  browser?: string;
  ip_address?: string;
  location?: string;
  login_at: string;
  last_activity?: string;
  is_current: boolean;
}

export interface ESSLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: ESSUser;
}

// ==================== Profile Types ====================

export interface ESSProfile {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email?: string;
  mobile: string;
  date_of_birth?: string;
  gender?: string;
  marital_status?: string;
  blood_group?: string;
  department?: string;
  designation?: string;
  reporting_manager?: string;
  date_of_joining: string;
  employment_type?: string;
  work_location?: string;
  personal_email?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  current_address?: string;
  permanent_address?: string;
  pan_number?: string;
  aadhaar_number?: string;
  bank_name?: string;
  bank_account_number?: string;
  ifsc_code?: string;
  profile_photo_url?: string;
}

export interface ESSProfileUpdateRequest {
  id: string;
  request_number: string;
  update_type: ProfileUpdateType;
  current_values: Record<string, any>;
  requested_values: Record<string, any>;
  change_reason?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reviewed_by?: string;
  reviewed_at?: string;
  reviewer_remarks?: string;
  created_at: string;
}

export interface ESSDashboard {
  employee: {
    name: string;
    employee_code: string;
    department: string;
    designation: string;
    profile_photo_url?: string;
  };
  attendance: {
    present_days: number;
    absent_days: number;
    leave_days: number;
    wfh_days: number;
    current_month: string;
  };
  leave_balance: {
    casual_leave: number;
    sick_leave: number;
    earned_leave: number;
    total_available: number;
  };
  pending_actions: {
    pending_claims: number;
    pending_tickets: number;
    pending_regularizations: number;
    pending_declarations: number;
  };
  recent_payslip?: {
    month: string;
    net_salary: number;
    payslip_id: string;
  };
  announcements: Array<{
    id: string;
    title: string;
    message: string;
    created_at: string;
  }>;
}

// ==================== Payslip Types ====================

export interface Payslip {
  id: string;
  month: string;
  year: number;
  basic_salary: number;
  hra: number;
  other_allowances: number;
  gross_salary: number;
  pf_deduction: number;
  tax_deduction: number;
  other_deductions: number;
  total_deductions: number;
  net_salary: number;
  payment_date?: string;
  payment_status: string;
}

export interface YTDSummary {
  financial_year: string;
  total_earnings: number;
  total_deductions: number;
  total_net_pay: number;
  total_tax_deducted: number;
  total_pf_contribution: number;
  months_paid: number;
  breakdown: {
    earnings: Record<string, number>;
    deductions: Record<string, number>;
  };
}

// ==================== Leave Types ====================

export interface LeaveBalance {
  leave_type: string;
  leave_name: string;
  total_entitled: number;
  taken: number;
  pending_approval: number;
  available: number;
  carry_forward?: number;
  lapsed?: number;
}

// ==================== Attendance Types ====================

export interface AttendanceSummary {
  month: string;
  year: number;
  working_days: number;
  present_days: number;
  absent_days: number;
  leave_days: number;
  holidays: number;
  late_arrivals: number;
  early_departures: number;
  wfh_days: number;
  on_duty_days: number;
  daily_records: AttendanceRecord[];
}

export interface AttendanceRecord {
  date: string;
  status: 'PRESENT' | 'ABSENT' | 'LEAVE' | 'HOLIDAY' | 'WEEKEND' | 'WFH' | 'ON_DUTY';
  in_time?: string;
  out_time?: string;
  working_hours?: number;
  is_late?: boolean;
  is_early_departure?: boolean;
  remarks?: string;
}

// ==================== Reimbursement Types ====================

export interface ReimbursementCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  max_amount_per_claim?: number;
  max_amount_per_year?: number;
  requires_bills: boolean;
  is_active: boolean;
}

export interface ReimbursementClaim {
  id: string;
  claim_number: string;
  claim_date: string;
  category_id?: string;
  category_name?: string;
  claim_type: ClaimType;
  expense_from: string;
  expense_to: string;
  claimed_amount: number;
  approved_amount?: number;
  description: string;
  purpose?: string;
  status: ClaimStatus;
  bills_attached: number;
  submitted_date?: string;
  approved_date?: string;
  payment_date?: string;
  rejection_reason?: string;
  line_items?: ReimbursementLineItem[];
  approvals?: ReimbursementApproval[];
  created_at: string;
}

export interface ReimbursementLineItem {
  id: string;
  line_number: number;
  expense_date: string;
  description: string;
  amount: number;
  approved_amount?: number;
  bill_number?: string;
  bill_date?: string;
  vendor_name?: string;
  attachment_url?: string;
  is_verified: boolean;
  verification_remarks?: string;
}

export interface ReimbursementApproval {
  id: string;
  approval_level: number;
  approver_name: string;
  action: 'APPROVED' | 'REJECTED' | 'FORWARDED';
  action_date: string;
  remarks?: string;
  approved_amount?: number;
}

export interface ReimbursementSummary {
  total_claims: number;
  pending_claims: number;
  approved_claims: number;
  rejected_claims: number;
  total_claimed_amount: number;
  total_approved_amount: number;
  total_paid_amount: number;
  by_category: Record<string, { count: number; amount: number }>;
}

// ==================== Helpdesk Types ====================

export interface HelpdeskCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  department: string;
  response_sla_hours: number;
  resolution_sla_hours: number;
}

export interface HelpdeskTicket {
  id: string;
  ticket_number: string;
  subject: string;
  description?: string;
  category_type: TicketCategory;
  category_name?: string;
  priority: TicketPriority;
  status: TicketStatus;
  assigned_department?: string;
  assigned_to?: string;
  resolution?: string;
  resolution_date?: string;
  rating?: number;
  feedback?: string;
  response_sla_breached: boolean;
  resolution_sla_breached: boolean;
  response_due_at?: string;
  resolution_due_at?: string;
  first_response_at?: string;
  is_escalated: boolean;
  reopen_count: number;
  comments?: TicketComment[];
  created_at: string;
  closed_date?: string;
}

export interface TicketComment {
  id: string;
  author_type: 'EMPLOYEE' | 'AGENT' | 'SYSTEM';
  author_name?: string;
  comment: string;
  attachments?: any;
  created_at: string;
}

export interface TicketSummary {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
  by_status: Record<string, number>;
}

// ==================== IT Declaration Types ====================

export interface ITDeclarationSection {
  id: string;
  section_code: string;
  section_name: string;
  description?: string;
  category: string;
  max_limit: number;
  requires_proof: boolean;
  help_text?: string;
  applicable_in_old_regime: boolean;
  applicable_in_new_regime: boolean;
  display_order: number;
}

export interface ITDeclaration {
  id: string;
  financial_year: string;
  tax_regime: TaxRegime;
  total_declared_amount: number;
  total_verified_amount: number;
  total_approved_amount: number;
  rent_paid_monthly?: number;
  landlord_name?: string;
  landlord_pan?: string;
  landlord_address?: string;
  metro_city: boolean;
  hra_declared?: number;
  home_loan_interest?: number;
  home_loan_principal?: number;
  lender_name?: string;
  lender_pan?: string;
  estimated_taxable_income?: number;
  estimated_tax_liability?: number;
  monthly_tds?: number;
  status: ITDeclarationStatus;
  submitted_date?: string;
  proof_submitted_date?: string;
  verified_date?: string;
  items: ITDeclarationItem[];
  hra_receipts?: HRAReceipt[];
  created_at: string;
}

export interface ITDeclarationItem {
  id: string;
  section_id?: string;
  section_code: string;
  section_name?: string;
  particular: string;
  description?: string;
  declared_amount: number;
  verified_amount?: number;
  approved_amount?: number;
  investment_date?: string;
  policy_number?: string;
  institution_name?: string;
  proof_submitted: boolean;
  proof_url?: string;
  is_verified: boolean;
  verification_remarks?: string;
}

export interface HRAReceipt {
  id: string;
  month: string;
  receipt_number?: string;
  rent_amount: number;
  receipt_url?: string;
  receipt_uploaded: boolean;
  is_verified: boolean;
}

export interface TaxCalculation {
  gross_income: number;
  standard_deduction: number;
  chapter_vi_a_deductions: number;
  hra_exemption: number;
  lta_exemption: number;
  other_exemptions: number;
  taxable_income: number;
  tax_on_income: number;
  surcharge: number;
  education_cess: number;
  total_tax_liability: number;
  monthly_tds: number;
  tax_regime: TaxRegime;
  breakdown: {
    deductions_by_section: Record<string, number>;
    tax_slabs: Array<{
      slab: string;
      rate: number;
      tax: number;
    }>;
  };
}

// ==================== Attendance Regularization Types ====================

export interface AttendanceRegularization {
  id: string;
  request_number: string;
  attendance_date: string;
  regularization_type: RegularizationType;
  requested_in_time?: string;
  requested_out_time?: string;
  actual_in_time?: string;
  actual_out_time?: string;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  approved_by?: string;
  approved_date?: string;
  approver_remarks?: string;
  created_at: string;
}
