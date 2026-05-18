/**
 * Vendor Portal API Service
 */

import axios from 'axios';

import type {
  VendorLoginRequest,
  VendorLoginResponse,
  VendorOTPRequest,
  VendorUser,
  VendorInfo,
  PurchaseOrder,
  POAcknowledgementCreate,
  POAcknowledgement,
  POChangeRequestCreate,
  POChangeRequest,
  VendorInvoice,
  VendorInvoiceCreate,
  InvoiceMatchingResult,
  AdvancedShippingNotice,
  ASNCreate,
  ASNDispatch,
  VendorPayment,
  VendorAgingReport,
  VendorStatement,
  ComplianceDocument,
  ComplianceDocumentCreate,
  ComplianceSummary,
  RequiredDocument,
  VendorNotification,
  VendorDashboardSummary,
  PendingAction,
  ListResponse,
} from '@/types/vendor';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

// Create axios instance for vendor portal
const vendorApi = axios.create({
  baseURL: `${API_BASE_URL}/vendor-portal`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
vendorApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('vendor_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
vendorApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('vendor_refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/vendor-portal/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('vendor_access_token', access_token);
          localStorage.setItem('vendor_refresh_token', refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return vendorApi(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('vendor_access_token');
          localStorage.removeItem('vendor_refresh_token');
          localStorage.removeItem('vendor_user');
          window.location.href = '/vendor/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// ============= Auth APIs =============
export const vendorAuthApi = {
  login: (data: VendorLoginRequest) =>
    vendorApi.post<VendorLoginResponse>('/auth/login', data),

  requestOtp: (data: VendorOTPRequest) =>
    vendorApi.post('/auth/request-otp', data),

  verifyOtp: (data: { email?: string; phone?: string; otp: string; purpose?: string }) =>
    vendorApi.post<{ valid: boolean }>('/auth/verify-otp', data),

  refreshToken: (refreshToken: string) =>
    vendorApi.post<{ access_token: string; refresh_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    }),

  logout: (sessionId: string) =>
    vendorApi.post(`/auth/logout?session_id=${sessionId}`),

  forgotPassword: (data: VendorOTPRequest) =>
    vendorApi.post('/auth/forgot-password', data),

  resetPassword: (data: { email: string; otp: string; new_password: string }) =>
    vendorApi.post('/auth/reset-password', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    vendorApi.post('/auth/change-password', data),

  getCurrentUser: () =>
    vendorApi.get<VendorUser>('/auth/me'),
};

// ============= Profile APIs =============
export const vendorProfileApi = {
  getProfile: () =>
    vendorApi.get<VendorInfo>('/profile'),

  updateProfile: (data: Partial<VendorInfo>) =>
    vendorApi.put<VendorInfo>('/profile', data),

  getBankAccounts: () =>
    vendorApi.get('/profile/bank-accounts'),

  addBankAccount: (data: { bank_name: string; branch: string; account_number: string; ifsc_code: string }) =>
    vendorApi.post('/profile/bank-accounts', data),

  getContacts: () =>
    vendorApi.get('/profile/contacts'),

  addContact: (data: { first_name: string; last_name?: string; email: string; phone?: string; designation?: string }) =>
    vendorApi.post('/profile/contacts', data),

  getPortalUsers: (params?: { skip?: number; limit?: number; status?: string }) =>
    vendorApi.get('/profile/users', { params }),
};

// ============= Purchase Order APIs =============
export const vendorPOApi = {
  list: (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    from_date?: string;
    to_date?: string;
    search?: string;
  }) =>
    vendorApi.get<ListResponse<PurchaseOrder>>('/purchase-orders', { params }),

  get: (id: string) =>
    vendorApi.get<{ purchase_order: PurchaseOrder; acknowledgement?: POAcknowledgement }>(`/purchase-orders/${id}`),

  getLines: (id: string) =>
    vendorApi.get(`/purchase-orders/${id}/lines`),

  getPending: () =>
    vendorApi.get<PurchaseOrder[]>('/purchase-orders/pending'),

  getSummary: () =>
    vendorApi.get('/purchase-orders/summary'),

  acknowledge: (id: string, data: POAcknowledgementCreate) =>
    vendorApi.post<POAcknowledgement>(`/purchase-orders/${id}/acknowledge`, data),

  reject: (id: string, reason: string) =>
    vendorApi.post<POAcknowledgement>(`/purchase-orders/${id}/reject`, { reason }),

  requestChange: (id: string, data: POChangeRequestCreate) =>
    vendorApi.post<POChangeRequest>(`/purchase-orders/${id}/request-change`, data),

  downloadPdf: (id: string) =>
    vendorApi.get(`/purchase-orders/${id}/download`, { responseType: 'blob' }),

  // Change requests
  listChangeRequests: (params?: { po_id?: string; status?: string; skip?: number; limit?: number }) =>
    vendorApi.get<ListResponse<POChangeRequest>>('/purchase-orders/change-requests', { params }),

  getChangeRequest: (id: string) =>
    vendorApi.get<POChangeRequest>(`/purchase-orders/change-requests/${id}`),

  cancelChangeRequest: (id: string, reason?: string) =>
    vendorApi.post<POChangeRequest>(`/purchase-orders/change-requests/${id}/cancel`, { reason }),
};

// ============= Invoice APIs =============
export const vendorInvoiceApi = {
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    vendorApi.get<ListResponse<VendorInvoice>>('/invoices', { params }),

  get: (id: string) =>
    vendorApi.get<VendorInvoice>(`/invoices/${id}`),

  create: (data: VendorInvoiceCreate) =>
    vendorApi.post<VendorInvoice>('/invoices', data),

  update: (id: string, data: Partial<VendorInvoiceCreate>) =>
    vendorApi.put<VendorInvoice>(`/invoices/${id}`, data),

  addLine: (id: string, data: Omit<VendorInvoiceCreate['lines'][0], 'line_number'>) =>
    vendorApi.post(`/invoices/${id}/lines`, data),

  uploadDocument: (id: string, formData: FormData) =>
    vendorApi.post(`/invoices/${id}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  validate: (id: string) =>
    vendorApi.post<InvoiceMatchingResult>(`/invoices/${id}/validate`),

  submit: (id: string) =>
    vendorApi.post<VendorInvoice>(`/invoices/${id}/submit`),
};

// ============= ASN APIs =============
export const vendorASNApi = {
  list: (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    po_id?: string;
    from_date?: string;
    to_date?: string;
  }) =>
    vendorApi.get<ListResponse<AdvancedShippingNotice>>('/asn', { params }),

  get: (id: string) =>
    vendorApi.get<AdvancedShippingNotice>(`/asn/${id}`),

  getSummary: () =>
    vendorApi.get('/asn/summary'),

  getAvailablePOLines: (poId: string) =>
    vendorApi.get(`/asn/po/${poId}/available-lines`),

  create: (data: ASNCreate) =>
    vendorApi.post<AdvancedShippingNotice>('/asn', data),

  update: (id: string, data: Partial<ASNCreate>) =>
    vendorApi.put<AdvancedShippingNotice>(`/asn/${id}`, data),

  addLine: (id: string, data: Omit<ASNCreate['lines'][0], 'line_number'>) =>
    vendorApi.post(`/asn/${id}/lines`, data),

  updateLine: (id: string, lineId: string, data: Omit<ASNCreate['lines'][0], 'line_number'>) =>
    vendorApi.put(`/asn/${id}/lines/${lineId}`, data),

  removeLine: (id: string, lineId: string) =>
    vendorApi.delete(`/asn/${id}/lines/${lineId}`),

  dispatch: (id: string, data: ASNDispatch) =>
    vendorApi.post<AdvancedShippingNotice>(`/asn/${id}/dispatch`, data),

  updateTracking: (id: string, data: { tracking_number?: string; carrier_name?: string }) =>
    vendorApi.put<AdvancedShippingNotice>(`/asn/${id}/tracking`, data),

  cancel: (id: string, reason: string) =>
    vendorApi.post<AdvancedShippingNotice>(`/asn/${id}/cancel`, null, { params: { reason } }),
};

// ============= Payment APIs =============
export const vendorPaymentApi = {
  list: (params?: { skip?: number; limit?: number; from_date?: string; to_date?: string; status?: string }) =>
    vendorApi.get<ListResponse<VendorPayment>>('/payments', { params }),

  get: (id: string) =>
    vendorApi.get<VendorPayment>(`/payments/${id}`),

  getSummary: () =>
    vendorApi.get('/payments/summary'),

  getUpcoming: (days?: number) =>
    vendorApi.get('/payments/upcoming', { params: { days } }),

  getAging: (asOfDate?: string) =>
    vendorApi.get<VendorAgingReport>('/payments/aging', { params: { as_of_date: asOfDate } }),

  getStatement: (fromDate: string, toDate: string) =>
    vendorApi.get<VendorStatement>('/payments/statement', { params: { from_date: fromDate, to_date: toDate } }),

  downloadStatement: (fromDate: string, toDate: string) =>
    vendorApi.get('/payments/statement/download', {
      params: { from_date: fromDate, to_date: toDate },
      responseType: 'blob',
    }),

  getRemittance: (id: string) =>
    vendorApi.get(`/payments/${id}/remittance`),

  downloadRemittance: (id: string) =>
    vendorApi.get(`/payments/${id}/remittance/download`, { responseType: 'blob' }),
};

// ============= Compliance APIs =============
export const vendorComplianceApi = {
  list: (includeInactive?: boolean) =>
    vendorApi.get<ListResponse<ComplianceDocument>>('/compliance', {
      params: { include_inactive: includeInactive },
    }),

  get: (id: string) =>
    vendorApi.get<ComplianceDocument>(`/compliance/${id}`),

  getSummary: () =>
    vendorApi.get<ComplianceSummary>('/compliance/summary'),

  getRequired: () =>
    vendorApi.get<{ total_required: number; total_uploaded: number; is_complete: boolean; documents: RequiredDocument[] }>(
      '/compliance/required'
    ),

  getExpiring: (days?: number) =>
    vendorApi.get<ComplianceDocument[]>('/compliance/expiring', { params: { days } }),

  getExpired: () =>
    vendorApi.get<ComplianceDocument[]>('/compliance/expired'),

  upload: (formData: FormData) =>
    vendorApi.post<ComplianceDocument>('/compliance', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  update: (id: string, data: Partial<ComplianceDocumentCreate>) =>
    vendorApi.put<ComplianceDocument>(`/compliance/${id}`, data),

  delete: (id: string) =>
    vendorApi.delete(`/compliance/${id}`),

  // Notifications
  getNotifications: (params?: { skip?: number; limit?: number; unread_only?: boolean }) =>
    vendorApi.get<ListResponse<VendorNotification>>('/compliance/notifications', { params }),

  getUserNotifications: (params?: { skip?: number; limit?: number; unread_only?: boolean }) =>
    vendorApi.get<ListResponse<VendorNotification>>('/compliance/notifications/user', { params }),

  getUnreadCount: () =>
    vendorApi.get<{ unread_count: number }>('/compliance/notifications/unread-count'),

  markNotificationRead: (id: string) =>
    vendorApi.post<VendorNotification>(`/compliance/notifications/${id}/read`),

  markAllNotificationsRead: () =>
    vendorApi.post<{ marked_read: number }>('/compliance/notifications/read-all'),
};

// ============= Dashboard APIs =============
export const vendorDashboardApi = {
  getSummary: () =>
    vendorApi.get<VendorDashboardSummary>('/dashboard/summary'),

  getPendingActions: () =>
    vendorApi.get<{ total: number; actions: PendingAction[] }>('/dashboard/pending-actions'),

  getNotifications: () =>
    vendorApi.get<ListResponse<VendorNotification>>('/dashboard/notifications'),

  getQuickStats: () =>
    vendorApi.get<{
      pending_pos: number;
      unread_notifications: number;
      outstanding_amount: number;
      pending_payments: number;
    }>('/dashboard/quick-stats'),

  getRecentActivity: (limit?: number) =>
    vendorApi.get<{
      total: number;
      activities: {
        id: string;
        type: string;
        title: string;
        message: string;
        timestamp: string;
        is_read: boolean;
      }[];
    }>('/dashboard/recent-activity', { params: { limit } }),
};

export default vendorApi;
