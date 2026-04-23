/**
 * Customer Portal API Service
 * Handles all Customer Portal API calls for borrowers
 */

import api from './api';

// Create a separate axios instance for portal with different token
const portalApi = api; // Uses same base, but we'll use different token storage

// ==================== Auth APIs ====================

export const portalAuthApi = {
  sendOtp: (data: { mobile: string; purpose?: string }) =>
    api.post('/portal/auth/send-otp', data),

  login: (data: { mobile: string; otp: string; device_info?: any }) =>
    api.post('/portal/auth/verify-otp', data),

  refresh: (data: { refresh_token: string }) =>
    api.post('/portal/auth/refresh', data),

  logout: () =>
    api.post('/portal/auth/logout'),

  getSessions: () =>
    api.get('/portal/auth/sessions'),
};

// ==================== Dashboard APIs ====================

export const portalDashboardApi = {
  getDashboard: () =>
    api.get('/portal/dashboard'),

  getLoans: () =>
    api.get('/portal/loans'),

  getLoan: (loanId: string) =>
    api.get(`/portal/loans/${loanId}`),

  getLoanSchedule: (loanId: string) =>
    api.get(`/portal/loans/${loanId}/schedule`),

  getLoanPayments: (loanId: string) =>
    api.get(`/portal/loans/${loanId}/payments`),

  getUpcomingDues: () =>
    api.get('/portal/upcoming-dues'),
};

// ==================== Payment APIs ====================

export const portalPaymentApi = {
  initiatePayment: (data: {
    loan_account_id: string;
    amount: number;
    payment_type: string;
    payment_mode: string;
  }) =>
    api.post('/portal/payments/initiate', data),

  getPaymentStatus: (paymentId: string) =>
    api.get(`/portal/payments/${paymentId}/status`),

  getPrepaymentQuote: (data: {
    loan_account_id: string;
    prepayment_amount: number;
    prepayment_date: string;
  }) =>
    api.post('/portal/payments/prepayment-quote', data),

  getForeclosureQuote: (data: {
    loan_account_id: string;
    foreclosure_date: string;
  }) =>
    api.post('/portal/payments/foreclosure-quote', data),

  setupNachMandate: (data: {
    loan_account_id: string;
    bank_account_id: string;
    max_amount: number;
    frequency: string;
    start_date: string;
    end_date: string;
  }) =>
    api.post('/portal/payments/mandate/setup', data),
};

// ==================== Document APIs ====================

export const portalDocumentApi = {
  getDocuments: (loanId?: string) =>
    api.get('/portal/documents', { params: { loan_account_id: loanId } }),

  downloadDocument: (documentId: string) =>
    api.get(`/portal/documents/${documentId}/download`, { responseType: 'blob' }),

  getStatement: (data: { loan_account_id: string; from_date: string; to_date: string }) =>
    api.get('/portal/documents/statement', { params: data, responseType: 'blob' }),

  getInterestCertificate: (data: { loan_account_id: string; financial_year: string }) =>
    api.get('/portal/documents/interest-cert', { params: data, responseType: 'blob' }),

  getTdsCertificate: (data: { financial_year: string }) =>
    api.get('/portal/documents/tds-cert', { params: data, responseType: 'blob' }),
};

// ==================== Service Request APIs ====================

export const portalServiceRequestApi = {
  createRequest: (data: {
    request_type: string;
    loan_account_id?: string;
    subject: string;
    description: string;
    attachments?: any;
  }) =>
    api.post('/portal/service-requests', data),

  getRequests: (params?: { status?: string; loan_account_id?: string }) =>
    api.get('/portal/service-requests', { params }),

  getRequest: (requestId: string) =>
    api.get(`/portal/service-requests/${requestId}`),

  submitPrepaymentRequest: (data: {
    loan_account_id: string;
    prepayment_amount: number;
    preferred_date: string;
    source_of_funds: string;
    remarks?: string;
  }) =>
    api.post('/portal/service-requests/prepayment', data),

  submitForeclosureRequest: (data: {
    loan_account_id: string;
    foreclosure_date: string;
    source_of_funds: string;
    remarks?: string;
  }) =>
    api.post('/portal/service-requests/foreclosure', data),
};

// ==================== Communication APIs ====================

export const portalCommunicationApi = {
  getNotifications: (params?: { unread_only?: boolean }) =>
    api.get('/portal/notifications', { params }),

  markAsRead: (notificationId: string) =>
    api.post(`/portal/notifications/${notificationId}/read`),

  createTicket: (data: {
    subject: string;
    description: string;
    category: string;
    loan_account_id?: string;
  }) =>
    api.post('/portal/support/ticket', data),

  getTickets: (params?: { status?: string }) =>
    api.get('/portal/support/tickets', { params }),

  getTicket: (ticketId: string) =>
    api.get(`/portal/support/tickets/${ticketId}`),

  addTicketReply: (ticketId: string, data: { message: string }) =>
    api.post(`/portal/support/tickets/${ticketId}/reply`, data),
};

export default {
  auth: portalAuthApi,
  dashboard: portalDashboardApi,
  payment: portalPaymentApi,
  document: portalDocumentApi,
  serviceRequest: portalServiceRequestApi,
  communication: portalCommunicationApi,
};
