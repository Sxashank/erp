import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getDepreciationRun,
  getDepreciationRunEntries,
  listDepreciationRuns,
  runDepreciation,
  submitDepreciationPosting,
  type DepreciationRunPayload,
} from '@/services/fixed-assets';
import type {
  DepreciationEntry,
  DepreciationPostingActionResponse,
  DepreciationRun,
  OffsetPaginatedResponse,
} from '@/types/fixed-assets';

export const depreciationRunsQueryKey = (organizationId: string) =>
  ['fixed-assets', 'depreciation-runs', organizationId] as const;

export const depreciationRunDetailQueryKey = (runId: string) =>
  ['fixed-assets', 'depreciation-run', runId] as const;

export const depreciationEntriesQueryKey = (runId: string) =>
  ['fixed-assets', 'depreciation-run', runId, 'entries'] as const;

export function useDepreciationRuns(organizationId: string, skip = 0, limit = 20) {
  return useQuery<OffsetPaginatedResponse<DepreciationRun>>({
    queryKey: [...depreciationRunsQueryKey(organizationId), skip, limit],
    queryFn: () => listDepreciationRuns(organizationId, { skip, limit }),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDepreciationRun(runId: string | undefined) {
  return useQuery<DepreciationRun>({
    queryKey: depreciationRunDetailQueryKey(runId ?? 'missing'),
    queryFn: () => getDepreciationRun(runId!),
    enabled: Boolean(runId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDepreciationRunEntries(runId: string | undefined, skip = 0, limit = 50) {
  return useQuery<OffsetPaginatedResponse<DepreciationEntry>>({
    queryKey: [...depreciationEntriesQueryKey(runId ?? 'missing'), skip, limit],
    queryFn: () => getDepreciationRunEntries(runId!, { skip, limit }),
    enabled: Boolean(runId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useRunDepreciation(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DepreciationRunPayload) => runDepreciation(payload),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: depreciationRunsQueryKey(organizationId) });
      queryClient.invalidateQueries({ queryKey: depreciationRunDetailQueryKey(run.id) });
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'reports', organizationId] });
    },
  });
}

export function useSubmitDepreciationPosting(organizationId: string, runId: string) {
  const queryClient = useQueryClient();
  return useMutation<DepreciationPostingActionResponse, unknown, void>({
    mutationFn: () => submitDepreciationPosting(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: depreciationRunsQueryKey(organizationId) });
      queryClient.invalidateQueries({ queryKey: depreciationRunDetailQueryKey(runId) });
      queryClient.invalidateQueries({ queryKey: depreciationEntriesQueryKey(runId) });
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'reports', organizationId] });
    },
  });
}
