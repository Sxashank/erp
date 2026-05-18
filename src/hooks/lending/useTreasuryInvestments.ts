/**
 * useTreasuryInvestments — react-query hooks for the treasury investment
 * portfolio (`/lending/treasury/investments/*`).
 *
 * Hooks follow the CLAUDE.md §5.4 contract — pages never call axios
 * directly. Mutations invalidate the list + summary on success so the
 * UI stays consistent. Error handling is left to the caller via the
 * mutation's `onError` so it can surface the
 * `{error_code, message, correlation_id}` envelope via `showErrorToast`.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  type InvestmentCreateRequest,
  type InvestmentFilters,
  type InvestmentListResponse,
  type InvestmentMatureRequest,
  type InvestmentMaturityResponse,
  type InvestmentResponse,
  type PortfolioSummaryResponse,
  createInvestment,
  getInvestment,
  getMaturitySchedule,
  getPortfolioSummary,
  listInvestments,
  markMatured,
} from '@/services/lending/treasuryInvestmentApi';

// --------------------------------------------------------------------------
// Query keys
// --------------------------------------------------------------------------

export const investmentsBaseKey = ['lending', 'treasury', 'investments'] as const;

export const investmentsQueryKey = (filters?: InvestmentFilters) =>
  [...investmentsBaseKey, 'list', filters ?? {}] as const;

export const investmentQueryKey = (id: string) => [...investmentsBaseKey, 'detail', id] as const;

export const investmentPortfolioSummaryKey = () =>
  [...investmentsBaseKey, 'portfolio-summary'] as const;

export const investmentMaturityKey = (months: number) =>
  [...investmentsBaseKey, 'maturity', months] as const;

// --------------------------------------------------------------------------
// Queries
// --------------------------------------------------------------------------

export function useInvestments(filters?: InvestmentFilters) {
  return useQuery<InvestmentListResponse>({
    queryKey: investmentsQueryKey(filters),
    queryFn: () => listInvestments(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useInvestment(id: string | undefined) {
  return useQuery<InvestmentResponse>({
    queryKey: investmentQueryKey(id ?? ''),
    queryFn: () => getInvestment(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortfolioSummary() {
  return useQuery<PortfolioSummaryResponse>({
    queryKey: investmentPortfolioSummaryKey(),
    queryFn: () => getPortfolioSummary(),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useMaturitySchedule(months = 12) {
  return useQuery<InvestmentMaturityResponse>({
    queryKey: investmentMaturityKey(months),
    queryFn: () => getMaturitySchedule(months),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

// --------------------------------------------------------------------------
// Mutations
// --------------------------------------------------------------------------

/**
 * Create an investment.
 *
 * Service layer (`createInvestment`) injects the `Idempotency-Key` header
 * on every call (CLAUDE.md §6.3). On success we invalidate every list +
 * portfolio-summary + maturity query so the new investment appears
 * everywhere immediately.
 *
 * Error envelope `{error_code, message, correlation_id}` is left on the
 * thrown AxiosError so callers can pipe it through `showErrorToast` from
 * `@/lib/errorToast`.
 */
export function useCreateInvestment() {
  const queryClient = useQueryClient();
  return useMutation<InvestmentResponse, unknown, InvestmentCreateRequest>({
    mutationFn: (payload) => createInvestment(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: investmentsBaseKey });
    },
  });
}

/**
 * Mark an investment matured / sold.
 */
export function useMarkMatured() {
  const queryClient = useQueryClient();
  return useMutation<
    InvestmentResponse,
    unknown,
    { id: string; payload?: InvestmentMatureRequest }
  >({
    mutationFn: ({ id, payload }) => markMatured(id, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: investmentsBaseKey });
      // Also nudge the specific detail key so the open detail page refreshes.
      void queryClient.invalidateQueries({
        queryKey: investmentQueryKey(variables.id),
      });
    },
  });
}
