/**
 * useLegalCases — list query for /lending/collections/legal-cases.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type LegalCaseStatusValue =
  | 'DRAFT'
  | 'NOTICE_ISSUED'
  | 'FILED'
  | 'PENDING'
  | 'INTERIM_ORDER'
  | 'DECREE_OBTAINED'
  | 'EXECUTION'
  | 'SETTLED'
  | 'DISMISSED';

export type LegalCaseTypeValue =
  | 'SARFAESI'
  | 'DRT_APPLICATION'
  | 'RECOVERY_SUIT'
  | 'WINDING_UP'
  | 'IBC'
  | 'ARBITRATION'
  | 'EXECUTION'
  | 'APPEAL';

export type LegalForumValue =
  | 'DRT'
  | 'NCLT'
  | 'CIVIL_COURT'
  | 'HIGH_COURT'
  | 'ARBITRATION'
  | 'LOK_ADALAT';

export interface LegalCaseListItem {
  id: string;
  caseReference: string;
  caseNumber: string | null;
  caseType: LegalCaseTypeValue;
  forumType: LegalForumValue;
  courtName: string;
  courtLocation: string;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  status: LegalCaseStatusValue;
  filingDate: string | null;
  nextHearingDate: string | null;
  // Monetary fields are JSON strings on the wire (Pydantic Decimal —
  // CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
  totalClaim: string;
  recoveryThroughCase: string;
  advocateName: string | null;
  lawFirm: string | null;
}

export interface LegalCaseFilters {
  status?: LegalCaseStatusValue;
  caseType?: LegalCaseTypeValue;
  page?: number;
  pageSize?: number;
}

export const legalCasesQueryKey = (filters?: LegalCaseFilters) =>
  ['lending', 'collections', 'legal-cases', filters ?? {}] as const;

async function fetchLegalCases(filters?: LegalCaseFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.caseType) params.append('case_type', filters.caseType);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<LegalCaseListItem>>(
    `/lending/collections/legal-cases?${params.toString()}`,
  );
  return data;
}

export function useLegalCases(filters?: LegalCaseFilters) {
  return useQuery<PaginatedResponse<LegalCaseListItem>>({
    queryKey: legalCasesQueryKey(filters),
    queryFn: () => fetchLegalCases(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
