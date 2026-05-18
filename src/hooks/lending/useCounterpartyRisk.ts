/**
 * Counterparty Risk react-query hooks (CLAUDE.md §5.4).
 *
 * The aggregates these endpoints return don't change every second — a
 * 5-minute staleTime keeps the table snappy without spamming the BE.
 */

import { useQuery } from '@tanstack/react-query';

import {
  getCounterpartyExposures,
  getLimitBreaches,
  getRatingDistribution,
  getSectorConcentration,
  type CounterpartyExposureResponse,
  type LimitBreachResponse,
  type RatingDistributionResponse,
  type SectorConcentrationResponse,
} from '@/services/lending/counterpartyRiskApi';

const STALE_TIME = 5 * 60 * 1000; // 5 minutes

export const counterpartyRiskKeys = {
  all: ['lending', 'risk', 'counterparty'] as const,
  exposures: (topN: number) => ['lending', 'risk', 'counterparty', 'exposures', topN] as const,
  sectors: () => ['lending', 'risk', 'counterparty', 'sectors'] as const,
  ratings: () => ['lending', 'risk', 'counterparty', 'ratings'] as const,
  breaches: () => ['lending', 'risk', 'counterparty', 'breaches'] as const,
};

export function useCounterpartyExposures(topN = 50) {
  return useQuery<CounterpartyExposureResponse>({
    queryKey: counterpartyRiskKeys.exposures(topN),
    queryFn: () => getCounterpartyExposures(topN),
    staleTime: STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useSectorConcentration() {
  return useQuery<SectorConcentrationResponse>({
    queryKey: counterpartyRiskKeys.sectors(),
    queryFn: getSectorConcentration,
    staleTime: STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useRatingDistribution() {
  return useQuery<RatingDistributionResponse>({
    queryKey: counterpartyRiskKeys.ratings(),
    queryFn: getRatingDistribution,
    staleTime: STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useLimitBreaches() {
  return useQuery<LimitBreachResponse>({
    queryKey: counterpartyRiskKeys.breaches(),
    queryFn: getLimitBreaches,
    staleTime: STALE_TIME,
    refetchOnWindowFocus: false,
  });
}
