/**
 * useLoanAccounts — list query for /lending/accounts.
 *
 * Wraps the existing `loanAccountApi.getLoanAccounts` service so pages
 * get react-query caching, loading state, and a typed error.
 *
 * The reference pattern for every other entity hook in this folder. Copy
 * the shape, change the service call + key, done.
 *
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import { getLoanAccounts, type LoanAccountListItem } from '@/services/lending/loanAccountApi';
import type { LoanAccountFilters, PaginatedResponse } from '@/types/lending';

/**
 * `filters` is part of the query key so changing pagination / search /
 * status invalidates the cache automatically.
 */
export const loanAccountsQueryKey = (filters?: LoanAccountFilters) =>
  ['lending', 'loan-accounts', filters ?? {}] as const;

export function useLoanAccounts(filters?: LoanAccountFilters) {
  return useQuery<PaginatedResponse<LoanAccountListItem>>({
    queryKey: loanAccountsQueryKey(filters),
    queryFn: () => getLoanAccounts(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
