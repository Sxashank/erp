import { useQuery } from '@tanstack/react-query';

import { getRiskCockpit, type RiskCockpitResponse } from '@/services/lending/riskCockpitApi';

export const riskCockpitQueryKeys = {
  all: ['lending', 'risk-cockpit'] as const,
  detail: (topN: number) => [...riskCockpitQueryKeys.all, topN] as const,
};

export function useRiskCockpit(topN = 10) {
  return useQuery<RiskCockpitResponse>({
    queryKey: riskCockpitQueryKeys.detail(topN),
    queryFn: () => getRiskCockpit(topN),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
