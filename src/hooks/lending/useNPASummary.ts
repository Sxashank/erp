/**
 * useNPASummary — query for /lending/collections/summary/npa.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Monetary + rate
 * fields are JSON strings (Pydantic Decimal — CLAUDE.md §6.2).
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface NPASummaryResponse {
  totalNpaAccounts: number;
  totalNpaAmount: string;
  grossNpaRatio: string;
  netNpaRatio: string;
  totalProvisionHeld: string;
  provisionCoverageRatio: string;

  sma0Count: number;
  sma0Amount: string;
  sma1Count: number;
  sma1Amount: string;
  sma2Count: number;
  sma2Amount: string;

  substandardCount: number;
  substandardAmount: string;
  doubtful1Count: number;
  doubtful1Amount: string;
  doubtful2Count: number;
  doubtful2Amount: string;
  doubtful3Count: number;
  doubtful3Amount: string;
  lossCount: number;
  lossAmount: string;

  totalLoans: number;
  standardCount: number;
  standardAmount: string;
}

export const npaSummaryQueryKey = ['lending', 'collections', 'summary', 'npa'] as const;

async function fetchNPASummary(): Promise<NPASummaryResponse> {
  const { data } = await api.get<NPASummaryResponse>('/lending/collections/summary/npa');
  return data;
}

export function useNPASummary() {
  return useQuery<NPASummaryResponse>({
    queryKey: npaSummaryQueryKey,
    queryFn: fetchNPASummary,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
