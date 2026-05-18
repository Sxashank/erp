import { useQuery } from '@tanstack/react-query';

import {
  getLendingDashboard,
  type LendingDashboardResponse,
} from '@/services/lending/dashboardApi';

export const lendingDashboardQueryKey = ['lending', 'dashboard'] as const;

export function useLendingDashboard() {
  return useQuery<LendingDashboardResponse>({
    queryKey: lendingDashboardQueryKey,
    queryFn: getLendingDashboard,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
