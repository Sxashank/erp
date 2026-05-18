import { useQuery } from '@tanstack/react-query';

import { portalReportsApi, type PortalReportingSummary } from '@/services/portalApi';

export const portalReportsQueryKey = ['portal', 'reports', 'summary'] as const;

export function usePortalReports() {
  return useQuery<PortalReportingSummary>({
    queryKey: portalReportsQueryKey,
    queryFn: async () => {
      const res = await portalReportsApi.getSummary();
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDownloadPortalReportCsv() {
  return async (fileName = 'scheme-portal-report.csv') => {
    const response = await portalReportsApi.downloadSummaryCsv();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const anchor = window.document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    window.document.body.appendChild(anchor);
    anchor.click();
    window.document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
  };
}
