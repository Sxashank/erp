import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { misApi, type AsOfParams, type DateRangeParams } from '@/services/reports/misApi';

const KEY_ROOT = ['reports', 'mis'] as const;
const MIS_STALE_MS = 5 * 60_000;

export function useMisCatalog() {
  return useQuery({
    queryKey: [...KEY_ROOT, 'catalog'] as const,
    queryFn: () => misApi.getCatalog(),
    staleTime: 60 * 60_000,
  });
}

export function useMisDashboard(params?: AsOfParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'dashboard', params?.asOfDate ?? 'today'] as const,
    queryFn: () => misApi.getDashboard(params),
    staleTime: MIS_STALE_MS,
  });
}

export function usePortfolioSummary(params?: AsOfParams & { unitId?: string }) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'portfolio-summary', params] as const,
    queryFn: () => misApi.getPortfolioSummary(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useDisbursementReport(
  params?: DateRangeParams & { groupBy?: 'PRODUCT' | 'BRANCH' | 'CHANNEL' },
) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'disbursement', params] as const,
    queryFn: () => misApi.getDisbursement(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useCollectionReport(params?: DateRangeParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'collection', params] as const,
    queryFn: () => misApi.getCollection(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useDelinquencyReport(params?: AsOfParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'delinquency', params?.asOfDate ?? 'today'] as const,
    queryFn: () => misApi.getDelinquency(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useProfitabilityReport(params?: DateRangeParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'profitability', params] as const,
    queryFn: () => misApi.getProfitability(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useBranchPerformanceReport(params?: DateRangeParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'branch-performance', params] as const,
    queryFn: () => misApi.getBranchPerformance(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useAllModulesReport(params?: DateRangeParams & AsOfParams) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'all-modules', params] as const,
    queryFn: () => misApi.getAllModules(params),
    staleTime: MIS_STALE_MS,
  });
}

export function useReportRuns(limit = 50) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'runs', limit] as const,
    queryFn: () => misApi.listRuns(limit),
    staleTime: MIS_STALE_MS,
  });
}

export function useReportSchedules(activeOnly = false) {
  return useQuery({
    queryKey: [...KEY_ROOT, 'schedules', activeOnly] as const,
    queryFn: () => misApi.listSchedules(activeOnly),
    staleTime: MIS_STALE_MS,
  });
}

export function useCreateReportRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: misApi.createRun,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'runs'] });
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'dashboard'] });
    },
  });
}

export function useCreateReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: misApi.createSchedule,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'schedules'] });
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'dashboard'] });
    },
  });
}

export function useRunScheduleNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: misApi.runScheduleNow,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'runs'] });
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'schedules'] });
      void queryClient.invalidateQueries({ queryKey: [...KEY_ROOT, 'dashboard'] });
    },
  });
}
