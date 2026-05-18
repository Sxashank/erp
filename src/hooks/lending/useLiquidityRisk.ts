/**
 * Liquidity Risk hooks — react-query wrappers for the LCR / NSFR /
 * cash-flow-ladder / funding-concentration endpoints.
 *
 * Snapshots are read-only and recompute on every call on the backend; we
 * cache them for 15 minutes (staleTime 15 * 60_000) to avoid re-issuing the
 * heavy aggregations on every tab switch. See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import {
  getCashflowLadder,
  getFundingConcentration,
  getLcrSnapshot,
  getNsfrSnapshot,
  type CashflowLadderSnapshot,
  type FundingConcentrationSnapshot,
  type LCRSnapshot,
  type NSFRSnapshot,
} from '@/services/lending/liquidityRiskApi';

const STALE_TIME_MS = 15 * 60 * 1000;

export const liquidityRiskKeys = {
  all: ['lending', 'liquidity-risk'] as const,
  lcr: (asOfDate?: string) => ['lending', 'liquidity-risk', 'lcr', asOfDate ?? 'today'] as const,
  nsfr: (asOfDate?: string) => ['lending', 'liquidity-risk', 'nsfr', asOfDate ?? 'today'] as const,
  cashflow: (asOfDate?: string) =>
    ['lending', 'liquidity-risk', 'cashflow', asOfDate ?? 'today'] as const,
  concentration: (topN: number, asOfDate?: string) =>
    ['lending', 'liquidity-risk', 'concentration', topN, asOfDate ?? 'today'] as const,
};

export function useLcr(asOfDate?: string) {
  return useQuery<LCRSnapshot>({
    queryKey: liquidityRiskKeys.lcr(asOfDate),
    queryFn: () => getLcrSnapshot(asOfDate),
    staleTime: STALE_TIME_MS,
    refetchOnWindowFocus: false,
  });
}

export function useNsfr(asOfDate?: string) {
  return useQuery<NSFRSnapshot>({
    queryKey: liquidityRiskKeys.nsfr(asOfDate),
    queryFn: () => getNsfrSnapshot(asOfDate),
    staleTime: STALE_TIME_MS,
    refetchOnWindowFocus: false,
  });
}

export function useCashflowLadder(asOfDate?: string) {
  return useQuery<CashflowLadderSnapshot>({
    queryKey: liquidityRiskKeys.cashflow(asOfDate),
    queryFn: () => getCashflowLadder(asOfDate),
    staleTime: STALE_TIME_MS,
    refetchOnWindowFocus: false,
  });
}

export function useFundingConcentration(topN = 10, asOfDate?: string) {
  return useQuery<FundingConcentrationSnapshot>({
    queryKey: liquidityRiskKeys.concentration(topN, asOfDate),
    queryFn: () => getFundingConcentration(topN, asOfDate),
    staleTime: STALE_TIME_MS,
    refetchOnWindowFocus: false,
  });
}
