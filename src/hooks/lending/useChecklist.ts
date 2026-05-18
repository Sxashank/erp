/**
 * Approval Checklist react-query hooks.
 *
 * Query-key prefix: ['lending', 'checklist', ...]. Mutations invalidate the
 * relevant slice on success. Error toasts use the typed {error_code, message,
 * correlation_id} envelope helper (lib/errorToast.ts).
 *
 * See CLAUDE.md §5.4.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
} from '@tanstack/react-query';

import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import {
  applicationChecklistApi,
  checklistTemplatesApi,
  type ApplyTemplatePayload,
  type ChecklistTemplate,
  type ChecklistTemplateCreate,
  type ChecklistTemplateItem,
  type ChecklistTemplateItemCreate,
  type ChecklistTemplateItemUpdate,
  type ChecklistTemplateListParams,
  type ChecklistTemplateUpdate,
  type LoanChecklist,
  type LoanChecklistItem,
  type MarkMetPayload,
  type MarkNAPayload,
  type UpdateChecklistItemPayload,
  type WaivePayload,
} from '@/services/lending/checklistApi';

const MASTER_STALE_TIME = 5 * 60 * 1000;
const TXN_STALE_TIME = 30 * 1000;

// ============================================================================
// Query keys
// ============================================================================

export const checklistKeys = {
  all: ['lending', 'checklist'] as const,
  templates: (params?: ChecklistTemplateListParams) =>
    ['lending', 'checklist', 'templates', params ?? {}] as const,
  template: (id: string) => ['lending', 'checklist', 'template', id] as const,
  applicationChecklist: (applicationId: string) =>
    ['lending', 'checklist', 'application', applicationId] as const,
};

// ============================================================================
// Templates
// ============================================================================

export function useChecklistTemplates(params?: ChecklistTemplateListParams) {
  return useQuery<ChecklistTemplate[]>({
    queryKey: checklistKeys.templates(params),
    queryFn: () => checklistTemplatesApi.list(params),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

export function useChecklistTemplate(id: string | undefined) {
  return useQuery<ChecklistTemplate>({
    queryKey: checklistKeys.template(id ?? ''),
    queryFn: () => checklistTemplatesApi.get(id as string),
    enabled: Boolean(id),
    staleTime: MASTER_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

function invalidateTemplates(qc: ReturnType<typeof useQueryClient>, id?: string) {
  qc.invalidateQueries({ queryKey: ['lending', 'checklist', 'templates'] });
  if (id) qc.invalidateQueries({ queryKey: checklistKeys.template(id) });
}

export function useCreateTemplate(
  options?: UseMutationOptions<ChecklistTemplate, unknown, ChecklistTemplateCreate>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<ChecklistTemplate, unknown, ChecklistTemplateCreate>({
    mutationFn: (payload) => checklistTemplatesApi.create(payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateTemplates(qc);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useUpdateTemplate(
  options?: UseMutationOptions<
    ChecklistTemplate,
    unknown,
    { id: string; payload: ChecklistTemplateUpdate }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<ChecklistTemplate, unknown, { id: string; payload: ChecklistTemplateUpdate }>({
    mutationFn: ({ id, payload }) => checklistTemplatesApi.update(id, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateTemplates(qc, vars.id);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useDeleteTemplate(options?: UseMutationOptions<void, unknown, string>) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<void, unknown, string>({
    mutationFn: (id) => checklistTemplatesApi.remove(id),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, id, onMutateResult, ctx) => {
      invalidateTemplates(qc, id);
      options?.onSuccess?.(data, id, onMutateResult, ctx);
    },
  });
}

export function useAddTemplateItem(
  options?: UseMutationOptions<
    ChecklistTemplateItem,
    unknown,
    { templateId: string; payload: ChecklistTemplateItemCreate }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    ChecklistTemplateItem,
    unknown,
    { templateId: string; payload: ChecklistTemplateItemCreate }
  >({
    mutationFn: ({ templateId, payload }) => checklistTemplatesApi.addItem(templateId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateTemplates(qc, vars.templateId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useUpdateTemplateItem(
  options?: UseMutationOptions<
    ChecklistTemplateItem,
    unknown,
    {
      templateId: string;
      itemId: string;
      payload: ChecklistTemplateItemUpdate;
    }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    ChecklistTemplateItem,
    unknown,
    {
      templateId: string;
      itemId: string;
      payload: ChecklistTemplateItemUpdate;
    }
  >({
    mutationFn: ({ templateId, itemId, payload }) =>
      checklistTemplatesApi.updateItem(templateId, itemId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateTemplates(qc, vars.templateId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useDeleteTemplateItem(
  options?: UseMutationOptions<void, unknown, { templateId: string; itemId: string }>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<void, unknown, { templateId: string; itemId: string }>({
    mutationFn: ({ templateId, itemId }) => checklistTemplatesApi.deleteItem(templateId, itemId),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateTemplates(qc, vars.templateId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useSetDefaultTemplate(
  options?: UseMutationOptions<ChecklistTemplate, unknown, string>,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<ChecklistTemplate, unknown, string>({
    mutationFn: (id) => checklistTemplatesApi.setDefault(id),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, id, onMutateResult, ctx) => {
      invalidateTemplates(qc, id);
      options?.onSuccess?.(data, id, onMutateResult, ctx);
    },
  });
}

// ============================================================================
// Per-application checklist
// ============================================================================

export function useApplicationChecklist(applicationId: string | undefined) {
  return useQuery<LoanChecklist | null>({
    queryKey: checklistKeys.applicationChecklist(applicationId ?? ''),
    queryFn: () => applicationChecklistApi.get(applicationId as string),
    enabled: Boolean(applicationId),
    staleTime: TXN_STALE_TIME,
    refetchOnWindowFocus: false,
  });
}

function invalidateApplicationChecklist(
  qc: ReturnType<typeof useQueryClient>,
  applicationId: string,
) {
  qc.invalidateQueries({
    queryKey: checklistKeys.applicationChecklist(applicationId),
  });
}

export function useApplyTemplateToApplication(
  options?: UseMutationOptions<
    LoanChecklist,
    unknown,
    { applicationId: string; payload: ApplyTemplatePayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklist,
    unknown,
    { applicationId: string; payload: ApplyTemplatePayload }
  >({
    mutationFn: ({ applicationId, payload }) =>
      applicationChecklistApi.apply(applicationId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useReplaceApplicationTemplate(
  options?: UseMutationOptions<
    LoanChecklist,
    unknown,
    { applicationId: string; payload: ApplyTemplatePayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklist,
    unknown,
    { applicationId: string; payload: ApplyTemplatePayload }
  >({
    mutationFn: ({ applicationId, payload }) =>
      applicationChecklistApi.replace(applicationId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useUpdateChecklistItem(
  options?: UseMutationOptions<
    LoanChecklistItem,
    unknown,
    {
      applicationId: string;
      itemId: string;
      payload: UpdateChecklistItemPayload;
    }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklistItem,
    unknown,
    {
      applicationId: string;
      itemId: string;
      payload: UpdateChecklistItemPayload;
    }
  >({
    mutationFn: ({ applicationId, itemId, payload }) =>
      applicationChecklistApi.updateItem(applicationId, itemId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useMarkChecklistItemMet(
  options?: UseMutationOptions<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: MarkMetPayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: MarkMetPayload }
  >({
    mutationFn: ({ applicationId, itemId, payload }) =>
      applicationChecklistApi.markMet(applicationId, itemId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useWaiveChecklistItem(
  options?: UseMutationOptions<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: WaivePayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: WaivePayload }
  >({
    mutationFn: ({ applicationId, itemId, payload }) =>
      applicationChecklistApi.waive(applicationId, itemId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useMarkChecklistItemNA(
  options?: UseMutationOptions<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: MarkNAPayload }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string; payload: MarkNAPayload }
  >({
    mutationFn: ({ applicationId, itemId, payload }) =>
      applicationChecklistApi.markNotApplicable(applicationId, itemId, payload),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}

export function useResetChecklistItem(
  options?: UseMutationOptions<
    LoanChecklistItem,
    unknown,
    { applicationId: string; itemId: string }
  >,
) {
  const qc = useQueryClient();
  const { toast } = useToast();
  return useMutation<LoanChecklistItem, unknown, { applicationId: string; itemId: string }>({
    mutationFn: ({ applicationId, itemId }) => applicationChecklistApi.reset(applicationId, itemId),
    onError: (err) => showErrorToast(err, toast),
    ...options,
    onSuccess: (data, vars, onMutateResult, ctx) => {
      invalidateApplicationChecklist(qc, vars.applicationId);
      options?.onSuccess?.(data, vars, onMutateResult, ctx);
    },
  });
}
