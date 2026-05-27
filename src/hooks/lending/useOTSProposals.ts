/**
 * useOTSProposals — list query for /lending/collections/ots-proposals.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type OTSStatusValue =
  | 'DRAFT'
  | 'PROPOSED'
  | 'NEGOTIATION'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'ACCEPTED'
  | 'CANCELLED'
  | 'COMPLETED'
  | 'DEFAULTED';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
export interface OTSProposalListItem {
  id: string;
  otsReference: string;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  proposalDate: string;
  status: OTSStatusValue;
  totalOutstanding: string;
  otsAmount: string;
  haircutAmount: string;
  haircutPercent: string;
  upfrontAmount: string;
  numberOfInstallments: number;
  validTill: string;
  totalReceived: string;
  balancePending: string;
  approvalDate: string | null;
}

export interface OTSFilters {
  status?: OTSStatusValue;
  page?: number;
  pageSize?: number;
}

export const otsProposalsQueryKey = (filters?: OTSFilters) =>
  ['lending', 'collections', 'ots-proposals', filters ?? {}] as const;

async function fetchOTS(filters?: OTSFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<OTSProposalListItem>>(
    `/lending/collections/ots-proposals?${params.toString()}`,
  );
  return data;
}

export function useOTSProposals(filters?: OTSFilters) {
  return useQuery<PaginatedResponse<OTSProposalListItem>>({
    queryKey: otsProposalsQueryKey(filters),
    queryFn: () => fetchOTS(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
