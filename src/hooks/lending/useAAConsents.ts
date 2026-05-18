/**
 * useAAConsents — list query for /lending/aa/consents.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type AAConsentStatusValue =
  | 'PENDING'
  | 'APPROVED'
  | 'ACTIVE'
  | 'REJECTED'
  | 'PAUSED'
  | 'REVOKED'
  | 'EXPIRED'
  | 'FAILED';

export type AAProviderValue = 'FINVU' | 'ONEMONEY' | 'SETU' | 'NADL' | 'CAMS_FINSERV' | 'PERFIOS';

export type AAPurposeValue =
  | 'UNDERWRITING'
  | 'MONITORING'
  | 'BANK_STATEMENT_ANALYSIS'
  | 'INCOME_VERIFICATION'
  | 'ACCOUNT_AGGREGATION';

export interface AAConsentListItem {
  id: string;
  consentHandle: string | null;
  consentId: string | null;
  customerId: string;
  customerName: string | null;
  customerMobile: string | null;
  provider: AAProviderValue;
  purpose: AAPurposeValue;
  fiTypes: string[];
  fiDataFrom: string | null;
  fiDataTo: string | null;
  status: AAConsentStatusValue;
  consentExpiry: string | null;
  entityName: string | null;
  loanApplicationNumber: string | null;
  fetchSessionCount: number;
  lastFetchAt: string | null;
  createdAt: string;
  approvedAt: string | null;
  rejectedAt: string | null;
  revokedAt: string | null;
}

export interface AAConsentFilters {
  status?: AAConsentStatusValue;
  provider?: AAProviderValue;
  page?: number;
  pageSize?: number;
}

export const aaConsentsQueryKey = (filters?: AAConsentFilters) =>
  ['lending', 'aa', 'consents', filters ?? {}] as const;

async function fetchConsents(filters?: AAConsentFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.provider) params.append('provider', filters.provider);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<AAConsentListItem>>(
    `/lending/aa/consents?${params.toString()}`,
  );
  return data;
}

export function useAAConsents(filters?: AAConsentFilters) {
  return useQuery<PaginatedResponse<AAConsentListItem>>({
    queryKey: aaConsentsQueryKey(filters),
    queryFn: () => fetchConsents(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
