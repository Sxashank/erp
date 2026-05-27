import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  dmsFilingApi,
  documentPackageApi,
  documentStudioApi,
  type DocumentPackage,
  type DocumentModule,
  type DocumentTemplate,
  type DocumentTemplateVersion,
  type FilingRule,
} from '@/services/documentStudioApi';

export const documentStudioKeys = {
  templates: (params?: Record<string, unknown>) =>
    ['document-studio', 'templates', params ?? {}] as const,
  template: (id?: string) => ['document-studio', 'template', id] as const,
  variables: (module: DocumentModule, documentType?: string) =>
    ['document-studio', 'variables', module, documentType ?? ''] as const,
  filingRules: (params?: Record<string, unknown>) => ['dms', 'filing-rules', params ?? {}] as const,
  packages: (params?: Record<string, unknown>) => ['documents', 'packages', params ?? {}] as const,
  package: (id?: string) => ['documents', 'package', id ?? ''] as const,
  entityVault: (entityType?: string, entityId?: string) =>
    ['documents', 'entity-vault', entityType ?? '', entityId ?? ''] as const,
};

export function useDocumentTemplates(params?: { module?: DocumentModule; documentType?: string }) {
  return useQuery({
    queryKey: documentStudioKeys.templates(params),
    queryFn: () => documentStudioApi.listTemplates(params),
    staleTime: 60_000,
  });
}

export function useDocumentTemplate(id?: string) {
  return useQuery({
    queryKey: documentStudioKeys.template(id),
    queryFn: () => documentStudioApi.getTemplate(id as string),
    enabled: Boolean(id),
    staleTime: 60_000,
  });
}

export function useDocumentVariables(module: DocumentModule, documentType?: string) {
  return useQuery({
    queryKey: documentStudioKeys.variables(module, documentType),
    queryFn: () => documentStudioApi.variables({ module, documentType }),
    staleTime: 5 * 60_000,
  });
}

export function useCreateDocumentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<DocumentTemplate>) => documentStudioApi.createTemplate(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['document-studio', 'templates'] }),
  });
}

export function useCreateDocumentTemplateVersion(templateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<DocumentTemplateVersion>) =>
      documentStudioApi.createVersion(templateId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-studio', 'templates'] });
      queryClient.invalidateQueries({ queryKey: documentStudioKeys.template(templateId) });
    },
  });
}

export function useTransitionDocumentTemplateVersion(templateId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      versionId,
      action,
    }: {
      versionId: string;
      action: 'submit-review' | 'approve' | 'publish';
    }) => documentStudioApi.transitionVersion(versionId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-studio', 'templates'] });
      if (templateId) {
        queryClient.invalidateQueries({ queryKey: documentStudioKeys.template(templateId) });
      }
    },
  });
}

export function usePreviewDocument() {
  return useMutation({
    mutationFn: documentStudioApi.preview,
  });
}

export function useGenerateDocument() {
  return useMutation({
    mutationFn: documentStudioApi.generate,
  });
}

export function useDocumentPackages(params?: { entityType?: string; entityId?: string }) {
  return useQuery({
    queryKey: documentStudioKeys.packages(params),
    queryFn: () => documentPackageApi.list(params),
    staleTime: 60_000,
  });
}

export function useDocumentPackage(id?: string) {
  return useQuery({
    queryKey: documentStudioKeys.package(id),
    queryFn: () => documentPackageApi.get(id as string),
    enabled: Boolean(id),
    staleTime: 60_000,
  });
}

export function useCreateDocumentPackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: documentPackageApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents', 'packages'] }),
  });
}

export function useAddDocumentPackageItem(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof documentPackageApi.addItem>[1]) =>
      documentPackageApi.addItem(packageId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'packages'] });
      queryClient.invalidateQueries({ queryKey: documentStudioKeys.package(packageId) });
    },
  });
}

export function useFinalizeDocumentPackage(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload?: { manifest?: Record<string, unknown> }) =>
      documentPackageApi.finalize(packageId, payload),
    onSuccess: (data: DocumentPackage) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'packages'] });
      queryClient.invalidateQueries({ queryKey: documentStudioKeys.package(data.id) });
    },
  });
}

export function useDmsFilingRules(params?: { module?: string; documentType?: string }) {
  return useQuery({
    queryKey: documentStudioKeys.filingRules(params),
    queryFn: () => dmsFilingApi.listRules(params),
    staleTime: 60_000,
  });
}

export function useCreateDmsFilingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<FilingRule>) => dmsFilingApi.createRule(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dms', 'filing-rules'] }),
  });
}

export function useEntityVault(entityType?: string, entityId?: string) {
  return useQuery({
    queryKey: documentStudioKeys.entityVault(entityType, entityId),
    queryFn: () => dmsFilingApi.entityVault(entityType as string, entityId as string),
    enabled: Boolean(entityType && entityId),
    staleTime: 60_000,
  });
}
