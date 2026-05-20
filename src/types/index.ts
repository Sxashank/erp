// Common types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  page_size: number;
  total_pages: number;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

// Auth types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  employee_code?: string;
  phone?: string;
  timezone: string;
  auth_type: string;
  mfa_enabled: boolean;
  status: string;
  organization_id?: string;
  organization_name?: string;
  default_unit_id?: string;
  default_unit_name?: string;
  last_login_at?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  roles: UserRole[];
  permissions: string[];
}

export interface UserRole {
  id: string;
  code: string;
  name: string;
  unit_id?: string;
  unit_name?: string;
}

export interface UserCreate {
  username: string;
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  employee_code?: string;
  phone?: string;
  timezone?: string;
  organization_id?: string;
  default_unit_id?: string;
  role_ids?: string[];
  mfa_enabled?: boolean;
  status?: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  full_name?: string;
  password?: string;
  confirm_password?: string;
  employee_code?: string;
  phone?: string;
  timezone?: string;
  organization_id?: string;
  default_unit_id?: string;
  status?: string;
  mfa_enabled?: boolean;
}

// Role types
export interface Role {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_system_role: boolean;
  is_default: boolean;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  permissions: Permission[];
}

export interface RoleListItem {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_system_role: boolean;
  is_default: boolean;
  permission_count: number;
  user_count: number;
}

export interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
  resource: string;
  action: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface RoleCreate {
  code: string;
  name: string;
  description?: string;
  permission_ids?: string[];
  is_default?: boolean;
}

export interface RoleUpdate {
  code?: string;
  name?: string;
  description?: string;
  is_default?: boolean;
}

// Organization types
export interface Organization {
  id: string;
  code: string;
  name: string;
  legal_name: string;
  short_name?: string;
  description?: string;
  cin?: string;
  pan: string;
  tan?: string;
  gstin?: string;
  rbi_registration?: string;
  reg_address_line1?: string;
  reg_address_line2?: string;
  reg_city?: string;
  reg_district?: string;
  reg_state_code?: string;
  reg_pincode?: string;
  reg_country: string;
  phone?: string;
  email?: string;
  website?: string;
  base_currency: string;
  financial_year_start_month: number;
  logo_path?: string;
  primary_color?: string;
  status: string;
  is_primary: boolean;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  unit_count?: number;
  department_count?: number;
  user_count?: number;
}

export interface OrganizationCreate {
  code: string;
  name: string;
  legal_name: string;
  short_name?: string;
  description?: string;
  cin?: string;
  pan: string;
  tan?: string;
  gstin?: string;
  rbi_registration?: string;
  reg_address_line1?: string;
  reg_address_line2?: string;
  reg_city?: string;
  reg_district?: string;
  reg_state_code?: string;
  reg_pincode?: string;
  reg_country?: string;
  phone?: string;
  email?: string;
  website?: string;
  base_currency?: string;
  financial_year_start_month?: number;
  logo_path?: string;
  primary_color?: string;
}

export interface OrganizationUpdate {
  code?: string;
  pan?: string;
  name?: string;
  legal_name?: string;
  short_name?: string;
  description?: string;
  tan?: string;
  gstin?: string;
  rbi_registration?: string;
  reg_address_line1?: string;
  reg_address_line2?: string;
  reg_city?: string;
  reg_district?: string;
  reg_state_code?: string;
  reg_pincode?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_path?: string;
  primary_color?: string;
  status?: string;
}

// Organization Bank Account types
export interface OrganizationBankAccount {
  id: string;
  organization_id?: string;
  account_name: string;
  account_number: string;
  ifsc_code: string;
  bank_name: string;
  branch_name?: string;
  account_type: string;
  ledger_account_id?: string;
  ledger_account_name?: string;
  sanctioned_limit?: number;
  drawing_power?: number;
  is_primary: boolean;
  allow_payments: boolean;
  allow_receipts: boolean;
  status: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface OrganizationBankAccountCreate {
  account_name: string;
  account_number: string;
  ifsc_code: string;
  bank_name: string;
  branch_name?: string;
  account_type: string;
  ledger_account_id?: string;
  sanctioned_limit?: number;
  drawing_power?: number;
  is_primary?: boolean;
  allow_payments?: boolean;
  allow_receipts?: boolean;
}

export interface OrganizationBankAccountUpdate {
  account_number?: string;
  ifsc_code?: string;
  bank_name?: string;
  account_name?: string;
  branch_name?: string;
  ledger_account_id?: string;
  sanctioned_limit?: number;
  drawing_power?: number;
  is_primary?: boolean;
  allow_payments?: boolean;
  allow_receipts?: boolean;
  status?: string;
}

// Organization Address types
export interface OrganizationAddress {
  id: string;
  organization_id: string;
  address_type: string;
  address_line1: string;
  address_line2?: string;
  landmark?: string;
  city: string;
  district?: string;
  state_code: string;
  state_name?: string;
  pincode: string;
  country: string;
  latitude?: number;
  longitude?: number;
  is_primary: boolean;
  status: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface OrganizationAddressCreate {
  address_type: string;
  address_line1: string;
  address_line2?: string;
  landmark?: string;
  city: string;
  district?: string;
  state_code: string;
  pincode: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  is_primary?: boolean;
}

export interface OrganizationAddressUpdate {
  address_type?: string;
  address_line1?: string;
  address_line2?: string;
  landmark?: string;
  city?: string;
  district?: string;
  state_code?: string;
  pincode?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  is_primary?: boolean;
  status?: string;
}

// Unit types
export interface Unit {
  id: string;
  code: string;
  name: string;
  unitType: string;
  organizationId: string;
  parentUnitId?: string | null;
  isSeparateAccounting: boolean;
  gstStateCode?: string | null;
  addressLine1?: string | null;
  addressLine2?: string | null;
  stateCode?: string | null;
  managerName?: string | null;
  isHeadOffice: boolean;
  createdAt: string;
  updatedAt?: string | null;
  isActive: boolean;
  organizationName?: string | null;
  parentUnitName?: string | null;
  short_name?: string;
  description?: string;
  unit_type: string;
  organization_id: string;
  parent_unit_id?: string;
  level: number;
  path?: string;
  is_separate_accounting: boolean;
  gstin?: string;
  gst_state_code?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  state_code?: string;
  pincode?: string;
  country: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  status: string;
  is_head_office: boolean;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  organization_name?: string;
  parent_unit_name?: string;
}

export interface UnitCreate {
  code: string;
  name: string;
  short_name?: string;
  description?: string;
  unit_type?: string;
  organization_id: string;
  parent_unit_id?: string;
  is_separate_accounting?: boolean;
  gstin?: string;
  gst_state_code?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  state_code?: string;
  pincode?: string;
  country?: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  is_head_office?: boolean;
}

export interface UnitUpdate {
  code?: string;
  name?: string;
  short_name?: string;
  description?: string;
  unit_type?: string;
  parent_unit_id?: string;
  is_separate_accounting?: boolean;
  gstin?: string;
  gst_state_code?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  state_code?: string;
  pincode?: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  status?: string;
}

// Department types
export interface Department {
  id: string;
  code: string;
  name: string;
  short_name?: string;
  description?: string;
  organization_id: string;
  parent_dept_id?: string;
  level: number;
  path?: string;
  cost_center_code?: string;
  head_name?: string;
  email?: string;
  phone?: string;
  status: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  organization_name?: string;
  parent_dept_name?: string;
  designation_count?: number;
}

export interface DepartmentCreate {
  code: string;
  name: string;
  short_name?: string;
  description?: string;
  organization_id: string;
  parent_dept_id?: string;
  cost_center_code?: string;
  head_name?: string;
  email?: string;
  phone?: string;
}

export interface DepartmentUpdate {
  code?: string;
  name?: string;
  short_name?: string;
  description?: string;
  parent_dept_id?: string;
  cost_center_code?: string;
  head_name?: string;
  email?: string;
  phone?: string;
  status?: string;
}

// Designation types
export interface Designation {
  id: string;
  code: string;
  name: string;
  short_name?: string;
  description?: string;
  department_id?: string;
  level: number;
  reporting_to_id?: string;
  min_experience_years: number;
  min_qualification?: string;
  job_description?: string;
  responsibilities?: string;
  status: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  department_name?: string;
  reporting_to_name?: string;
}

export interface DesignationCreate {
  code: string;
  name: string;
  short_name?: string;
  description?: string;
  department_id?: string;
  level?: number;
  reporting_to_id?: string;
  min_experience_years?: number;
  min_qualification?: string;
  job_description?: string;
  responsibilities?: string;
}

export interface DesignationUpdate {
  code?: string;
  name?: string;
  short_name?: string;
  description?: string;
  department_id?: string;
  level?: number;
  reporting_to_id?: string;
  min_experience_years?: number;
  min_qualification?: string;
  job_description?: string;
  responsibilities?: string;
  status?: string;
}

// Tree types for hierarchical views
export interface UnitTreeNode {
  id: string;
  code: string;
  name: string;
  unitType: string;
  unit_type: string;
  level: number;
  isHeadOffice: boolean;
  is_head_office: boolean;
  status: string;
  children: UnitTreeNode[];
}

export interface DepartmentTreeNode {
  id: string;
  code: string;
  name: string;
  level: number;
  cost_center_code?: string;
  status: string;
  children: DepartmentTreeNode[];
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
  otp?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Constants
export const UNIT_TYPES = [
  { value: 'HEAD_OFFICE', label: 'Head Office' },
  { value: 'BRANCH', label: 'Branch' },
  { value: 'REGIONAL_OFFICE', label: 'Regional Office' },
  { value: 'PROJECT_OFFICE', label: 'Project Office' },
];

export const STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
];

// Finance types

// Financial Year
export interface FinancialYear {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_closed: boolean;
  closed_at?: string;
  organization_id: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  periods?: FinancialPeriod[];
}

export interface FinancialPeriod {
  id: string;
  financial_year_id: string;
  period_number: number;
  name: string;
  start_date: string;
  end_date: string;
  is_closed: boolean;
  closed_at?: string;
  is_active: boolean;
}

export interface FinancialYearCreate {
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  organization_id: string;
  is_current?: boolean;
}

export interface FinancialYearUpdate {
  organization_id?: string;
  code?: string;
  start_date?: string;
  end_date?: string;
  name?: string;
  is_current?: boolean;
}

// Account Group
export type AccountNature = 'ASSETS' | 'LIABILITIES' | 'INCOME' | 'EXPENSES' | 'EQUITY';

export interface AccountGroup {
  id: string;
  code: string;
  name: string;
  nature: AccountNature;
  parent_group_id?: string;
  parent_group_name?: string;
  level: number;
  path?: string;
  sequence: number;
  description?: string;
  is_system: boolean;
  organization_id: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  account_count?: number;
}

export interface AccountGroupCreate {
  code: string;
  name: string;
  nature: AccountNature;
  parent_group_id?: string;
  sequence?: number;
  description?: string;
  organization_id: string;
}

export interface AccountGroupUpdate {
  code?: string;
  name?: string;
  parent_group_id?: string;
  sequence?: number;
  description?: string;
}

export interface AccountGroupTreeNode {
  id: string;
  code: string;
  name: string;
  nature: AccountNature;
  level: number;
  sequence: number;
  is_system: boolean;
  children: AccountGroupTreeNode[];
}

// Account
export type AccountType = 'LEDGER' | 'CONTROL' | 'BANK' | 'CASH';
export type BalanceType = 'DR' | 'CR';

export interface Account {
  id: string;
  code: string;
  name: string;
  account_group_id: string;
  account_group_name?: string;
  account_group_nature?: AccountNature;
  account_type: AccountType;
  description?: string;
  is_control_account: boolean;
  control_type?: string;
  currency_code: string;
  opening_balance: number;
  opening_balance_type: BalanceType;
  current_balance: number;
  current_balance_type: BalanceType;
  bank_name?: string;
  bank_branch?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  tds_applicable: boolean;
  tds_section_code?: string;
  gst_applicable: boolean;
  hsn_sac_code?: string;
  organization_id: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface AccountCreate {
  code: string;
  name: string;
  account_group_id: string;
  account_type?: AccountType;
  description?: string;
  is_control_account?: boolean;
  control_type?: string;
  currency_code?: string;
  opening_balance?: number;
  opening_balance_type?: BalanceType;
  bank_name?: string;
  bank_branch?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  tds_applicable?: boolean;
  tds_section_code?: string;
  gst_applicable?: boolean;
  hsn_sac_code?: string;
  organization_id: string;
}

export interface AccountUpdate {
  code?: string;
  name?: string;
  account_group_id?: string;
  account_type?: AccountType;
  description?: string;
  is_control_account?: boolean;
  control_type?: string;
  bank_name?: string;
  bank_branch?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  tds_applicable?: boolean;
  tds_section_code?: string;
  gst_applicable?: boolean;
  hsn_sac_code?: string;
}

// Voucher Type
export type VoucherClass =
  | 'JOURNAL'
  | 'PAYMENT'
  | 'RECEIPT'
  | 'CONTRA'
  | 'SALES'
  | 'PURCHASE'
  | 'DEBIT_NOTE'
  | 'CREDIT_NOTE';

export interface VoucherType {
  id: string;
  code: string;
  name: string;
  voucher_class: VoucherClass;
  prefix?: string;
  auto_numbering: boolean;
  starting_number: number;
  current_number: number;
  number_format?: string;
  requires_approval: boolean;
  approval_levels: number;
  default_narration?: string;
  description?: string;
  is_system: boolean;
  organization_id: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface VoucherTypeCreate {
  code: string;
  name: string;
  voucher_class: VoucherClass;
  prefix?: string;
  auto_numbering?: boolean;
  starting_number?: number;
  number_format?: string;
  requires_approval?: boolean;
  approval_levels?: number;
  default_narration?: string;
  description?: string;
  organization_id: string;
}

export interface VoucherTypeUpdate {
  code?: string;
  name?: string;
  prefix?: string;
  auto_numbering?: boolean;
  number_format?: string;
  requires_approval?: boolean;
  approval_levels?: number;
  default_narration?: string;
  description?: string;
}

// Voucher
export type VoucherStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'POSTED'
  | 'REJECTED'
  | 'CANCELLED';
export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface VoucherLine {
  id?: string;
  line_number: number;
  account_id: string;
  account_code?: string;
  account_name?: string;
  debit_amount: number;
  credit_amount: number;
  narration?: string;
  cost_center_id?: string;
  party_type?: string;
  party_id?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  cheque_number?: string;
  cheque_date?: string;
}

export interface Voucher {
  id: string;
  voucher_type_id: string;
  voucher_type_code?: string;
  voucher_type_name?: string;
  voucher_class?: VoucherClass;
  voucher_number: string;
  voucher_date: string;
  financial_year_id: string;
  financial_year_code?: string;
  period_id?: string;
  reference_number?: string;
  reference_date?: string;
  narration?: string;
  total_debit: number;
  total_credit: number;
  status: VoucherStatus;
  approval_status?: ApprovalStatus;
  current_approval_level?: number;
  submitted_at?: string;
  approved_at?: string;
  posted_at?: string;
  cancelled_at?: string;
  cancellation_reason?: string;
  rejection_reason?: string;
  is_reversed: boolean;
  reversal_voucher_id?: string;
  original_voucher_id?: string;
  organization_id: string;
  unit_id?: string;
  unit_name?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  lines?: VoucherLine[];
}

export interface VoucherLineCreate {
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  narration?: string;
  cost_center_id?: string;
  party_type?: string;
  party_id?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  cheque_number?: string;
  cheque_date?: string;
}

export interface VoucherCreate {
  voucher_type_id: string;
  voucher_date: string;
  financial_year_id: string;
  reference_number?: string;
  reference_date?: string;
  narration?: string;
  organization_id?: string;
  unit_id?: string;
  lines: VoucherLineCreate[];
}

export interface VoucherUpdate {
  voucher_date?: string;
  reference_number?: string;
  reference_date?: string;
  narration?: string;
  unit_id?: string;
  lines?: VoucherLineCreate[];
}

// Finance constants
export const ACCOUNT_NATURES = [
  { value: 'ASSETS', label: 'Assets' },
  { value: 'LIABILITIES', label: 'Liabilities' },
  { value: 'INCOME', label: 'Income' },
  { value: 'EXPENSES', label: 'Expenses' },
  { value: 'EQUITY', label: 'Equity' },
];

export const ACCOUNT_TYPES = [
  { value: 'LEDGER', label: 'Ledger Account' },
  { value: 'CONTROL', label: 'Control Account' },
  { value: 'BANK', label: 'Bank Account' },
  { value: 'CASH', label: 'Cash Account' },
];

export const BALANCE_TYPES = [
  { value: 'DR', label: 'Debit' },
  { value: 'CR', label: 'Credit' },
];

export const VOUCHER_CLASSES = [
  { value: 'JOURNAL', label: 'Journal Voucher' },
  { value: 'PAYMENT', label: 'Payment Voucher' },
  { value: 'RECEIPT', label: 'Receipt Voucher' },
  { value: 'CONTRA', label: 'Contra Voucher' },
  { value: 'SALES', label: 'Sales Voucher' },
  { value: 'PURCHASE', label: 'Purchase Voucher' },
  { value: 'DEBIT_NOTE', label: 'Debit Note' },
  { value: 'CREDIT_NOTE', label: 'Credit Note' },
];

export const VOUCHER_STATUSES = [
  { value: 'DRAFT', label: 'Draft', color: 'bg-slate-100 text-slate-600' },
  { value: 'PENDING_APPROVAL', label: 'Pending Approval', color: 'bg-amber-50 text-amber-700' },
  { value: 'APPROVED', label: 'Approved', color: 'bg-blue-50 text-blue-700' },
  { value: 'POSTED', label: 'Posted', color: 'bg-emerald-50 text-emerald-700' },
  { value: 'REJECTED', label: 'Rejected', color: 'bg-red-50 text-red-700' },
  { value: 'CANCELLED', label: 'Cancelled', color: 'bg-gray-100 text-gray-600' },
];

export const INDIAN_STATES = [
  { code: '01', name: 'Jammu & Kashmir' },
  { code: '02', name: 'Himachal Pradesh' },
  { code: '03', name: 'Punjab' },
  { code: '04', name: 'Chandigarh' },
  { code: '05', name: 'Uttarakhand' },
  { code: '06', name: 'Haryana' },
  { code: '07', name: 'Delhi' },
  { code: '08', name: 'Rajasthan' },
  { code: '09', name: 'Uttar Pradesh' },
  { code: '10', name: 'Bihar' },
  { code: '11', name: 'Sikkim' },
  { code: '12', name: 'Arunachal Pradesh' },
  { code: '13', name: 'Nagaland' },
  { code: '14', name: 'Manipur' },
  { code: '15', name: 'Mizoram' },
  { code: '16', name: 'Tripura' },
  { code: '17', name: 'Meghalaya' },
  { code: '18', name: 'Assam' },
  { code: '19', name: 'West Bengal' },
  { code: '20', name: 'Jharkhand' },
  { code: '21', name: 'Odisha' },
  { code: '22', name: 'Chhattisgarh' },
  { code: '23', name: 'Madhya Pradesh' },
  { code: '24', name: 'Gujarat' },
  { code: '26', name: 'Dadra & Nagar Haveli and Daman & Diu' },
  { code: '27', name: 'Maharashtra' },
  { code: '28', name: 'Andhra Pradesh (Old)' },
  { code: '29', name: 'Karnataka' },
  { code: '30', name: 'Goa' },
  { code: '31', name: 'Lakshadweep' },
  { code: '32', name: 'Kerala' },
  { code: '33', name: 'Tamil Nadu' },
  { code: '34', name: 'Puducherry' },
  { code: '35', name: 'Andaman & Nicobar Islands' },
  { code: '36', name: 'Telangana' },
  { code: '37', name: 'Andhra Pradesh' },
  { code: '38', name: 'Ladakh' },
];
