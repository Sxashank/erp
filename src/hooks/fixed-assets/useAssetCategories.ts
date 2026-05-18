import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createAssetCategory,
  deleteAssetCategory,
  getAssetCategory,
  getAssetCategoryTree,
  listAssetCategories,
  updateAssetCategory,
  type AssetCategoryPayload,
} from '@/services/fixed-assets';
import type { OffsetPaginatedResponse, AssetCategory, AssetCategoryTreeNode } from '@/types/fixed-assets';

export const assetCategoriesQueryKey = (organizationId: string) =>
  ['fixed-assets', 'categories', organizationId] as const;

export const assetCategoryTreeQueryKey = (organizationId: string) =>
  ['fixed-assets', 'category-tree', organizationId] as const;

export const assetCategoryDetailQueryKey = (categoryId: string) =>
  ['fixed-assets', 'category', categoryId] as const;

export function useAssetCategories(organizationId: string) {
  return useQuery<OffsetPaginatedResponse<AssetCategory>>({
    queryKey: assetCategoriesQueryKey(organizationId),
    queryFn: () => listAssetCategories({ organizationId, limit: 500 }),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useAssetCategoryTree(organizationId: string) {
  return useQuery<AssetCategoryTreeNode[]>({
    queryKey: assetCategoryTreeQueryKey(organizationId),
    queryFn: () => getAssetCategoryTree(organizationId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useAssetCategory(categoryId: string | undefined) {
  return useQuery<AssetCategory>({
    queryKey: assetCategoryDetailQueryKey(categoryId ?? 'missing'),
    queryFn: () => getAssetCategory(categoryId!),
    enabled: Boolean(categoryId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateAssetCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssetCategoryPayload) => createAssetCategory(payload),
    onSuccess: (category) => {
      queryClient.invalidateQueries({
        queryKey: assetCategoriesQueryKey(category.organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: assetCategoryTreeQueryKey(category.organizationId),
      });
    },
  });
}

export function useUpdateAssetCategory(categoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<AssetCategoryPayload>) => updateAssetCategory(categoryId, payload),
    onSuccess: (category) => {
      queryClient.invalidateQueries({
        queryKey: assetCategoriesQueryKey(category.organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: assetCategoryTreeQueryKey(category.organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: assetCategoryDetailQueryKey(category.id),
      });
    },
  });
}

export function useDeleteAssetCategory(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (categoryId: string) => deleteAssetCategory(categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: assetCategoriesQueryKey(organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: assetCategoryTreeQueryKey(organizationId),
      });
    },
  });
}
