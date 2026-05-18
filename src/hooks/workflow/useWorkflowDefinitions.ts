/**
 * Workflow definition hooks — react-query around `/workflows/definitions/*`.
 *
 * Mutations invalidate the list + the per-record query key on success.
 * Errors surface through the standard backend envelope (CLAUDE.md §7) — the
 * caller uses `showErrorToast` from `@/lib/errorToast` to map them.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  definitionsApi,
  type DefinitionListFilters,
  type PaginatedResponse,
  type WorkflowDefinitionCreate,
  type WorkflowDefinitionResponse,
  type WorkflowDefinitionUpdate,
  type WorkflowDefinitionWithStepsResponse,
} from '@/services/workflow/workflowApi';

export const workflowDefinitionsQueryKey = (filters?: DefinitionListFilters) =>
  ['workflow', 'definitions', filters ?? {}] as const;

export const workflowDefinitionQueryKey = (id: string) => ['workflow', 'definition', id] as const;

export function useWorkflowDefinitions(filters?: DefinitionListFilters) {
  return useQuery<PaginatedResponse<WorkflowDefinitionResponse>>({
    queryKey: workflowDefinitionsQueryKey(filters),
    queryFn: () => {
      if (!filters?.organization_id) {
        throw new Error('organization_id is required');
      }
      return definitionsApi.list(filters);
    },
    enabled: Boolean(filters?.organization_id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useWorkflowDefinition(id: string | undefined) {
  return useQuery<WorkflowDefinitionWithStepsResponse>({
    queryKey: workflowDefinitionQueryKey(id ?? ''),
    queryFn: () => {
      if (!id) throw new Error('id is required');
      return definitionsApi.get(id);
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

function invalidateDefinition(queryClient: ReturnType<typeof useQueryClient>, id?: string) {
  queryClient.invalidateQueries({ queryKey: ['workflow', 'definitions'] });
  if (id) {
    queryClient.invalidateQueries({ queryKey: workflowDefinitionQueryKey(id) });
  }
}

export function useCreateWorkflowDefinition() {
  const queryClient = useQueryClient();
  return useMutation<WorkflowDefinitionWithStepsResponse, unknown, WorkflowDefinitionCreate>({
    mutationFn: (body) => definitionsApi.create(body),
    onSuccess: (data) => invalidateDefinition(queryClient, data.id),
  });
}

export function useUpdateWorkflowDefinition() {
  const queryClient = useQueryClient();
  return useMutation<
    WorkflowDefinitionResponse,
    unknown,
    { id: string; body: WorkflowDefinitionUpdate }
  >({
    mutationFn: ({ id, body }) => definitionsApi.update(id, body),
    onSuccess: (data) => invalidateDefinition(queryClient, data.id),
  });
}

export function useDeleteWorkflowDefinition() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, unknown, string>({
    mutationFn: (id) => definitionsApi.delete(id),
    onSuccess: (_data, id) => invalidateDefinition(queryClient, id),
  });
}

export function useSetDefaultDefinition() {
  const queryClient = useQueryClient();
  return useMutation<WorkflowDefinitionResponse, unknown, string>({
    mutationFn: (id) => definitionsApi.setDefault(id),
    onSuccess: (data) => invalidateDefinition(queryClient, data.id),
  });
}
