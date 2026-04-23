/**
 * Vendor Portal TypeScript Types
 */

// ============= Enums =============
export enum VendorPortalUserStatus {
  PENDING_ACTIVATION = 'PENDING_ACTIVATION',
  ACTIVE = 'ACTIVE',
  SUSPENDED = 'SUSPENDED',
  DEACTIVATED = 'DEACTIVATED',
}

export enum BusinessType {
  PROPRIETORSHIP = 'PROPRIETORSHIP',
  PARTNERSHIP = 'PARTNERSHIP',
  LLP = 'LLP',
  PRIVATE_LIMITED = 'PRIVATE_LIMITED',
  PUBLIC_LIMITED = 'PUBLIC_LIMITED',
  GOVERNMENT = 'GOVERNMENT',
  TRUST = 'TRUST',
  SOCIETY = 'SOCIETY',
  OTHERS = 'OTHERS',
}

export enum RegistrationStatus {
  DRAFT = 'DRAFT',
  SUBMITTED = 'SUBMITTED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  ADDITIONAL_INFO_REQUIRED = 'ADDITIONAL_INFO_REQUIRED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export enum POAcknowledgementStatus {
  PENDING = 'PENDING',
  ACKNOWLEDGED = 'ACKNOWLEDGED',
  REJECTED = 'REJECTED',
  CHANGE_REQUESTED = 'CHANGE_REQUESTED',
  EXPIRED = 'EXPIRED',
}

export enum VendorInvoiceStatus {
  DRAFT = 'DRAFT',
  SUBMITTED = 'SUBMITTED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  MATCHED = 'MATCHED',
  EXCEPTION = 'EXCEPTION',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  PARTIALLY_PAID = 'PARTIALLY_PAID',
  PAID = 'PAID',
  CANCELLED = 'CANCELLED',
}

export enum ASNStatus {
  DRAFT = 'DRAFT',
  DISPATCHED = 'DISPATCHED',
  IN_TRANSIT = 'IN_TRANSIT',
  DELIVERED = 'DELIVERED',
  PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED',
  CANCELLED = 'CANCELLED',
}

export enum ComplianceDocumentType {
  PAN_CARD = 'PAN_CARD',
  GST_CERTIFICATE = 'GST_CERTIFICATE',
  MSME_CERTIFICATE = 'MSME_CERTIFICATE',
  ISO_CERTIFICATE = 'ISO_CERTIFICATE',
  TDS_CERTIFICATE = 'TDS_CERTIFICATE',
  FORM_16A = 'FORM_16A',
  INSURANCE_POLICY = 'INSURANCE_POLICY',
  FSSAI_LICENSE = 'FSSAI_LICENSE',
  POLLUTION_CERT = 'POLLUTION_CERT',
  FACTORY_LICENSE = 'FACTORY_LICENSE',
  DRUG_LICENSE = 'DRUG_LICENSE',
  CANCELLED_CHEQUE = 'CANCELLED_CHEQUE',
  OTHER = 'OTHER',
}

export enum VerificationStatus {
  PENDING = 'PENDING',
  VERIFIED = 'VERIFIED',
  REJECTED = 'REJECTED',
}

export enum NotificationCategory {
  PO = 'PO',
  INVOICE = 'INVOICE',
  PAYMENT = 'PAYMENT',
  ASN = 'ASN',
  COMPLIANCE = 'COMPLIANCE',
  REGISTRATION = 'REGISTRATION',
  GENERAL = 'GENERAL',
}

export enum NotificationPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

// ============= User & Auth =============
export interface VendorUserPermissions {
  can_view_pos: boolean;
  can_acknowledge_pos: boolean;
  can_submit_invoices: boolean;
  can_create_asn: boolean;
  can_view_payments: boolean;
  can_manage_users: boolean;
  can_manage_compliance: boolean;
}

export interface VendorUser {
  id: string;
  vendor_id: string;
  organization_id: string;
  email: string;
  phone?: string;
  first_name: string;
  last_name?: string;
  designation?: string;
  department?: string;
  is_primary_contact: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  status: VendorPortalUserStatus;
  last_login_at?: string;
  permissions: VendorUserPermissions;
}

export interface VendorLoginRequest {
  email: string;
  password?: string;
  otp?: string;
}

export interface VendorLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: VendorUser;
}

export interface VendorOTPRequest {
  email?: string;
  phone?: string;
  purpose?: string;
  organization_id?: string;
}

// ============= Vendor Info =============
export interface VendorInfo {
  id: string;
  code: string;
  name: string;
  trade_name?: string;
  pan: string;
  gstin?: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  state_code?: string;
  pincode?: string;
  bank_name?: string;
  bank_account_number?: string;
  bank_ifsc_code?: string;
  is_active: boolean;
}

// ============= Purchase Orders =============
export interface PurchaseOrderLine {
  id: string;
  line_number: number;
  item_code?: string;
  item_description: string;
  hsn_sac_code?: string;
  uom?: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  taxable_amount: number;
  cgst_rate: number;
  cgst_amount: number;
  sgst_rate: number;
  sgst_amount: number;
  igst_rate: number;
  igst_amount: number;
  net_amount: number;
  delivered_quantity?: number;
  pending_quantity?: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  po_date: string;
  vendor_id: string;
  organization_id: string;
  delivery_date?: string;
  payment_terms?: string;
  subtotal: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  total_amount: number;
  status: string;
  acknowledgement_status?: string;
  lines?: PurchaseOrderLine[];
  created_at: string;
}

export interface POAcknowledgement {
  id: string;
  purchase_order_id: string;
  vendor_id: string;
  status: POAcknowledgementStatus;
  acknowledged_at?: string;
  committed_delivery_date?: string;
  delivery_remarks?: string;
  rejection_reason?: string;
}

export interface POAcknowledgementCreate {
  committed_delivery_date?: string;
  delivery_remarks?: string;
}

export interface POChangeRequest {
  id: string;
  purchase_order_id: string;
  vendor_id: string;
  request_type: string;
  request_details: string;
  line_changes?: Record<string, unknown>[];
  justification?: string;
  status: string;
  submitted_at?: string;
  reviewed_at?: string;
  review_remarks?: string;
}

export interface POChangeRequestCreate {
  request_type: string;
  request_details: string;
  line_changes?: Record<string, unknown>[];
  justification?: string;
}

// ============= Invoices =============
export interface VendorInvoiceLine {
  id?: string;
  line_number: number;
  po_line_id?: string;
  item_code?: string;
  item_description: string;
  hsn_sac_code?: string;
  uom?: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  discount_percent: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_rate: number;
  cgst_amount: number;
  sgst_rate: number;
  sgst_amount: number;
  igst_rate: number;
  igst_amount: number;
  cess_rate: number;
  cess_amount: number;
  net_amount: number;
}

export interface VendorInvoice {
  id: string;
  vendor_id: string;
  organization_id: string;
  purchase_order_id?: string;
  grn_id?: string;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  vendor_gstin?: string;
  place_of_supply?: string;
  subtotal: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  cess_amount: number;
  tds_applicable: boolean;
  tds_rate?: number;
  tds_amount: number;
  total_amount: number;
  payable_amount: number;
  balance_amount?: number;
  matching_type: string;
  matching_status?: string;
  po_matched: boolean;
  grn_matched: boolean;
  matching_remarks?: string;
  status: VendorInvoiceStatus;
  submitted_at?: string;
  approved_at?: string;
  rejected_at?: string;
  rejection_reason?: string;
  lines?: VendorInvoiceLine[];
  documents?: VendorInvoiceDocument[];
  created_at: string;
}

export interface VendorInvoiceDocument {
  id: string;
  invoice_id: string;
  document_type: string;
  document_name: string;
  document_number?: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
}

export interface VendorInvoiceCreate {
  purchase_order_id?: string;
  grn_id?: string;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  vendor_gstin?: string;
  place_of_supply?: string;
  matching_type?: string;
  lines: Omit<VendorInvoiceLine, 'id'>[];
}

export interface InvoiceMatchingResult {
  is_matched: boolean;
  matching_status: string;
  po_matched: boolean;
  grn_matched: boolean;
  variances: {
    line_number: number;
    quantity_variance?: number;
    price_variance?: number;
    amount_variance?: number;
    within_tolerance: boolean;
  }[];
  remarks?: string;
}

// ============= ASN =============
export interface ASNLine {
  id?: string;
  line_number: number;
  po_line_id?: string;
  item_code?: string;
  item_description: string;
  shipped_quantity: number;
  uom?: string;
  batch_number?: string;
  serial_numbers?: string[];
  manufacturing_date?: string;
  expiry_date?: string;
  package_number?: string;
  weight?: number;
  received_quantity?: number;
}

export interface AdvancedShippingNotice {
  id: string;
  vendor_id: string;
  organization_id: string;
  purchase_order_id: string;
  asn_number: string;
  ship_date?: string;
  expected_delivery_date?: string;
  actual_delivery_date?: string;
  carrier_name?: string;
  tracking_number?: string;
  vehicle_number?: string;
  driver_name?: string;
  driver_phone?: string;
  total_packages?: number;
  total_weight?: number;
  weight_uom?: string;
  status: ASNStatus;
  dispatched_at?: string;
  delivery_remarks?: string;
  cancellation_reason?: string;
  lines?: ASNLine[];
  created_at: string;
}

export interface ASNCreate {
  purchase_order_id: string;
  expected_delivery_date?: string;
  carrier_name?: string;
  tracking_number?: string;
  vehicle_number?: string;
  driver_name?: string;
  driver_phone?: string;
  total_packages?: number;
  total_weight?: number;
  weight_uom?: string;
  lines: Omit<ASNLine, 'id' | 'line_number'>[];
}

export interface ASNDispatch {
  ship_date?: string;
  expected_delivery_date?: string;
  carrier_name?: string;
  tracking_number?: string;
  vehicle_number?: string;
  driver_name?: string;
  driver_phone?: string;
}

// ============= Payments =============
export interface VendorPayment {
  id: string;
  payment_reference: string;
  payment_date: string;
  payment_mode: string;
  amount: number;
  vendor_id: string;
  status: string;
  invoices?: {
    invoice_number: string;
    invoice_amount: number;
    allocated_amount: number;
  }[];
  deductions?: {
    deduction_type: string;
    description: string;
    amount: number;
  }[];
}

export interface AgingBucket {
  label: string;
  min_days: number;
  max_days?: number;
  amount: number;
  count: number;
}

export interface VendorAgingReport {
  as_of_date: string;
  total_outstanding: number;
  invoice_count: number;
  buckets: AgingBucket[];
  invoices: {
    invoice_number: string;
    invoice_date: string;
    due_date?: string;
    invoice_amount: number;
    balance_amount: number;
    days_overdue: number;
  }[];
}

export interface VendorStatementLine {
  date: string;
  reference: string;
  description: string;
  document_type: string;
  debit: number;
  credit: number;
  balance: number;
}

export interface VendorStatement {
  vendor_id: string;
  vendor_name: string;
  vendor_code: string;
  from_date: string;
  to_date: string;
  opening_balance: number;
  closing_balance: number;
  total_invoices: number;
  total_payments: number;
  lines: VendorStatementLine[];
  generated_at: string;
}

// ============= Compliance =============
export interface ComplianceDocument {
  id: string;
  vendor_id: string;
  document_type: ComplianceDocumentType;
  document_name: string;
  document_number?: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
  original_filename?: string;
  issue_date?: string;
  expiry_date?: string;
  is_perpetual: boolean;
  is_expired: boolean;
  days_to_expiry?: number;
  verification_status?: VerificationStatus;
  verified_at?: string;
  verification_remarks?: string;
  created_at: string;
}

export interface ComplianceDocumentCreate {
  document_type: ComplianceDocumentType;
  document_name: string;
  document_number?: string;
  issue_date?: string;
  expiry_date?: string;
  is_perpetual?: boolean;
}

export interface ComplianceSummary {
  total: number;
  verified: number;
  pending: number;
  rejected: number;
  expired: number;
  expiring_soon: number;
}

export interface RequiredDocument {
  document_type: ComplianceDocumentType;
  is_required: boolean;
  is_uploaded: boolean;
  document?: ComplianceDocument;
}

// ============= Notifications =============
export interface VendorNotification {
  id: string;
  vendor_id: string;
  user_id?: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  title: string;
  message: string;
  reference_type?: string;
  reference_id?: string;
  action_url?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

// ============= Dashboard =============
export interface VendorDashboardSummary {
  purchase_orders: {
    pending_acknowledgement: number;
    acknowledged: number;
    change_requested: number;
  };
  invoices: {
    total: number;
    draft: number;
    submitted: number;
    approved: number;
    rejected: number;
  };
  asn: {
    draft: number;
    dispatched: number;
    in_transit: number;
    delivered: number;
  };
  payments: {
    total_outstanding: number;
    pending_payments: number;
    last_payment_date?: string;
    last_payment_amount?: number;
  };
  compliance: {
    total_documents: number;
    verified: number;
    pending_verification: number;
    expired: number;
  };
}

export interface PendingAction {
  type: string;
  title: string;
  description: string;
  reference_id: string;
  priority: string;
}

// ============= List Response =============
export interface ListResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
