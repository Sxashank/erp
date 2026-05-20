/**
 * Scheme-portal claim hooks.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import {
  portalClaimsApi,
  type PaginatedPortalClaims,
  type PortalClaim,
  type PortalClaimEnrollment,
  type PortalClaimsWorkbench,
  type PortalCreateClaimRequest,
} from '@/services/portalApi';

export const portalClaimsWorkbenchQueryKey = ['portal', 'claims', 'workbench'] as const;

export const portalClaimEnrollmentsQueryKey = ['portal', 'claims', 'enrollments'] as const;

export const portalClaimsQueryKey = (params?: {
  loanAccountId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}) => ['portal', 'claims', params ?? {}] as const;

export const portalClaimQueryKey = (id: string) => ['portal', 'claim', id] as const;

export const portalEligibleClaimPeriodsQueryKey = (enrollmentId: string) =>
  ['portal', 'claim-eligible-periods', enrollmentId] as const;

export function usePortalClaimsWorkbench() {
  return useQuery<PortalClaimsWorkbench>({
    queryKey: portalClaimsWorkbenchQueryKey,
    queryFn: async () => {
      const res = await portalClaimsApi.workbench();
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalClaimEnrollments() {
  return useQuery<PortalClaimEnrollment[]>({
    queryKey: portalClaimEnrollmentsQueryKey,
    queryFn: async () => {
      const res = await portalClaimsApi.listEnrollments();
      return res.data.items;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalClaims(params?: {
  loanAccountId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}) {
  return useQuery<PaginatedPortalClaims>({
    queryKey: portalClaimsQueryKey(params),
    queryFn: async () => {
      const res = await portalClaimsApi.list(params);
      return res.data;
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalClaim(id: string | undefined) {
  return useQuery<PortalClaim>({
    queryKey: portalClaimQueryKey(id ?? ''),
    queryFn: async () => {
      const res = await portalClaimsApi.get(id as string);
      return res.data;
    },
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalEligibleClaimPeriods(enrollmentId: string | undefined) {
  return useQuery<{
    enrollmentId: string;
    claimFrequency: string;
    periods: {
      periodStart: string;
      periodEnd: string;
      label: string;
      claimFrequency: string;
      alreadyClaimed: boolean;
      existingClaimId?: string | null;
      existingStatus?: string | null;
    }[];
  }>({
    queryKey: portalEligibleClaimPeriodsQueryKey(enrollmentId ?? ''),
    queryFn: async () => {
      const res = await portalClaimsApi.listEligiblePeriods(enrollmentId as string);
      return res.data;
    },
    enabled: Boolean(enrollmentId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreatePortalClaim() {
  const queryClient = useQueryClient();
  return useMutation<PortalClaim, unknown, PortalCreateClaimRequest>({
    mutationFn: async (body) => {
      const res = await portalClaimsApi.create(body);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.invalidateQueries({ queryKey: portalClaimEnrollmentsQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

export function useUploadPortalClaimDocument() {
  const queryClient = useQueryClient();
  return useMutation<
    PortalClaim,
    unknown,
    {
      id: string;
      file: File;
      documentName?: string;
      documentCategory?: string;
    }
  >({
    mutationFn: async ({ id, file, documentName, documentCategory }) => {
      const res = await portalClaimsApi.uploadDocument(id, file, documentName, documentCategory);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

export function useSubmitPortalClaim() {
  const queryClient = useQueryClient();
  return useMutation<PortalClaim, unknown, { id: string; declarationSignedAt?: string | null }>({
    mutationFn: async ({ id, declarationSignedAt }) => {
      const res = await portalClaimsApi.submit(id, {
        declarationSignedAt,
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.invalidateQueries({ queryKey: portalClaimEnrollmentsQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

export function useVerifyPortalClaim() {
  const queryClient = useQueryClient();
  return useMutation<
    PortalClaim,
    unknown,
    { id: string; decision: 'APPROVE' | 'REJECT'; reason?: string | null }
  >({
    mutationFn: async ({ id, decision, reason }) => {
      const res = await portalClaimsApi.verify(id, { decision, reason });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

export function useInitiatePortalClaimRelease() {
  const queryClient = useQueryClient();
  return useMutation<
    PortalClaim,
    unknown,
    {
      id: string;
      releaseInstructionReference: string;
      releaseInitiatedDate?: string | null;
      releaseInstructionNotes?: string | null;
    }
  >({
    mutationFn: async ({
      id,
      releaseInstructionReference,
      releaseInitiatedDate,
      releaseInstructionNotes,
    }) => {
      const res = await portalClaimsApi.initiateRelease(id, {
        releaseInstructionReference,
        releaseInitiatedDate,
        releaseInstructionNotes,
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

export function useMarkPortalClaimReleased() {
  const queryClient = useQueryClient();
  return useMutation<
    PortalClaim,
    unknown,
    { id: string; releaseReference: string; releasedDate?: string | null }
  >({
    mutationFn: async ({ id, releaseReference, releasedDate }) => {
      const res = await portalClaimsApi.markReleased(id, {
        releaseReference,
        releasedDate,
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['portal', 'claims'] });
      queryClient.invalidateQueries({ queryKey: portalClaimsWorkbenchQueryKey });
      queryClient.setQueryData(portalClaimQueryKey(data.id), data);
    },
  });
}

type PortalClaimDownloadFormat = 'csv' | 'xlsx' | 'pdf';

export function useDownloadPortalClaimReport(
  claimId: string | undefined,
  format: PortalClaimDownloadFormat = 'csv',
) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const download = useCallback(
    async (overrideFilename?: string) => {
      if (!claimId) return;
      setError(null);
      setIsDownloading(true);
      try {
        const res =
          format === 'xlsx'
            ? await portalClaimsApi.downloadClaimXlsx(claimId)
            : format === 'pdf'
              ? await portalClaimsApi.downloadClaimPdf(claimId)
              : await portalClaimsApi.downloadClaimCsv(claimId);
        const blob =
          res.data instanceof Blob
            ? res.data
            : new Blob([res.data as unknown as ArrayBuffer], {
                type:
                  format === 'xlsx'
                    ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    : format === 'pdf'
                      ? 'application/pdf'
                      : 'text/csv',
              });
        const url = window.URL.createObjectURL(blob);
        const a = window.document.createElement('a');
        a.href = url;
        a.download = overrideFilename ?? `claim_${claimId}.${format}`;
        window.document.body.appendChild(a);
        a.click();
        window.document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setIsDownloading(false);
      }
    },
    [claimId, format],
  );

  return { download, isDownloading, error };
}

export function useDownloadPortalClaimCsv(claimId: string | undefined) {
  return useDownloadPortalClaimReport(claimId, 'csv');
}
