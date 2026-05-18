import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createFundDeployment,
  getFundDeployments,
  getFundDeploymentProfitability,
  getFundDeploymentSummary,
  type FundDeployment,
  type FundDeploymentCreateBody,
  type FundDeploymentFilters,
  type FundProfitabilityResponse,
  type FundDeploymentSummary,
} from '@/services/lending/fundDeploymentApi';
import type { PaginatedResponse } from '@/types/lending';

export const fundDeploymentSummaryQueryKey = () =>
  ['lending', 'treasury', 'fund-deployments', 'summary'] as const;

export const fundDeploymentsQueryKey = (filters: FundDeploymentFilters = {}) =>
  ['lending', 'treasury', 'fund-deployments', filters] as const;

export const fundDeploymentProfitabilityQueryKey = (limit = 50) =>
  ['lending', 'treasury', 'fund-deployments', 'profitability', limit] as const;

export function useFundDeploymentSummary() {
  return useQuery<FundDeploymentSummary>({
    queryKey: fundDeploymentSummaryQueryKey(),
    queryFn: getFundDeploymentSummary,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFundDeployments(filters: FundDeploymentFilters = {}) {
  return useQuery<PaginatedResponse<FundDeployment>>({
    queryKey: fundDeploymentsQueryKey(filters),
    queryFn: () => getFundDeployments(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFundDeploymentProfitability(limit = 50) {
  return useQuery<FundProfitabilityResponse>({
    queryKey: fundDeploymentProfitabilityQueryKey(limit),
    queryFn: () => getFundDeploymentProfitability(limit),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateFundDeployment() {
  const queryClient = useQueryClient();
  return useMutation<FundDeployment, unknown, FundDeploymentCreateBody>({
    mutationFn: createFundDeployment,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['lending', 'treasury', 'fund-deployments'],
      });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'treasury'] });
    },
  });
}
