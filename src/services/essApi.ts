/**
 * ESS Portal API Service
 * Handles all Employee Self-Service portal API calls
 */

import axios from 'axios';

import { useEssAuthStore } from '@/stores/essAuthStore';
import type {
  ESSDashboard,
  Payslip,
  YTDSummary,
  ReimbursementSummary,
  TaxCalculation,
} from '@/types/ess';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

function getCurrentIndianFinancialYear() {
  const today = new Date();
  const startYear = today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1;
  const endYear = String((startYear + 1) % 100).padStart(2, '0');
  return `${startYear}-${endYear}`;
}

api.interceptors.request.use((config) => {
  const token = useEssAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !String(originalRequest.url ?? '').includes('/ess/auth/refresh')
    ) {
      originalRequest._retry = true;
      const refreshToken = useEssAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/ess/auth/refresh`, {
            refreshToken,
          });
          useEssAuthStore
            .getState()
            .setSession(
              response.data.accessToken,
              response.data.refreshToken,
              response.data.user,
            );
          originalRequest.headers.Authorization = `Bearer ${response.data.accessToken}`;
          return api(originalRequest);
        } catch (_refreshError) {
          useEssAuthStore.getState().clear();
          window.location.href = '/ess/login';
        }
      }
    }
    return Promise.reject(error);
  },
);

// Backend responses come in different shapes between phases of the ESS rollout;
// each normalizer is defensive — it accepts a loose payload and coerces it to
// the shape the UI expects.
type RawPayload = Record<string, unknown>;

function pickNumber(v: unknown, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function pickString(v: unknown, fallback = ''): string {
  return v == null ? fallback : String(v);
}

function asObject(v: unknown): RawPayload {
  return v && typeof v === 'object' ? (v as RawPayload) : {};
}

function normalizePayslip(raw: RawPayload): Payslip {
  return {
    ...raw,
    month: raw.month ?? raw.pay_period ?? '',
    gross_salary: raw.gross_salary ?? raw.total_earnings ?? 0,
    tax_deduction: raw.tax_deduction ?? raw.tax_deducted ?? 0,
    payment_status: raw.payment_status ?? raw.status ?? 'GENERATED',
  } as unknown as Payslip;
}

function normalizeYtdSummary(raw: RawPayload): YTDSummary {
  return {
    ...raw,
    total_earnings: raw.total_earnings ?? raw.total_gross ?? 0,
    total_net_pay: raw.total_net_pay ?? raw.total_net ?? 0,
    total_tax_deducted: raw.total_tax_deducted ?? raw.total_tax ?? 0,
    total_pf_contribution: raw.total_pf_contribution ?? 0,
    months_paid: raw.months_paid ?? raw.months_processed ?? 0,
    breakdown: raw.breakdown ?? { earnings: {}, deductions: {} },
  } as unknown as YTDSummary;
}

interface LeaveBalanceItem {
  code?: string;
  balance?: number | string;
}

function normalizeDashboard(raw: RawPayload): ESSDashboard {
  const leaveBalances: LeaveBalanceItem[] = Array.isArray(raw.leave_balance)
    ? (raw.leave_balance as LeaveBalanceItem[])
    : [];
  const leaveByCode = leaveBalances.reduce(
    (acc: Record<string, number>, leave: LeaveBalanceItem) => {
      acc[pickString(leave.code).toUpperCase()] = pickNumber(leave.balance);
      return acc;
    },
    {},
  );
  const attendance = asObject(raw.attendance_this_month);
  const latestPayslip = asObject(raw.latest_payslip);
  const employee = asObject(raw.employee);

  return {
    ...raw,
    employee: {
      ...employee,
      employee_code: employee.employee_code ?? employee.code ?? '',
      name: employee.name ?? 'Employee',
    },
    attendance: raw.attendance ?? {
      present_days: attendance.present ?? 0,
      absent_days: attendance.absent ?? 0,
      leave_days: attendance.leave ?? 0,
      wfh_days: attendance.work_from_home ?? 0,
      current_month: attendance.month ?? '',
    },
    leave_balance: {
      casual_leave: leaveByCode.CL ?? 0,
      sick_leave: leaveByCode.SL ?? 0,
      earned_leave: leaveByCode.EL ?? leaveByCode.PL ?? 0,
      total_available: leaveBalances.reduce(
        (sum: number, leave: LeaveBalanceItem) => sum + pickNumber(leave.balance),
        0,
      ),
    },
    pending_actions: raw.pending_actions ?? {
      pending_claims: 0,
      pending_tickets: 0,
      pending_regularizations: 0,
      pending_declarations: raw.pending_requests ?? 0,
    },
    recent_payslip:
      raw.recent_payslip ??
      (Object.keys(latestPayslip).length
        ? {
            month: latestPayslip.period ?? '',
            net_salary: latestPayslip.net ?? 0,
            payslip_id: latestPayslip.id ?? '',
          }
        : undefined),
    announcements: raw.announcements ?? [],
  } as unknown as ESSDashboard;
}

function listResponse<T extends { data: unknown }>(response: T) {
  const data = response.data;
  const items = Array.isArray(data)
    ? data
    : ((data as { items?: unknown[] } | null | undefined)?.items ?? []);
  return {
    ...response,
    data: { items },
  };
}

function normalizeReimbursementSummary(raw: RawPayload): ReimbursementSummary {
  const byStatus = asObject(raw.by_status);
  return {
    ...raw,
    total_claimed_amount: raw.total_claimed_amount ?? raw.total_claimed ?? 0,
    total_approved_amount: raw.total_approved_amount ?? raw.total_approved ?? 0,
    total_paid_amount: raw.total_paid_amount ?? raw.total_paid ?? 0,
    approved_claims: raw.approved_claims ?? pickNumber(byStatus.APPROVED),
    rejected_claims: raw.rejected_claims ?? pickNumber(byStatus.REJECTED),
    by_category: raw.by_category ?? {},
  } as unknown as ReimbursementSummary;
}

function normalizeTaxCalculation(raw: RawPayload): TaxCalculation {
  return {
    ...raw,
    gross_income: raw.gross_income ?? raw.gross_salary ?? 0,
    standard_deduction: raw.standard_deduction ?? 0,
    chapter_vi_a_deductions: raw.chapter_vi_a_deductions ?? raw.total_deductions ?? 0,
    hra_exemption: raw.hra_exemption ?? 0,
    lta_exemption: raw.lta_exemption ?? 0,
    other_exemptions: raw.other_exemptions ?? 0,
    education_cess: raw.education_cess ?? raw.cess ?? 0,
    total_tax_liability: raw.total_tax_liability ?? raw.total_tax ?? 0,
    breakdown: raw.breakdown ?? { deductions_by_section: {}, tax_slabs: [] },
  } as unknown as TaxCalculation;
}

export interface ESSAssignedAsset {
  id: string;
  assetCode: string;
  assetName: string;
  category: string;
  status: string;
  serialNumber?: string | null;
  assignedDate: string;
  location?: string | null;
  department?: string | null;
  totalCost: number;
  warrantyExpiryDate?: string | null;
  insuranceExpiryDate?: string | null;
  returnRequired: boolean;
}

export interface ESSAssignedAssetsResponse {
  items: ESSAssignedAsset[];
  totalAssets: number;
  totalAssetValue: number;
}

export interface ESSTrainingSummary {
  completedPrograms: number;
  upcomingPrograms: number;
  mandatoryPrograms: number;
  feedbackPending: number;
  totalHoursCompleted: number;
}

export interface ESSTrainingProgram {
  programId: string;
  programCode: string;
  title: string;
  category: string;
  mode: string;
  trainerName: string;
  startDate: string;
  endDate: string;
  durationHours: number;
  location: string;
  status: string;
  nominationStatus: string;
  attendanceMarked: boolean;
  feedbackSubmitted: boolean;
  certificateProvided: boolean;
}

export interface ESSTrainingListResponse {
  summary: ESSTrainingSummary;
  items: ESSTrainingProgram[];
}

export interface ESSTrainingFeedbackDetail {
  id: string;
  overallRating: number;
  contentRating: number;
  trainerRating: number;
  facilitiesRating: number;
  relevanceRating: number;
  wouldRecommend: boolean;
  strengths?: string | null;
  improvements?: string | null;
  comments?: string | null;
  submittedOn: string;
}

export interface ESSTrainingDetailResponse {
  programId: string;
  programCode: string;
  title: string;
  description: string;
  category: string;
  mode: string;
  trainerType: string;
  trainerName: string;
  trainerContact?: string | null;
  startDate: string;
  endDate: string;
  durationHours: number;
  location: string;
  isMandatory: boolean;
  certificateProvided: boolean;
  nominationStatus: string;
  attendanceMarked: boolean;
  feedback?: ESSTrainingFeedbackDetail | null;
}

export interface ESSPerformanceGoal {
  id: string;
  employeeId: string;
  goalNumber: number;
  title: string;
  description?: string | null;
  category?: string | null;
  weightage: number;
  targetValue?: string | null;
  measurementCriteria?: string | null;
  startDate?: string | null;
  dueDate?: string | null;
  status: string;
  progressPercent: number;
  achievementValue?: string | null;
  selfRating?: number | null;
  selfComments?: string | null;
  managerRating?: number | null;
  managerComments?: string | null;
  finalRating?: number | null;
}

export interface ESSPerformancePacket {
  appraisal?: {
    cycle: {
      id: string;
      code: string;
      name: string;
      cycleType: string;
      startDate: string;
      endDate: string;
      goalSettingEnd?: string | null;
      selfAppraisalEnd?: string | null;
      managerReviewEnd?: string | null;
      status: string;
      eligibleEmployees: number;
      completedAppraisals: number;
      pendingSelfAppraisal: number;
      pendingManagerReview: number;
      ratingScale: number;
      weightageGoals: number;
      weightageCompetencies: number;
      allowSelfRating: boolean;
      allowPeerFeedback: boolean;
    };
    employee: {
      employeeId: string;
      employeeCode: string;
      employeeName: string;
      department?: string | null;
      designation?: string | null;
      reviewerName?: string | null;
      status: string;
      goalCount: number;
      submittedGoals: number;
      completedGoals: number;
      overallRating?: number | null;
      finalGrade?: string | null;
    };
    appraisal: {
      id: string;
      status: string;
      goalRating?: number | null;
      competencyRating?: number | null;
      overallRating?: number | null;
      finalGrade?: string | null;
      selfSummary?: string | null;
      selfAchievements?: string | null;
      selfChallenges?: string | null;
      selfDevelopmentAreas?: string | null;
      employeeComments?: string | null;
      managerSummary?: string | null;
      managerImprovements?: string | null;
      managerRecommendations?: string | null;
      calibrationNotes?: string | null;
    };
    goals: ESSPerformanceGoal[];
  } | null;
}

export interface ESSPerformanceSelfAssessmentPayload {
  goalId: string;
  selfRating: number;
  selfProgress: number;
  selfComments: string;
  achievementValue?: string;
}

export interface ESSPerformanceSelfAppraisalPayload {
  goals: ESSPerformanceSelfAssessmentPayload[];
  competencyRating: number;
  selfSummary: string;
  selfAchievements: string;
  selfChallenges?: string;
  selfDevelopmentAreas: string;
  employeeComments?: string;
}

export interface AttendanceSummaryResponse {
  month: string;
  workingDays: number;
  present: number;
  absent: number;
  leave: number;
  holiday: number;
  halfDay: number;
  workFromHome: number;
}

export interface AttendanceRecordRow {
  date: string;
  status: string;
  inTime?: string | null;
  outTime?: string | null;
  workingHours: number;
  shift?: string | null;
}

export interface AttendanceRecordsResponse {
  items: AttendanceRecordRow[];
}

export interface AttendanceRegularizationRow {
  id: string;
  attendanceDate: string;
  requestType: string;
  reason: string;
  status: string;
  approvedBy?: string | null;
  approvedAt?: string | null;
  approverRemarks?: string | null;
  rejectedAt?: string | null;
  rejectionReason?: string | null;
  createdAt: string;
}

export interface RegularizationTypeOption {
  code: string;
  label: string;
  description: string;
}

export interface ESSLeaveTypeOption {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  annualQuota: number;
  availableBalance: number;
  used: number;
  documentRequired: boolean;
  documentRequiredAfterDays?: number | null;
  halfDayAllowed: boolean;
}

export interface ESSLeaveBalanceRow {
  leaveTypeId: string;
  code: string;
  name: string;
  openingBalance: number;
  accrued: number;
  carryForward: number;
  used: number;
  lapsed: number;
  availableBalance: number;
}

export interface ESSLeaveApplication {
  id: string;
  applicationNumber: string;
  leaveTypeId: string;
  leaveTypeCode?: string | null;
  leaveTypeName?: string | null;
  fromDate: string;
  toDate: string;
  isHalfDay: boolean;
  halfDayType?: string | null;
  totalDays: number;
  workingDays: number;
  reason: string;
  contactNumber?: string | null;
  contactAddress?: string | null;
  attachments?: string[] | null;
  status: string;
  approverRemarks?: string | null;
  rejectionReason?: string | null;
  cancellationReason?: string | null;
  approvedAt?: string | null;
  rejectedAt?: string | null;
  cancelledAt?: string | null;
  createdAt: string;
}

export interface ESSLeaveSummaryResponse {
  balances: ESSLeaveBalanceRow[];
  applications: ESSLeaveApplication[];
  leaveTypes: ESSLeaveTypeOption[];
  pendingCount: number;
  approvedThisYear: number;
}

// ==================== Auth APIs ====================

export const essAuthApi = {
  /**
   * Send OTP to mobile number
   */
  sendOtp: (data: { mobile: string; purpose?: string }) => api.post('/ess/auth/send-otp', data),

  /**
   * Verify OTP and login
   */
  login: (data: { mobile: string; otp: string; deviceInfo?: Record<string, unknown> }) =>
    api.post('/ess/auth/login', data),

  /**
   * Refresh access token
   */
  refresh: (data: { refreshToken: string }) => api.post('/ess/auth/refresh', data),

  /**
   * Logout current session
   */
  logout: () => api.post('/ess/auth/logout'),

  /**
   * Get active sessions
   */
  getSessions: () => api.get('/ess/auth/sessions'),

  /**
   * Revoke a specific session
   */
  revokeSession: (sessionId: string) => api.delete(`/ess/auth/sessions/${sessionId}`),

  /**
   * Register device for push notifications
   */
  registerDevice: (data: {
    device_uuid: string;
    device_name: string;
    device_type?: string;
    fcm_token?: string;
  }) => api.post('/ess/auth/devices', { device_type: 'web', ...data }),
};

// ==================== Profile APIs ====================

export const essProfileApi = {
  /**
   * Get employee dashboard summary
   */
  getDashboard: () =>
    api
      .get('/ess/profile/dashboard')
      .then((response) => ({ ...response, data: normalizeDashboard(response.data) })),

  /**
   * Get employee profile
   */
  getProfile: () => api.get('/ess/profile/me'),

  /**
   * Request profile update
   */
  requestUpdate: (data: {
    update_type: string;
    requested_values: Record<string, unknown>;
    change_reason?: string;
    attachments?: unknown;
  }) => api.post('/ess/profile/update-requests', data),

  /**
   * Get profile update requests
   */
  getUpdateRequests: (params?: { status?: string }) =>
    api.get('/ess/profile/update-requests', { params }),

  /**
   * Get payslips
   */
  getPayslips: (params?: { year?: number; limit?: number }) =>
    api
      .get('/ess/profile/payslips', {
        params: {
          financial_year: params?.year ? `${params.year}-${params.year + 1}` : undefined,
          limit: params?.limit,
        },
      })
      .then((response) => ({
        ...response,
        data: {
          items: Array.isArray(response.data)
            ? (response.data as RawPayload[]).map(normalizePayslip)
            : [],
        },
      })),

  /**
   * Download payslip PDF
   */
  downloadPayslip: (payslipId: string) =>
    api.get(`/ess/profile/payslips/${payslipId}/download`, { responseType: 'blob' }),

  /**
   * Get YTD salary summary
   */
  getYtdSummary: (financialYear?: string) =>
    api
      .get('/ess/profile/ytd-summary', { params: { financial_year: financialYear } })
      .then((response) => ({ ...response, data: normalizeYtdSummary(response.data) })),

  /**
   * Get leave balance
   */
  getLeaveBalance: () => api.get('/ess/profile/leave-balance'),

  /**
   * Get attendance summary
   */
  getAttendanceRecords: (params: { fromDate: string; toDate: string }) =>
    api.get<AttendanceRecordsResponse>('/ess/profile/attendance', {
      params: {
        from_date: params.fromDate,
        to_date: params.toDate,
      },
    }),

  getAttendanceSummary: (month: string) =>
    api.get<AttendanceSummaryResponse>('/ess/profile/attendance/summary', {
      params: { month },
    }),
};

// ==================== Reimbursement APIs ====================

export const essReimbursementApi = {
  /**
   * Get reimbursement categories
   */
  getCategories: () => api.get('/ess/reimbursements/categories'),

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
  }) => api.get('/ess/reimbursements', { params }).then(listResponse),

  /**
   * Get claim details
   */
  getClaim: (claimId: string) => api.get(`/ess/reimbursements/${claimId}`),

  /**
   * Create new claim
   */
  createClaim: (data: {
    category_id?: string;
    claim_type: string;
    expense_from: string;
    expense_to: string;
    description: string;
    claimed_amount: number;
    purpose?: string;
  }) => api.post('/ess/reimbursements', data),

  /**
   * Update claim
   */
  updateClaim: (claimId: string, data: Record<string, unknown>) =>
    api.patch(`/ess/reimbursements/${claimId}`, data),

  /**
   * Delete draft claim
   */
  deleteClaim: (claimId: string) => api.delete(`/ess/reimbursements/${claimId}`),

  /**
   * Add line item to claim
   */
  addLineItem: (
    claimId: string,
    data: {
      expense_date: string;
      description: string;
      amount: number;
      bill_number?: string;
      bill_date?: string;
      vendor_name?: string;
    },
  ) => api.post(`/ess/reimbursements/${claimId}/items`, data),

  /**
   * Update line item
   */
  updateLineItem: (claimId: string, itemId: string, data: Record<string, unknown>) =>
    api.put(`/ess/reimbursements/${claimId}/items/${itemId}`, data),

  /**
   * Delete line item
   */
  deleteLineItem: (claimId: string, itemId: string) =>
    api.delete(`/ess/reimbursements/${claimId}/items/${itemId}`),

  /**
   * Submit claim for approval
   */
  submitClaim: (claimId: string) => api.post(`/ess/reimbursements/${claimId}/submit`),

  /**
   * Get claim summary
   */
  getSummary: () =>
    api
      .get('/ess/reimbursements/summary')
      .then((response) => ({ ...response, data: normalizeReimbursementSummary(response.data) })),
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
  }) => api.get('/ess/helpdesk', { params }).then(listResponse),

  /**
   * Get ticket details
   */
  getTicket: (ticketId: string) => api.get(`/ess/helpdesk/${ticketId}`),

  /**
   * Create new ticket
   */
  createTicket: (data: {
    subject: string;
    description: string;
    category_type: string;
    category_id?: string;
    priority?: string;
    attachments?: unknown;
  }) => api.post('/ess/helpdesk', data),

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
  getSummary: () => api.get('/ess/helpdesk/summary'),
};

// ==================== IT Declaration APIs ====================

export const essITDeclarationApi = {
  /**
   * Get IT declaration sections
   */
  getSections: (_financialYear?: string, taxRegime = 'OLD') =>
    api.get('/ess/it-declaration/sections', { params: { tax_regime: taxRegime } }),

  /**
   * Get current declaration
   */
  getDeclaration: (financialYear = getCurrentIndianFinancialYear(), taxRegime = 'OLD') =>
    api.post(`/ess/it-declaration/${financialYear}`, null, { params: { tax_regime: taxRegime } }),

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
    api.post(`/ess/it-declaration/${data.financial_year}`, null, {
      params: { tax_regime: data.tax_regime },
    }),

  /**
   * Add declaration item
   */
  addItem: (
    declarationId: string,
    data: {
      section_code: string;
      particular: string;
      declared_amount: number;
      investment_date?: string;
      policy_number?: string;
      institution_name?: string;
    },
  ) => api.post(`/ess/it-declaration/${declarationId}/items`, data),

  /**
   * Update declaration item
   */
  updateItem: (declarationId: string, itemId: string, data: Record<string, unknown>) =>
    api.patch(`/ess/it-declaration/${declarationId}/items/${itemId}`, data),

  /**
   * Delete declaration item
   */
  deleteItem: (declarationId: string, itemId: string) =>
    api.delete(`/ess/it-declaration/${declarationId}/items/${itemId}`),

  /**
   * Add HRA receipt
   */
  addHRAReceipt: (
    declarationId: string,
    data: {
      month: string;
      rent_amount: number;
      receipt_number?: string;
    },
  ) => api.post(`/ess/it-declaration/${declarationId}/hra-receipts`, data),

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
  calculateTax: (
    declarationId: string,
    data: { gross_salary?: number; other_income?: number } = {},
  ) =>
    api
      .post(`/ess/it-declaration/${declarationId}/calculate-tax`, {
        gross_salary: data.gross_salary ?? 0,
        other_income: data.other_income ?? 0,
      })
      .then((response) => ({ ...response, data: normalizeTaxCalculation(response.data) })),
};

// ==================== Attendance Regularization APIs ====================

export const essAttendanceApi = {
  getRegularizationTypes: () =>
    api
      .get<RegularizationTypeOption[]>('/ess/attendance/regularization-types')
      .then((response) => response.data),

  /**
   * Get regularization requests
   */
  getRegularizations: (params?: {
    status?: string;
    fromDate?: string;
    toDate?: string;
    limit?: number;
    offset?: number;
  }) =>
    api
      .get<AttendanceRegularizationRow[]>('/ess/attendance/regularizations', {
        params: {
          status: params?.status,
          fromDate: params?.fromDate,
          toDate: params?.toDate,
          limit: params?.limit,
          offset: params?.offset,
        },
      })
      .then((response) => response.data),

  /**
   * Create regularization request
   */
  createRegularization: (data: {
    attendanceDate: string;
    requestType: string;
    requestedFirstIn?: string;
    requestedLastOut?: string;
    reason: string;
  }) =>
    api
      .post<AttendanceRegularizationRow>('/ess/attendance/regularizations', {
        attendanceDate: data.attendanceDate,
        requestType: data.requestType,
        requestedFirstIn: data.requestedFirstIn,
        requestedLastOut: data.requestedLastOut,
        reason: data.reason,
      })
      .then((response) => response.data),

  getAttendanceSummary: (month: string) =>
    api
      .get<AttendanceSummaryResponse>('/ess/attendance/summary', { params: { month } })
      .then((response) => response.data),
  getAttendanceRecords: (params: { fromDate: string; toDate: string }) =>
    api
      .get<AttendanceRecordsResponse>('/ess/attendance/records', {
        params: { fromDate: params.fromDate, toDate: params.toDate },
      })
      .then((response) => response.data),
};

export const essLeaveApi = {
  getSummary: (year?: number) =>
    api
      .get<ESSLeaveSummaryResponse>('/ess/leave/summary', { params: { year } })
      .then((response) => response.data),

  getApplications: (params?: {
    status?: string;
    fromDate?: string;
    toDate?: string;
    limit?: number;
    offset?: number;
  }) =>
    api
      .get<ESSLeaveApplication[]>('/ess/leave/applications', { params })
      .then((response) => response.data),

  createApplication: (data: {
    leaveTypeId: string;
    fromDate: string;
    toDate: string;
    isHalfDay?: boolean;
    halfDayType?: string;
    reason: string;
    contactNumber?: string;
    contactAddress?: string;
    attachments?: string[];
    compOffDate?: string;
  }) => api.post<ESSLeaveApplication>('/ess/leave/applications', data).then((response) => response.data),

  updateApplication: (
    applicationId: string,
    data: Partial<{
      fromDate: string;
      toDate: string;
      isHalfDay: boolean;
      halfDayType: string;
      reason: string;
      contactNumber: string;
      contactAddress: string;
      attachments: string[];
    }>,
  ) =>
    api
      .put<ESSLeaveApplication>(`/ess/leave/applications/${applicationId}`, data)
      .then((response) => response.data),

  cancelApplication: (applicationId: string, reason: string) =>
    api
      .post<ESSLeaveApplication>(`/ess/leave/applications/${applicationId}/cancel`, { reason })
      .then((response) => response.data),
};

export const essOperationsApi = {
  getAssets: () =>
    api.get<ESSAssignedAssetsResponse>('/ess/assets').then((response) => response.data),

  getTrainingList: () =>
    api.get<ESSTrainingListResponse>('/ess/training').then((response) => response.data),

  getTrainingDetail: (programId: string) =>
    api
      .get<ESSTrainingDetailResponse>(`/ess/training/${programId}`)
      .then((response) => response.data),

  getPerformanceGoals: () =>
    api.get<ESSPerformancePacket>('/ess/performance/goals').then((response) => response.data),

  getSelfAppraisal: () =>
    api
      .get<ESSPerformancePacket>('/ess/performance/self-appraisal')
      .then((response) => response.data),

  submitSelfAppraisal: (payload: ESSPerformanceSelfAppraisalPayload) =>
    api
      .post<ESSPerformancePacket>('/ess/performance/self-appraisal', payload)
      .then((response) => response.data),
};

export default {
  auth: essAuthApi,
  profile: essProfileApi,
  reimbursement: essReimbursementApi,
  helpdesk: essHelpdeskApi,
  itDeclaration: essITDeclarationApi,
  attendance: essAttendanceApi,
  leave: essLeaveApi,
  operations: essOperationsApi,
};
