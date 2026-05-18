import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  capitalizeFixedAsset,
  createFixedAsset,
  deleteFixedAsset,
  disposeFixedAsset,
  getAssetDepreciationHistory,
  getAssetDepreciationSchedule,
  getFixedAsset,
  impairFixedAsset,
  listFixedAssets,
  revalueFixedAsset,
  submitDisposal,
  transferFixedAsset,
  updateFixedAsset,
  type AssetCapitalizePayload,
  type AssetDisposePayload,
  type AssetImpairPayload,
  type AssetRevaluePayload,
  type AssetTransferPayload,
  type FixedAssetListFilters,
  type FixedAssetPayload,
} from '@/services/fixed-assets';
import type {
  AssetRevaluationRecord,
  AssetTransferRecord,
  DepreciationScheduleResponse,
  FixedAsset,
  OffsetPaginatedResponse,
  DepreciationEntry,
  DisposalActionResponse,
} from '@/types/fixed-assets';

export const fixedAssetsQueryKey = (filters: FixedAssetListFilters) =>
  ['fixed-assets', 'assets', filters] as const;

export const fixedAssetDetailQueryKey = (assetId: string) =>
  ['fixed-assets', 'asset', assetId] as const;

export const fixedAssetDepreciationHistoryKey = (assetId: string) =>
  ['fixed-assets', 'asset', assetId, 'depreciation-history'] as const;

export const fixedAssetDepreciationScheduleKey = (assetId: string) =>
  ['fixed-assets', 'asset', assetId, 'depreciation-schedule'] as const;

export function useFixedAssets(filters: FixedAssetListFilters) {
  return useQuery<OffsetPaginatedResponse<FixedAsset>>({
    queryKey: fixedAssetsQueryKey(filters),
    queryFn: () => listFixedAssets(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAsset(assetId: string | undefined) {
  return useQuery<FixedAsset>({
    queryKey: fixedAssetDetailQueryKey(assetId ?? 'missing'),
    queryFn: () => getFixedAsset(assetId!),
    enabled: Boolean(assetId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAssetDepreciationHistory(assetId: string | undefined) {
  return useQuery<OffsetPaginatedResponse<DepreciationEntry>>({
    queryKey: fixedAssetDepreciationHistoryKey(assetId ?? 'missing'),
    queryFn: () => getAssetDepreciationHistory(assetId!, { limit: 100 }),
    enabled: Boolean(assetId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAssetDepreciationSchedule(assetId: string | undefined) {
  return useQuery<DepreciationScheduleResponse>({
    queryKey: fixedAssetDepreciationScheduleKey(assetId ?? 'missing'),
    queryFn: () => getAssetDepreciationSchedule(assetId!),
    enabled: Boolean(assetId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

function invalidateAssetQueries(queryClient: ReturnType<typeof useQueryClient>, organizationId: string, assetId?: string) {
  queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'assets'] });
  queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'depreciation-runs', organizationId] });
  queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'disposals', organizationId] });
  queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'reports', organizationId] });
  if (assetId) {
    queryClient.invalidateQueries({ queryKey: fixedAssetDetailQueryKey(assetId) });
    queryClient.invalidateQueries({ queryKey: fixedAssetDepreciationHistoryKey(assetId) });
    queryClient.invalidateQueries({ queryKey: fixedAssetDepreciationScheduleKey(assetId) });
  }
}

export function useCreateFixedAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: FixedAssetPayload) => createFixedAsset(payload),
    onSuccess: (asset) => {
      invalidateAssetQueries(queryClient, asset.organizationId, asset.id);
    },
  });
}

export function useUpdateFixedAsset(assetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<FixedAssetPayload>) => updateFixedAsset(assetId, payload),
    onSuccess: (asset) => {
      invalidateAssetQueries(queryClient, asset.organizationId, asset.id);
    },
  });
}

export function useDeleteFixedAsset(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assetId: string) => deleteFixedAsset(assetId),
    onSuccess: () => invalidateAssetQueries(queryClient, organizationId),
  });
}

export function useCapitalizeFixedAsset(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssetCapitalizePayload) => capitalizeFixedAsset(assetId, payload),
    onSuccess: (asset) => invalidateAssetQueries(queryClient, organizationId, asset.id),
  });
}

export function useTransferFixedAsset(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation<AssetTransferRecord, unknown, AssetTransferPayload>({
    mutationFn: (payload) => transferFixedAsset(assetId, payload),
    onSuccess: () => invalidateAssetQueries(queryClient, organizationId, assetId),
  });
}

export function useRevalueFixedAsset(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation<AssetRevaluationRecord, unknown, AssetRevaluePayload>({
    mutationFn: (payload) => revalueFixedAsset(assetId, payload),
    onSuccess: () => invalidateAssetQueries(queryClient, organizationId, assetId),
  });
}

export function useImpairFixedAsset(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation<AssetRevaluationRecord, unknown, AssetImpairPayload>({
    mutationFn: (payload) => impairFixedAsset(assetId, payload),
    onSuccess: () => invalidateAssetQueries(queryClient, organizationId, assetId),
  });
}

export function useDisposeFixedAsset(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation<FixedAsset, unknown, AssetDisposePayload>({
    mutationFn: (payload) => disposeFixedAsset(assetId, payload),
    onSuccess: (asset) => invalidateAssetQueries(queryClient, organizationId, asset.id),
  });
}

export function useSubmitDisposal(assetId: string, organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation<DisposalActionResponse, unknown, AssetDisposePayload>({
    mutationFn: (payload) => submitDisposal(assetId, payload),
    onSuccess: () => invalidateAssetQueries(queryClient, organizationId, assetId),
  });
}
