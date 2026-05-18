/**
 * Workflow task hooks — react-query around `/workflows/tasks/*`.
 *
 * Approve and Delegate are maker-checker actions and the service wrapper
 * sends an `Idempotency-Key` header (see CLAUDE.md §6.3 / §8.4).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  tasksApi,
  type ApprovalActionRequest,
  type DelegateTaskRequest,
  type PendingTaskFilters,
  type WorkflowInstanceDetailResponse,
  type WorkflowTaskResponse,
} from '@/services/workflow/workflowApi';

export const pendingTasksQueryKey = (filters?: PendingTaskFilters) =>
  ['workflow', 'tasks', 'pending', filters ?? {}] as const;

export function usePendingTasks(filters?: PendingTaskFilters) {
  return useQuery<WorkflowTaskResponse[]>({
    queryKey: pendingTasksQueryKey(filters),
    queryFn: () => tasksApi.pending(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

function invalidateTasks(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['workflow', 'tasks'] });
  // Approving / rejecting a task may move the instance forward or end it.
  queryClient.invalidateQueries({ queryKey: ['workflow', 'instances'] });
}

export function useApproveTask() {
  const queryClient = useQueryClient();
  return useMutation<
    WorkflowInstanceDetailResponse,
    unknown,
    { id: string; body: ApprovalActionRequest }
  >({
    mutationFn: ({ id, body }) => tasksApi.approve(id, body),
    onSuccess: () => invalidateTasks(queryClient),
  });
}

export function useDelegateTask() {
  const queryClient = useQueryClient();
  return useMutation<WorkflowTaskResponse, unknown, { id: string; body: DelegateTaskRequest }>({
    mutationFn: ({ id, body }) => tasksApi.delegate(id, body),
    onSuccess: () => invalidateTasks(queryClient),
  });
}
