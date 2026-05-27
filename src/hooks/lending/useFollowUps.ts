/**
 * useFollowUps — list query for /lending/collections/follow-ups.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type FollowUpStatusValue =
  | 'SCHEDULED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'RESCHEDULED'
  | 'NO_RESPONSE'
  | 'PTP_RECEIVED';

export type FollowUpTypeValue =
  | 'CALL'
  | 'EMAIL'
  | 'SMS'
  | 'VISIT'
  | 'LETTER'
  | 'LEGAL_NOTICE'
  | 'OTHER';

export type CollectionStageValue = 'SOFT' | 'FOLLOWUP' | 'INTENSIVE' | 'LEGAL' | 'RECOVERY';

export type FollowUpOutcomeValue =
  | 'CONTACTED'
  | 'NOT_REACHABLE'
  | 'PROMISED_TO_PAY'
  | 'REFUSED_TO_PAY'
  | 'DISPUTED'
  | 'PARTIAL_PAYMENT'
  | 'FULL_PAYMENT'
  | 'REQUESTED_RESTRUCTURE'
  | 'REQUESTED_OTS'
  | 'OTHER';

export interface FollowUpListItem {
  id: string;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  followUpType: FollowUpTypeValue;
  collectionStage: CollectionStageValue;
  scheduledDate: string;
  scheduledTime: string | null;
  assignedToName: string | null;
  status: FollowUpStatusValue;
  executedDate: string | null;
  outcome: FollowUpOutcomeValue | null;
  ptpDate: string | null;
  // PTP amount is a JSON string on the wire (Pydantic Decimal — CLAUDE.md §6.2).
  ptpAmount: string | null;
  ptpBroken: boolean;
  contactPerson: string | null;
  contactNumber: string | null;
  nextFollowUpDate: string | null;
}

export interface FollowUpFilters {
  status?: FollowUpStatusValue;
  page?: number;
  pageSize?: number;
}

export const followUpsQueryKey = (filters?: FollowUpFilters) =>
  ['lending', 'collections', 'follow-ups', filters ?? {}] as const;

async function fetchFollowUps(filters?: FollowUpFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<FollowUpListItem>>(
    `/lending/collections/follow-ups?${params.toString()}`,
  );
  return data;
}

export function useFollowUps(filters?: FollowUpFilters) {
  return useQuery<PaginatedResponse<FollowUpListItem>>({
    queryKey: followUpsQueryKey(filters),
    queryFn: () => fetchFollowUps(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
