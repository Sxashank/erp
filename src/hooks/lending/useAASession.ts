/**
 * useAASession — single-session detail + fetch-data mutation for
 * /lending/aa/sessions/:id. See CLAUDE.md §3.3, §5.4, §6.3.
 *
 * `fetch-data` pulls financial info from upstream FIPs and is billed per
 * call by the AA provider, so the mutation carries an `Idempotency-Key`
 * (allowlist: `lending/aa`).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  fetchSessionData,
  getFetchSession,
  type FetchSessionDetail,
} from '@/services/lending/aaApi';

export const aaSessionQueryKey = (sessionId: string | undefined) =>
  ['lending', 'aa', 'sessions', sessionId ?? null] as const;

export function useAASession(sessionId: string | undefined) {
  return useQuery<FetchSessionDetail>({
    queryKey: aaSessionQueryKey(sessionId),
    queryFn: () => getFetchSession(sessionId as string),
    enabled: Boolean(sessionId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useFetchAASessionData(sessionId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<FetchSessionDetail, unknown, void>({
    mutationFn: async () => fetchSessionData(sessionId as string, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: aaSessionQueryKey(sessionId) });
      // Account list changes whenever a session fetch lands.
      void queryClient.invalidateQueries({ queryKey: ['lending', 'aa', 'bank-accounts'] });
    },
  });
}
