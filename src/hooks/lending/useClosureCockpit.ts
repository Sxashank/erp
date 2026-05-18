import { useQuery } from '@tanstack/react-query';

import {
  getClosureCockpit,
  type ClosureCockpitFilters,
  type ClosureCockpitResponse,
} from '@/services/lending/closureCockpitApi';

export const closureCockpitQueryKeys = {
  all: ['lending', 'closure-cockpit'] as const,
  detail: (filters: ClosureCockpitFilters) => [...closureCockpitQueryKeys.all, filters] as const,
};

export function useClosureCockpit(filters: ClosureCockpitFilters = {}) {
  return useQuery<ClosureCockpitResponse>({
    queryKey: closureCockpitQueryKeys.detail(filters),
    queryFn: () => getClosureCockpit(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
