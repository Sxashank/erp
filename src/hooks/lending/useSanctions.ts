/**
 * useSanctions — list query for /lending/sanctions.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import { getSanctions, type SanctionListItem } from '@/services/lending/sanctionApi';
import type { SanctionFilters, PaginatedResponse } from '@/types/lending';

export const sanctionsQueryKey = (filters?: SanctionFilters) =>
  ['lending', 'sanctions', filters ?? {}] as const;

export function useSanctions(filters?: SanctionFilters) {
  return useQuery<PaginatedResponse<SanctionListItem>>({
    queryKey: sanctionsQueryKey(filters),
    queryFn: () => getSanctions(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
