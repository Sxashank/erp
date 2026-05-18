/**
 * useCollateral — react-query hooks for `/lending/collaterals/*`.
 *
 * Mutations attach an `Idempotency-Key` header per CLAUDE.md §6.3.
 * Monetary fields are JSON strings on the wire (CLAUDE.md §6.2).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createCollateral,
  getCollateralsByLoan,
  getCoverage,
  updateValuation,
  type CollateralResponse,
  type CollateralsByLoanResponse,
  type CoverageResponse,
  type CreateCollateralRequest,
  type UpdateValuationRequest,
  type UpdateValuationResponse,
} from '@/services/lending/collateralApi';

// ============== Query keys ==============

export const collateralsByLoanQueryKey = (loanAccountId: string | undefined) =>
  ['lending', 'collaterals', 'by-loan', loanAccountId ?? null] as const;

export const collateralCoverageQueryKey = (sanctionId: string | undefined) =>
  ['lending', 'collaterals', 'coverage', sanctionId ?? null] as const;

// ============== Queries ==============

export function useCollateralsByLoan(loanAccountId: string | undefined) {
  return useQuery<CollateralsByLoanResponse>({
    queryKey: collateralsByLoanQueryKey(loanAccountId),
    queryFn: () => getCollateralsByLoan(loanAccountId as string),
    enabled: !!loanAccountId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCollateralCoverage(sanctionId: string | undefined) {
  return useQuery<CoverageResponse>({
    queryKey: collateralCoverageQueryKey(sanctionId),
    queryFn: () => getCoverage(sanctionId as string),
    enabled: !!sanctionId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

// ============== Mutations ==============

export function useCreateCollateral() {
  const queryClient = useQueryClient();
  return useMutation<CollateralResponse, unknown, CreateCollateralRequest>({
    mutationFn: (payload) => createCollateral(payload, crypto.randomUUID()),
    onSuccess: (_data, variables) => {
      // Invalidate list views that may depend on the affected sanction.
      void queryClient.invalidateQueries({ queryKey: ['lending', 'collaterals'] });
      void queryClient.invalidateQueries({
        queryKey: collateralCoverageQueryKey(variables.sanctionId),
      });
    },
  });
}

export function useUpdateValuation() {
  const queryClient = useQueryClient();
  return useMutation<UpdateValuationResponse, unknown, UpdateValuationRequest>({
    mutationFn: (payload) => updateValuation(payload, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'collaterals'] });
    },
  });
}
