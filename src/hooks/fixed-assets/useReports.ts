import { useQuery } from '@tanstack/react-query';

import { getAssetRegisterReport, getDepreciationSummaryReport, type FixedAssetReportFilters } from '@/services/fixed-assets';
import type { AssetRegisterReport, DepreciationSummaryReport } from '@/types/fixed-assets';

export const fixedAssetRegisterQueryKey = (filters: FixedAssetReportFilters) =>
  ['fixed-assets', 'reports', filters.organizationId, 'asset-register', filters] as const;

export const fixedAssetDepSummaryQueryKey = (organizationId: string, depreciationPeriod: string) =>
  ['fixed-assets', 'reports', organizationId, 'depreciation-summary', depreciationPeriod] as const;

export function useAssetRegisterReport(filters: FixedAssetReportFilters) {
  return useQuery<AssetRegisterReport>({
    queryKey: fixedAssetRegisterQueryKey(filters),
    queryFn: () => getAssetRegisterReport(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDepreciationSummaryReport(
  organizationId: string,
  depreciationPeriod: string | undefined,
) {
  return useQuery<DepreciationSummaryReport>({
    queryKey: fixedAssetDepSummaryQueryKey(organizationId, depreciationPeriod ?? 'missing'),
    queryFn: () => getDepreciationSummaryReport(organizationId, depreciationPeriod!),
    enabled: Boolean(depreciationPeriod),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
