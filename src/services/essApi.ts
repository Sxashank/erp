/**
 * ESS Portal API Service
 * Handles all Employee Self-Service portal API calls
 */

import api from './api';

// ==================== Auth APIs ====================

export const essAuthApi = {
  /**
   * Send OTP to mobile number
   */
  sendOtp: (data: { mobile: string; purpose?: string }) =>
    api.post('/ess/auth/send-otp', data),

  /**
   * Verify OTP and login
   */
  login: (data: { mobile: string; otp: string; device_info?: any }) =>
    api.post('/ess/auth/login', data),

  /**
   * Refresh access token
   */
  refresh: (data: { refresh_token: string }) =>
    api.post('/ess/auth/refresh', data),

  /**
   * Logout current session
   */
  logout: () =>
    api.post('/ess/auth/logout'),

  /**
   * Get active sessions
   */
  getSessions: () =>
    api.get('/ess/auth/sessions'),

  /**
   * Revoke a specific session
   */
  revokeSession: (sessionId: string) =>
    api.delete(`/ess/auth/sessions/${sessionId}`),

  /**
   * Register device for push notifications
   */
  registerDevice: (data: { device_uuid: string; device_name: string; fcm_token?: string }) =>
    api.post('/ess/auth/devices', data),
};

// ==================== Profile APIs ====================

export const essProfileApi = {
  /**
   * Get employee dashboard summary
   */
  getDashboard: () =>
    api.get('/ess/profile/dashboard'),

  /**
   * Get employee profile
   */
  getProfile: () =>
    api.get('/ess/profile'),

  /**
   * Request profile update
   */
  requestUpdate: (data: {
    update_type: string;
    requested_values: Record<string, any>;
    change_reason?: string;
    attachments?: any;
  }) =>
    api.post('/ess/profile/update-request', data),

  /**
   * Get profile update requests
   */
  getUpdateRequests: (params?: { status?: string }) =>
    api.get('/ess/profile/update-requests', { params }),

  /**
   * Get payslips
   */
  getPayslips: (params?: { year?: number; limit?: number }) =>
    api.get('/ess/profile/payslips', { params }),

  /**
   * Download payslip PDF
   */
  downloadPayslip: (payslipId: string) =>
    api.get(`/ess/profile/payslips/${payslipId}/download`, { responseType: 'blob' }),

  /**
   * Get YTD salary summary
   */
  getYtdSummary: (financialYear?: string) =>
    api.get('/ess/profile/ytd-summary', { params: { financial_year: financialYear } }),

  /**
   * Get leave balance
   */
  getLeaveBalance: () =>
    api.get('/ess/profile/leave-balance'),

  /**
   * Get attendance summary
   */
  getAttendance: (params?: { month?: string; year?: number }) =>
    api.get('/ess/profile/attendance', { params }),
};

// ==================== Reimbursement APIs ====================

export const essReimbursementApi = {
  /**
   * Get reimbursement categories
   */
  getCategories: () =>
    api.get('/ess/reimbursement/categories'),

  /**
   * Get reimbursement claims
   */
  getClaims: (params?: {
    status?: string;
    category_id?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get('/ess/reimbursement/claims', { params }),

  /**
   * Get claim details
   */
  getClaim: (claimId: string) =>
    api.get(`/ess/reimbursement/claims/${claimId}`),

  /**
   * Create new claim
   */
  createClaim: (data: {
    category_id?: string;
    claim_type: string;
    expense_from: string;
    expense_to: string;
    description: string;
    purpose?: string;
  }) =>
    api.post('/ess/reimbursement/claims', data),

  /**
   * Update claim
   */
  updateClaim: (claimId: string, data: any) =>
    api.put(`/ess/reimbursement/claims/${claimId}`, data),

  /**
   * Delete draft claim
   */
  deleteClaim: (claimId: string) =>
    api.delete(`/ess/reimbursement/claims/${claimId}`),

  /**
   * Add line item to claim
   */
  addLineItem: (claimId: string, data: {
    expense_date: string;
    description: string;
    amount: number;
    bill_number?: string;
    bill_date?: string;
    vendor_name?: string;
  }) =>
    api.post(`/ess/reimbursement/claims/${claimId}/items`, data),

  /**
   * Update line item
   */
  updateLineItem: (claimId: string, itemId: string, data: any) =>
    api.put(`/ess/reimbursement/claims/${claimId}/items/${itemId}`, data),

  /**
   * Delete line item
   */
  deleteLineItem: (claimId: string, itemId: string) =>
    api.delete(`/ess/reimbursement/claims/${claimId}/items/${itemId}`),

  /**
   * Submit claim for approval
   */
  submitClaim: (claimId: string) =>
    api.post(`/ess/reimbursement/claims/${claimId}/submit`),

  /**
   * Get claim summary
   */
  getSummary: () =>
    api.get('/ess/reimbursement/summary'),
};

// ==================== Helpdesk APIs ====================

export const essHelpdeskApi = {
  /**
   * Get helpdesk categories
   */
  getCategories: (department?: string) =>
    api.get('/ess/helpdesk/categories', { params: { department } }),

  /**
   * Get tickets
   */
  getTickets: (params?: {
    status?: string;
    category_type?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get('/ess/helpdesk', { params }),

  /**
   * Get ticket details
   */
  getTicket: (ticketId: string) =>
    api.get(`/ess/helpdesk/${ticketId}`),

  /**
   * Create new ticket
   */
  createTicket: (data: {
    subject: string;
    description: string;
    category_type: string;
    category_id?: string;
    priority?: string;
    attachments?: any;
  }) =>
    api.post('/ess/helpdesk', data),

  /**
   * Add comment to ticket
   */
  addComment: (ticketId: string, data: { comment: string }) =>
    api.post(`/ess/helpdesk/${ticketId}/comments`, data),

  /**
   * Close ticket
   */
  closeTicket: (ticketId: string, remarks?: string) =>
    api.post(`/ess/helpdesk/${ticketId}/close`, { remarks }),

  /**
   * Reopen ticket
   */
  reopenTicket: (ticketId: string, reason: string) =>
    api.post(`/ess/helpdesk/${ticketId}/reopen`, { reason }),

  /**
   * Submit feedback
   */
  submitFeedback: (ticketId: string, data: { rating: number; feedback?: string }) =>
    api.post(`/ess/helpdesk/${ticketId}/feedback`, data),

  /**
   * Get ticket summary
   */
  getSummary: () =>
    api.get('/ess/helpdesk/summary'),
};

// ==================== IT Declaration APIs ====================

export const essITDeclarationApi = {
  /**
   * Get IT declaration sections
   */
  getSections: (financialYear?: string) =>
    api.get('/ess/it-declaration/sections', { params: { financial_year: financialYear } }),

  /**
   * Get current declaration
   */
  getDeclaration: (financialYear?: string) =>
    api.get('/ess/it-declaration', { params: { financial_year: financialYear } }),

  /**
   * Create/update declaration
   */
  saveDeclaration: (data: {
    financial_year: string;
    tax_regime: string;
    rent_paid_monthly?: number;
    landlord_name?: string;
    landlord_pan?: string;
    metro_city?: boolean;
    home_loan_interest?: number;
    home_loan_principal?: number;
    lender_name?: string;
  }) =>
    api.post('/ess/it-declaration', data),

  /**
   * Add declaration item
   */
  addItem: (declarationId: string, data: {
    section_code: string;
    particular: string;
    declared_amount: number;
    investment_date?: string;
    policy_number?: string;
    institution_name?: string;
  }) =>
    api.post(`/ess/it-declaration/${declarationId}/items`, data),

  /**
   * Update declaration item
   */
  updateItem: (declarationId: string, itemId: string, data: any) =>
    api.put(`/ess/it-declaration/${declarationId}/items/${itemId}`, data),

  /**
   * Delete declaration item
   */
  deleteItem: (declarationId: string, itemId: string) =>
    api.delete(`/ess/it-declaration/${declarationId}/items/${itemId}`),

  /**
   * Add HRA receipt
   */
  addHRAReceipt: (declarationId: string, data: {
    month: string;
    rent_amount: number;
    receipt_number?: string;
  }) =>
    api.post(`/ess/it-declaration/${declarationId}/hra-receipts`, data),

  /**
   * Submit declaration
   */
  submitDeclaration: (declarationId: string) =>
    api.post(`/ess/it-declaration/${declarationId}/submit`),

  /**
   * Submit proofs
   */
  submitProofs: (declarationId: string) =>
    api.post(`/ess/it-declaration/${declarationId}/submit-proofs`),

  /**
   * Calculate tax
   */
  calculateTax: (declarationId: string) =>
    api.get(`/ess/it-declaration/${declarationId}/calculate-tax`),
};

// ==================== Attendance Regularization APIs ====================

export const essAttendanceApi = {
  /**
   * Get regularization requests
   */
  getRegularizations: (params?: {
    status?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get('/ess/it-declaration/regularizations', { params }),

  /**
   * Create regularization request
   */
  createRegularization: (data: {
    attendance_date: string;
    regularization_type: string;
    requested_in_time?: string;
    requested_out_time?: string;
    reason: string;
  }) =>
    api.post('/ess/it-declaration/regularizations', data),

  /**
   * Cancel regularization request
   */
  cancelRegularization: (requestId: string) =>
    api.delete(`/ess/it-declaration/regularizations/${requestId}`),
};

export default {
  auth: essAuthApi,
  profile: essProfileApi,
  reimbursement: essReimbursementApi,
  helpdesk: essHelpdeskApi,
  itDeclaration: essITDeclarationApi,
  attendance: essAttendanceApi,
};
