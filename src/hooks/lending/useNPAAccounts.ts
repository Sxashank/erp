/**
 * useNPAAccounts — list query for /lending/collections/npa-accounts.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * Source: LoanAccount filtered to NPA-grade classifications, joined to
 * NPARecord for provision data.
 * See CLAUDE.md §4.8 for the NPA bucket math and §5.4 for the FE pattern.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type NPAClassificationValue =
  | 'SUBSTANDARD'
  | 'DOUBTFUL_1'
  | 'DOUBTFUL_2'
  | 'DOUBTFUL_3'
  | 'LOSS';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
export interface NPAAccountListItem {
  id: string;
  loanAccountId: string;
  loanAccountNumber: string;
  entityId: string | null;
  entityName: string | null;
  productId: string | null;
  productName: string | null;
  totalOutstanding: string;
  principalOutstanding: string;
  daysPastDue: number;
  classification: NPAClassificationValue;
  npaDate: string | null;
  provisionRate: string | null;
  provisionAmount: string | null;
}

export interface NPAFilters {
  classification?: NPAClassificationValue;
  page?: number;
  pageSize?: number;
}

export const npaAccountsQueryKey = (filters?: NPAFilters) =>
  ['lending', 'collections', 'npa-accounts', filters ?? {}] as const;

async function fetchNPAAccounts(filters?: NPAFilters) {
  const params = new URLSearchParams();
  if (filters?.classification) params.append('classification', filters.classification);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<NPAAccountListItem>>(
    `/lending/collections/npa-accounts?${params.toString()}`,
  );
  return data;
}

export function useNPAAccounts(filters?: NPAFilters) {
  return useQuery<PaginatedResponse<NPAAccountListItem>>({
    queryKey: npaAccountsQueryKey(filters),
    queryFn: () => fetchNPAAccounts(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
