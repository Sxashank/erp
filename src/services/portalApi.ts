/**
 * Borrower Portal API Service
 * Handles SFC borrower-side workflows.
 */

import axios from 'axios';

interface PortalEnv {
  VITE_API_URL?: string;
  VITE_PORTAL_ORGANIZATION_ID?: string;
}

const portalEnv = (import.meta.env ?? {}) as PortalEnv;
const API_BASE_URL = portalEnv.VITE_API_URL || 'http://localhost:8001/api/v1';
const PORTAL_DEFAULT_ORGANIZATION_ID = (portalEnv.VITE_PORTAL_ORGANIZATION_ID ?? '').toString();

export function resolvePortalOrganizationId(): string | undefined {
  const trimmed = PORTAL_DEFAULT_ORGANIZATION_ID.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

const portalApiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

portalApiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

portalApiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !String(originalRequest.url ?? '').includes('/portal/auth/refresh')
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('portal_refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/portal/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const accessToken = response.data.access_token ?? response.data.session_token;
          const nextRefreshToken = response.data.refresh_token;
          if (accessToken) {
            localStorage.setItem('portal_access_token', accessToken);
          }
          if (nextRefreshToken) {
            localStorage.setItem('portal_refresh_token', nextRefreshToken);
          }
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return portalApiClient(originalRequest);
        } catch (_refreshError) {
          localStorage.removeItem('portal_access_token');
          localStorage.removeItem('portal_refresh_token');
          localStorage.removeItem('portal_user');
          window.location.href = '/portal/login';
        }
      }
    }

    return Promise.reject(error);
  },
);

const portalPublic = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ----------------------------------------------------------------------------
// Session / auth shapes
// ----------------------------------------------------------------------------

export type PortalActorRole =
  | 'scheme_borrower'
  | 'scheme_lender'
  | 'scheme_smfcl_reviewer'
  | 'scheme_smfcl_approver'
  | 'scheme_ministry_viewer'
  | 'scheme_admin';

export interface PortalLinkedEntity {
  id: string;
  legal_name?: string;
  legalName?: string;
}

export interface PortalSessionUser {
  id: string;
  mobile: string;
  email?: string | null;
  preferred_language?: string;
  preferredLanguage?: string;
  display_name?: string;
  displayName?: string;
  full_name?: string;
  fullName?: string;
  organization_id?: string;
  organizationId?: string;
  actor_role?: PortalActorRole;
  actorRole?: PortalActorRole;
  linked_entities?: PortalLinkedEntity[];
  linkedEntities?: { id: string; legalName: string }[];
}

export interface PortalLoginResponse {
  success: boolean;
  error?: string | null;
  message?: string | null;
  requires_mfa?: boolean;
  user?: PortalSessionUser | null;
  access_token?: string | null;
  session_token?: string | null;
  refresh_token?: string | null;
  expires_at?: string | null;
}

export interface RegisterRequest {
  cin?: string;
  gstin?: string;
  llpin?: string;
  pan?: string;
  loanAccountNumber?: string;
  sanctionedAmount?: string;
  authorizedSignatoryName: string;
  mobile: string;
  email: string;
}

export interface RegisterResponse {
  registrationReference: string;
  status: 'OTP_SENT';
  maskedMobile: string;
}

export interface RegisterVerifyOtpRequest {
  registrationReference: string;
  otp: string;
}

export interface RegisterVerifyOtpResponse {
  registrationReference: string;
  portalUserId: string;
  registrationStatus: 'PENDING_APPROVAL' | 'ACTIVE';
  autoApproved: boolean;
  linkedEntityIds: string[];
}

export interface RegistrationStatusResponse {
  registrationReference: string;
  registrationStatus: 'PENDING_APPROVAL' | 'ACTIVE' | 'REJECTED';
  maskedMobile: string;
  rejectionReason: string | null;
  approvedAt: string | null;
}

export interface PortalPasswordLoginRequest {
  organization_id?: string;
  email: string;
  password: string;
  otp?: string;
  device_info?: Record<string, string>;
}

export interface PortalActivateInviteRequest {
  token: string;
  password: string;
  device_info?: Record<string, string>;
}

export interface PortalForgotPasswordRequest {
  organization_id?: string;
  email: string;
}

export interface PortalForgotPasswordResponse {
  success: boolean;
  message: string;
  reset_token?: string | null;
  reset_url?: string | null;
  expires_at?: string | null;
}

export interface PortalResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface PortalMfaSetupResponse {
  secret: string;
  provisioning_uri: string;
  is_enabled: boolean;
}

// ----------------------------------------------------------------------------
// Workbench / products
// ----------------------------------------------------------------------------

export interface PortalWorkbenchStat {
  key: string;
  label: string;
  value: number;
  hint?: string | null;
}

export interface PortalWorkbenchAction {
  title: string;
  description: string;
  href: string;
  status: 'info' | 'attention' | 'success';
}

export interface PortalWorkbenchApplication {
  id: string;
  applicationNumber: string;
  entityLegalName?: string | null;
  productName?: string | null;
  schemeStatus: string;
  submittedAt?: string | null;
  updatedAt?: string | null;
}

export interface PortalWorkbench {
  actorRole: PortalActorRole;
  displayName: string;
  activeEntityCount: number;
  stats: PortalWorkbenchStat[];
  priorityActions: PortalWorkbenchAction[];
  recentApplications: PortalWorkbenchApplication[];
}

export interface PortalProduct {
  id: string;
  code: string;
  name: string;
  category: string;
  minAmount: string;
  maxAmount: string;
  minTenureMonths: number;
  maxTenureMonths: number;
  defaultTenureMonths?: number | null;
  allowsMoratorium?: boolean;
  maxMoratoriumMonths?: number | null;
  interestType?: string | null;
  allowedRepaymentFrequencies?: string[];
  defaultRepaymentFrequency?: string | null;
  allowedRepaymentModes?: string[];
  defaultRepaymentMode?: string | null;
  documentRequirements?: PortalApplicationDocumentRequirement[];
}

export interface PortalUtilizationCategory {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  sortOrder: number;
}

export interface PortalReportApplicationSummary {
  total: number;
  submitted: number;
  underReview: number;
  queryPending: number;
  approved: number;
  released: number;
  requestedAmount: string;
}

export interface PortalReportClaimSummary {
  total: number;
  draft: number;
  submitted: number;
  verified: number;
  releaseInProgress: number;
  released: number;
  rejected: number;
  releasedAmount: string;
}

export interface PortalReportStatusBreakdownItem {
  status: string;
  count: number;
}

export interface PortalReportBorrowerBreakdownItem {
  entityId?: string | null;
  entityLegalName: string;
  applicationCount: number;
  approvedCount: number;
  requestedAmount: string;
  claimsReleasedCount: number;
  claimsReleasedAmount: string;
}

export interface PortalReportReviewBreakdownItem {
  reviewOwner: string;
  applicationCount: number;
  pendingSfcReview: number;
  approvedCount: number;
  requestedAmount: string;
}

export interface PortalReportRecentReleaseItem {
  claimId: string;
  claimReference: string;
  entityLegalName?: string | null;
  schemeName?: string | null;
  applicableSubventionAmount: string;
  releasedDate?: string | null;
  releaseReference?: string | null;
}

export interface PortalReportingSummary {
  actorRole: PortalActorRole;
  generatedAt: string;
  applicationSummary: PortalReportApplicationSummary;
  claimSummary: PortalReportClaimSummary;
  applicationStatusBreakdown: PortalReportStatusBreakdownItem[];
  claimStatusBreakdown: PortalReportStatusBreakdownItem[];
  borrowerBreakdown: PortalReportBorrowerBreakdownItem[];
  reviewBreakdown: PortalReportReviewBreakdownItem[];
  recentReleases: PortalReportRecentReleaseItem[];
}

// ----------------------------------------------------------------------------
// Applications / claims
// ----------------------------------------------------------------------------

export type PortalApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'ADDITIONAL_INFO_REQUIRED'
  | 'SANCTIONED'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'CANCELLED'
  | 'EXPIRED';

export type PortalSchemeApplicationStatus =
  | 'DRAFT'
  | 'LENDER_REVIEW'
  | 'LENDER_VALIDATED'
  | 'SMFCL_PRELIM_REVIEW'
  | 'QUERY_PENDING'
  | 'SMFCL_APPRAISAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'SANCTION_ISSUED'
  | 'CLAIM_OPEN'
  | 'RELEASE_IN_PROGRESS'
  | 'RELEASED'
  | 'CLOSED';

export interface PortalFundUtilizationLine {
  categoryId: string;
  amount: string;
  remarks?: string | null;
}

export interface PortalApplication {
  id: string;
  applicationNumber: string;
  entityId: string;
  entityLegalName: string;
  productId: string;
  productName: string;
  requestedAmount: string;
  tenureMonths: number;
  purposeDescription: string;
  status: PortalApplicationStatus;
  schemeStatus: PortalSchemeApplicationStatus | string;
  submittedAt: string | null;
  decisionAt: string | null;
  reviewRemarks?: string | null;
  rejectionReason?: string | null;
}

export interface PortalApplicationDetail extends PortalApplication {
  detailedPurpose?: string | null;
  projectName?: string | null;
  projectLocation?: string | null;
  projectCost?: string | null;
  shipyardName?: string | null;
  maritimeSegment?: string | null;
  declarationAccepted?: boolean | null;
  reviewRemarks?: string | null;
  rejectionReason?: string | null;
  fundUtilization?: {
    categoryId: string;
    categoryLabel?: string;
    amount: string;
    approvedAmount?: string | null;
    remarks?: string | null;
  }[];
  documentRequirements?: PortalApplicationDocumentRequirement[];
}

export interface PortalApplicationDocumentRequirement {
  code: string;
  name: string;
  category: string;
  requiredAtStage: string;
  isMandatory: boolean;
  minFileCount: number;
  maxFileCount: number;
  uploadedCount: number;
  isUploaded: boolean;
  missing: boolean;
  helpText?: string | null;
}

export interface CreatePortalApplicationRequest {
  entityId: string;
  productId: string;
  requestedAmount: string;
  tenureMonths: number;
  purposeDescription: string;
  detailedPurpose?: string | null;
  projectName?: string | null;
  projectLocation?: string | null;
  projectCost?: string | null;
  shipyardName?: string | null;
  maritimeSegment?: string | null;
  declarationAccepted: boolean;
  fundUtilization: PortalFundUtilizationLine[];
}

export type UpdatePortalApplicationRequest = Partial<
  Omit<CreatePortalApplicationRequest, 'entityId' | 'productId'>
>;

export interface PortalApplicationDocument {
  id: string;
  applicationId?: string;
  dmsDocumentId?: string | null;
  documentCode?: string;
  documentType?: string;
  documentName?: string;
  fileName: string;
  fileSizeBytes?: number | null;
  fileMimeType?: string | null;
  status?: string;
  uploadedAt?: string;
  uploadDate?: string;
  downloadUrl?: string | null;
}

export type PortalApplicationQueryStatus =
  | 'RAISED'
  | 'RESPONDED'
  | 'RE_REVIEW'
  | 'RESOLVED'
  | 'LAPSED';

export interface PortalApplicationQuery {
  id: string;
  applicationId: string;
  queryNumber: number;
  raisedById: string;
  raisedAt: string;
  raisedReasonCode: string;
  queryText: string;
  requiredAttachments: string[];
  slaDueAt?: string | null;
  status: PortalApplicationQueryStatus;
  respondedById?: string | null;
  respondedAt?: string | null;
  responseText?: string | null;
  responseAttachments: Record<string, unknown>[];
  resolvedById?: string | null;
  resolvedAt?: string | null;
  resolutionRemark?: string | null;
}

export interface PortalApplicationQueryListResponse {
  items: PortalApplicationQuery[];
  total: number;
}

export interface RespondToPortalApplicationQueryRequest {
  responseText: string;
  responseAttachments: Record<string, unknown>[];
}

export type PortalSubsidyClaimStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'VERIFIED'
  | 'RELEASE_IN_PROGRESS'
  | 'RELEASED'
  | 'REJECTED'
  | 'CANCELLED';

export interface PortalSubsidyClaim {
  id: string;
  claimReference: string;
  periodStart: string;
  periodEnd: string;
  status: PortalSubsidyClaimStatus;
  applicableSubventionAmount: string;
  releasedDate: string | null;
  releaseReference: string | null;
}

export interface PortalClaimDocument {
  documentId?: string | null;
  name: string;
  fileName?: string | null;
  documentCategory?: string | null;
  uploadedAt?: string | null;
  downloadUrl?: string | null;
}

export interface PortalEligibleClaimPeriod {
  periodStart: string;
  periodEnd: string;
  label: string;
  claimFrequency: string;
  alreadyClaimed: boolean;
  existingClaimId?: string | null;
  existingStatus?: string | null;
}

export interface PortalClaimEnrollment {
  enrollmentId: string;
  loanAccountId: string;
  loanAccountNumber?: string | null;
  schemeId: string;
  schemeCode?: string | null;
  schemeName?: string | null;
  status: string;
  enrolledDate: string;
  totalClaimedToDate: string;
  totalPaidToDate: string;
  eligiblePeriods: PortalEligibleClaimPeriod[];
}

export interface PortalClaim {
  id: string;
  enrollmentId: string;
  loanAccountId?: string | null;
  loanAccountNumber?: string | null;
  schemeId?: string | null;
  schemeCode?: string | null;
  claimReference: string;
  periodStart: string;
  periodEnd: string;
  claimFrequency: string;
  interestPaidInPeriod: string;
  applicableSubventionAmount: string;
  status: PortalSubsidyClaimStatus | string;
  submittedDate?: string | null;
  verifiedDate?: string | null;
  releaseInitiatedDate?: string | null;
  releasedDate?: string | null;
  rejectionReason?: string | null;
  releaseInstructionReference?: string | null;
  releaseInstructionNotes?: string | null;
  releaseReference?: string | null;
  declarationSignedAt?: string | null;
  documents: PortalClaimDocument[];
  createdAt: string;
  updatedAt?: string | null;
}

export interface PortalClaimStats {
  draft: number;
  submitted: number;
  verified: number;
  releaseInProgress: number;
  released: number;
  eligiblePeriods: number;
}

export interface PortalClaimsWorkbench {
  stats: PortalClaimStats;
  enrollments: PortalClaimEnrollment[];
  claims: PortalClaim[];
}

export interface PortalCreateClaimRequest {
  enrollmentId: string;
  periodStart: string;
  periodEnd: string;
  documents?: PortalClaimDocument[];
}

export interface PortalApplicationReasonRequest {
  reason: string;
}

export interface FailedScheduleItem {
  installmentNumber: number;
  dueDate: string;
  principalDue: string;
  interestDue: string;
  dpdDays: number;
  failReason: string | null;
  lastAttemptDate: string | null;
}

export type MissedScheduleItem = FailedScheduleItem;

export interface PaginatedPortalApplications {
  items: PortalApplication[];
  total: number;
  page: number;
  pageSize: number;
}

// ----------------------------------------------------------------------------
// Auth APIs
// ----------------------------------------------------------------------------

export const portalAuthApi = {
  sendOtp: (data: { organization_id?: string; mobile: string; purpose?: string }) =>
    portalPublic.post('/portal/auth/send-otp', data),

  login: (data: {
    organization_id?: string;
    mobile: string;
    otp: string;
    device_info?: Record<string, unknown>;
  }) => portalPublic.post<PortalLoginResponse>('/portal/auth/verify-otp', data),

  loginWithPassword: (data: PortalPasswordLoginRequest) =>
    portalPublic.post<PortalLoginResponse>('/portal/auth/login/password', data),

  activateInvite: (data: PortalActivateInviteRequest) =>
    portalPublic.post<PortalLoginResponse>('/portal/auth/activate-invite', data),

  forgotPassword: (data: PortalForgotPasswordRequest) =>
    portalPublic.post<PortalForgotPasswordResponse>('/portal/auth/forgot-password', data),

  resetPassword: (data: PortalResetPasswordRequest) =>
    portalPublic.post<PortalForgotPasswordResponse>('/portal/auth/reset-password', data),

  refresh: (data: { refresh_token: string }) =>
    portalPublic.post<PortalLoginResponse>('/portal/auth/refresh', data),

  logout: () => portalApiClient.post('/portal/auth/logout'),

  me: () => portalApiClient.get<PortalSessionUser>('/portal/auth/me'),

  setupMfa: () => portalApiClient.post<PortalMfaSetupResponse>('/portal/auth/mfa/setup'),

  verifyMfa: (otp: string) =>
    portalApiClient.post<{ is_enabled: boolean }>('/portal/auth/mfa/verify', { otp }),

  getSessions: () => portalApiClient.get('/portal/auth/sessions'),
};

export function persistPortalSession(response: PortalLoginResponse): void {
  const accessToken = response.access_token ?? response.session_token;
  if (!accessToken || !response.refresh_token || !response.user) {
    throw new Error('Scheme portal session payload is incomplete.');
  }
  localStorage.setItem('portal_access_token', accessToken);
  localStorage.setItem('portal_refresh_token', response.refresh_token);
  localStorage.setItem('portal_user', JSON.stringify(response.user));
}

export function clearPortalSession(): void {
  localStorage.removeItem('portal_access_token');
  localStorage.removeItem('portal_refresh_token');
  localStorage.removeItem('portal_user');
}

// ----------------------------------------------------------------------------
// Workbench / products APIs
// ----------------------------------------------------------------------------

export const portalWorkbenchApi = {
  get: () => portalApiClient.get<PortalWorkbench>('/portal/workbench'),
};

export const portalReportsApi = {
  getSummary: () => portalApiClient.get<PortalReportingSummary>('/portal/reports/summary'),
  downloadSummaryCsv: () =>
    portalApiClient.get<Blob>('/portal/reports/summary.csv', {
      responseType: 'blob',
    }),
};

export const portalProductsApi = {
  list: (params?: { entityId?: string }) =>
    portalApiClient.get<PortalProduct[]>('/portal/products', { params }),
};

export const portalUtilizationCategoriesApi = {
  list: () => portalApiClient.get<PortalUtilizationCategory[]>('/portal/utilization-categories'),
};

// ----------------------------------------------------------------------------
// Legacy dashboard / loan wrappers retained for compatibility.
// ----------------------------------------------------------------------------

export const portalDashboardApi = {
  getDashboard: () => portalApiClient.get('/portal/dashboard'),
  getLoans: () => portalApiClient.get('/portal/dashboard/loans'),
  getLoan: (loanId: string) => portalApiClient.get(`/portal/dashboard/loans/${loanId}`),
  getLoanSchedule: (loanId: string) =>
    portalApiClient.get(`/portal/dashboard/loans/${loanId}/schedule`),
  getLoanPayments: (loanId: string) =>
    portalApiClient.get(`/portal/dashboard/loans/${loanId}/payments`),
  getUpcomingDues: () => portalApiClient.get('/portal/dashboard/upcoming-dues'),
};

export const portalPaymentApi = {
  initiatePayment: (data: {
    loan_account_id: string;
    amount: number;
    payment_type: string;
    payment_mode: string;
  }) => portalApiClient.post('/portal/payments/initiate', data),

  getPaymentStatus: (paymentId: string) =>
    portalApiClient.get(`/portal/payments/${paymentId}/status`),

  getPrepaymentQuote: (data: {
    loan_account_id: string;
    prepayment_amount: number;
    prepayment_date: string;
  }) => portalApiClient.post('/portal/payments/prepayment-quote', data),

  getForeclosureQuote: (data: { loan_account_id: string; foreclosure_date: string }) =>
    portalApiClient.post('/portal/payments/foreclosure-quote', data),

  setupNachMandate: (data: {
    loan_account_id: string;
    bank_account_id: string;
    max_amount: number;
    frequency: string;
    start_date: string;
    end_date: string;
  }) => portalApiClient.post('/portal/payments/mandate/setup', data),
};

export const portalDocumentApi = {
  getDocuments: (loanId?: string) =>
    portalApiClient.get('/portal/documents', { params: { loan_account_id: loanId } }),

  downloadDocument: (documentId: string) =>
    portalApiClient.get(`/portal/documents/${documentId}/download`, {
      responseType: 'blob',
    }),

  getStatement: (data: { loan_account_id: string; from_date: string; to_date: string }) =>
    portalApiClient.get('/portal/documents/statement', {
      params: data,
      responseType: 'blob',
    }),

  getInterestCertificate: (data: { loan_account_id: string; financial_year: string }) =>
    portalApiClient.get('/portal/documents/interest-cert', {
      params: data,
      responseType: 'blob',
    }),

  getTdsCertificate: (data: { loan_account_id: string; financial_year: string; quarter: string }) =>
    portalApiClient.get('/portal/documents/tds-cert', {
      params: data,
      responseType: 'blob',
    }),
};

export const portalServiceRequestApi = {
  createRequest: (data: {
    request_type: string;
    loan_account_id?: string;
    subject: string;
    description: string;
    attachments?: unknown;
  }) => portalApiClient.post('/portal/service-requests', data),

  getRequests: (params?: { status?: string; loan_account_id?: string }) =>
    portalApiClient.get('/portal/service-requests', { params }),

  getRequest: (requestId: string) => portalApiClient.get(`/portal/service-requests/${requestId}`),
};

export const portalCommunicationApi = {
  getNotifications: (params?: { unread_only?: boolean }) =>
    portalApiClient.get('/portal/notifications', { params }),

  markAsRead: (notificationId: string) =>
    portalApiClient.post(`/portal/notifications/${notificationId}/read`),

  getTickets: async (params?: {
    status?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }) => {
    const response = await portalApiClient.get('/portal/tickets', { params });
    return {
      ...response,
      data: response.data?.items ?? [],
    };
  },

  getTicket: (ticketId: string) => portalApiClient.get(`/portal/tickets/${ticketId}`),

  createTicket: (data: {
    subject: string;
    category: string;
    description: string;
    loan_account_id?: string;
    priority?: string;
  }) => portalApiClient.post('/portal/tickets', data),

  addTicketReply: (ticketId: string, data: { message: string }) =>
    portalApiClient.post(`/portal/tickets/${ticketId}/reply`, data),
};

// ----------------------------------------------------------------------------
// Registration APIs
// ----------------------------------------------------------------------------

export const portalRegistrationApi = {
  register: (data: RegisterRequest) =>
    portalPublic.post<RegisterResponse>('/portal/auth/register', data, {
      headers: idempotencyHeaders(),
    }),

  verifyOtp: (data: RegisterVerifyOtpRequest) =>
    portalPublic.post<RegisterVerifyOtpResponse>('/portal/auth/register/verify-otp', data, {
      headers: idempotencyHeaders(),
    }),

  status: (params: { reference: string; mobile: string }) =>
    portalPublic.get<RegistrationStatusResponse>('/portal/auth/registration-status', { params }),
};

// ----------------------------------------------------------------------------
// Applications APIs
// ----------------------------------------------------------------------------

export const portalApplicationsApi = {
  list: (params: {
    status?: PortalApplicationStatus | PortalSchemeApplicationStatus | string;
    entityId?: string;
    page?: number;
    pageSize?: number;
  }) =>
    portalApiClient.get<PaginatedPortalApplications>('/portal/applications', {
      params,
    }),

  get: (id: string) => portalApiClient.get<PortalApplicationDetail>(`/portal/applications/${id}`),

  createDraft: (data: CreatePortalApplicationRequest) =>
    portalApiClient.post<PortalApplicationDetail>('/portal/applications', data, {
      headers: idempotencyHeaders(),
    }),

  updateDraft: (id: string, data: UpdatePortalApplicationRequest) =>
    portalApiClient.patch<PortalApplicationDetail>(`/portal/applications/${id}`, data, {
      headers: idempotencyHeaders(),
    }),

  submit: (id: string) =>
    portalApiClient.post<PortalApplicationDetail>(
      `/portal/applications/${id}/submit`,
      {},
      { headers: idempotencyHeaders() },
    ),

  resubmit: (id: string) =>
    portalApiClient.post<PortalApplicationDetail>(
      `/portal/applications/${id}/resubmit`,
      {},
      { headers: idempotencyHeaders() },
    ),

  withdraw: (id: string, data: PortalApplicationReasonRequest) =>
    portalApiClient.post<PortalApplicationDetail>(`/portal/applications/${id}/withdraw`, data, {
      headers: idempotencyHeaders(),
    }),

  uploadDocument: (id: string, file: File, documentType: string, documentName?: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('documentCode', documentType);
    if (documentName) {
      form.append('documentName', documentName);
    }
    return portalApiClient.post<PortalApplicationDocument>(
      `/portal/applications/${id}/documents/upload`,
      form,
      {
        headers: {
          ...idempotencyHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      },
    );
  },

  listDocuments: (id: string) =>
    portalApiClient.get<PortalApplicationDocument[]>(`/portal/applications/${id}/documents`),

  listQueries: (id: string) =>
    portalApiClient.get<PortalApplicationQueryListResponse>(`/portal/applications/${id}/queries`),

  respondToQuery: (
    applicationId: string,
    queryId: string,
    data: RespondToPortalApplicationQueryRequest,
  ) =>
    portalApiClient.post<PortalApplicationQuery>(
      `/portal/applications/${applicationId}/queries/${queryId}/respond`,
      data,
      { headers: idempotencyHeaders() },
    ),
};

export const portalClaimsApi = {
  workbench: () => portalApiClient.get<PortalClaimsWorkbench>('/portal/claims/workbench'),

  listDocumentTypes: () =>
    portalApiClient.get<{ code: string; label: string }[]>('/portal/claims/document-types'),

  listEnrollments: () =>
    portalApiClient.get<{ items: PortalClaimEnrollment[]; total: number }>(
      '/portal/claims/enrollments',
    ),

  listEligiblePeriods: (enrollmentId: string) =>
    portalApiClient.get<{
      enrollmentId: string;
      claimFrequency: string;
      periods: PortalEligibleClaimPeriod[];
    }>(`/portal/claims/enrollments/${enrollmentId}/eligible-periods`),

  list: (params?: { loanAccountId?: string; status?: string; page?: number; pageSize?: number }) =>
    portalApiClient.get<PaginatedPortalClaims>('/portal/claims', { params }),

  get: (id: string) => portalApiClient.get<PortalClaim>(`/portal/claims/${id}`),

  create: (data: PortalCreateClaimRequest) =>
    portalApiClient.post<PortalClaim>('/portal/claims', data, {
      headers: idempotencyHeaders(),
    }),

  uploadDocument: (
    id: string,
    file: File,
    documentName?: string,
    documentCategory = 'BORROWER_CLAIM_SUPPORTING_DOCUMENT',
  ) => {
    const form = new FormData();
    form.append('file', file);
    form.append('documentCategory', documentCategory);
    if (documentName) {
      form.append('documentName', documentName);
    }
    return portalApiClient.post<PortalClaim>(`/portal/claims/${id}/documents/upload`, form, {
      headers: {
        ...idempotencyHeaders(),
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  submit: (id: string, data?: { declarationSignedAt?: string | null }) =>
    portalApiClient.post<PortalClaim>(`/portal/claims/${id}/submit`, data ?? {}, {
      headers: idempotencyHeaders(),
    }),

  downloadClaimCsv: (claimId: string) =>
    portalApiClient.get<Blob>(`/portal/claims/${claimId}/report.csv`, {
      responseType: 'blob',
    }),

  downloadClaimXlsx: (claimId: string) =>
    portalApiClient.get<Blob>(`/portal/claims/${claimId}/report.xlsx`, {
      responseType: 'blob',
    }),

  downloadClaimPdf: (claimId: string) =>
    portalApiClient.get<Blob>(`/portal/claims/${claimId}/report.pdf`, {
      responseType: 'blob',
    }),

  downloadClaimCertificate: (claimId: string) =>
    portalApiClient.get<Blob>(`/portal/claims/${claimId}/certificate.pdf`, {
      responseType: 'blob',
    }),
};

export const portalScheduleApi = {
  getFailed: (loanId: string) =>
    portalApiClient.get<FailedScheduleItem[]>(`/portal/dashboard/loans/${loanId}/schedule/failed`),

  getMissed: (loanId: string) =>
    portalApiClient.get<MissedScheduleItem[]>(`/portal/dashboard/loans/${loanId}/schedule/missed`),

  downloadCsv: (loanId: string) =>
    portalApiClient.get<Blob>(`/portal/dashboard/loans/${loanId}/schedule.csv`, {
      responseType: 'blob',
    }),
};

export interface PaginatedPortalClaims {
  items: PortalClaim[];
  total: number;
  page: number;
  pageSize: number;
}

export default {
  auth: portalAuthApi,
  workbench: portalWorkbenchApi,
  products: portalProductsApi,
  dashboard: portalDashboardApi,
  payment: portalPaymentApi,
  document: portalDocumentApi,
  serviceRequest: portalServiceRequestApi,
  communication: portalCommunicationApi,
  registration: portalRegistrationApi,
  applications: portalApplicationsApi,
  claims: portalClaimsApi,
  schedule: portalScheduleApi,
};
