import { useQuery } from '@tanstack/react-query';

import { portalWorkbenchApi, type PortalWorkbench } from '@/services/portalApi';

export const portalWorkbenchQueryKey = ['portal', 'workbench'] as const;

export function usePortalWorkbench() {
  return useQuery<PortalWorkbench>({
    queryKey: portalWorkbenchQueryKey,
    queryFn: async () => {
      const res = await portalWorkbenchApi.get();
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
