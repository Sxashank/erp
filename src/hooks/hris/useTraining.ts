import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  trainingApi,
  type TrainingFeedbackPayload,
  type TrainingProgramFilters,
  type TrainingProgramPayload,
} from '@/services/hris/trainingApi';

const TRAINING_QUERY_KEY = ['hris', 'training'] as const;

export function useTrainingPrograms(filters: TrainingProgramFilters) {
  return useQuery({
    queryKey: [...TRAINING_QUERY_KEY, 'programs', filters] as const,
    queryFn: () => trainingApi.listPrograms(filters),
  });
}

export function useTrainingProgram(programId?: string) {
  return useQuery({
    queryKey: [...TRAINING_QUERY_KEY, 'program', programId] as const,
    queryFn: () => trainingApi.getProgram(programId as string),
    enabled: Boolean(programId),
  });
}

export function useCreateTrainingProgram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TrainingProgramPayload) => trainingApi.createProgram(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TRAINING_QUERY_KEY });
    },
  });
}

export function useUpdateTrainingProgram(programId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<TrainingProgramPayload>) =>
      trainingApi.updateProgram(programId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TRAINING_QUERY_KEY });
    },
  });
}

export function useTrainingAvailableEmployees(programId?: string, search?: string) {
  return useQuery({
    queryKey: [...TRAINING_QUERY_KEY, 'available-employees', programId, search] as const,
    queryFn: () => trainingApi.listAvailableEmployees(programId as string, search),
    enabled: Boolean(programId),
  });
}

export function useTrainingNominations(programId?: string) {
  return useQuery({
    queryKey: [...TRAINING_QUERY_KEY, 'nominations', programId] as const,
    queryFn: () => trainingApi.listNominations(programId as string),
    enabled: Boolean(programId),
  });
}

export function useAddTrainingNominations(programId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (employeeIds: string[]) => trainingApi.addNominations(programId, employeeIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TRAINING_QUERY_KEY, 'nominations', programId],
      });
      void queryClient.invalidateQueries({
        queryKey: [...TRAINING_QUERY_KEY, 'available-employees', programId],
      });
      void queryClient.invalidateQueries({ queryKey: TRAINING_QUERY_KEY });
    },
  });
}

export function useUpdateTrainingNomination(programId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      nominationId,
      payload,
    }: {
      nominationId: string;
      payload: {
        status: Parameters<typeof trainingApi.updateNomination>[2]['status'];
        attendanceMarked?: boolean;
      };
    }) => trainingApi.updateNomination(programId, nominationId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TRAINING_QUERY_KEY, 'nominations', programId],
      });
      void queryClient.invalidateQueries({ queryKey: TRAINING_QUERY_KEY });
    },
  });
}

export function useTrainingFeedback(programId?: string) {
  return useQuery({
    queryKey: [...TRAINING_QUERY_KEY, 'feedback', programId] as const,
    queryFn: () => trainingApi.getFeedback(programId as string),
    enabled: Boolean(programId),
  });
}

export function useRecordTrainingFeedback(programId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TrainingFeedbackPayload) =>
      trainingApi.recordFeedback(programId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TRAINING_QUERY_KEY, 'feedback', programId],
      });
      void queryClient.invalidateQueries({
        queryKey: [...TRAINING_QUERY_KEY, 'nominations', programId],
      });
      void queryClient.invalidateQueries({ queryKey: TRAINING_QUERY_KEY });
    },
  });
}
