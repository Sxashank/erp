import { api } from '@/services/api';

export type TrainingProgramStatus =
  | 'DRAFT'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';

export type TrainingProgramMode =
  | 'CLASSROOM'
  | 'VIRTUAL'
  | 'E_LEARNING'
  | 'WORKSHOP'
  | 'ON_THE_JOB';

export type TrainingTrainerType = 'INTERNAL' | 'EXTERNAL';

export type TrainingNominationStatus =
  | 'NOMINATED'
  | 'CONFIRMED'
  | 'ATTENDED'
  | 'NO_SHOW'
  | 'CANCELLED';

export interface TrainingProgram {
  id: string;
  organizationId: string;
  programCode: string;
  title: string;
  description: string;
  category: string;
  mode: TrainingProgramMode;
  trainerType: TrainingTrainerType;
  trainerName: string;
  trainerContact?: string | null;
  startDate: string;
  endDate: string;
  durationHours: number;
  location: string;
  maxParticipants: number;
  enrolledCount: number;
  status: TrainingProgramStatus;
  costPerParticipant: number;
  preRequisites?: string | null;
  learningObjectives?: string | null;
  isMandatory: boolean;
  certificateProvided: boolean;
}

export interface TrainingProgramSummary {
  totalPrograms: number;
  scheduled: number;
  inProgress: number;
  completed: number;
  totalParticipants: number;
}

export interface TrainingProgramListResponse {
  items: TrainingProgram[];
  total: number;
  skip: number;
  limit: number;
  summary: TrainingProgramSummary;
}

export interface TrainingProgramPayload {
  title: string;
  description: string;
  category: string;
  mode: TrainingProgramMode;
  trainerType: TrainingTrainerType;
  trainerName: string;
  trainerContact?: string;
  startDate: string;
  endDate: string;
  durationHours: number;
  location: string;
  maxParticipants: number;
  costPerParticipant: number;
  preRequisites?: string;
  learningObjectives?: string;
  isMandatory: boolean;
  certificateProvided: boolean;
  status?: TrainingProgramStatus;
}

export interface TrainingProgramFilters {
  search?: string;
  category?: string;
  mode?: TrainingProgramMode;
  status?: TrainingProgramStatus;
  skip?: number;
  limit?: number;
}

export interface TrainingAvailableEmployee {
  id: string;
  employeeCode: string;
  fullName: string;
  department: string;
  designation: string;
  email?: string | null;
}

export interface TrainingNomination {
  id: string;
  employeeId: string;
  employeeCode: string;
  employeeName: string;
  department: string;
  designation: string;
  nominatedBy?: string | null;
  nominatedOn: string;
  status: TrainingNominationStatus;
  attendanceMarked: boolean;
}

export interface TrainingFeedbackRatingSummary {
  category: string;
  rating: number;
  maxRating: number;
}

export interface TrainingFeedbackDistributionItem {
  stars: number;
  count: number;
}

export interface TrainingFeedbackSummary {
  totalParticipants: number;
  feedbackReceived: number;
  responseRate: number;
  overallRating: number;
  ratings: TrainingFeedbackRatingSummary[];
  ratingDistribution: TrainingFeedbackDistributionItem[];
  recommendPercentage: number;
}

export interface TrainingFeedback {
  id: string;
  nominationId?: string | null;
  employeeId: string;
  employeeName: string;
  employeeCode: string;
  department: string;
  overallRating: number;
  contentRating: number;
  trainerRating: number;
  facilitiesRating: number;
  relevanceRating: number;
  wouldRecommend: boolean;
  strengths?: string | null;
  improvements?: string | null;
  comments?: string | null;
  submittedOn: string;
}

export interface TrainingFeedbackBundle {
  program: TrainingProgram;
  summary: TrainingFeedbackSummary;
  individualFeedbacks: TrainingFeedback[];
}

export interface TrainingFeedbackPayload {
  employeeId: string;
  overallRating: number;
  contentRating: number;
  trainerRating: number;
  facilitiesRating: number;
  relevanceRating: number;
  wouldRecommend: boolean;
  strengths?: string;
  improvements?: string;
  comments?: string;
  submittedOn: string;
}

export const trainingApi = {
  listPrograms: async (params?: TrainingProgramFilters): Promise<TrainingProgramListResponse> => {
    const response = await api.get<TrainingProgramListResponse>('/hris/training/programs', {
      params,
    });
    return response.data;
  },

  getProgram: async (programId: string): Promise<TrainingProgram> => {
    const response = await api.get<TrainingProgram>(`/hris/training/programs/${programId}`);
    return response.data;
  },

  createProgram: async (payload: TrainingProgramPayload): Promise<TrainingProgram> => {
    const response = await api.post<TrainingProgram>('/hris/training/programs', payload);
    return response.data;
  },

  updateProgram: async (
    programId: string,
    payload: Partial<TrainingProgramPayload>,
  ): Promise<TrainingProgram> => {
    const response = await api.put<TrainingProgram>(
      `/hris/training/programs/${programId}`,
      payload,
    );
    return response.data;
  },

  listAvailableEmployees: async (
    programId: string,
    search?: string,
  ): Promise<TrainingAvailableEmployee[]> => {
    const response = await api.get<TrainingAvailableEmployee[]>(
      `/hris/training/programs/${programId}/available-employees`,
      { params: { search } },
    );
    return response.data;
  },

  listNominations: async (programId: string): Promise<TrainingNomination[]> => {
    const response = await api.get<TrainingNomination[]>(
      `/hris/training/programs/${programId}/nominations`,
    );
    return response.data;
  },

  addNominations: async (
    programId: string,
    employeeIds: string[],
  ): Promise<TrainingNomination[]> => {
    const response = await api.post<TrainingNomination[]>(
      `/hris/training/programs/${programId}/nominations`,
      { employeeIds },
    );
    return response.data;
  },

  updateNomination: async (
    programId: string,
    nominationId: string,
    payload: { status: TrainingNominationStatus; attendanceMarked?: boolean },
  ): Promise<TrainingNomination> => {
    const response = await api.patch<TrainingNomination>(
      `/hris/training/programs/${programId}/nominations/${nominationId}`,
      payload,
    );
    return response.data;
  },

  getFeedback: async (programId: string): Promise<TrainingFeedbackBundle> => {
    const response = await api.get<TrainingFeedbackBundle>(
      `/hris/training/programs/${programId}/feedback`,
    );
    return response.data;
  },

  recordFeedback: async (
    programId: string,
    payload: TrainingFeedbackPayload,
  ): Promise<TrainingFeedbackBundle> => {
    const response = await api.post<TrainingFeedbackBundle>(
      `/hris/training/programs/${programId}/feedback`,
      payload,
    );
    return response.data;
  },
};
