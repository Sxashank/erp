/**
 * Portal Registration hooks.
 *
 *  - `useStartRegistration`             → POST /portal/auth/register
 *  - `useVerifyRegistrationOtp`         → POST /portal/auth/register/verify-otp
 *  - `useRegistrationStatus(ref,mobile)`→ GET  /portal/auth/registration-status
 *    polls every 30 s while the status is `PENDING_APPROVAL`.
 *
 * Wire shape: camelCase per the BE contract.  Mutations carry the
 * `Idempotency-Key` header at the service layer (`portalRegistrationApi`).
 */

import { useMutation, useQuery } from '@tanstack/react-query';

import {
  portalRegistrationApi,
  type RegisterRequest,
  type RegisterResponse,
  type RegisterVerifyOtpRequest,
  type RegisterVerifyOtpResponse,
  type RegistrationStatusResponse,
} from '@/services/portalApi';

export function useStartRegistration() {
  return useMutation<RegisterResponse, unknown, RegisterRequest>({
    mutationFn: async (body) => {
      const res = await portalRegistrationApi.register(body);
      return res.data;
    },
  });
}

export function useVerifyRegistrationOtp() {
  return useMutation<RegisterVerifyOtpResponse, unknown, RegisterVerifyOtpRequest>({
    mutationFn: async (body) => {
      const res = await portalRegistrationApi.verifyOtp(body);
      return res.data;
    },
  });
}

export const registrationStatusQueryKey = (reference: string, mobile: string) =>
  ['portal', 'registration-status', reference, mobile] as const;

export function useRegistrationStatus(
  reference: string | null | undefined,
  mobile: string | null | undefined,
) {
  return useQuery<RegistrationStatusResponse>({
    queryKey: registrationStatusQueryKey(reference ?? '', mobile ?? ''),
    queryFn: async () => {
      const res = await portalRegistrationApi.status({
        reference: reference as string,
        mobile: mobile as string,
      });
      return res.data;
    },
    enabled: Boolean(reference && mobile),
    refetchInterval: (query) => {
      const data = query.state.data as RegistrationStatusResponse | undefined;
      // Stop polling once we have a terminal status; keep polling while
      // approval is pending.
      if (!data) return 30_000;
      return data.registrationStatus === 'PENDING_APPROVAL' ? 30_000 : false;
    },
    refetchOnWindowFocus: false,
    staleTime: 0,
  });
}
