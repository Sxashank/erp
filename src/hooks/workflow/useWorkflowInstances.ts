/**
 * Workflow instance hooks — react-query around `/workflows/instances/*`.
 *
 * Cancel is treated as a high-risk mutation (it terminates an in-flight
 * approval chain), so the service wrapper sends an `Idempotency-Key` header
 * — see `services/workflow/workflowApi.ts`.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  instancesApi,
  type CancelWorkflowRequest,
  type InstanceListFilters,
  type PaginatedResponse,
  type WorkflowHistoryResponse,
  type WorkflowInstanceDetailResponse,
  type WorkflowInstanceResponse,
} from '@/services/workflow/workflowApi';

export const workflowInstancesQueryKey = (filters?: InstanceListFilters) =>
  ['workflow', 'instances', filters ?? {}] as const;

export const workflowInstanceQueryKey = (id: string) => ['workflow', 'instance', id] as const;

export const workflowInstanceHistoryQueryKey = (id: string) =>
  ['workflow', 'instance', id, 'history'] as const;

export function useWorkflowInstances(filters?: InstanceListFilters) {
  return useQuery<PaginatedResponse<WorkflowInstanceResponse>>({
    queryKey: workflowInstancesQueryKey(filters),
    queryFn: () => instancesApi.list(filters ?? {}),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useWorkflowInstance(id: string | undefined) {
  return useQuery<WorkflowInstanceDetailResponse>({
    queryKey: workflowInstanceQueryKey(id ?? ''),
    queryFn: () => {
      if (!id) throw new Error('id is required');
      return instancesApi.get(id);
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useWorkflowInstanceHistory(id: string | undefined) {
  return useQuery<WorkflowHistoryResponse[]>({
    queryKey: workflowInstanceHistoryQueryKey(id ?? ''),
    queryFn: () => {
      if (!id) throw new Error('id is required');
      return instancesApi.history(id);
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

function invalidateInstance(queryClient: ReturnType<typeof useQueryClient>, id?: string) {
  queryClient.invalidateQueries({ queryKey: ['workflow', 'instances'] });
  if (id) {
    queryClient.invalidateQueries({ queryKey: workflowInstanceQueryKey(id) });
    queryClient.invalidateQueries({
      queryKey: workflowInstanceHistoryQueryKey(id),
    });
  }
}

export function useCancelInstance() {
  const queryClient = useQueryClient();
  return useMutation<
    WorkflowInstanceResponse,
    unknown,
    { id: string; body: CancelWorkflowRequest }
  >({
    mutationFn: ({ id, body }) => instancesApi.cancel(id, body),
    onSuccess: (data) => invalidateInstance(queryClient, data.id),
  });
}
