import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  adminPortalUsersApi,
  type AdminPortalInviteResponse,
  type AdminPortalUserDetail,
  type AdminPortalUserListResponse,
  type CreateAdminPortalUserBody,
  type PortalActorRole,
  type PortalUserStatus,
  type UpdateAdminPortalUserBody,
} from '@/services/admin/portalUsersApi';

export interface AdminPortalUsersFilters {
  actorRole?: PortalActorRole;
  status?: PortalUserStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

export const adminPortalUsersQueryKey = (filters?: AdminPortalUsersFilters) =>
  ['admin', 'portal-users', filters ?? {}] as const;

export const adminPortalUserQueryKey = (id: string) => ['admin', 'portal-user', id] as const;

export function useAdminPortalUsers(filters?: AdminPortalUsersFilters) {
  return useQuery<AdminPortalUserListResponse>({
    queryKey: adminPortalUsersQueryKey(filters),
    queryFn: async () => {
      const res = await adminPortalUsersApi.list(filters);
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useAdminPortalUser(id: string | undefined) {
  return useQuery<AdminPortalUserDetail>({
    queryKey: adminPortalUserQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await adminPortalUsersApi.get(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
}

function invalidatePortalUsers(queryClient: ReturnType<typeof useQueryClient>, id?: string) {
  queryClient.invalidateQueries({ queryKey: ['admin', 'portal-users'] });
  if (id) {
    queryClient.invalidateQueries({ queryKey: adminPortalUserQueryKey(id) });
  }
}

export function useCreateAdminPortalUser() {
  const queryClient = useQueryClient();
  return useMutation<AdminPortalUserDetail, unknown, CreateAdminPortalUserBody>({
    mutationFn: async (body) => {
      const res = await adminPortalUsersApi.create(body);
      return res.data;
    },
    onSuccess: (data) => invalidatePortalUsers(queryClient, data.portalUserId),
  });
}

export function useUpdateAdminPortalUser() {
  const queryClient = useQueryClient();
  return useMutation<
    AdminPortalUserDetail,
    unknown,
    { id: string; body: UpdateAdminPortalUserBody }
  >({
    mutationFn: async ({ id, body }) => {
      const res = await adminPortalUsersApi.update(id, body);
      return res.data;
    },
    onSuccess: (data) => invalidatePortalUsers(queryClient, data.portalUserId),
  });
}

export function useInviteAdminPortalUser() {
  const queryClient = useQueryClient();
  return useMutation<AdminPortalInviteResponse, unknown, string>({
    mutationFn: async (id) => {
      const res = await adminPortalUsersApi.invite(id);
      return res.data;
    },
    onSuccess: (data) => invalidatePortalUsers(queryClient, data.portalUserId),
  });
}
