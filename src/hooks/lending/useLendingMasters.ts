import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  lendingMasterDataApi,
  type MasterCatalogItem,
  type MasterRow,
  type MasterRowListResponse,
  type MasterRowMutation,
} from '@/services/lending/masterDataApi';

const STALE_TIME = 5 * 60 * 1000;

export const lendingMasterKeys = {
  catalog: ['lending', 'masters', 'catalog'] as const,
  rows: (masterKey: string, params?: Record<string, unknown>) =>
    ['lending', 'masters', masterKey, params ?? {}] as const,
};

export function useLendingMasterCatalog() {
  return useQuery({
    queryKey: lendingMasterKeys.catalog,
    queryFn: () => lendingMasterDataApi.getCatalog(),
    staleTime: STALE_TIME,
  });
}

export function useLendingMasterCatalogItem(masterKey: string): MasterCatalogItem | undefined {
  const catalogQuery = useLendingMasterCatalog();
  return catalogQuery.data?.items.find((item) => item.key === masterKey);
}

export function useLendingMasterRows(
  masterKey: string | undefined,
  params?: { page?: number; pageSize?: number; optionGroup?: string },
) {
  return useQuery<MasterRowListResponse>({
    queryKey: lendingMasterKeys.rows(masterKey ?? '', params),
    queryFn: () => lendingMasterDataApi.listRows(masterKey as string, params),
    enabled: Boolean(masterKey),
    staleTime: STALE_TIME,
  });
}

export function useLendingOptionRows(optionGroup: string | undefined) {
  return useLendingMasterRows(
    optionGroup ? 'lending-options' : undefined,
    optionGroup ? { optionGroup, pageSize: 500 } : undefined,
  );
}

export function masterRowsToOptions(
  rows: MasterRow[] | undefined,
  labelKey = 'label',
): { value: string; label: string }[] {
  return (rows ?? [])
    .map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data[labelKey] ?? row.data.label ?? row.data.name ?? row.data.code ?? ''),
    }))
    .filter((option) => option.value.length > 0);
}

export function useCreateLendingMasterRow(masterKey: string) {
  const queryClient = useQueryClient();
  return useMutation<MasterRow, unknown, MasterRowMutation>({
    mutationFn: (payload) => lendingMasterDataApi.createRow(masterKey, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lending', 'masters', masterKey] });
    },
  });
}

export function useUpdateLendingMasterRow(masterKey: string) {
  const queryClient = useQueryClient();
  return useMutation<MasterRow, unknown, { rowId: string; payload: MasterRowMutation }>({
    mutationFn: ({ rowId, payload }) => lendingMasterDataApi.updateRow(masterKey, rowId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lending', 'masters', masterKey] });
    },
  });
}

export function useDeleteLendingMasterRow(masterKey: string) {
  const queryClient = useQueryClient();
  return useMutation<void, unknown, string>({
    mutationFn: (rowId) => lendingMasterDataApi.deleteRow(masterKey, rowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lending', 'masters', masterKey] });
    },
  });
}
