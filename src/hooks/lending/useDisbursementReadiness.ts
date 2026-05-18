import { useQuery } from '@tanstack/react-query';

import {
  getDisbursementReadiness,
  type DisbursementReadinessFilters,
  type DisbursementReadinessResponse,
} from '@/services/lending/disbursementReadinessApi';

export const disbursementReadinessQueryKeys = {
  all: ['lending', 'disbursement-readiness'] as const,
  detail: (filters: DisbursementReadinessFilters) =>
    [...disbursementReadinessQueryKeys.all, filters] as const,
};

export function useDisbursementReadiness(filters: DisbursementReadinessFilters = {}) {
  return useQuery<DisbursementReadinessResponse>({
    queryKey: disbursementReadinessQueryKeys.detail(filters),
    queryFn: () => getDisbursementReadiness(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
