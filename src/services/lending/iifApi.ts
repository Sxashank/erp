/**
 * IIF (Interest Incentivization Fund) API service.
 *
 * Backend mounts under `/api/v1/lending/iif/*`. All wire shapes are camelCase
 * (Pydantic CamelSchema). Money fields are Decimal-as-string per CLAUDE.md §6.2.
 *
 * Mutating endpoints (POST/PUT/DELETE that create/update state on the backend)
 * emit an Idempotency-Key per CLAUDE.md §6.3. Pure preview/compute endpoints
 * (compute, eligibility-check, report fetches) do NOT.
 */

import api from '../api';

// ============================================================================
// Wire shapes
// ============================================================================

export type ClaimFrequency = 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY';
export type EligibleLoanType = 'TERM_LOAN_CAPEX' | 'WORKING_CAPITAL';

export type EnrollmentStatus =
  | 'PENDING_APPROVAL'
  | 'ENROLLED'
  | 'REJECTED'
  | 'SUSPENDED'
  | 'TERMINATED';

export type ClaimStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'VERIFIED'
  | 'RELEASE_IN_PROGRESS'
  | 'RELEASED'
  | 'REJECTED'
  | 'CANCELLED';

export interface SubventionScheme {
  id: string;
  organizationId: string | null;
  schemeCode: string;
  schemeName: string;
  administeringMinistry: string | null;
  implementingAgency: string | null;
  subventionRatePercent: string;
  maxSubventionPerBeneficiary: string | null;
  schemeCorpus: string | null;
  eligibleLoanTypes: EligibleLoanType[];
  maxTenureTermLoanMonths: number | null;
  maxTenureWorkingCapitalMonths: number | null;
  schemeStartDate: string;
  schemeEndDate: string;
  eligibilityWindowMonths: number | null;
  claimFrequency: ClaimFrequency;
  npaDisqualificationDpdDays: number;
  calculationRules?: Record<string, unknown>;
  eligibilityRules?: Record<string, unknown>;
  requiredDocuments?: Array<Record<string, unknown>>;
  workflowRules?: Record<string, unknown>;
  fundRules?: Record<string, unknown>;
  description: string | null;
  isActive: boolean;
}

export interface FundUtilizationCategory {
  id: string;
  organizationId: string | null;
  schemeId: string | null;
  code: string;
  label: string;
  description: string | null;
  sortOrder: number;
  isActive: boolean;
}

export interface ApplicationUtilization {
  id: string;
  organizationId: string;
  applicationId: string;
  categoryId: string;
  categoryLabel: string;
  amount: string;
  /**
   * Lender-side approved amount per category. Populated at sanction stage;
   * null while still in application stage. Decimal-as-string per CLAUDE.md §6.2.
   */
  approvedAmount?: string | null;
  remarks: string | null;
}

export interface LoanSubventionEnrollment {
  id: string;
  organizationId: string;
  loanAccountId: string;
  loanAccountNumber: string;
  entityName: string;
  schemeId: string;
  schemeCode: string;
  enrolledDate: string;
  status: EnrollmentStatus;
  rejectionReason: string | null;
  totalClaimedToDate: string;
  totalPaidToDate: string;
  notes: string | null;
}

export interface SubventionClaimDocument {
  name: string;
  path: string;
  uploadedAt: string;
}

export interface SubventionClaim {
  id: string;
  organizationId: string;
  enrollmentId: string;
  loanAccountNumber: string;
  schemeCode: string;
  claimReference: string;
  periodStart: string;
  periodEnd: string;
  claimFrequency: ClaimFrequency;
  interestPaidInPeriod: string;
  applicableSubventionAmount: string;
  status: ClaimStatus;
  submittedDate: string | null;
  verifiedDate: string | null;
  releaseInitiatedDate: string | null;
  releasedDate: string | null;
  rejectionReason: string | null;
  releaseInstructionReference: string | null;
  releaseInstructionNotes: string | null;
  releaseReference: string | null;
  declarationSignedBy: string | null;
  declarationSignedAt: string | null;
  documents: SubventionClaimDocument[];
}

export interface ClaimComputePreview {
  enrollmentId: string;
  periodStart: string;
  periodEnd: string;
  interestPaidInPeriod: string;
  applicableSubventionAmount: string;
  subventionRatePercent: string;
  calculationMethod?: string | null;
  eligibleBaseAmount?: string | null;
}

export interface EligibilityCheckResult {
  eligible: boolean;
  reasons: string[];
  /** Map of rule-name → pass/fail; rendered as a checklist by the UI. */
  checks: Record<string, boolean>;
}

export interface EligibleLoan {
  enrollmentId: string;
  loanAccountId: string;
  loanAccountNumber: string | null;
  schemeId: string;
  schemeCode: string;
  claimFrequency: 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY';
  periodStart: string;
  periodEnd: string;
  label: string;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page?: number;
  pageSize?: number;
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Build an `Idempotency-Key` header for every mutating call. CLAUDE.md §6.3.
 * Uses `crypto.randomUUID` which is available in all evergreen browsers and
 * Node 19+.
 */
function idempotencyHeader(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

// ============================================================================
// Subvention schemes (master)
// ============================================================================

export interface SubventionSchemeCreate {
  organizationId?: string | null;
  schemeCode: string;
  schemeName: string;
  administeringMinistry?: string | null;
  implementingAgency?: string | null;
  subventionRatePercent: string;
  maxSubventionPerBeneficiary?: string | null;
  schemeCorpus?: string | null;
  eligibleLoanTypes: EligibleLoanType[];
  maxTenureTermLoanMonths?: number | null;
  maxTenureWorkingCapitalMonths?: number | null;
  schemeStartDate: string;
  schemeEndDate: string;
  eligibilityWindowMonths?: number | null;
  claimFrequency: ClaimFrequency;
  npaDisqualificationDpdDays: number;
  calculationRules?: Record<string, unknown>;
  eligibilityRules?: Record<string, unknown>;
  requiredDocuments?: Array<Record<string, unknown>>;
  workflowRules?: Record<string, unknown>;
  fundRules?: Record<string, unknown>;
  description?: string | null;
  isActive?: boolean;
}

export type SubventionSchemeUpdate = Partial<SubventionSchemeCreate>;

export interface SchemeListParams {
  organizationId?: string;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
}

export const subventionSchemesApi = {
  async list(params?: SchemeListParams): Promise<PaginatedList<SubventionScheme>> {
    const { data } = await api.get<PaginatedList<SubventionScheme>>('/lending/iif/schemes', {
      params,
    });
    return data;
  },
  async get(id: string): Promise<SubventionScheme> {
    const { data } = await api.get<SubventionScheme>(`/lending/iif/schemes/${id}`);
    return data;
  },
  async create(payload: SubventionSchemeCreate): Promise<SubventionScheme> {
    const { data } = await api.post<SubventionScheme>('/lending/iif/schemes', payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async update(id: string, payload: SubventionSchemeUpdate): Promise<SubventionScheme> {
    const { data } = await api.put<SubventionScheme>(`/lending/iif/schemes/${id}`, payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async deactivate(id: string): Promise<SubventionScheme> {
    const { data } = await api.post<SubventionScheme>(
      `/lending/iif/schemes/${id}/deactivate`,
      null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
};

// ============================================================================
// Fund utilization categories (master)
// ============================================================================

export interface FundUtilizationCategoryCreate {
  organizationId?: string | null;
  schemeId?: string | null;
  code: string;
  label: string;
  description?: string | null;
  sortOrder?: number;
  isActive?: boolean;
}

export type FundUtilizationCategoryUpdate = Partial<FundUtilizationCategoryCreate>;

export interface CategoryListParams {
  schemeId?: string;
  organizationId?: string;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
}

export const utilizationCategoriesApi = {
  async list(params?: CategoryListParams): Promise<PaginatedList<FundUtilizationCategory>> {
    const { data } = await api.get<PaginatedList<FundUtilizationCategory>>(
      '/lending/iif/categories',
      { params },
    );
    return data;
  },
  async get(id: string): Promise<FundUtilizationCategory> {
    const { data } = await api.get<FundUtilizationCategory>(`/lending/iif/categories/${id}`);
    return data;
  },
  async create(payload: FundUtilizationCategoryCreate): Promise<FundUtilizationCategory> {
    const { data } = await api.post<FundUtilizationCategory>('/lending/iif/categories', payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async update(
    id: string,
    payload: FundUtilizationCategoryUpdate,
  ): Promise<FundUtilizationCategory> {
    const { data } = await api.put<FundUtilizationCategory>(
      `/lending/iif/categories/${id}`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async deactivate(id: string): Promise<FundUtilizationCategory> {
    const { data } = await api.post<FundUtilizationCategory>(
      `/lending/iif/categories/${id}/deactivate`,
      null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
};

// ============================================================================
// Application utilization (per loan application)
// ============================================================================

export interface ApplicationUtilizationLine {
  categoryId: string;
  amount: string;
  remarks?: string | null;
}

export interface ApplicationUtilizationApprovedLine {
  categoryId: string;
  approvedAmount: string;
  remarks?: string | null;
}

export interface ApplicationUtilizationBulkReplace {
  lines: ApplicationUtilizationLine[];
}

export const applicationUtilizationApi = {
  async list(applicationId: string): Promise<ApplicationUtilization[]> {
    const { data } = await api.get<ApplicationUtilization[]>(
      `/lending/iif/applications/${applicationId}/utilization`,
    );
    return data;
  },
  async bulkReplace(
    applicationId: string,
    lines: ApplicationUtilizationLine[],
  ): Promise<ApplicationUtilization[]> {
    const { data } = await api.put<ApplicationUtilization[]>(
      `/lending/iif/applications/${applicationId}/utilization`,
      { lines },
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async delete(applicationId: string, lineId: string): Promise<void> {
    await api.delete(`/lending/iif/applications/${applicationId}/utilization/${lineId}`, {
      headers: idempotencyHeader(),
    });
  },
  /**
   * Lender-side approved-amount submission. Persists per-category
   * approvedAmount values during the sanction stage. Backend validates that
   * SUM(approvedAmount) == sanction.sanctionedAmount.
   */
  async submitApproved(
    applicationId: string,
    lines: ApplicationUtilizationApprovedLine[],
  ): Promise<ApplicationUtilization[]> {
    const { data } = await api.post<ApplicationUtilization[]>(
      `/lending/iif/applications/${applicationId}/utilization/approved`,
      { lines },
      { headers: idempotencyHeader() },
    );
    return data;
  },
};

// ============================================================================
// Enrollments
// ============================================================================

export interface EnrollmentListParams {
  organizationId?: string;
  status?: EnrollmentStatus;
  schemeId?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface EnrollmentCreate {
  loanAccountId: string;
  schemeId: string;
  notes?: string | null;
}

export const enrollmentsApi = {
  async list(params?: EnrollmentListParams): Promise<PaginatedList<LoanSubventionEnrollment>> {
    const { data } = await api.get<PaginatedList<LoanSubventionEnrollment>>(
      '/lending/iif/enrollments',
      { params },
    );
    return data;
  },
  async get(id: string): Promise<LoanSubventionEnrollment> {
    const { data } = await api.get<LoanSubventionEnrollment>(`/lending/iif/enrollments/${id}`);
    return data;
  },
  async create(payload: EnrollmentCreate): Promise<LoanSubventionEnrollment> {
    const { data } = await api.post<LoanSubventionEnrollment>('/lending/iif/enrollments', payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async approve(id: string, notes?: string): Promise<LoanSubventionEnrollment> {
    const { data } = await api.post<LoanSubventionEnrollment>(
      `/lending/iif/enrollments/${id}/approve`,
      notes ? { notes } : null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async reject(id: string, reason: string): Promise<LoanSubventionEnrollment> {
    const { data } = await api.post<LoanSubventionEnrollment>(
      `/lending/iif/enrollments/${id}/reject`,
      { reason },
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async suspend(id: string, reason: string): Promise<LoanSubventionEnrollment> {
    const { data } = await api.post<LoanSubventionEnrollment>(
      `/lending/iif/enrollments/${id}/suspend`,
      { reason },
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async reinstate(id: string, notes?: string): Promise<LoanSubventionEnrollment> {
    const { data } = await api.post<LoanSubventionEnrollment>(
      `/lending/iif/enrollments/${id}/reinstate`,
      notes ? { notes } : null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  /** Preview-only; no idempotency key. */
  async eligibilityCheck(payload: {
    loanAccountId: string;
    schemeId: string;
  }): Promise<EligibilityCheckResult> {
    const { data } = await api.post<EligibilityCheckResult>(
      '/lending/iif/enrollments/eligibility-check',
      payload,
    );
    return data;
  },
};

// ============================================================================
// Claims
// ============================================================================

export interface ClaimListParams {
  organizationId?: string;
  enrollmentId?: string;
  schemeId?: string;
  status?: ClaimStatus;
  periodStartFrom?: string;
  periodEndTo?: string;
  page?: number;
  pageSize?: number;
}

export interface ClaimComputePayload {
  enrollmentId: string;
  periodStart: string;
  periodEnd: string;
}

export interface ClaimCreatePayload extends ClaimComputePayload {
  declarationSignedBy?: string | null;
  notes?: string | null;
}

export interface ClaimMarkPaidPayload {
  releaseReference: string;
  releasedDate: string;
}

export interface ClaimInitiateReleasePayload {
  releaseInstructionReference: string;
  releaseInitiatedDate?: string | null;
  releaseInstructionNotes?: string | null;
}

export const claimsApi = {
  async list(params?: ClaimListParams): Promise<PaginatedList<SubventionClaim>> {
    const { data } = await api.get<PaginatedList<SubventionClaim>>('/lending/iif/claims', {
      params,
    });
    return data;
  },
  async get(id: string): Promise<SubventionClaim> {
    const { data } = await api.get<SubventionClaim>(`/lending/iif/claims/${id}`);
    return data;
  },
  /** Preview-only; no idempotency key (no state change). */
  async compute(payload: ClaimComputePayload): Promise<ClaimComputePreview> {
    const { data } = await api.post<ClaimComputePreview>('/lending/iif/claims/compute', payload);
    return data;
  },
  async create(payload: ClaimCreatePayload): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>('/lending/iif/claims', payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async submit(id: string): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>(
      `/lending/iif/claims/${id}/submit`,
      {},
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async verify(
    id: string,
    payload: { decision: 'APPROVE' | 'REJECT'; reason?: string | null },
  ): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>(`/lending/iif/claims/${id}/verify`, payload, {
      headers: idempotencyHeader(),
    });
    return data;
  },
  async initiateRelease(
    id: string,
    payload: ClaimInitiateReleasePayload,
  ): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>(
      `/lending/iif/claims/${id}/initiate-release`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async markReleased(id: string, payload: ClaimMarkPaidPayload): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>(
      `/lending/iif/claims/${id}/mark-released`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async cancel(id: string, reason: string): Promise<SubventionClaim> {
    const { data } = await api.post<SubventionClaim>(
      `/lending/iif/claims/${id}/cancel`,
      { reason },
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async getEligibleLoans(params?: { page?: number; pageSize?: number }): Promise<EligibleLoan[]> {
    const { data } = await api.get<{ items: EligibleLoan[]; total: number }>(
      '/lending/iif/claims/eligible-loans',
      { params: { page: params?.page, page_size: params?.pageSize } },
    );
    return data.items ?? [];
  },
  async getReportJson(id: string): Promise<Record<string, unknown>> {
    const { data } = await api.get<Record<string, unknown>>(`/lending/iif/claims/${id}/report`);
    return data;
  },
  async downloadReportCsv(id: string): Promise<Blob> {
    const { data } = await api.get<Blob>(`/lending/iif/claims/${id}/report.csv`, {
      responseType: 'blob',
    });
    return data;
  },
  async downloadReportXlsx(id: string): Promise<Blob> {
    const { data } = await api.get<Blob>(`/lending/iif/claims/${id}/report.xlsx`, {
      responseType: 'blob',
    });
    return data;
  },
  async downloadReportPdf(id: string): Promise<Blob> {
    const { data } = await api.get<Blob>(`/lending/iif/claims/${id}/report.pdf`, {
      responseType: 'blob',
    });
    return data;
  },
};

export const iifApi = {
  schemes: subventionSchemesApi,
  categories: utilizationCategoriesApi,
  applicationUtilization: applicationUtilizationApi,
  enrollments: enrollmentsApi,
  claims: claimsApi,
};

export default iifApi;
