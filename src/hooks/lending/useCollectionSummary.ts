/**
 * Collection & recovery summary hooks.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Monetary fields are
 * JSON strings (Pydantic Decimal — CLAUDE.md §6.2).
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface CollectionActivitySummary {
  totalOverdueAccounts: number;
  totalOverdueAmount: string;
  pendingFollowUps: number;
  completedFollowUpsToday: number;
  ptpReceivedCount: number;
  ptpTotalAmount: string;
  collectionsToday: string;
  collectionsMtd: string;
}

export interface RecoverySummary {
  totalOtsProposals: number;
  approvedOts: number;
  completedOts: number;
  otsSettlementAmount: string;
  totalRestructures: number;
  approvedRestructures: number;
  implementedRestructures: number;
  totalLegalCases: number;
  pendingCases: number;
  decreeObtained: number;
  recoveryThroughLegal: string;
  totalWrittenOff?: string;
  recoveryFromWrittenOff?: string;
}

export function useCollectionSummary() {
  return useQuery<CollectionActivitySummary>({
    queryKey: ['lending', 'collections', 'summary', 'collection'] as const,
    queryFn: async () => {
      const { data } = await api.get<CollectionActivitySummary>(
        '/lending/collections/summary/collection',
      );
      return data;
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}

export function useRecoverySummary() {
  return useQuery<RecoverySummary>({
    queryKey: ['lending', 'collections', 'summary', 'recovery'] as const,
    queryFn: async () => {
      const { data } = await api.get<RecoverySummary>('/lending/collections/summary/recovery');
      return data;
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
