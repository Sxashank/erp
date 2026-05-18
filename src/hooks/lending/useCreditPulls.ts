/**
 * useCreditPulls — list query + create mutation for /lending/credit/*.
 *
 * Wire format is camelCase per Pydantic CamelSchema. FastAPI query names are
 * translated only at the URLSearchParams boundary below.
 *
 * See CLAUDE.md §5.4 (one hook per server interaction), §6.3 (Idempotency-Key
 * on financial mutations — a bureau pull triggers a paid API call), §7 (error
 * envelope handled via `showErrorToast`).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '@/services/api';
import {
  createCreditPull,
  type CreateCreditPullRequest,
  type CreditPullDetail,
} from '@/services/lending/creditApi';
import type { PaginatedResponse } from '@/types/lending';

export type CreditPullStatusValue =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCESS'
  | 'FAILED'
  | 'NO_HIT'
  | 'EXPIRED';

export type CreditBureauValue = 'CIBIL' | 'EXPERIAN' | 'EQUIFAX' | 'CRIF';

export type PullTypeValue = 'SOFT' | 'HARD';

export type ScoreBandValue = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'VERY_POOR' | 'NA';

export interface CreditPullListItem {
  id: string;
  organizationId: string;
  entityId: string | null;
  loanApplicationId: string | null;
  bureau: CreditBureauValue;
  pullType: PullTypeValue;
  status: CreditPullStatusValue;
  customerName: string;
  panNumber: string | null;
  creditScore: number | null;
  scoreBand: ScoreBandValue | null;
  pulledAt: string | null;
  expiresAt: string | null;
  isValid: boolean;
  createdAt: string;
}

export interface CreditPullFilters {
  bureau?: CreditBureauValue;
  pullStatus?: CreditPullStatusValue;
  page?: number;
  pageSize?: number;
}

export const creditPullsQueryKey = (filters?: CreditPullFilters) =>
  ['lending', 'credit', 'pulls', filters ?? {}] as const;

async function fetchPulls(filters?: CreditPullFilters) {
  const params = new URLSearchParams();
  if (filters?.bureau) params.append('bureau', filters.bureau);
  if (filters?.pullStatus) params.append('pull_status', filters.pullStatus);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<CreditPullListItem>>(
    `/lending/credit/pulls?${params.toString()}`,
  );
  return data;
}

export function useCreditPulls(filters?: CreditPullFilters) {
  return useQuery<PaginatedResponse<CreditPullListItem>>({
    queryKey: creditPullsQueryKey(filters),
    queryFn: () => fetchPulls(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation hook for initiating a credit pull.
 *
 * Service layer (`createCreditPull`) injects the `Idempotency-Key` header on
 * every call (CLAUDE.md §6.3). On success we invalidate the list query so the
 * new pull appears immediately when the user lands on the result page.
 *
 * Backend error envelope `{ error_code, message, details, correlation_id }` is
 * surfaced via the AxiosError on the mutation; callers should pipe through
 * `showErrorToast` from `@/lib/errorToast` to render it.
 */
export function useCreateCreditPull() {
  const queryClient = useQueryClient();
  return useMutation<CreditPullDetail, unknown, CreateCreditPullRequest>({
    mutationFn: (payload) => createCreditPull(payload),
    onSuccess: () => {
      // Invalidate every variant of the pulls list query so any filter view
      // refetches and shows the new pull.
      void queryClient.invalidateQueries({
        queryKey: ['lending', 'credit', 'pulls'],
      });
    },
  });
}
