/**
 * Regulatory report hooks — read-only react-query wrappers around
 * `/api/v1/reports/regulatory/*`.
 *
 * Errors are surfaced through the standard backend envelope
 * `{ error_code, message, correlation_id }`. Pages render `<ErrorState>`
 * directly from `query.error`; mutating callers (none here yet) would use
 * `showErrorToast` from `@/lib/errorToast`. See CLAUDE.md §5.4 / §9.7.
 */

import { useQuery } from '@tanstack/react-query';

import {
  getAlm,
  getCrar,
  getCrarComposition,
  getCrarTrend,
  getInfrastructureRatio,
  getLargeExposure,
  getLiquidity,
  getNpa,
  getSectorExposure,
  type ALMParams,
  type ALMReport,
  type CRARParams,
  type CRARReport,
  type CapitalCompositionResponse,
  type CrarCompositionParams,
  type CrarTrendParams,
  type CrarTrendResponse,
  type InfrastructureRatioParams,
  type InfrastructureRatioResponse,
  type LargeExposureParams,
  type LargeExposureReport,
  type LiquidityParams,
  type LiquidityReport,
  type NPAParams,
  type NPAReport,
  type SectorExposureParams,
  type SectorExposureReport,
} from '@/services/reports/regulatoryApi';

/** Cache lifetimes: regulatory reports are heavy aggregates that change
 *  slowly; an hour of staleness is reasonable for cold-start dashboards. */
const REGULATORY_STALE_MS = 60 * 60_000;

/** Query-key prefix shared by every regulatory hook so a future
 *  `queryClient.invalidateQueries(['reports', 'regulatory'])` purges all
 *  of them in one call (e.g. when the org changes). */
const KEY_ROOT = ['reports', 'regulatory'] as const;

export function useCrar(params?: CRARParams) {
  return useQuery<CRARReport>({
    queryKey: [...KEY_ROOT, 'crar', params?.as_of_date ?? 'today'] as const,
    queryFn: () => getCrar(params),
    staleTime: REGULATORY_STALE_MS,
  });
}

export function useAlm(params?: ALMParams) {
  return useQuery<ALMReport>({
    queryKey: [
      ...KEY_ROOT,
      'alm',
      params?.as_of_date ?? 'today',
      params?.report_type ?? 'STRUCTURAL',
    ] as const,
    queryFn: () => getAlm(params),
    staleTime: REGULATORY_STALE_MS,
  });
}

export function useNpa(params?: NPAParams) {
  return useQuery<NPAReport>({
    queryKey: [
      ...KEY_ROOT,
      'npa',
      params?.as_of_date ?? 'today',
      params?.detailed ?? false,
    ] as const,
    queryFn: () => getNpa(params),
    staleTime: REGULATORY_STALE_MS,
  });
}

export function useLiquidity(params?: LiquidityParams) {
  return useQuery<LiquidityReport>({
    queryKey: [...KEY_ROOT, 'liquidity', params?.as_of_date ?? 'today'] as const,
    queryFn: () => getLiquidity(params),
    staleTime: REGULATORY_STALE_MS,
  });
}

export function useLargeExposure(params?: LargeExposureParams) {
  return useQuery<LargeExposureReport>({
    queryKey: [
      ...KEY_ROOT,
      'large-exposure',
      params?.as_of_date ?? 'today',
      params?.threshold_percentage ?? 10,
    ] as const,
    queryFn: () => getLargeExposure(params),
    staleTime: REGULATORY_STALE_MS,
  });
}

/** CRAR sub-section caches — sub-30-minute staleness is fine; these aggregates
 *  shift slowly and never via in-page mutation. */
const CRAR_SUBSECTION_STALE_MS = 30 * 60_000;

export function useCrarComposition(params?: CrarCompositionParams) {
  return useQuery<CapitalCompositionResponse>({
    queryKey: [...KEY_ROOT, 'crar', 'composition', params?.as_of_date ?? 'today'] as const,
    queryFn: () => getCrarComposition(params),
    staleTime: CRAR_SUBSECTION_STALE_MS,
  });
}

export function useCrarTrend(params?: CrarTrendParams) {
  return useQuery<CrarTrendResponse>({
    queryKey: [...KEY_ROOT, 'crar', 'trend', params?.months ?? 12] as const,
    queryFn: () => getCrarTrend(params),
    staleTime: CRAR_SUBSECTION_STALE_MS,
  });
}

export function useInfrastructureRatio(params?: InfrastructureRatioParams) {
  return useQuery<InfrastructureRatioResponse>({
    queryKey: [...KEY_ROOT, 'crar', 'infrastructure-ratio', params?.as_of_date ?? 'today'] as const,
    queryFn: () => getInfrastructureRatio(params),
    staleTime: CRAR_SUBSECTION_STALE_MS,
  });
}

export function useSectorExposure(params?: SectorExposureParams) {
  return useQuery<SectorExposureReport>({
    queryKey: [...KEY_ROOT, 'sector-exposure', params?.as_of_date ?? 'today'] as const,
    queryFn: () => getSectorExposure(params),
    staleTime: REGULATORY_STALE_MS,
  });
}
