import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { logout, refreshTokens } from './auth';

import { useAuthStore } from '@/stores/authStore';
import { useOrganizationStore } from '@/stores/organizationStore';


const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — reads tokens from the auth store, NOT localStorage.
// See CLAUDE.md §5.6.
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const orgId = useOrganizationStore.getState().activeOrganizationId;
  if (orgId) {
    // Backend ignores unless it needs it; harmless hint for RLS context.
    config.headers['X-Organization-Id'] = orgId;
  }
  return config;
});

// Response interceptor — handles 401 by refreshing once, then logs out on
// refresh failure. Concurrent 401s share a single in-flight refresh so we
// don't invalidate our own new refresh token. See CLAUDE.md §8.1.
let refreshInFlight: Promise<string | null> | null = null;

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;
    const status = error.response?.status;

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      // Avoid refresh loop if /auth/refresh itself 401s.
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      originalRequest._retry = true;

      if (!refreshInFlight) {
        refreshInFlight = refreshTokens().finally(() => {
          refreshInFlight = null;
        });
      }
      const newAccess = await refreshInFlight;

      if (newAccess) {
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      }

      // Refresh failed — hard logout and redirect.
      await logout();
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  },
);

// Auth API
export const authApi = {
  login: (data: { username: string; password: string; otp?: string }) =>
    api.post('/auth/login', data),
  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),
  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  me: () => api.get('/auth/me'),
  changePassword: (data: { current_password: string; new_password: string; confirm_password: string }) =>
    api.post('/auth/change-password', data),
  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),
  resetPassword: (data: { token: string; new_password: string; confirm_password: string }) =>
    api.post('/auth/reset-password', data),
};

// Organizations API
export const organizationsApi = {
  list: (params?: { page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/organizations', { params }),
  get: (id: string) => api.get(`/organizations/${id}`),
  create: (data: unknown) => api.post('/organizations', data),
  update: (id: string, data: unknown) => api.put(`/organizations/${id}`, data),
  delete: (id: string) => api.delete(`/organizations/${id}`),

  // Bank Accounts
  listBankAccounts: (orgId: string, params?: { include_inactive?: boolean }) =>
    api.get(`/organizations/${orgId}/bank-accounts`, { params }),
  getBankAccount: (orgId: string, id: string) =>
    api.get(`/organizations/${orgId}/bank-accounts/${id}`),
  createBankAccount: (orgId: string, data: unknown) =>
    api.post(`/organizations/${orgId}/bank-accounts`, data),
  updateBankAccount: (orgId: string, id: string, data: unknown) =>
    api.put(`/organizations/${orgId}/bank-accounts/${id}`, data),
  deleteBankAccount: (orgId: string, id: string) =>
    api.delete(`/organizations/${orgId}/bank-accounts/${id}`),
  setPrimaryBankAccount: (orgId: string, id: string) =>
    api.post(`/organizations/${orgId}/bank-accounts/${id}/set-primary`),

  // Addresses
  listAddresses: (orgId: string, params?: { include_inactive?: boolean }) =>
    api.get(`/organizations/${orgId}/addresses`, { params }),
  getAddress: (orgId: string, id: string) =>
    api.get(`/organizations/${orgId}/addresses/${id}`),
  createAddress: (orgId: string, data: unknown) =>
    api.post(`/organizations/${orgId}/addresses`, data),
  updateAddress: (orgId: string, id: string, data: unknown) =>
    api.put(`/organizations/${orgId}/addresses/${id}`, data),
  deleteAddress: (orgId: string, id: string) =>
    api.delete(`/organizations/${orgId}/addresses/${id}`),
  setPrimaryAddress: (orgId: string, id: string) =>
    api.post(`/organizations/${orgId}/addresses/${id}/set-primary`),
};

// Units API
export const unitsApi = {
  list: (params?: { organization_id?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/units', { params }),
  get: (id: string) => api.get(`/units/${id}`),
  create: (data: unknown) => api.post('/units', data),
  update: (id: string, data: unknown) => api.put(`/units/${id}`, data),
  delete: (id: string) => api.delete(`/units/${id}`),
  getTree: (organizationId: string) => api.get('/units/tree', { params: { organization_id: organizationId } }),
  getChildren: (id: string) => api.get(`/units/${id}/children`),
};

// Departments API
export const departmentsApi = {
  list: (params?: { organization_id?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/departments', { params }),
  get: (id: string) => api.get(`/departments/${id}`),
  create: (data: unknown) => api.post('/departments', data),
  update: (id: string, data: unknown) => api.put(`/departments/${id}`, data),
  delete: (id: string) => api.delete(`/departments/${id}`),
  getTree: (organizationId: string) => api.get('/departments/tree', { params: { organization_id: organizationId } }),
  getChildren: (id: string) => api.get(`/departments/${id}/children`),
};

// Designations API
export const designationsApi = {
  list: (params?: { department_id?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/designations', { params }),
  get: (id: string) => api.get(`/designations/${id}`),
  create: (data: unknown) => api.post('/designations', data),
  update: (id: string, data: unknown) => api.put(`/designations/${id}`, data),
  delete: (id: string) => api.delete(`/designations/${id}`),
  getReports: (id: string) => api.get(`/designations/${id}/reports`),
  getHierarchy: (id: string) => api.get(`/designations/${id}/hierarchy`),
};

// Users API
export const usersApi = {
  list: (params?: { page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/users', { params }),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: unknown) => api.post('/users', data),
  update: (id: string, data: unknown) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
  assignRole: (id: string, data: unknown) => api.post(`/users/${id}/roles`, data),
  removeRole: (userId: string, roleId: string, unitId?: string) =>
    api.delete(`/users/${userId}/roles/${roleId}`, { params: { unit_id: unitId } }),
  unlock: (id: string) => api.post(`/users/${id}/unlock`),
  resetPassword: (id: string, newPassword: string, mustChange?: boolean) =>
    api.post(`/users/${id}/reset-password`, null, { params: { new_password: newPassword, must_change: mustChange } }),
};

// Roles API
export const rolesApi = {
  list: () => api.get('/roles'),
  get: (id: string) => api.get(`/roles/${id}`),
  create: (data: unknown) => api.post('/roles', data),
  update: (id: string, data: unknown) => api.put(`/roles/${id}`, data),
  delete: (id: string) => api.delete(`/roles/${id}`),
  setPermissions: (id: string, permissionIds: string[]) =>
    api.put(`/roles/${id}/permissions`, { permission_ids: permissionIds }),
  getPermissions: () => api.get('/roles/permissions'),
  getPermissionsGrouped: () => api.get('/roles/permissions/grouped'),
};

export type ApprovalWorkflowType =
  | 'FIN_VOUCHER'
  | 'FIN_JOURNAL'
  | 'PAYMENT_RELEASE'
  | 'PAYROLL_POSTING'
  | 'LOAN_SANCTION'
  | 'LOAN_DISBURSEMENT'
  | 'LOAN_WRITE_OFF'
  | 'LOAN_OTS'
  | 'FA_ASSET_CREATION'
  | 'FA_ASSET_CAPITALIZATION'
  | 'FA_ASSET_DISPOSAL'
  | 'FA_ASSET_REVALUATION'
  | 'FA_ASSET_IMPAIRMENT'
  | 'FA_ASSET_TRANSFER'
  | 'FA_DEPRECIATION_RUN'
  | 'FA_INSURANCE_CLAIM'
  | 'FA_LEASE_ACTIVATION'
  | 'FA_LEASE_MODIFICATION'
  | 'FA_LEASE_TERMINATION';

export interface ApprovalWorkflowLevelPayload {
  levelNumber: number;
  levelName: string;
  approverRoles?: string[] | null;
  approverUsers?: string[] | null;
  minApprovers: number;
  thresholdAmount?: number | null;
  escalationHours?: number | null;
  escalationUserId?: string | null;
}

export interface ApprovalWorkflowPayload {
  organizationId: string;
  workflowType: ApprovalWorkflowType;
  workflowName: string;
  description?: string | null;
  thresholdAmount: number;
  thresholdCurrency?: string;
  approvalLevels: number;
  isSequential?: boolean;
  autoApproveOnTimeout?: boolean;
  timeoutHours?: number | null;
  allowSelfApproval?: boolean;
  notifyOnSubmit?: boolean;
  notifyOnApproval?: boolean;
  notifyOnRejection?: boolean;
  levels: ApprovalWorkflowLevelPayload[];
}

export interface ApprovalWorkflowUpdatePayload extends Partial<Omit<ApprovalWorkflowPayload, 'organizationId' | 'workflowType'>> {
  isActive?: boolean;
}

export interface ApprovalWorkflowResponse extends ApprovalWorkflowPayload {
  id: string;
  thresholdCurrency: string;
  isSequential: boolean;
  autoApproveOnTimeout: boolean;
  timeoutHours: number | null;
  allowSelfApproval: boolean;
  notifyOnSubmit: boolean;
  notifyOnApproval: boolean;
  notifyOnRejection: boolean;
  levels: (ApprovalWorkflowLevelPayload & {
    id: string;
    workflowId: string;
    createdAt: string;
    updatedAt: string | null;
    isActive: boolean;
  })[];
  createdAt: string;
  updatedAt: string | null;
  isActive: boolean;
}

export const approvalsApi = {
  listWorkflows: (params: { organization_id: string; skip?: number; limit?: number }) =>
    api.get<{
      items: ApprovalWorkflowResponse[];
      total: number;
      page: number;
      pageSize: number;
      totalPages: number;
    }>('/approvals/workflows', { params }),
  getWorkflow: (id: string) => api.get<ApprovalWorkflowResponse>(`/approvals/workflows/${id}`),
  createWorkflow: (data: ApprovalWorkflowPayload) =>
    api.post<ApprovalWorkflowResponse>('/approvals/workflows', data),
  updateWorkflow: (id: string, data: ApprovalWorkflowUpdatePayload) =>
    api.put<ApprovalWorkflowResponse>(`/approvals/workflows/${id}`, data),
  deleteWorkflow: (id: string) => api.delete(`/approvals/workflows/${id}`),
};

// Financial Years API
export const financialYearsApi = {
  list: (params?: { organization_id: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/financial-years', { params }),
  get: (id: string) => api.get(`/financial-years/${id}`),
  create: (data: unknown) => api.post('/financial-years', data),
  update: (id: string, data: unknown) => api.put(`/financial-years/${id}`, data),
  delete: (id: string) => api.delete(`/financial-years/${id}`),
  setCurrent: (id: string) => api.post(`/financial-years/${id}/set-current`),
  closePeriod: (yearId: string, periodId: string) =>
    api.post(`/financial-years/${yearId}/close-period`, { period_id: periodId }),
  lockPeriod: (yearId: string, periodId: string, reason: string) =>
    api.post(`/financial-years/${yearId}/lock-period`, { period_id: periodId, reason }),
  closeYear: (id: string) => api.post(`/financial-years/${id}/close`),
};

// Account Groups API
export const accountGroupsApi = {
  list: (params?: { organization_id: string; nature?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/account-groups', { params }),
  get: (id: string) => api.get(`/account-groups/${id}`),
  create: (data: unknown) => api.post('/account-groups', data),
  update: (id: string, data: unknown) => api.put(`/account-groups/${id}`, data),
  delete: (id: string) => api.delete(`/account-groups/${id}`),
  getTree: (organizationId: string) => api.get('/account-groups/tree', { params: { organization_id: organizationId } }),
};

// Accounts API
export const accountsApi = {
  list: (params?: { organization_id: string; account_group_id?: string; account_type?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/accounts', { params }),
  get: (id: string) => api.get(`/accounts/${id}`),
  create: (data: unknown) => api.post('/accounts', data),
  update: (id: string, data: unknown) => api.put(`/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
  search: (params: { organization_id: string; query: string; limit?: number }) =>
    api.get('/accounts/search', { params }),
};

// Voucher Types API
export const voucherTypesApi = {
  list: (params?: { organization_id: string; voucher_class?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/voucher-types', { params }),
  get: (id: string) => api.get(`/voucher-types/${id}`),
  create: (data: unknown) => api.post('/voucher-types', data),
  update: (id: string, data: unknown) => api.put(`/voucher-types/${id}`, data),
  delete: (id: string) => api.delete(`/voucher-types/${id}`),
};

// Vouchers API
export const vouchersApi = {
  list: (params?: {
    organization_id: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    voucher_class?: string;
    page?: number;
    page_size?: number;
    include_inactive?: boolean;
  }) => api.get('/vouchers', { params }),
  get: (id: string) => api.get(`/vouchers/${id}`),
  create: (data: unknown) => api.post('/vouchers', data),
  update: (id: string, data: unknown) => api.put(`/vouchers/${id}`, data),
  delete: (id: string) => api.delete(`/vouchers/${id}`),
  submit: (id: string) => api.post(`/vouchers/${id}/submit`),
  approve: (id: string, remarks?: string) =>
    api.post(`/vouchers/${id}/approve`, remarks ? { remarks } : null),
  reject: (id: string, reason: string) =>
    api.post(`/vouchers/${id}/reject`, { reason }),
  post: (id: string) => api.post(`/vouchers/${id}/post`),
  cancel: (id: string, reason: string) =>
    api.post(`/vouchers/${id}/cancel`, { reason }),
  getPendingApproval: (params: { organization_id: string; page?: number; page_size?: number }) =>
    api.get('/vouchers/pending-approval', { params }),
};

// Year-End Closing API
export const yearEndApi = {
  getPreview: (financialYearId: string) =>
    api.get(`/year-end/preview/${financialYearId}`),
  execute: (data: {
    source_financial_year_id: string;
    target_financial_year_id: string;
    skip_validations?: boolean;
  }) => api.post('/year-end/execute', data),
  reopen: (financialYearId: string, reason: string) =>
    api.post(`/year-end/reopen/${financialYearId}`, { reason }),
};

// Recurring Vouchers API
export const recurringVouchersApi = {
  list: (params: {
    organization_id: string;
    status?: string;
    frequency?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/recurring-vouchers', { params }),
  get: (id: string) => api.get(`/recurring-vouchers/${id}`),
  create: (data: unknown) => api.post('/recurring-vouchers', data),
  update: (id: string, data: unknown) => api.put(`/recurring-vouchers/${id}`, data),
  delete: (id: string) => api.delete(`/recurring-vouchers/${id}`),
  pause: (id: string, reason?: string) =>
    api.post(`/recurring-vouchers/${id}/pause`, { reason }),
  resume: (id: string) => api.post(`/recurring-vouchers/${id}/resume`),
  cancel: (id: string, reason?: string) =>
    api.post(`/recurring-vouchers/${id}/cancel`, { reason }),
  generate: (id: string, data?: { voucher_date?: string; narration_override?: string }) =>
    api.post(`/recurring-vouchers/${id}/generate`, data || {}),
  processDue: (organizationId: string) =>
    api.post('/recurring-vouchers/process-due', null, { params: { organization_id: organizationId } }),
  getUpcoming: (organizationId: string, daysAhead?: number) =>
    api.get('/recurring-vouchers/upcoming', { params: { organization_id: organizationId, days_ahead: daysAhead } }),
  getStats: (organizationId: string) =>
    api.get('/recurring-vouchers/stats', { params: { organization_id: organizationId } }),
  getLogs: (id: string, params?: { page?: number; page_size?: number }) =>
    api.get(`/recurring-vouchers/${id}/logs`, { params }),
};

// Voucher Templates API
export const voucherTemplatesApi = {
  list: (params: {
    organization_id: string;
    category?: string;
    is_active?: boolean;
    is_favorite?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/voucher-templates', { params }),
  get: (id: string) => api.get(`/voucher-templates/${id}`),
  create: (data: unknown) => api.post('/voucher-templates', data),
  update: (id: string, data: unknown) => api.put(`/voucher-templates/${id}`, data),
  delete: (id: string) => api.delete(`/voucher-templates/${id}`),
  toggleFavorite: (id: string) => api.post(`/voucher-templates/${id}/toggle-favorite`),
  use: (id: string, data: { voucher_date: string; narration_override?: string; amount_multiplier?: number }) =>
    api.post(`/voucher-templates/${id}/use`, data),
  duplicate: (id: string, newName?: string) =>
    api.post(`/voucher-templates/${id}/duplicate`, null, { params: { new_name: newName } }),
  getCategories: (organizationId: string) =>
    api.get('/voucher-templates/categories', { params: { organization_id: organizationId } }),
  getStats: (organizationId: string) =>
    api.get('/voucher-templates/stats', { params: { organization_id: organizationId } }),
};

// GST Rates API
export const gstRatesApi = {
  list: (params?: { page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/gst/rates', { params }),
  get: (id: string) => api.get(`/gst/rates/${id}`),
  create: (data: unknown) => api.post('/gst/rates', data),
  update: (id: string, data: unknown) => api.put(`/gst/rates/${id}`, data),
  delete: (id: string) => api.delete(`/gst/rates/${id}`),
  getActive: (params?: { as_of_date?: string; page?: number; page_size?: number }) =>
    api.get('/gst/rates/active', { params }),
};

// HSN/SAC API
export const hsnSacApi = {
  list: (params?: { search?: string; hsn_sac_type?: string; page?: number; page_size?: number }) =>
    api.get('/gst/hsn-sac', { params }),
  get: (id: string) => api.get(`/gst/hsn-sac/${id}`),
  create: (data: unknown) => api.post('/gst/hsn-sac', data),
  update: (id: string, data: unknown) => api.put(`/gst/hsn-sac/${id}`, data),
  delete: (id: string) => api.delete(`/gst/hsn-sac/${id}`),
};

// GST Registrations API
export const gstRegistrationsApi = {
  list: (params?: { organization_id?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/gst/registrations', { params }),
  get: (id: string) => api.get(`/gst/registrations/${id}`),
  create: (data: unknown) => api.post('/gst/registrations', data),
  update: (id: string, data: unknown) => api.put(`/gst/registrations/${id}`, data),
  delete: (id: string) => api.delete(`/gst/registrations/${id}`),
};

function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

// TDS Sections API
export const tdsSectionsApi = {
  list: (params?: { return_form?: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/tds/sections', { params }),
  get: (id: string) => api.get(`/tds/sections/${id}`),
  create: (data: unknown) => api.post('/tds/sections', data),
  update: (id: string, data: unknown) => api.put(`/tds/sections/${id}`, data),
  delete: (id: string) => api.delete(`/tds/sections/${id}`),
  getActive: (params?: { as_of_date?: string; is_tcs?: boolean; page?: number; page_size?: number }) =>
    api.get('/tds/sections/active', { params }),
};

// TDS Entries API
export const tdsEntriesApi = {
  list: (params: {
    organization_id: string;
    from_date?: string;
    to_date?: string;
    challan_status?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/tds/entries', { params }),
  get: (id: string) => api.get(`/tds/entries/${id}`),
  create: (data: unknown) => api.post('/tds/entries', data),
  validateThreshold: (data: unknown) => api.post('/tds/entries/validate-threshold', data),
  update: (id: string, data: unknown) => api.put(`/tds/entries/${id}`, data),
  delete: (id: string) => api.delete(`/tds/entries/${id}`),
  getPendingChallans: (params: { organization_id: string; page?: number; page_size?: number }) =>
    api.get('/tds/entries/pending-challans', { params }),
  getByQuarter: (params: { organization_id: string; financial_year: string; quarter: string }) =>
    api.get(`/tds/entries/quarter/${params.financial_year}/${params.quarter}`, { params: { organization_id: params.organization_id } }),
  updateChallan: (id: string, data: unknown) => api.post(`/tds/entries/${id}/challan`, data),
};

// TDS Challans API
export const tdsChallansApi = {
  list: (params: {
    organization_id: string;
    from_date?: string;
    to_date?: string;
    status?: string;
    tds_section_id?: string;
    financial_year_id?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/tds/challans', { params }),
  getSummary: (params: { organization_id: string; financial_year_id?: string }) =>
    api.get('/tds/challans/summary', { params }),
  getDue: (params: { organization_id: string }) => api.get('/tds/challans/due', { params }),
  get: (id: string, includeEntries?: boolean) =>
    api.get(`/tds/challans/${id}`, { params: { include_entries: includeEntries } }),
  create: (data: unknown) => api.post('/tds/challans', data, { headers: idempotencyHeaders() }),
  generate: (data: unknown) => api.post('/tds/challans/generate', data, { headers: idempotencyHeaders() }),
  update: (id: string, data: unknown) => api.put(`/tds/challans/${id}`, data, { headers: idempotencyHeaders() }),
  addEntries: (id: string, data: unknown) => api.post(`/tds/challans/${id}/entries`, data, { headers: idempotencyHeaders() }),
  removeEntries: (id: string, data: unknown) =>
    api.delete(`/tds/challans/${id}/entries`, { data, headers: idempotencyHeaders() }),
  finalize: (id: string) => api.post(`/tds/challans/${id}/finalize`, undefined, { headers: idempotencyHeaders() }),
  recordPayment: (id: string, data: unknown) => api.post(`/tds/challans/${id}/payment`, data, { headers: idempotencyHeaders() }),
  verifyOltas: (id: string, data: unknown) => api.post(`/tds/challans/${id}/verify-oltas`, data, { headers: idempotencyHeaders() }),
  cancel: (id: string, data: unknown) => api.post(`/tds/challans/${id}/cancel`, data, { headers: idempotencyHeaders() }),
};

// TDS Returns API
export const tdsReturnsApi = {
  list: (params: {
    organization_id: string;
    return_type?: string;
    financial_year_id?: string;
    quarter?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/tds/returns', { params }),
  getPending: (params: { organization_id: string }) => api.get('/tds/returns/pending', { params }),
  getDue: (params: { organization_id: string }) => api.get('/tds/returns/due', { params }),
  get: (id: string) => api.get(`/tds/returns/${id}`),
  create: (data: unknown) => api.post('/tds/returns', data),
  update: (id: string, data: unknown) => api.put(`/tds/returns/${id}`, data),
  validate: (id: string) => api.post(`/tds/returns/${id}/validate`),
  generateFile: (id: string, data?: unknown) =>
    api.post(`/tds/returns/${id}/generate-file`, data),
  updateFilingDetails: (id: string, data: unknown) =>
    api.post(`/tds/returns/${id}/filing-details`, data),
  revise: (id: string, data: unknown) => api.post(`/tds/returns/${id}/revise`, data),
};

// TDS Form 16A API
export const tdsForm16AApi = {
  listCertificates: (params: {
    organization_id: string;
    financial_year: string;
    quarter?: string;
  }) => api.get('/tds/form16a/list', { params }),
  getDeductees: (params: { organization_id: string; financial_year: string; quarter: string }) =>
    api.get('/tds/form16a/deductees', { params }),
  generate: (data: unknown) => api.post('/tds/form16a/generate', data),
  generateBulk: (data: unknown) => api.post('/tds/form16a/generate-bulk', data),
  get: (certificateNumber: string, params: { organization_id: string }) =>
    api.get(`/tds/form16a/${certificateNumber}`, { params }),
  download: (certificateNumber: string, params: { organization_id: string }) =>
    api.get(`/tds/form16a/download/${certificateNumber}`, { params }),
};

// Payment Terms API
export const paymentTermsApi = {
  list: (params: { organization_id: string; page?: number; page_size?: number; include_inactive?: boolean }) =>
    api.get('/payment-terms', { params }),
  getActive: (params: { organization_id: string }) =>
    api.get('/payment-terms/active', { params }),
  get: (id: string) => api.get(`/payment-terms/${id}`),
  create: (data: unknown) => api.post('/payment-terms', data),
  update: (id: string, data: unknown) => api.put(`/payment-terms/${id}`, data),
  delete: (id: string) => api.delete(`/payment-terms/${id}`),
};

// Vendors API
export const vendorsApi = {
  list: (params: {
    organization_id: string;
    page?: number;
    page_size?: number;
    include_inactive?: boolean;
    search?: string;
    vendor_type?: string;
  }) => api.get('/vendors', { params }),
  getActive: (params: { organization_id: string }) =>
    api.get('/vendors/active', { params }),
  get: (id: string) => api.get(`/vendors/${id}`),
  generateCode: (params: { organization_id: string }) =>
    api.get('/vendors/generate-code', { params }),
  create: (data: unknown) => api.post('/vendors', data),
  update: (id: string, data: unknown) => api.put(`/vendors/${id}`, data),
  delete: (id: string) => api.delete(`/vendors/${id}`),
};

// Customers API
export const customersApi = {
  list: (params: {
    organization_id: string;
    page?: number;
    page_size?: number;
    include_inactive?: boolean;
    search?: string;
    customer_type?: string;
  }) => api.get('/customers', { params }),
  getActive: (params: { organization_id: string }) =>
    api.get('/customers/active', { params }),
  get: (id: string) => api.get(`/customers/${id}`),
  generateCode: (params: { organization_id: string }) =>
    api.get('/customers/generate-code', { params }),
  create: (data: unknown) => api.post('/customers', data),
  update: (id: string, data: unknown) => api.put(`/customers/${id}`, data),
  delete: (id: string) => api.delete(`/customers/${id}`),
};

// Purchase Bills API
export const purchaseBillsApi = {
  list: (params: {
    organization_id: string;
    page?: number;
    page_size?: number;
    include_inactive?: boolean;
    status?: string;
    payment_status?: string;
    vendor_id?: string;
    from_date?: string;
    to_date?: string;
    search?: string;
  }) => api.get('/purchase-bills', { params }),
  get: (id: string) => api.get(`/purchase-bills/${id}`),
  getUnpaid: (vendorId: string, params: { organization_id: string }) =>
    api.get(`/purchase-bills/unpaid/${vendorId}`, { params }),
  generateNumber: (params: { organization_id: string }) =>
    api.get('/purchase-bills/generate-number', { params }),
  create: (data: unknown) => api.post('/purchase-bills', data),
  update: (id: string, data: unknown) => api.put(`/purchase-bills/${id}`, data),
  delete: (id: string) => api.delete(`/purchase-bills/${id}`),
  submit: (id: string) => api.post(`/purchase-bills/${id}/submit`),
  approve: (id: string) => api.post(`/purchase-bills/${id}/approve`),
  cancel: (id: string, reason: string) =>
    api.post(`/purchase-bills/${id}/cancel`, null, { params: { reason } }),
};

// Sales Invoices API
export const salesInvoicesApi = {
  list: (params: {
    organization_id: string;
    page?: number;
    page_size?: number;
    include_inactive?: boolean;
    status?: string;
    receipt_status?: string;
    customer_id?: string;
    from_date?: string;
    to_date?: string;
    search?: string;
  }) => api.get('/sales-invoices', { params }),
  get: (id: string) => api.get(`/sales-invoices/${id}`),
  getUnreceived: (customerId: string, params: { organization_id: string }) =>
    api.get(`/sales-invoices/unreceived/${customerId}`, { params }),
  generateNumber: (params: { organization_id: string }) =>
    api.get('/sales-invoices/generate-number', { params }),
  create: (data: unknown) => api.post('/sales-invoices', data),
  update: (id: string, data: unknown) => api.put(`/sales-invoices/${id}`, data),
  delete: (id: string) => api.delete(`/sales-invoices/${id}`),
  submit: (id: string) => api.post(`/sales-invoices/${id}/submit`),
  approve: (id: string) => api.post(`/sales-invoices/${id}/approve`),
  cancel: (id: string, reason: string) =>
    api.post(`/sales-invoices/${id}/cancel`, null, { params: { reason } }),
};

// Payments API
export const paymentsApi = {
  list: (params: {
    organization_id: string;
    skip?: number;
    limit?: number;
    search?: string;
    payment_type?: string;
    party_type?: string;
    vendor_id?: string;
    customer_id?: string;
    payment_mode?: string;
    status?: string;
    cheque_status?: string;
    from_date?: string;
    to_date?: string;
    is_posted?: boolean;
    unit_id?: string;
  }) => api.get('/payments', { params }),
  get: (id: string) => api.get(`/payments/${id}`),
  generateNumber: (params: { organization_id: string; payment_type: string }) =>
    api.get('/payments/generate-number', { params }),
  getOutstandingDocuments: (partyType: string, partyId: string, params: { organization_id: string }) =>
    api.get(`/payments/outstanding/${partyType}/${partyId}`, { params }),
  getPendingCheques: (params: {
    organization_id: string;
    party_type?: string;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/payments/pending-cheques', { params }),
  create: (data: unknown) => api.post('/payments', data),
  update: (id: string, data: unknown) => api.put(`/payments/${id}`, data),
  delete: (id: string) => api.delete(`/payments/${id}`),
  submit: (id: string) => api.post(`/payments/${id}/submit`),
  approve: (id: string) => api.post(`/payments/${id}/approve`),
  cancel: (id: string, reason: string) =>
    api.post(`/payments/${id}/cancel`, null, { params: { reason } }),
  updateChequeStatus: (id: string, data: unknown) =>
    api.post(`/payments/${id}/cheque-status`, data),
};

// Bank Reconciliation API
export const bankReconciliationApi = {
  // Bank Statements
  listStatements: (params: {
    bank_account_id: string;
    organization_id: string;
    from_date?: string;
    to_date?: string;
    reconciliation_status?: string;
    transaction_type?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/bank-reconciliation/statements', { params }),
  getStatement: (id: string) => api.get(`/bank-reconciliation/statements/${id}`),
  importStatements: (data: unknown) => api.post('/bank-reconciliation/statements/import', data),
  parseCsvStatement: (formData: FormData) =>
    api.post('/bank-reconciliation/statements/parse-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteStatement: (id: string) => api.delete(`/bank-reconciliation/statements/${id}`),

  // Matching
  matchStatement: (data: { statementId: string; voucherId: string; matchedAmount: number; matchType?: string }) =>
    api.post('/bank-reconciliation/match', data),
  unmatchStatement: (matchId: string) => api.delete(`/bank-reconciliation/match/${matchId}`),
  autoMatch: (params: { bank_account_id: string; from_date: string; to_date: string }) =>
    api.post('/bank-reconciliation/auto-match', null, { params }),

  // Workspace
  getWorkspace: (params: { bank_account_id: string; from_date: string; to_date: string }) =>
    api.get('/bank-reconciliation/workspace', { params }),

  // Reconciliation Sessions
  listReconciliations: (params: {
    bank_account_id: string;
    organization_id: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/bank-reconciliation', { params }),
  getReconciliation: (id: string) => api.get(`/bank-reconciliation/${id}`),
  getLatestReconciliation: (bankAccountId: string) =>
    api.get(`/bank-reconciliation/latest/${bankAccountId}`),
  createReconciliation: (data: unknown) => api.post('/bank-reconciliation', data),
  updateReconciliation: (id: string, data: unknown) => api.put(`/bank-reconciliation/${id}`, data),
  completeReconciliation: (id: string) => api.post(`/bank-reconciliation/${id}/complete`),

  // BRS Report
  getBRSReport: (params: {
    bank_account_id: string;
    reconciliation_date: string;
    from_date: string;
    to_date: string;
    statement_opening_balance: number;
    statement_closing_balance: number;
    book_opening_balance: number;
    book_closing_balance: number;
  }) => api.get('/bank-reconciliation/report/brs', { params }),
};

// AP/AR Aging Reports API
export const agingReportsApi = {
  getAPAgingSummary: (params: {
    organization_id: string;
    as_of_date?: string;
    vendor_id?: string;
  }) => api.get('/ap-ar/aging/ap-summary', { params }),
  getARAgingSummary: (params: {
    organization_id: string;
    as_of_date?: string;
    customer_id?: string;
  }) => api.get('/ap-ar/aging/ar-summary', { params }),
  getAPAgingDetail: (vendorId: string, params: { organization_id: string; as_of_date?: string }) =>
    api.get(`/ap-ar/aging/ap-detail/${vendorId}`, { params }),
  getARAgingDetail: (customerId: string, params: { organization_id: string; as_of_date?: string }) =>
    api.get(`/ap-ar/aging/ar-detail/${customerId}`, { params }),
};

// Financial Reports API
export const reportsApi = {
  getTrialBalance: (params: {
    organization_id: string;
    financial_year_id: string;
    from_date?: string;
    to_date?: string;
    include_zero_balance?: boolean;
  }) => api.get('/reports/trial-balance', { params }),
  getProfitLoss: (params: {
    organization_id: string;
    financial_year_id: string;
    from_date?: string;
    to_date?: string;
  }) => api.get('/reports/profit-loss', { params }),
  getBalanceSheet: (params: {
    organization_id: string;
    financial_year_id: string;
    as_on_date?: string;
  }) => api.get('/reports/balance-sheet', { params }),
  getAccountLedger: (accountId: string, params: { from_date: string; to_date: string }) =>
    api.get(`/reports/account-ledger/${accountId}`, { params }),
  getCashFlowStatement: (params: {
    organization_id: string;
    financial_year_id: string;
    from_date?: string;
    to_date?: string;
  }) => api.get('/reports/cash-flow-statement', { params }),
  getDayBook: (params: {
    organization_id: string;
    from_date: string;
    to_date: string;
    voucher_type_id?: string;
  }) => api.get('/reports/day-book', { params }),
};

// Dashboard API
export const dashboardApi = {
  getSummary: (params: { organization_id: string }) =>
    api.get('/dashboard/summary', { params }),
  getAPSummary: (params: { organization_id: string }) =>
    api.get('/dashboard/ap-summary', { params }),
  getARSummary: (params: { organization_id: string }) =>
    api.get('/dashboard/ar-summary', { params }),
  getCashflow: (params: { organization_id: string }) =>
    api.get('/dashboard/cashflow', { params }),
  getTrends: (params: { organization_id: string; months?: number }) =>
    api.get('/dashboard/trends', { params }),
  getRecentActivity: (params: { organization_id: string; limit?: number }) =>
    api.get('/dashboard/recent-activity', { params }),
  getPendingApprovals: (params: { organization_id: string }) =>
    api.get('/dashboard/pending-approvals', { params }),
};

// Integrations API
export const integrationsApi = {
  // List all integrations for an organization
  list: (params: {
    organization_id: string;
    integration_type?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/integrations', { params }),

  // Get available integration types
  getTypes: () => api.get('/integrations/types'),

  // Get integration by type
  getByType: (integrationType: string, params: {
    organization_id: string;
    provider?: string;
  }) => api.get(`/integrations/by-type/${integrationType}`, { params }),

  // Get single integration config
  get: (configId: string) => api.get(`/integrations/${configId}`),

  // Create new integration
  create: (data: {
    organization_id: string;
    integration_type: string;
    provider: string;
    display_name?: string;
    config_data: Record<string, unknown>;
    sandbox_mode?: boolean;
    base_url?: string;
    sandbox_url?: string;
    webhook_url?: string;
    webhook_secret?: string;
  }) => api.post('/integrations', data),

  // Update integration
  update: (configId: string, data: {
    display_name?: string;
    config_data?: Record<string, unknown>;
    sandbox_mode?: boolean;
    base_url?: string;
    sandbox_url?: string;
    webhook_url?: string;
    webhook_secret?: string;
    is_active?: boolean;
  }) => api.put(`/integrations/${configId}`, data),

  // Delete integration
  delete: (configId: string) => api.delete(`/integrations/${configId}`),

  // Test integration connection
  test: (configId: string) => api.post(`/integrations/${configId}/test`),

  // Get logs for an integration
  getLogs: (configId: string, params?: {
    page?: number;
    page_size?: number;
  }) => api.get(`/integrations/${configId}/logs`, { params }),

  // Get all logs for an organization
  getOrganizationLogs: (params: {
    organization_id: string;
    integration_type?: string;
    from_date?: string;
    to_date?: string;
    success_only?: boolean;
    page?: number;
    page_size?: number;
  }) => api.get('/integrations/logs/organization', { params }),

  // Get log statistics
  getLogStats: (params: {
    organization_id: string;
    integration_type?: string;
    from_date?: string;
    to_date?: string;
  }) => api.get('/integrations/logs/stats', { params }),

  // Get config template
  getTemplate: (integrationType: string, provider: string) =>
    api.get(`/integrations/templates/${integrationType}`, { params: { provider } }),
};

// Fixed Assets API
export const fixedAssetsApi = {
  // Asset Categories
  listCategories: (params: {
    organization_id: string;
    skip?: number;
    limit?: number;
  }) => api.get('/fixed-assets/categories', { params }),
  getCategoryTree: (organizationId: string) =>
    api.get('/fixed-assets/categories/tree', { params: { organization_id: organizationId } }),
  getCategory: (id: string) => api.get(`/fixed-assets/categories/${id}`),
  createCategory: (data: unknown) => api.post('/fixed-assets/categories', data),
  updateCategory: (id: string, data: unknown) => api.put(`/fixed-assets/categories/${id}`, data),
  deleteCategory: (id: string) => api.delete(`/fixed-assets/categories/${id}`),

  // Fixed Assets
  listAssets: (params: {
    organization_id: string;
    category_id?: string;
    location_id?: string;
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/fixed-assets/assets', { params }),
  getAsset: (id: string) => api.get(`/fixed-assets/assets/${id}`),
  createAsset: (data: unknown) => api.post('/fixed-assets/assets', data),
  updateAsset: (id: string, data: unknown) => api.put(`/fixed-assets/assets/${id}`, data),
  deleteAsset: (id: string) => api.delete(`/fixed-assets/assets/${id}`),
  capitalizeAsset: (id: string, data: { put_to_use_date: string; remarks?: string }) =>
    api.post(`/fixed-assets/assets/${id}/capitalize`, data),
  disposeAsset: (id: string, data: {
    disposal_date: string;
    disposal_type: string;
    disposal_value: number;
    remarks?: string;
  }) => api.post(`/fixed-assets/assets/${id}/dispose`, data),
  transferAsset: (id: string, data: {
    transfer_date: string;
    to_location_id?: string;
    to_department_id?: string;
    to_custodian_id?: string;
    reason?: string;
  }) => api.post(`/fixed-assets/assets/${id}/transfer`, data),
  revalueAsset: (id: string, data: {
    revaluation_date: string;
    new_value: number;
    valuer_name?: string;
    valuation_report_number?: string;
    valuation_report_date?: string;
    valuation_method?: string;
    reason?: string;
  }) => api.post(`/fixed-assets/assets/${id}/revalue`, data),
  impairAsset: (id: string, data: {
    impairment_date: string;
    impairment_amount: number;
    reason?: string;
  }) => api.post(`/fixed-assets/assets/${id}/impair`, data),

  // Depreciation
  listDepreciationRuns: (params: {
    organization_id: string;
    skip?: number;
    limit?: number;
  }) => api.get('/fixed-assets/depreciation/runs', { params }),
  getDepreciationRun: (runId: string) =>
    api.get(`/fixed-assets/depreciation/runs/${runId}`),
  runDepreciation: (data: {
    organization_id: string;
    depreciation_period: string;
    remarks?: string;
  }) => api.post('/fixed-assets/depreciation/run', data),
  postDepreciationRun: (runId: string) =>
    api.post(`/fixed-assets/depreciation/runs/${runId}/post`),
  getRunEntries: (runId: string, params?: { skip?: number; limit?: number }) =>
    api.get(`/fixed-assets/depreciation/runs/${runId}/entries`, { params }),
  getAssetDepreciationHistory: (assetId: string, params?: { skip?: number; limit?: number }) =>
    api.get(`/fixed-assets/depreciation/history/${assetId}`, { params }),
  getDepreciationSchedule: (assetId: string, params?: { periods?: number }) =>
    api.get(`/fixed-assets/depreciation/schedule/${assetId}`, { params }),
  reverseDepreciation: (depreciationId: string, data: { reason: string }) =>
    api.post(`/fixed-assets/depreciation/${depreciationId}/reverse`, data),
};

// GSTN Portal API
export const gstnApi = {
  // Session Management
  requestOtp: (data: { gstin: string }) =>
    api.post('/gst/gstn/sessions/request-otp', data),
  verifyOtp: (data: { gstin: string; otp: string }) =>
    api.post('/gst/gstn/sessions/verify-otp', data),
  getSession: (gstin: string) =>
    api.get('/gst/gstn/sessions/status', { params: { gstin } }),

  // Return Filings
  listFilings: (params: {
    gstin: string;
    return_type?: string;
    return_period?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/gst/gstn/returns', { params }),
  getFiling: (filingId: string) => api.get(`/gst/gstn/returns/${filingId}`),

  // GSTR-1 Operations
  generateGstr1: (gstin: string, returnPeriod: string, params?: { regenerate?: boolean }) =>
    api.post(`/gst/gstn/returns/gstr1/generate/${gstin}/${returnPeriod}`, null, { params }),
  getGstr1: (gstin: string, returnPeriod: string) =>
    api.get(`/gst/gstn/returns/gstr1/${gstin}/${returnPeriod}`),
  submitGstr1: (gstin: string, returnPeriod: string) =>
    api.post(`/gst/gstn/returns/gstr1/submit/${gstin}/${returnPeriod}`),
  fileGstr1: (gstin: string, returnPeriod: string, data: { pan: string; otp: string }) =>
    api.post(`/gst/gstn/returns/gstr1/file/${gstin}/${returnPeriod}`, data),

  // GSTR-3B Operations
  generateGstr3b: (gstin: string, returnPeriod: string, params?: { regenerate?: boolean }) =>
    api.post(`/gst/gstn/returns/gstr3b/generate/${gstin}/${returnPeriod}`, null, { params }),
  getGstr3b: (gstin: string, returnPeriod: string) =>
    api.get(`/gst/gstn/returns/gstr3b/${gstin}/${returnPeriod}`),
  submitGstr3b: (gstin: string, returnPeriod: string) =>
    api.post(`/gst/gstn/returns/gstr3b/submit/${gstin}/${returnPeriod}`),
  fileGstr3b: (gstin: string, returnPeriod: string, data: { pan: string; otp: string }) =>
    api.post(`/gst/gstn/returns/gstr3b/file/${gstin}/${returnPeriod}`, data),

  // GSTR-2B Operations
  fetchGstr2b: (gstin: string, returnPeriod: string) =>
    api.post(`/gst/gstn/gstr2b/fetch/${gstin}/${returnPeriod}`),
  getGstr2b: (gstin: string, returnPeriod: string, params?: { page?: number; page_size?: number }) =>
    api.get(`/gst/gstn/gstr2b/${gstin}/${returnPeriod}`, { params }),
  getGstr2bSummary: (gstin: string, returnPeriod: string) =>
    api.get(`/gst/gstn/gstr2b/summary/${gstin}/${returnPeriod}`),

  // ITC Reconciliation
  runReconciliation: (gstin: string, returnPeriod: string) =>
    api.post(`/gst/gstn/itc/reconcile/${gstin}/${returnPeriod}`),
  getMismatches: (params: {
    gstin: string;
    return_period: string;
    mismatch_type?: string;
    resolution_status?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/gst/gstn/itc/mismatches', { params }),
  resolveMismatch: (mismatchId: string, data: { resolution_status: string; resolution_notes?: string }) =>
    api.post(`/gst/gstn/itc/mismatches/${mismatchId}/resolve`, data),

  // Statistics
  getStats: (params: { gstin: string; return_period?: string }) =>
    api.get('/gst/gstn/statistics', { params }),
};

// HRIS API
export const hrisApi = {
  // Employees
  listEmployees: (params: {
    organization_id?: string;
    department_id?: string;
    designation_id?: string;
    employment_status?: string;
    employment_type?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/hris/employees', { params }),
  getEmployee: (id: string) => api.get(`/hris/employees/${id}`),
  createEmployee: (data: unknown) => api.post('/hris/employees', data),
  updateEmployee: (id: string, data: unknown) => api.put(`/hris/employees/${id}`, data),
  deleteEmployee: (id: string) => api.delete(`/hris/employees/${id}`),

  // Employee Documents
  listEmployeeDocuments: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/documents`),
  createEmployeeDocument: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/documents`, data),
  updateEmployeeDocument: (employeeId: string, documentId: string, data: unknown) =>
    api.put(`/hris/employees/${employeeId}/documents/${documentId}`, data),
  deleteEmployeeDocument: (employeeId: string, documentId: string) =>
    api.delete(`/hris/employees/${employeeId}/documents/${documentId}`),

  // Employee Family
  listEmployeeFamily: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/family`),
  createEmployeeFamily: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/family`, data),
  updateEmployeeFamily: (employeeId: string, familyId: string, data: unknown) =>
    api.put(`/hris/employees/${employeeId}/family/${familyId}`, data),
  deleteEmployeeFamily: (employeeId: string, familyId: string) =>
    api.delete(`/hris/employees/${employeeId}/family/${familyId}`),

  // Employee Bank Accounts
  listEmployeeBankAccounts: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/bank-accounts`),
  createEmployeeBankAccount: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/bank-accounts`, data),
  updateEmployeeBankAccount: (employeeId: string, accountId: string, data: unknown) =>
    api.put(`/hris/employees/${employeeId}/bank-accounts/${accountId}`, data),
  deleteEmployeeBankAccount: (employeeId: string, accountId: string) =>
    api.delete(`/hris/employees/${employeeId}/bank-accounts/${accountId}`),

  // Employee Education
  listEmployeeEducation: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/education`),
  createEmployeeEducation: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/education`, data),
  updateEmployeeEducation: (employeeId: string, educationId: string, data: unknown) =>
    api.put(`/hris/employees/${employeeId}/education/${educationId}`, data),
  deleteEmployeeEducation: (employeeId: string, educationId: string) =>
    api.delete(`/hris/employees/${employeeId}/education/${educationId}`),

  // Employee Experience
  listEmployeeExperience: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/experience`),
  createEmployeeExperience: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/experience`, data),
  updateEmployeeExperience: (employeeId: string, experienceId: string, data: unknown) =>
    api.put(`/hris/employees/${employeeId}/experience/${experienceId}`, data),
  deleteEmployeeExperience: (employeeId: string, experienceId: string) =>
    api.delete(`/hris/employees/${employeeId}/experience/${experienceId}`),

  // Employee Statutory
  getEmployeeStatutory: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/statutory`),
  createOrUpdateEmployeeStatutory: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/statutory`, data),

  // Employee Lifecycle
  listEmployeeLifecycle: (employeeId: string) =>
    api.get(`/hris/employees/${employeeId}/lifecycle`),
  createEmployeeLifecycle: (employeeId: string, data: unknown) =>
    api.post(`/hris/employees/${employeeId}/lifecycle`, data),

  // Shifts
  listShifts: (params: {
    organization_id: string;
    active_only?: boolean;
  }) => api.get('/hris/shifts', { params }),
  getShift: (id: string) => api.get(`/hris/shifts/${id}`),
  createShift: (data: unknown) => api.post('/hris/shifts', data),
  updateShift: (id: string, data: unknown) => api.put(`/hris/shifts/${id}`, data),
  deleteShift: (id: string) => api.delete(`/hris/shifts/${id}`),

  // Holiday Calendars
  listHolidayCalendars: (params: {
    organization_id: string;
    year?: number;
  }) => api.get('/hris/holiday-calendars', { params }),
  getHolidayCalendar: (id: string) => api.get(`/hris/holiday-calendars/${id}`),
  createHolidayCalendar: (data: unknown) => api.post('/hris/holiday-calendars', data),
  updateHolidayCalendar: (id: string, data: unknown) => api.put(`/hris/holiday-calendars/${id}`, data),
  deleteHolidayCalendar: (id: string) => api.delete(`/hris/holiday-calendars/${id}`),

  // Holidays
  createHoliday: (calendarId: string, data: unknown) =>
    api.post(`/hris/holiday-calendars/${calendarId}/holidays`, data),
  updateHoliday: (calendarId: string, holidayId: string, data: unknown) =>
    api.put(`/hris/holiday-calendars/${calendarId}/holidays/${holidayId}`, data),
  deleteHoliday: (calendarId: string, holidayId: string) =>
    api.delete(`/hris/holiday-calendars/${calendarId}/holidays/${holidayId}`),

  // Leave Types
  listLeaveTypes: (params: {
    organization_id: string;
    active_only?: boolean;
  }) => api.get('/hris/leaves/types', { params }),
  getLeaveType: (id: string) => api.get(`/hris/leaves/types/${id}`),
  createLeaveType: (data: unknown) => api.post('/hris/leaves/types', data),
  updateLeaveType: (id: string, data: unknown) => api.put(`/hris/leaves/types/${id}`, data),
  deleteLeaveType: (id: string) => api.delete(`/hris/leaves/types/${id}`),

  // Leave Balances
  getLeaveBalances: (employeeId: string, year: number) =>
    api.get(`/hris/leaves/balances/${employeeId}`, { params: { year } }),
  createOrUpdateLeaveBalance: (data: unknown) =>
    api.post('/hris/leaves/balances', data),
  initializeLeaveBalances: (employeeId: string, organizationId: string, year: number) =>
    api.post(`/hris/leaves/balances/initialize/${employeeId}`, null, {
      params: { organization_id: organizationId, year },
    }),

  // Leave Applications
  listLeaveApplications: (params: {
    organization_id?: string;
    employee_id?: string;
    leave_type_id?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    department_id?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/hris/leaves/applications', { params }),
  getPendingLeaveApprovals: (params?: { skip?: number; limit?: number }) =>
    api.get('/hris/leaves/applications/pending-approval', { params }),
  getLeaveApplication: (id: string) => api.get(`/hris/leaves/applications/${id}`),
  createLeaveApplication: (data: unknown) => api.post('/hris/leaves/applications', data),
  updateLeaveApplication: (id: string, data: unknown) => api.put(`/hris/leaves/applications/${id}`, data),
  approveLeaveApplication: (id: string, remarks?: string) =>
    api.post(`/hris/leaves/applications/${id}/approve`, { remarks }),
  rejectLeaveApplication: (id: string, reason: string) =>
    api.post(`/hris/leaves/applications/${id}/reject`, { reason }),
  cancelLeaveApplication: (id: string, reason: string) =>
    api.post(`/hris/leaves/applications/${id}/cancel`, { reason }),

  // Attendance
  listAttendance: (params: {
    organization_id?: string;
    employee_id?: string;
    department_id?: string;
    shift_id?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    is_processed?: boolean;
    is_locked?: boolean;
    skip?: number;
    limit?: number;
  }) => api.get('/hris/attendance', { params }),
  getAttendance: (id: string) => api.get(`/hris/attendance/${id}`),
  updateAttendance: (id: string, data: unknown) => api.put(`/hris/attendance/${id}`, data),

  // Attendance Punches
  recordPunch: (data: unknown) => api.post('/hris/attendance/punch', data),
  getPunches: (employeeId: string, punchDate: string) =>
    api.get(`/hris/attendance/punches/${employeeId}`, { params: { punch_date: punchDate } }),

  // Attendance Regularization
  listRegularizations: (params: {
    organization_id?: string;
    employee_id?: string;
    department_id?: string;
    status?: string;
    request_type?: string;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/hris/attendance/regularizations', { params }),
  getRegularization: (id: string) => api.get(`/hris/attendance/regularizations/${id}`),
  createRegularization: (data: unknown) => api.post('/hris/attendance/regularizations', data),
  approveRegularization: (id: string, remarks?: string) =>
    api.post(`/hris/attendance/regularizations/${id}/approve`, { remarks }),
  rejectRegularization: (id: string, reason: string) =>
    api.post(`/hris/attendance/regularizations/${id}/reject`, { reason }),

  // Attendance Processing
  processDailyAttendance: (data: {
    organization_id: string;
    attendance_date: string;
    employee_ids?: string[];
  }) => api.post('/hris/attendance/process/daily', data),
  processMonthlyAttendance: (data: {
    organization_id: string;
    year: number;
    month: number;
    employee_ids?: string[];
  }) => api.post('/hris/attendance/process/monthly', data),
  lockAttendance: (data: {
    organization_id: string;
    year: number;
    month: number;
  }) => api.post('/hris/attendance/lock', data),

  // Separation and Full & Final
  listSeparations: (params?: {
    organization_id?: string;
    status?: string;
    separation_type?: string;
    employee_id?: string;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/hris/separation', { params }),
  getSeparation: (id: string) => api.get(`/hris/separation/${id}`),
  initiateSeparation: (data: {
    employee_id: string;
    separation_type: string;
    requested_last_working_date: string;
    reason_category?: string;
    reason_detail?: string;
    resignation_letter_path?: string;
  }) => api.post('/hris/separation', data),
  approveSeparation: (id: string, data: { approved_last_working_date: string; remarks?: string }) =>
    api.post(`/hris/separation/${id}/approve`, data),
  rejectSeparation: (id: string, rejectionReason: string) =>
    api.post(`/hris/separation/${id}/reject`, { rejection_reason: rejectionReason }),
  withdrawSeparation: (id: string, reason?: string) =>
    api.post(`/hris/separation/${id}/withdraw`, { reason }),
  getClearanceStatus: (separationId: string) =>
    api.get(`/hris/separation/${separationId}/clearance`),
  calculateFnF: (
    separationId: string,
    data?: {
      include_gratuity?: boolean;
      include_leave_encashment?: boolean;
      additional_earnings?: Record<string, number>;
      additional_deductions?: Record<string, number>;
    },
  ) => api.post(`/hris/separation/${separationId}/fnf/calculate`, data ?? {}),
  getFnF: (separationId: string) => api.get(`/hris/separation/${separationId}/fnf`),
  approveFnF: (fnfId: string, remarks?: string) =>
    api.post(`/hris/separation/fnf/${fnfId}/approve`, null, { params: { remarks } }),
  payFnF: (
    fnfId: string,
    data: { payment_date: string; payment_mode: string; payment_reference: string },
  ) => api.post(`/hris/separation/fnf/${fnfId}/pay`, data),
};

// Default export for convenience
export default api;
