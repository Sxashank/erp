/**
 * useIrsPreview — non-persisting IRS preview for the dashboard.
 *
 * Wire shape is camelCase per Pydantic CamelSchema on the BE; Decimal fields
 * arrive as JSON strings (CLAUDE.md §6.2). Callers must coerce with
 * `Number(...)` at the chart/arithmetic boundary only.
 *
 * GET /lending/treasury/irs/preview?as_of_date=YYYY-MM-DD
 */

import { useQuery } from '@tanstack/react-query';

import { getIrsPreview, type IRSPreviewResponseWire } from '@/services/lending/treasuryApi';

export type IRSShockBucket = IRSPreviewResponseWire['shocks'][number];
export type IRSPreviewSummary = IRSPreviewResponseWire['summary'];
export type IRSPreviewResponse = IRSPreviewResponseWire;

export const irsPreviewQueryKey = (asOfDate?: string) =>
  ['lending', 'treasury', 'irs', 'preview', asOfDate ?? 'today'] as const;

export function useIrsPreview(asOfDate?: string) {
  return useQuery<IRSPreviewResponse>({
    queryKey: irsPreviewQueryKey(asOfDate),
    queryFn: () => getIrsPreview(asOfDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
