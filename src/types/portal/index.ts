/**
 * Customer Portal TypeScript Types
 */

// ==================== User Types ====================

export interface PortalUser {
  id: string;
  customer_id: string;
  mobile: string;
  email?: string;
  full_name: string;
  is_verified: boolean;
  preferred_language: string;
  last_login?: string;
}

export interface PortalSession {
  id: string;
  device_type?: string;
  device_name?: string;
  ip_address?: string;
  login_at: string;
  is_current: boolean;
}

// ==================== Loan Types ====================

export interface LoanSummary {
  id: string;
  loan_account_number: string;
  product_name: string;
  sanctioned_amount: number;
  disbursed_amount: number;
  outstanding_principal: number;
  outstanding_interest: number;
  total_outstanding: number;
  emi_amount: number;
  interest_rate: number;
  tenure_months: number;
  remaining_tenure: number;
  disbursement_date: string;
  maturity_date: string;
  next_emi_date?: string;
  next_emi_amount?: number;
  overdue_amount: number;
  overdue_days: number;
  status: string;
}

export interface LoanDetail extends LoanSummary {
  borrower_name: string;
  co_borrowers?: string[];
  property_address?: string;
  collateral_details?: any;
  emi_start_date: string;
  emi_end_date: string;
  total_paid: number;
  total_principal_paid: number;
  total_interest_paid: number;
  prepaid_amount: number;
  charges_due: number;
  nach_mandate_status?: string;
}

export interface RepaymentScheduleItem {
  installment_number: number;
  due_date: string;
  opening_balance: number;
  emi_amount: number;
  principal: number;
  interest: number;
  closing_balance: number;
  status: 'PAID' | 'PARTIAL' | 'DUE' | 'OVERDUE' | 'FUTURE';
  paid_date?: string;
  paid_amount?: number;
}

export interface PaymentHistory {
  id: string;
  receipt_number: string;
  payment_date: string;
  amount: number;
  principal_applied: number;
  interest_applied: number;
  charges_applied: number;
  payment_mode: string;
  reference_number?: string;
  status: string;
}

// ==================== Dashboard Types ====================

export interface PortalDashboard {
  customer: {
    name: string;
    customer_id: string;
  };
  loans_summary: {
    total_loans: number;
    active_loans: number;
    total_outstanding: number;
    total_overdue: number;
    next_due_date?: string;
    next_due_amount?: number;
  };
  loans: LoanSummary[];
  upcoming_dues: UpcomingDue[];
  recent_payments: PaymentHistory[];
  announcements: Announcement[];
  pending_requests: number;
}

export interface UpcomingDue {
  loan_account_id: string;
  loan_account_number: string;
  due_date: string;
  emi_amount: number;
  overdue_amount: number;
  total_due: number;
  days_until_due: number;
  is_overdue: boolean;
}

export interface Announcement {
  id: string;
  title: string;
  message: string;
  type: 'INFO' | 'WARNING' | 'PROMO';
  created_at: string;
}

// ==================== Payment Types ====================

export interface PaymentInitiation {
  id: string;
  order_id: string;
  amount: number;
  payment_mode: string;
  gateway_url?: string;
  upi_link?: string;
  status: string;
  expires_at: string;
}

export interface PrepaymentQuote {
  loan_account_id: string;
  prepayment_date: string;
  prepayment_amount: number;
  outstanding_principal: number;
  accrued_interest: number;
  prepayment_charges: number;
  gst_on_charges: number;
  total_payable: number;
  new_emi_amount?: number;
  new_tenure_months?: number;
  interest_savings: number;
  valid_until: string;
}

export interface ForeclosureQuote {
  loan_account_id: string;
  foreclosure_date: string;
  outstanding_principal: number;
  accrued_interest: number;
  pending_charges: number;
  foreclosure_charges: number;
  gst_on_charges: number;
  total_payable: number;
  interest_savings: number;
  valid_until: string;
}

export interface NachMandate {
  id: string;
  loan_account_id: string;
  umrn?: string;
  bank_name: string;
  account_number_masked: string;
  max_amount: number;
  frequency: string;
  start_date: string;
  end_date: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'CANCELLED';
  registration_date?: string;
}

// ==================== Document Types ====================

export interface PortalDocument {
  id: string;
  document_type: string;
  document_name: string;
  loan_account_id?: string;
  loan_account_number?: string;
  description?: string;
  file_size?: number;
  uploaded_at: string;
  is_downloadable: boolean;
}

// ==================== Service Request Types ====================

export type ServiceRequestType =
  | 'PREPAYMENT'
  | 'FORECLOSURE'
  | 'EMI_DATE_CHANGE'
  | 'ADDRESS_CHANGE'
  | 'NOC_REQUEST'
  | 'STATEMENT_REQUEST'
  | 'GENERAL_QUERY'
  | 'COMPLAINT';

export type ServiceRequestStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED' | 'CANCELLED';

export interface ServiceRequest {
  id: string;
  request_number: string;
  request_type: ServiceRequestType;
  loan_account_id?: string;
  loan_account_number?: string;
  subject: string;
  description: string;
  status: ServiceRequestStatus;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolution?: string;
  documents?: PortalDocument[];
}

// ==================== Communication Types ====================

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'PAYMENT_DUE' | 'PAYMENT_RECEIVED' | 'REQUEST_UPDATE' | 'ANNOUNCEMENT' | 'ALERT';
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

export interface SupportTicket {
  id: string;
  ticket_number: string;
  subject: string;
  category: string;
  loan_account_id?: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  created_at: string;
  updated_at: string;
  messages: TicketMessage[];
}

export interface TicketMessage {
  id: string;
  sender_type: 'CUSTOMER' | 'AGENT';
  message: string;
  created_at: string;
}
