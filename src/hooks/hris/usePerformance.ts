import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  performanceApi,
  type AppraisalStatus,
  type AppraisalCyclePayload,
  type PerformanceCalibrationPayload,
  type PerformanceCycleFilters,
  type PerformanceGoalPayload,
  type PerformanceManagerReviewPayload,
  type PerformanceSelfAppraisalPayload,
} from '@/services/hris/performanceApi';

const PERFORMANCE_QUERY_KEY = ['hris', 'performance'] as const;

export function usePerformanceCycles(filters: PerformanceCycleFilters) {
  return useQuery({
    queryKey: [...PERFORMANCE_QUERY_KEY, 'cycles', filters] as const,
    queryFn: () => performanceApi.listCycles(filters),
  });
}

export function usePerformanceCycle(cycleId?: string) {
  return useQuery({
    queryKey: [...PERFORMANCE_QUERY_KEY, 'cycle', cycleId] as const,
    queryFn: () => performanceApi.getCycle(cycleId as string),
    enabled: Boolean(cycleId),
  });
}

export function useCycleEmployees(
  cycleId?: string,
  params?: { search?: string; status?: AppraisalStatus },
) {
  return useQuery({
    queryKey: [...PERFORMANCE_QUERY_KEY, 'employees', cycleId, params] as const,
    queryFn: () => performanceApi.listCycleEmployees(cycleId as string, params),
    enabled: Boolean(cycleId),
  });
}

export function useEmployeePerformanceDetail(cycleId?: string, employeeId?: string) {
  return useQuery({
    queryKey: [...PERFORMANCE_QUERY_KEY, 'detail', cycleId, employeeId] as const,
    queryFn: () =>
      performanceApi.getEmployeePerformanceDetail(cycleId as string, employeeId as string),
    enabled: Boolean(cycleId && employeeId),
  });
}

export function useCreateCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AppraisalCyclePayload) => performanceApi.createCycle(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useUpdateCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      cycleId,
      payload,
    }: {
      cycleId: string;
      payload: Partial<AppraisalCyclePayload>;
    }) => performanceApi.updateCycle(cycleId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useStartCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (cycleId: string) => performanceApi.startCycle(cycleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useCloseCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (cycleId: string) => performanceApi.closeCycle(cycleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useCreateGoal(cycleId: string, employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PerformanceGoalPayload) =>
      performanceApi.createGoal(cycleId, employeeId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useUpdateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      goalId,
      payload,
    }: {
      goalId: string;
      payload: Partial<PerformanceGoalPayload>;
    }) => performanceApi.updateGoal(goalId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useDeleteGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: string) => performanceApi.deleteGoal(goalId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useSubmitGoals(cycleId: string, employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => performanceApi.submitGoals(cycleId, employeeId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useSubmitSelfAppraisal(cycleId: string, employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PerformanceSelfAppraisalPayload) =>
      performanceApi.submitSelfAppraisal(cycleId, employeeId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useSubmitManagerReview(cycleId: string, employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PerformanceManagerReviewPayload) =>
      performanceApi.submitManagerReview(cycleId, employeeId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}

export function useCalibrateAppraisal(cycleId: string, employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PerformanceCalibrationPayload) =>
      performanceApi.calibrateAppraisal(cycleId, employeeId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERFORMANCE_QUERY_KEY });
    },
  });
}
