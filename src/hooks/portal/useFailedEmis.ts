/**
 * Portal failed-EMI / missed-payment / schedule-CSV hooks.
 *
 *  - `useFailedSchedule(loanId)`    → GET /portal/loans/:id/schedule/failed
 *  - `useMissedSchedule(loanId)`    → GET /portal/loans/:id/schedule/missed
 *  - `useDownloadScheduleCsv(loanId)` → triggerable Blob download
 *
 * Schedule rows mirror the failed/missed wire shape — amounts are
 * Decimal-as-string, DPD is a non-negative integer.
 */

import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import {
  portalScheduleApi,
  type FailedScheduleItem,
  type MissedScheduleItem,
} from '@/services/portalApi';

export const failedScheduleQueryKey = (loanId: string) =>
  ['portal', 'schedule-failed', loanId] as const;

export const missedScheduleQueryKey = (loanId: string) =>
  ['portal', 'schedule-missed', loanId] as const;

export function useFailedSchedule(loanId: string | undefined) {
  return useQuery<FailedScheduleItem[]>({
    queryKey: failedScheduleQueryKey(loanId ?? ''),
    queryFn: async () => {
      const res = await portalScheduleApi.getFailed(loanId as string);
      return res.data;
    },
    enabled: Boolean(loanId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useMissedSchedule(loanId: string | undefined) {
  return useQuery<MissedScheduleItem[]>({
    queryKey: missedScheduleQueryKey(loanId ?? ''),
    queryFn: async () => {
      const res = await portalScheduleApi.getMissed(loanId as string);
      return res.data;
    },
    enabled: Boolean(loanId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDownloadScheduleCsv(loanId: string | undefined) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const download = useCallback(
    async (overrideFilename?: string) => {
      if (!loanId) return;
      setError(null);
      setIsDownloading(true);
      try {
        const res = await portalScheduleApi.downloadCsv(loanId);
        const blob =
          res.data instanceof Blob
            ? res.data
            : new Blob([res.data as unknown as ArrayBuffer], {
                type: 'text/csv',
              });
        const url = window.URL.createObjectURL(blob);
        const a = window.document.createElement('a');
        a.href = url;
        a.download = overrideFilename ?? `loan_schedule_${loanId}.csv`;
        window.document.body.appendChild(a);
        a.click();
        window.document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setIsDownloading(false);
      }
    },
    [loanId],
  );

  return { download, isDownloading, error };
}
