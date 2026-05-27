/**
 * Portal Application hooks.
 *
 *  - `usePortalApplications(filters)`  → GET  /portal/applications
 *  - `usePortalApplication(id)`        → GET  /portal/applications/:id
 *  - `useCreatePortalApplicationDraft` → POST /portal/applications
 *  - `useSubmitPortalApplication`      → POST /portal/applications/:id/submit
 *  - `useUploadApplicationDocument`    → POST /portal/applications/:id/documents/upload
 *  - `usePortalApplicationDocuments`   → GET  /portal/applications/:id/documents
 *
 * Mutations carry `Idempotency-Key` per CLAUDE.md §6.3 (at the service layer).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  portalApplicationsApi,
  portalProductsApi,
  portalUtilizationCategoriesApi,
  type CreatePortalApplicationRequest,
  type PaginatedPortalApplications,
  type PortalApplicationDetail,
  type PortalApplicationDocument,
  type PortalApplicationQueryListResponse,
  type PortalApplicationQuery,
  type PortalProduct,
  type PortalApplicationStatus,
  type PortalSchemeApplicationStatus,
  type PortalUtilizationCategory,
  type RespondToPortalApplicationQueryRequest,
  type UpdatePortalApplicationRequest,
} from '@/services/portalApi';

export interface PortalApplicationsFilters {
  status?: PortalApplicationStatus | PortalSchemeApplicationStatus | string;
  entityId?: string;
  page?: number;
  pageSize?: number;
}

export const portalApplicationsQueryKey = (filters?: PortalApplicationsFilters) =>
  ['portal', 'applications', filters ?? {}] as const;

export const portalApplicationQueryKey = (id: string) => ['portal', 'application', id] as const;

export const portalApplicationDocsQueryKey = (id: string) =>
  ['portal', 'application', id, 'documents'] as const;

export const portalApplicationQueriesQueryKey = (id: string) =>
  ['portal', 'application', id, 'queries'] as const;

export function usePortalApplications(filters?: PortalApplicationsFilters) {
  return useQuery<PaginatedPortalApplications>({
    queryKey: portalApplicationsQueryKey(filters),
    queryFn: async () => {
      const res = await portalApplicationsApi.list({
        status: filters?.status,
        entityId: filters?.entityId,
        page: filters?.page,
        pageSize: filters?.pageSize,
      });
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalApplication(id: string | undefined) {
  return useQuery<PortalApplicationDetail>({
    queryKey: portalApplicationQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await portalApplicationsApi.get(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useSubmitPortalApplication() {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDetail, unknown, string>({
    mutationFn: async (applicationId) => {
      const res = await portalApplicationsApi.submit(applicationId);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'applications'] });
      queryClient.setQueryData(portalApplicationQueryKey(data.id), data);
    },
  });
}

export function useResubmitPortalApplication() {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDetail, unknown, string>({
    mutationFn: async (applicationId) => {
      const res = await portalApplicationsApi.resubmit(applicationId);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'applications'] });
      queryClient.setQueryData(portalApplicationQueryKey(data.id), data);
    },
  });
}

export function useCreatePortalApplicationDraft() {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDetail, unknown, CreatePortalApplicationRequest>({
    mutationFn: async (body) => {
      const res = await portalApplicationsApi.createDraft(body);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'applications'] });
      queryClient.setQueryData(portalApplicationQueryKey(data.id), data);
    },
  });
}

export function useUpdatePortalApplicationDraft(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDetail, unknown, UpdatePortalApplicationRequest>({
    mutationFn: async (body) => {
      const res = await portalApplicationsApi.updateDraft(id as string, body);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'applications'] });
      queryClient.setQueryData(portalApplicationQueryKey(data.id), data);
    },
  });
}

export function useWithdrawPortalApplication() {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDetail, unknown, { id: string; reason: string }>({
    mutationFn: async ({ id, reason }) => {
      const res = await portalApplicationsApi.withdraw(id, { reason });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'applications'] });
      queryClient.setQueryData(portalApplicationQueryKey(data.id), data);
    },
  });
}

export interface UploadApplicationDocumentBody {
  applicationId: string;
  file: File;
  documentType: string;
  documentName?: string;
}

export function useUploadApplicationDocument() {
  const queryClient = useQueryClient();
  return useMutation<PortalApplicationDocument, unknown, UploadApplicationDocumentBody>({
    mutationFn: async ({ applicationId, file, documentType, documentName }) => {
      const res = await portalApplicationsApi.uploadDocument(
        applicationId,
        file,
        documentType,
        documentName,
      );
      return res.data;
    },
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({
        queryKey: portalApplicationDocsQueryKey(vars.applicationId),
      });
    },
  });
}

export function usePortalApplicationDocuments(id: string | undefined) {
  return useQuery<PortalApplicationDocument[]>({
    queryKey: portalApplicationDocsQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await portalApplicationsApi.listDocuments(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalApplicationQueries(id: string | undefined) {
  return useQuery<PortalApplicationQueryListResponse>({
    queryKey: portalApplicationQueriesQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await portalApplicationsApi.listQueries(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useRespondPortalApplicationQuery(applicationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation<
    PortalApplicationQuery,
    unknown,
    { queryId: string; payload: RespondToPortalApplicationQueryRequest }
  >({
    mutationFn: async ({ queryId, payload }) => {
      const res = await portalApplicationsApi.respondToQuery(
        applicationId as string,
        queryId,
        payload,
      );
      return res.data;
    },
    onSuccess: () => {
      if (!applicationId) return;
      queryClient.invalidateQueries({
        queryKey: portalApplicationQueriesQueryKey(applicationId),
      });
      queryClient.invalidateQueries({
        queryKey: portalApplicationQueryKey(applicationId),
      });
    },
  });
}

export function usePortalProducts(entityId?: string) {
  return useQuery<PortalProduct[]>({
    queryKey: ['portal', 'products', entityId ?? 'all'],
    queryFn: async () => {
      const res = await portalProductsApi.list({
        entityId,
      });
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalUtilizationCategories() {
  return useQuery<PortalUtilizationCategory[]>({
    queryKey: ['portal', 'utilization-categories'],
    queryFn: async () => {
      const res = await portalUtilizationCategoriesApi.list();
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
