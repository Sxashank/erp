/**
 * useAAProviders — read-only query for /lending/aa/providers. See CLAUDE.md §3.3, §5.4.
 *
 * Provider lookups are configuration data and rarely change during a
 * session, so the cache is held for 5 minutes.
 */

import { useQuery } from '@tanstack/react-query';

import { listProviders, type ListProvidersResponse } from '@/services/lending/aaApi';

export const aaProvidersQueryKey = ['lending', 'aa', 'providers'] as const;

export function useAAProviders() {
  return useQuery<ListProvidersResponse>({
    queryKey: aaProvidersQueryKey,
    queryFn: listProviders,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
