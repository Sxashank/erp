/**
 * useRestructures — list query for /lending/collections/restructures.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type RestructureStatusValue =
  | 'DRAFT'
  | 'PROPOSED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'IMPLEMENTED'
  | 'CANCELLED';

export type RestructureTypeValue =
  | 'TENURE_EXTENSION'
  | 'RATE_REDUCTION'
  | 'EMI_REDUCTION'
  | 'MORATORIUM'
  | 'FITL'
  | 'COMPREHENSIVE'
  | 'OTHER';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display arithmetic.
export interface RestructureListItem {
  id: string;
  restructureReference: string;
  restructureType: RestructureTypeValue;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  proposalDate: string;
  status: RestructureStatusValue;
  preOutstandingPrincipal: string;
  postOutstandingPrincipal: string;
  preInterestRate: string;
  postInterestRate: string;
  preTenureMonths: number;
  postTenureMonths: number;
  moratoriumMonths: number;
  isStandardRestructure: boolean;
  approvalDate: string | null;
  implementationDate: string | null;
}

export interface RestructureFilters {
  status?: RestructureStatusValue;
  page?: number;
  pageSize?: number;
}

export const restructuresQueryKey = (filters?: RestructureFilters) =>
  ['lending', 'collections', 'restructures', filters ?? {}] as const;

async function fetchRestructures(filters?: RestructureFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<RestructureListItem>>(
    `/lending/collections/restructures?${params.toString()}`,
  );
  return data;
}

export function useRestructures(filters?: RestructureFilters) {
  return useQuery<PaginatedResponse<RestructureListItem>>({
    queryKey: restructuresQueryKey(filters),
    queryFn: () => fetchRestructures(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
