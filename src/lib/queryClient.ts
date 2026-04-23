/**
 * Singleton react-query client. See CLAUDE.md §5.4.
 *
 * Defaults are conservative for an ERP — we do not refetch on window focus
 * (auditors open many tabs), retries are limited, and 4xx errors never retry.
 */

import { QueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';

function shouldRetry(failureCount: number, error: unknown): boolean {
  const status = (error as AxiosError | undefined)?.response?.status;
  if (status && status >= 400 && status < 500) return false; // client errors
  return failureCount < 1;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: shouldRetry,
    },
    mutations: {
      retry: false,
    },
  },
});
