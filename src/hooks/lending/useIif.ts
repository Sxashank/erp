/**
 * IIF (Interest Incentivization Fund) react-query hooks.
 *
 * Query-key prefix: ['lending', 'iif', ...]. Mutations invalidate the
 * relevant slice on success. Error toasts are surfaced via showErrorToast,
 * which understands the backend `{error_code, message, correlation_id}`
 * envelope (CLAUDE.md §7, lib/errorToast.ts).
 *
 * See CLAUDE.md §5.4.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
} from '@tanstack/react-query';

import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import {
  applicationUtilizationApi,
  claimsApi,
  enrollmentsApi,
  subventionSchemesApi,
  utilizationCategoriesApi,
  type ApplicationUtilization,
  type ApplicationUtilizationLine,
  type CategoryListParams,
  type ClaimComputePayload,
  type ClaimComputePreview,
  type ClaimCreatePayload,
  type ClaimInitiateReleasePayload,
  type ClaimListParams,
  type ClaimMarkPaidPayload,
  type EligibilityCheckResult,
  type EligibleLoan,
  type EnrollmentCreate,
  type EnrollmentListParams,
  type FundUtilizationCategory,
  type FundUtilizationCategoryCreate,
  type FundUtilizationCategoryUpdate,
  type LoanSubventionEnrollment,
  type PaginatedList,
  type SchemeListParams,
  type SubventionClaim,
  type SubventionScheme,
  type SubventionSchemeCreate,
  type SubventionSchemeUpdate,
} from '@/services/lending/iifApi';

const MASTER_STALE_TIME = 5 * 60 * 1000;
const TXN_STALE_TIME = 30 * 1000;

// ============================================================================
// Query keys
// ============================================================================

export const iifKeys = {
  all: ['lending', 'iif'] as const,
  schemes: (params?: SchemeListParams) => ['lending', 'iif', 'schemes', params ?? {}] as const,
  scheme: (id: string) => ['lending', 'iif', 'scheme', id] as const,
  categories: (params?: CategoryListParams) =>
    ['lending', 'iif', 'categories', params ?? {}] as const,
  category: (id: string) => ['lending', 'iif', 'category', id] as const,
  applicationUtilization: (applicationId: string) =>
    ['lending', 'iif', 'application-utilization', applicationId] as const,
  enrollments: (params?: EnrollmentListParams) =>
    ['lending', 'iif', 'enrollments', params ?? {}] as const,
  enrollment: (id: string) => ['lending', 'iif', 'enrollment', id] as const,
  claims: (params?: ClaimListParams) => ['lending', 'iif', 'claims', params ?? {}] as const,
  claim: (id: string) => ['lending', 'iif', 'claim', id] as const,
  eligibleLoans: (params?: { page?: number; pageSize?: number }) =>
    ['lending', 'iif', 'eligible-loans', params ?? {}] as const,
  claimReport: (id: string) => ['lending', 'iif', 'claim-report', id] as const,
};

// ============================================================================
// Schemes
// ============================================================================

export function useSubventionSchemes(params?: SchemeListParams) {
  return useQuery<PaginatedList<SubventionScheme>>({
    queryKey: iifKeys.schemes(params),
    queryFn: () => subventionSchemesApi.list(params),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useSubventionScheme(id: string | undefined) {
  return useQuery<SubventionScheme>({
    queryKey: iifKeys.scheme(id ?? ''),
    queryFn: () => subventionSchemesApi.get(id as string),
    enabled: Boolean(id),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useCreateSubventionScheme(
  options?: UseMutationOptions<SubventionScheme, unknown, SubventionSchemeCreate>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionScheme, unknown, SubventionSchemeCreate>({
    mutationFn: (payload) => subventionSchemesApi.create(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'schemes'] });
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useUpdateSubventionScheme(
  options?: UseMutationOptions<
    SubventionScheme,
    unknown,
    { id: string; payload: SubventionSchemeUpdate }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionScheme, unknown, { id: string; payload: SubventionSchemeUpdate }>({
    mutationFn: ({ id, payload }) => subventionSchemesApi.update(id, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'schemes'] });
      qc.invalidateQueries({ queryKey: iifKeys.scheme(vars.id) });
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useDeactivateSubventionScheme(
  options?: UseMutationOptions<SubventionScheme, unknown, string>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionScheme, unknown, string>({
    mutationFn: (id) => subventionSchemesApi.deactivate(id),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, id, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'schemes'] });
      qc.invalidateQueries({ queryKey: iifKeys.scheme(id) });
      options?.onSuccess?.(data, id, onMutateResult, ctx);
    },
  });
}

// ============================================================================
// Categories
// ============================================================================

export function useUtilizationCategories(params?: CategoryListParams) {
  return useQuery<PaginatedList<FundUtilizationCategory>>({
    queryKey: iifKeys.categories(params),
    queryFn: () => utilizationCategoriesApi.list(params),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useUtilizationCategory(id: string | undefined) {
  return useQuery<FundUtilizationCategory>({
    queryKey: iifKeys.category(id ?? ''),
    queryFn: () => utilizationCategoriesApi.get(id as string),
    enabled: Boolean(id),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useCreateUtilizationCategory(
  options?: UseMutationOptions<FundUtilizationCategory, unknown, FundUtilizationCategoryCreate>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<FundUtilizationCategory, unknown, FundUtilizationCategoryCreate>({
    mutationFn: (payload) => utilizationCategoriesApi.create(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'categories'] });
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useUpdateUtilizationCategory(
  options?: UseMutationOptions<
    FundUtilizationCategory,
    unknown,
    { id: string; payload: FundUtilizationCategoryUpdate }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    FundUtilizationCategory,
    unknown,
    { id: string; payload: FundUtilizationCategoryUpdate }
  >({
    mutationFn: ({ id, payload }) => utilizationCategoriesApi.update(id, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'categories'] });
      qc.invalidateQueries({ queryKey: iifKeys.category(vars.id) });
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useDeactivateUtilizationCategory(
  options?: UseMutationOptions<FundUtilizationCategory, unknown, string>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<FundUtilizationCategory, unknown, string>({
    mutationFn: (id) => utilizationCategoriesApi.deactivate(id),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, id, onMutateResult, ctx) => {
      qc.invalidateQueries({ queryKey: ['lending', 'iif', 'categories'] });
      qc.invalidateQueries({ queryKey: iifKeys.category(id) });
      options?.onSuccess?.(data, id, onMutateResult, ctx);
    },
  });
}

// ============================================================================
// Application utilization
// ============================================================================

export function useApplicationUtilization(applicationId: string | undefined) {
  return useQuery<ApplicationUtilization[]>({
    queryKey: iifKeys.applicationUtilization(applicationId ?? ''),
    queryFn: () => applicationUtilizationApi.list(applicationId as string),
    enabled: Boolean(applicationId),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useReplaceApplicationUtilization(
  options?: UseMutationOptions<
    ApplicationUtilization[],
    unknown,
    { applicationId: string; lines: ApplicationUtilizationLine[] }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    ApplicationUtilization[],
    unknown,
    { applicationId: string; lines: ApplicationUtilizationLine[] }
  >({
    mutationFn: ({ applicationId, lines }) =>
      applicationUtilizationApi.bulkReplace(applicationId, lines),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      qc.invalidateQueries({
        queryKey: iifKeys.applicationUtilization(vars.applicationId),
      });
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

// ============================================================================
// Enrollments
// ============================================================================

export function useEnrollments(params?: EnrollmentListParams) {
  return useQuery<PaginatedList<LoanSubventionEnrollment>>({
    queryKey: iifKeys.enrollments(params),
    queryFn: () => enrollmentsApi.list(params),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useEnrollment(id: string | undefined) {
  return useQuery<LoanSubventionEnrollment>({
    queryKey: iifKeys.enrollment(id ?? ''),
    queryFn: () => enrollmentsApi.get(id as string),
    enabled: Boolean(id),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

function invalidateEnrollments(qc: ReturnType<typeof useQueryClient>, id?: string) {
  qc.invalidateQueries({ queryKey: ['lending', 'iif', 'enrollments'] });
  if (id) qc.invalidateQueries({ queryKey: iifKeys.enrollment(id) });
}

export function useCreateEnrollment(
  options?: UseMutationOptions<LoanSubventionEnrollment, unknown, EnrollmentCreate>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanSubventionEnrollment, unknown, EnrollmentCreate>({
    mutationFn: (payload) => enrollmentsApi.create(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateEnrollments(qc);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useApproveEnrollment(
  options?: UseMutationOptions<LoanSubventionEnrollment, unknown, { id: string; notes?: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanSubventionEnrollment, unknown, { id: string; notes?: string }>({
    mutationFn: ({ id, notes }) => enrollmentsApi.approve(id, notes),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateEnrollments(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useRejectEnrollment(
  options?: UseMutationOptions<LoanSubventionEnrollment, unknown, { id: string; reason: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanSubventionEnrollment, unknown, { id: string; reason: string }>({
    mutationFn: ({ id, reason }) => enrollmentsApi.reject(id, reason),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateEnrollments(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useSuspendEnrollment(
  options?: UseMutationOptions<LoanSubventionEnrollment, unknown, { id: string; reason: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanSubventionEnrollment, unknown, { id: string; reason: string }>({
    mutationFn: ({ id, reason }) => enrollmentsApi.suspend(id, reason),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateEnrollments(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useReinstateEnrollment(
  options?: UseMutationOptions<LoanSubventionEnrollment, unknown, { id: string; notes?: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanSubventionEnrollment, unknown, { id: string; notes?: string }>({
    mutationFn: ({ id, notes }) => enrollmentsApi.reinstate(id, notes),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateEnrollments(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useEligibilityCheck(
  options?: UseMutationOptions<
    EligibilityCheckResult,
    unknown,
    { loanAccountId: string; schemeId: string }
  >,
) {
  const { toast } = useToast();
  return useMutation<EligibilityCheckResult, unknown, { loanAccountId: string; schemeId: string }>({
    mutationFn: (payload) => enrollmentsApi.eligibilityCheck(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
  });
}

// ============================================================================
// Claims
// ============================================================================

export function useClaims(params?: ClaimListParams) {
  return useQuery<PaginatedList<SubventionClaim>>({
    queryKey: iifKeys.claims(params),
    queryFn: () => claimsApi.list(params),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useClaim(id: string | undefined) {
  return useQuery<SubventionClaim>({
    queryKey: iifKeys.claim(id ?? ''),
    queryFn: () => claimsApi.get(id as string),
    enabled: Boolean(id),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useEligibleLoans(params?: { page?: number; pageSize?: number }) {
  return useQuery<EligibleLoan[]>({
    queryKey: iifKeys.eligibleLoans(params),
    queryFn: () => claimsApi.getEligibleLoans(params),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useComputeClaim(
  options?: UseMutationOptions<ClaimComputePreview, unknown, ClaimComputePayload>,
) {
  const { toast } = useToast();
  return useMutation<ClaimComputePreview, unknown, ClaimComputePayload>({
    mutationFn: (payload) => claimsApi.compute(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
  });
}

function invalidateClaims(qc: ReturnType<typeof useQueryClient>, id?: string) {
  qc.invalidateQueries({ queryKey: ['lending', 'iif', 'claims'] });
  if (id) qc.invalidateQueries({ queryKey: iifKeys.claim(id) });
}

export function useCreateClaim(
  options?: UseMutationOptions<SubventionClaim, unknown, ClaimCreatePayload>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionClaim, unknown, ClaimCreatePayload>({
    mutationFn: (payload) => claimsApi.create(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateClaims(qc);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useSubmitClaim(options?: UseMutationOptions<SubventionClaim, unknown, string>) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionClaim, unknown, string>({
    mutationFn: (id) => claimsApi.submit(id),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, id, onMutateResult, ctx) => {
      invalidateClaims(qc, id);
      options?.onSuccess?.(data, id, onMutateResult, ctx);
    },
  });
}

export function useVerifyClaim(
  options?: UseMutationOptions<
    SubventionClaim,
    unknown,
    { id: string; decision: 'APPROVE' | 'REJECT'; reason?: string | null }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    SubventionClaim,
    unknown,
    { id: string; decision: 'APPROVE' | 'REJECT'; reason?: string | null }
  >({
    mutationFn: ({ id, decision, reason }) => claimsApi.verify(id, { decision, reason }),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateClaims(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useInitiateClaimRelease(
  options?: UseMutationOptions<
    SubventionClaim,
    unknown,
    { id: string; payload: ClaimInitiateReleasePayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    SubventionClaim,
    unknown,
    { id: string; payload: ClaimInitiateReleasePayload }
  >({
    mutationFn: ({ id, payload }) => claimsApi.initiateRelease(id, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateClaims(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useMarkClaimReleased(
  options?: UseMutationOptions<
    SubventionClaim,
    unknown,
    { id: string; payload: ClaimMarkPaidPayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionClaim, unknown, { id: string; payload: ClaimMarkPaidPayload }>({
    mutationFn: ({ id, payload }) => claimsApi.markReleased(id, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateClaims(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useCancelClaim(
  options?: UseMutationOptions<SubventionClaim, unknown, { id: string; reason: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<SubventionClaim, unknown, { id: string; reason: string }>({
    mutationFn: ({ id, reason }) => claimsApi.cancel(id, reason),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateClaims(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}
