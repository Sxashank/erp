import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  approveVerificationSchedule,
  completeVerificationSchedule,
  createVerificationSchedule,
  getVerificationSchedule,
  getVerificationSummary,
  listDiscrepancies,
  listVerificationEntries,
  listVerificationSchedules,
  startVerificationSchedule,
  updateDiscrepancy,
  updateVerificationSchedule,
  verifyVerificationEntry,
  type DiscrepancyUpdatePayload,
  type VerificationSchedulePayload,
  type VerifyEntryPayload,
} from '@/services/fixed-assets';
import type {
  Discrepancy,
  OffsetPaginatedResponse,
  VerificationEntry,
  VerificationSchedule,
  VerificationSummary,
} from '@/types/fixed-assets';

export const verificationSchedulesQueryKey = (organizationId: string) =>
  ['fixed-assets', 'verification-schedules', organizationId] as const;

export const verificationScheduleDetailQueryKey = (scheduleId: string) =>
  ['fixed-assets', 'verification-schedule', scheduleId] as const;

export const verificationEntriesQueryKey = (scheduleId: string) =>
  ['fixed-assets', 'verification-entries', scheduleId] as const;

export const verificationDiscrepanciesQueryKey = (organizationId: string) =>
  ['fixed-assets', 'verification-discrepancies', organizationId] as const;

export const verificationSummaryQueryKey = (organizationId: string, financialYear: string) =>
  ['fixed-assets', 'verification-summary', organizationId, financialYear] as const;

export function useVerificationSchedules(
  organizationId: string,
  params?: { financialYear?: string; status?: string; skip?: number; limit?: number },
) {
  return useQuery<OffsetPaginatedResponse<VerificationSchedule>>({
    queryKey: [...verificationSchedulesQueryKey(organizationId), params ?? {}],
    queryFn: () => listVerificationSchedules(organizationId, params),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useVerificationSchedule(scheduleId: string | undefined) {
  return useQuery<VerificationSchedule>({
    queryKey: verificationScheduleDetailQueryKey(scheduleId ?? 'missing'),
    queryFn: () => getVerificationSchedule(scheduleId!),
    enabled: Boolean(scheduleId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useVerificationEntries(scheduleId: string | undefined) {
  return useQuery<OffsetPaginatedResponse<VerificationEntry>>({
    queryKey: verificationEntriesQueryKey(scheduleId ?? 'missing'),
    queryFn: () => listVerificationEntries(scheduleId!, { limit: 200 }),
    enabled: Boolean(scheduleId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useVerificationDiscrepancies(
  organizationId: string,
  params?: { status?: string; skip?: number; limit?: number },
) {
  return useQuery<OffsetPaginatedResponse<Discrepancy>>({
    queryKey: [...verificationDiscrepanciesQueryKey(organizationId), params ?? {}],
    queryFn: () => listDiscrepancies(organizationId, params),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useVerificationSummary(organizationId: string, financialYear: string | undefined) {
  return useQuery<VerificationSummary>({
    queryKey: verificationSummaryQueryKey(organizationId, financialYear ?? 'missing'),
    queryFn: () => getVerificationSummary(organizationId, financialYear!),
    enabled: Boolean(financialYear),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

function invalidateVerificationQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  organizationId: string,
  scheduleId?: string,
) {
  queryClient.invalidateQueries({ queryKey: verificationSchedulesQueryKey(organizationId) });
  queryClient.invalidateQueries({ queryKey: verificationDiscrepanciesQueryKey(organizationId) });
  queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'reports', organizationId] });
  if (scheduleId) {
    queryClient.invalidateQueries({ queryKey: verificationScheduleDetailQueryKey(scheduleId) });
    queryClient.invalidateQueries({ queryKey: verificationEntriesQueryKey(scheduleId) });
  }
}

export function useCreateVerificationSchedule(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: VerificationSchedulePayload) => createVerificationSchedule(payload),
    onSuccess: (schedule) => invalidateVerificationQueries(queryClient, organizationId, schedule.id),
  });
}

export function useUpdateVerificationSchedule(organizationId: string, scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<VerificationSchedulePayload>) =>
      updateVerificationSchedule(scheduleId, payload),
    onSuccess: (schedule) => invalidateVerificationQueries(queryClient, organizationId, schedule.id),
  });
}

export function useStartVerificationSchedule(organizationId: string, scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => startVerificationSchedule(scheduleId),
    onSuccess: (schedule) => invalidateVerificationQueries(queryClient, organizationId, schedule.id),
  });
}

export function useCompleteVerificationSchedule(organizationId: string, scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => completeVerificationSchedule(scheduleId),
    onSuccess: (schedule) => invalidateVerificationQueries(queryClient, organizationId, schedule.id),
  });
}

export function useApproveVerificationSchedule(organizationId: string, scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => approveVerificationSchedule(scheduleId),
    onSuccess: (schedule) => invalidateVerificationQueries(queryClient, organizationId, schedule.id),
  });
}

export function useVerifyVerificationEntry(organizationId: string, scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: string; payload: VerifyEntryPayload }) =>
      verifyVerificationEntry(entryId, payload),
    onSuccess: () => invalidateVerificationQueries(queryClient, organizationId, scheduleId),
  });
}

export function useUpdateVerificationDiscrepancy(organizationId: string, scheduleId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      discrepancyId,
      payload,
    }: {
      discrepancyId: string;
      payload: DiscrepancyUpdatePayload;
    }) => updateDiscrepancy(discrepancyId, payload),
    onSuccess: () => invalidateVerificationQueries(queryClient, organizationId, scheduleId),
  });
}
