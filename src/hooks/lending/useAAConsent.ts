/**
 * useAAConsent — single-consent detail + mutation hooks for /lending/aa/consents/:id.
 *
 * Wraps `src/services/lending/aaApi.ts`. Pages never call axios; they consume
 * these hooks. See CLAUDE.md §3.3, §5.4, §6.3.
 *
 * Mutations on a consent (check-status, revoke, initiate-fetch) all hit
 * paid/billed AA bureau APIs externally, so each carries an `Idempotency-Key`
 * per CLAUDE.md §6.3 and the backend allowlist (`lending/aa`).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  checkConsentStatus,
  createConsent,
  getConsent,
  initiateFetch,
  revokeConsent,
  type ConsentDetail,
  type ConsentMutationResponse,
  type CreateConsentRequest,
  type CreateConsentResponse,
  type InitiateFetchRequest,
  type InitiateFetchResponse,
  type RevokeConsentRequest,
} from '@/services/lending/aaApi';

export const aaConsentQueryKey = (consentId: string | undefined) =>
  ['lending', 'aa', 'consents', consentId ?? null] as const;

export function useAAConsent(consentId: string | undefined) {
  return useQuery<ConsentDetail>({
    queryKey: aaConsentQueryKey(consentId),
    queryFn: () => getConsent(consentId as string),
    enabled: Boolean(consentId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateAAConsent() {
  const queryClient = useQueryClient();
  return useMutation<CreateConsentResponse, unknown, CreateConsentRequest>({
    mutationFn: async (body) => createConsent(body, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'aa', 'consents'] });
    },
  });
}

export function useCheckAAConsentStatus(consentId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<ConsentMutationResponse, unknown, void>({
    mutationFn: async () => checkConsentStatus(consentId as string, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: aaConsentQueryKey(consentId) });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'aa', 'consents'] });
    },
  });
}

export function useRevokeAAConsent(consentId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<ConsentMutationResponse, unknown, RevokeConsentRequest>({
    mutationFn: async (body) => revokeConsent(consentId as string, body, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: aaConsentQueryKey(consentId) });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'aa', 'consents'] });
    },
  });
}

export function useInitiateAAFetch(consentId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<InitiateFetchResponse, unknown, InitiateFetchRequest>({
    mutationFn: async (body) => initiateFetch(consentId as string, body, crypto.randomUUID()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: aaConsentQueryKey(consentId) });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'aa', 'consents'] });
    },
  });
}
