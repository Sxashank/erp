import { useQuery } from '@tanstack/react-query';

import { listAccounts, listDepartments, listUnits, listVendors } from '@/services/fixed-assets';
import type { MasterOption } from '@/types/fixed-assets';

export const fixedAssetAccountsQueryKey = (organizationId: string) =>
  ['fixed-assets', 'masters', organizationId, 'accounts'] as const;
export const fixedAssetUnitsQueryKey = (organizationId: string) =>
  ['fixed-assets', 'masters', organizationId, 'units'] as const;
export const fixedAssetDepartmentsQueryKey = (organizationId: string) =>
  ['fixed-assets', 'masters', organizationId, 'departments'] as const;
export const fixedAssetVendorsQueryKey = (organizationId: string) =>
  ['fixed-assets', 'masters', organizationId, 'vendors'] as const;

export function useFixedAssetAccounts(organizationId: string) {
  return useQuery<MasterOption[]>({
    queryKey: fixedAssetAccountsQueryKey(organizationId),
    queryFn: () => listAccounts(organizationId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAssetUnits(organizationId: string) {
  return useQuery<MasterOption[]>({
    queryKey: fixedAssetUnitsQueryKey(organizationId),
    queryFn: () => listUnits(organizationId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAssetDepartments(organizationId: string) {
  return useQuery<MasterOption[]>({
    queryKey: fixedAssetDepartmentsQueryKey(organizationId),
    queryFn: () => listDepartments(organizationId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFixedAssetVendors(organizationId: string) {
  return useQuery<MasterOption[]>({
    queryKey: fixedAssetVendorsQueryKey(organizationId),
    queryFn: () => listVendors(organizationId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
