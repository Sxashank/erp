import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  essAttendanceApi,
  essOperationsApi,
  type AttendanceRecordsResponse,
  type AttendanceSummaryResponse,
  type ESSPerformanceSelfAppraisalPayload,
} from '@/services/essApi';

const ESS_OPERATIONS_QUERY_KEY = ['ess', 'operations'] as const;

export function useAssignedAssets() {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'assets'] as const,
    queryFn: () => essOperationsApi.getAssets(),
  });
}

export function useEssTrainingList() {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'training'] as const,
    queryFn: () => essOperationsApi.getTrainingList(),
  });
}

export function useEssTrainingDetail(programId?: string) {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'training', programId] as const,
    queryFn: () => essOperationsApi.getTrainingDetail(programId as string),
    enabled: Boolean(programId),
  });
}

export function useEssPerformancePacket() {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'performance'] as const,
    queryFn: () => essOperationsApi.getPerformanceGoals(),
  });
}

export function useEssSelfAppraisalPacket() {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'self-appraisal'] as const,
    queryFn: () => essOperationsApi.getSelfAppraisal(),
  });
}

export function useSubmitEssSelfAppraisal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ESSPerformanceSelfAppraisalPayload) =>
      essOperationsApi.submitSelfAppraisal(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ESS_OPERATIONS_QUERY_KEY });
    },
  });
}

export function useAttendanceSummary(month: string) {
  return useQuery<AttendanceSummaryResponse>({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'attendance-summary', month] as const,
    queryFn: () => essAttendanceApi.getAttendanceSummary(month),
    enabled: Boolean(month),
  });
}

export function useAttendanceRecords(fromDate: string, toDate: string) {
  return useQuery<AttendanceRecordsResponse>({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'attendance-records', fromDate, toDate] as const,
    queryFn: () => essAttendanceApi.getAttendanceRecords({ fromDate, toDate }),
    enabled: Boolean(fromDate && toDate),
  });
}

export function useRegularizations(params?: {
  status?: string;
  fromDate?: string;
  toDate?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: [...ESS_OPERATIONS_QUERY_KEY, 'regularizations', params] as const,
    queryFn: () => essAttendanceApi.getRegularizations(params),
  });
}

export function useCreateRegularization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      attendanceDate: string;
      regularizationType: string;
      requestedInTime?: string;
      requestedOutTime?: string;
      reason: string;
    }) => essAttendanceApi.createRegularization(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ESS_OPERATIONS_QUERY_KEY });
    },
  });
}
