/**
 * useTreasurySummary — aggregator for /lending/treasury/summary.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display arithmetic.
export interface BorrowingSummary {
  totalSanctioned: string;
  totalDrawn: string;
  totalAvailable: string;
  totalOutstanding: string;
  activeBorrowings: number;
  lenderCount: number;
  weightedAvgRate: string | null;
  upcomingRepayments30D: string;
  upcomingMaturities90D: number;
}

export interface ALMGapBucket {
  bucket: string;
  assets: string;
  liabilities: string;
  gap: string;
  cumulativeGap: string;
  gapPercent: string;
}

export interface ALMSummary {
  positionDate: string;
  totalAssets: string;
  totalLiabilities: string;
  netPosition: string;
  cumulativeGap1Year: string;
  cumulativeGapPercent: string;
  gapAnalysis: ALMGapBucket[];
}

export interface TopExposure {
  type?: string;
  key?: string;
  exposure?: number | string;
  status?: string;
  lenderName?: string;
  // Exposure summary percent fields come from a free-form dict on the BE;
  // tolerate either shape.
  exposurePercent?: number | string;
  limitPercent?: number | string;
}

export interface ExposureSummary {
  totalLimits: number;
  withinLimit: number;
  nearLimit: number;
  breachCount: number;
  totalExposure: string;
  topExposures: TopExposure[];
}

export interface TreasurySummaryResponse {
  borrowingSummary: BorrowingSummary;
  almSummary: ALMSummary | null;
  exposureSummary: ExposureSummary;
}

export const treasurySummaryQueryKey = ['lending', 'treasury', 'summary'] as const;

async function fetchTreasurySummary(): Promise<TreasurySummaryResponse> {
  const { data } = await api.get<TreasurySummaryResponse>('/lending/treasury/summary');
  return data;
}

export function useTreasurySummary() {
  return useQuery<TreasurySummaryResponse>({
    queryKey: treasurySummaryQueryKey,
    queryFn: fetchTreasurySummary,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
