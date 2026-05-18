/**
 * Admin Portal-Registration hooks.
 *
 *  - `usePendingRegistrations`   → GET  /admin/portal-registrations?status=…
 *  - `usePortalRegistration(id)` → GET  /admin/portal-registrations/:id
 *  - `useApproveRegistration`    → POST /admin/portal-registrations/:id/approve
 *  - `useRejectRegistration`     → POST /admin/portal-registrations/:id/reject
 *
 * Mutations carry Idempotency-Key at the service layer per CLAUDE.md §6.3.
 * The admin queue invalidates on approve / reject so the row leaves the
 * Pending tab.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  adminPortalRegistrationsApi,
  type AdminRegistrationDetail,
  type AdminRegistrationListResponse,
  type ApproveRegistrationBody,
  type PortalRegistrationStatus,
  type RejectRegistrationBody,
} from '@/services/admin/portalRegistrationsApi';

export interface AdminPortalRegistrationsFilters {
  status?: PortalRegistrationStatus;
  page?: number;
  pageSize?: number;
}

export const adminPortalRegistrationsQueryKey = (filters?: AdminPortalRegistrationsFilters) =>
  ['admin', 'portal-registrations', filters ?? {}] as const;

export const adminPortalRegistrationQueryKey = (id: string) =>
  ['admin', 'portal-registration', id] as const;

export function usePendingRegistrations(filters?: AdminPortalRegistrationsFilters) {
  // Default to PENDING_APPROVAL when caller omits status — the admin queue
  // is primarily for triage.
  const effective: AdminPortalRegistrationsFilters = {
    status: filters?.status ?? 'PENDING_APPROVAL',
    page: filters?.page ?? 1,
    pageSize: filters?.pageSize ?? 50,
  };
  return useQuery<AdminRegistrationListResponse>({
    queryKey: adminPortalRegistrationsQueryKey(effective),
    queryFn: async () => {
      const res = await adminPortalRegistrationsApi.list(effective);
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalRegistration(id: string | undefined) {
  return useQuery<AdminRegistrationDetail>({
    queryKey: adminPortalRegistrationQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await adminPortalRegistrationsApi.get(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
}

function invalidateRegistrations(queryClient: ReturnType<typeof useQueryClient>, id?: string) {
  queryClient.invalidateQueries({
    queryKey: ['admin', 'portal-registrations'],
  });
  if (id) {
    queryClient.invalidateQueries({
      queryKey: adminPortalRegistrationQueryKey(id),
    });
  }
}

export interface ApproveRegistrationVars extends ApproveRegistrationBody {
  id: string;
}
export function useApproveRegistration() {
  const queryClient = useQueryClient();
  return useMutation<AdminRegistrationDetail, unknown, ApproveRegistrationVars>({
    mutationFn: async ({ id, entityIds }) => {
      const res = await adminPortalRegistrationsApi.approve(id, {
        entityIds,
      });
      return res.data;
    },
    onSuccess: (data) => invalidateRegistrations(queryClient, data.portalUserId),
  });
}

export interface RejectRegistrationVars extends RejectRegistrationBody {
  id: string;
}
export function useRejectRegistration() {
  const queryClient = useQueryClient();
  return useMutation<AdminRegistrationDetail, unknown, RejectRegistrationVars>({
    mutationFn: async ({ id, reason }) => {
      const res = await adminPortalRegistrationsApi.reject(id, { reason });
      return res.data;
    },
    onSuccess: (data) => invalidateRegistrations(queryClient, data.portalUserId),
  });
}
