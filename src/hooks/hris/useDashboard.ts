import { useQuery } from '@tanstack/react-query';

import { hrDashboardApi } from '@/services/hris/dashboardApi';

const HR_DASHBOARD_QUERY_KEY = ['hris', 'dashboard'] as const;

export function useHRDashboard() {
  return useQuery({
    queryKey: HR_DASHBOARD_QUERY_KEY,
    queryFn: () => hrDashboardApi.getDashboard(),
  });
}
