import { api } from '@/services/api';

export type AppraisalCycleStatus =
  | 'DRAFT'
  | 'GOAL_SETTING'
  | 'IN_PROGRESS'
  | 'REVIEW'
  | 'CALIBRATION'
  | 'COMPLETED'
  | 'CANCELLED';

export type GoalStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'DEFERRED';

export type AppraisalStatus =
  | 'NOT_STARTED'
  | 'GOAL_SETTING'
  | 'SELF_APPRAISAL'
  | 'MANAGER_REVIEW'
  | 'CALIBRATION'
  | 'COMPLETED'
  | 'CANCELLED';

export type AppraisalCycleType = 'ANNUAL' | 'HALF_YEARLY' | 'QUARTERLY';

export interface AppraisalCycle {
  id: string;
  organizationId: string;
  code: string;
  name: string;
  description?: string | null;
  financialYearId?: string | null;
  cycleType: AppraisalCycleType;
  startDate: string;
  endDate: string;
  goalSettingStart?: string | null;
  goalSettingEnd?: string | null;
  selfAppraisalStart?: string | null;
  selfAppraisalEnd?: string | null;
  managerReviewStart?: string | null;
  managerReviewEnd?: string | null;
  calibrationStart?: string | null;
  calibrationEnd?: string | null;
  ratingScale: number;
  weightageGoals: number;
  weightageCompetencies: number;
  allowSelfRating: boolean;
  allowPeerFeedback: boolean;
  status: AppraisalCycleStatus;
  eligibleEmployees: number;
  completedAppraisals: number;
  pendingSelfAppraisal: number;
  pendingManagerReview: number;
}

export interface AppraisalCycleListItem {
  id: string;
  code: string;
  name: string;
  financialYear?: string | null;
  cycleType: AppraisalCycleType;
  startDate: string;
  endDate: string;
  goalSettingEnd?: string | null;
  selfAppraisalEnd?: string | null;
  managerReviewEnd?: string | null;
  status: AppraisalCycleStatus;
  eligibleEmployees: number;
  completedAppraisals: number;
  pendingSelfAppraisal: number;
  pendingManagerReview: number;
}

export interface AppraisalCycleSummary {
  totalCycles: number;
  active: number;
  completed: number;
  draft: number;
  employeesAppraised: number;
}

export interface AppraisalCycleListBundle {
  items: AppraisalCycleListItem[];
  total: number;
  skip: number;
  limit: number;
  summary: AppraisalCycleSummary;
}

export interface PerformanceEmployeeSummary {
  appraisalId: string;
  employeeId: string;
  employeeCode: string;
  employeeName: string;
  department?: string | null;
  designation?: string | null;
  reviewerName?: string | null;
  status: AppraisalStatus;
  goalCount: number;
  submittedGoals: number;
  completedGoals: number;
  overallRating?: number | null;
  finalGrade?: string | null;
  selfAppraisalDate?: string | null;
  managerReviewDate?: string | null;
  calibratedAt?: string | null;
}

export interface PerformanceGoal {
  id: string;
  employeeId: string;
  goalNumber: number;
  title: string;
  description?: string | null;
  category?: string | null;
  weightage: number;
  targetValue?: string | null;
  measurementCriteria?: string | null;
  startDate?: string | null;
  dueDate?: string | null;
  status: GoalStatus;
  progressPercent: number;
  achievementValue?: string | null;
  selfRating?: number | null;
  selfComments?: string | null;
  managerRating?: number | null;
  managerComments?: string | null;
  finalRating?: number | null;
  approvedAt?: string | null;
}

export interface EmployeeAppraisal {
  id: string;
  appraisalCycleId: string;
  employeeId: string;
  reviewerId?: string | null;
  status: AppraisalStatus;
  goalRating?: number | null;
  competencyRating?: number | null;
  overallRating?: number | null;
  finalGrade?: string | null;
  selfAppraisalDate?: string | null;
  selfSummary?: string | null;
  selfAchievements?: string | null;
  selfChallenges?: string | null;
  selfDevelopmentAreas?: string | null;
  managerReviewDate?: string | null;
  managerSummary?: string | null;
  managerAchievements?: string | null;
  managerImprovements?: string | null;
  managerRecommendations?: string | null;
  calibrationNotes?: string | null;
  calibratedRating?: number | null;
  calibratedGrade?: string | null;
  calibratedBy?: string | null;
  calibratedAt?: string | null;
  employeeAcknowledgment: boolean;
  acknowledgmentDate?: string | null;
  employeeComments?: string | null;
}

export interface EmployeePerformanceDetail {
  cycle: AppraisalCycle;
  employee: PerformanceEmployeeSummary;
  appraisal: EmployeeAppraisal;
  goals: PerformanceGoal[];
}

export interface AppraisalCyclePayload {
  name: string;
  description?: string;
  financialYearId?: string | null;
  cycleType: AppraisalCycleType;
  startDate: string;
  endDate: string;
  goalSettingStart?: string | null;
  goalSettingEnd?: string | null;
  selfAppraisalStart?: string | null;
  selfAppraisalEnd?: string | null;
  managerReviewStart?: string | null;
  managerReviewEnd?: string | null;
  calibrationStart?: string | null;
  calibrationEnd?: string | null;
  ratingScale: number;
  weightageGoals: number;
  weightageCompetencies: number;
  allowSelfRating: boolean;
  allowPeerFeedback: boolean;
  includeAllActiveEmployees: boolean;
  employeeIds: string[];
}

export interface PerformanceGoalPayload {
  title: string;
  description?: string;
  category?: string;
  weightage: number;
  targetValue?: string;
  measurementCriteria?: string;
  startDate?: string | null;
  dueDate?: string | null;
}

export interface PerformanceSelfAssessmentPayload {
  goalId: string;
  selfRating: number;
  selfProgress: number;
  selfComments: string;
  achievementValue?: string;
}

export interface PerformanceSelfAppraisalPayload {
  goals: PerformanceSelfAssessmentPayload[];
  competencyRating: number;
  selfSummary: string;
  selfAchievements: string;
  selfChallenges?: string;
  selfDevelopmentAreas: string;
  employeeComments?: string;
}

export interface PerformanceManagerGoalReviewPayload {
  goalId: string;
  managerRating: number;
  managerComments: string;
  finalRating?: number;
}

export interface PerformanceManagerReviewPayload {
  goals: PerformanceManagerGoalReviewPayload[];
  competencyRating: number;
  managerSummary: string;
  managerAchievements?: string;
  managerImprovements: string;
  managerRecommendations?: string;
}

export interface PerformanceCalibrationPayload {
  calibratedRating: number;
  calibrationNotes?: string;
  finalGrade?: string;
}

export interface PerformanceCycleFilters {
  search?: string;
  status?: AppraisalCycleStatus;
  skip?: number;
  limit?: number;
}

export const performanceApi = {
  listCycles: async (params?: PerformanceCycleFilters): Promise<AppraisalCycleListBundle> => {
    const response = await api.get<AppraisalCycleListBundle>('/hris/performance/cycles', {
      params,
    });
    return response.data;
  },

  createCycle: async (payload: AppraisalCyclePayload): Promise<AppraisalCycle> => {
    const response = await api.post<AppraisalCycle>('/hris/performance/cycles', payload);
    return response.data;
  },

  getCycle: async (cycleId: string): Promise<AppraisalCycle> => {
    const response = await api.get<AppraisalCycle>(`/hris/performance/cycles/${cycleId}`);
    return response.data;
  },

  updateCycle: async (
    cycleId: string,
    payload: Partial<AppraisalCyclePayload>,
  ): Promise<AppraisalCycle> => {
    const response = await api.put<AppraisalCycle>(`/hris/performance/cycles/${cycleId}`, payload);
    return response.data;
  },

  startCycle: async (cycleId: string): Promise<AppraisalCycle> => {
    const response = await api.post<AppraisalCycle>(`/hris/performance/cycles/${cycleId}/start`);
    return response.data;
  },

  closeCycle: async (cycleId: string): Promise<AppraisalCycle> => {
    const response = await api.post<AppraisalCycle>(`/hris/performance/cycles/${cycleId}/close`);
    return response.data;
  },

  listCycleEmployees: async (
    cycleId: string,
    params?: { search?: string; status?: AppraisalStatus },
  ): Promise<PerformanceEmployeeSummary[]> => {
    const response = await api.get<PerformanceEmployeeSummary[]>(
      `/hris/performance/cycles/${cycleId}/employees`,
      { params },
    );
    return response.data;
  },

  getEmployeePerformanceDetail: async (
    cycleId: string,
    employeeId: string,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.get<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}`,
    );
    return response.data;
  },

  createGoal: async (
    cycleId: string,
    employeeId: string,
    payload: PerformanceGoalPayload,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.post<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}/goals`,
      payload,
    );
    return response.data;
  },

  updateGoal: async (
    goalId: string,
    payload: Partial<PerformanceGoalPayload>,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.put<EmployeePerformanceDetail>(
      `/hris/performance/goals/${goalId}`,
      payload,
    );
    return response.data;
  },

  deleteGoal: async (goalId: string): Promise<EmployeePerformanceDetail> => {
    const response = await api.delete<EmployeePerformanceDetail>(
      `/hris/performance/goals/${goalId}`,
    );
    return response.data;
  },

  submitGoals: async (cycleId: string, employeeId: string): Promise<EmployeePerformanceDetail> => {
    const response = await api.post<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}/goals/submit`,
    );
    return response.data;
  },

  submitSelfAppraisal: async (
    cycleId: string,
    employeeId: string,
    payload: PerformanceSelfAppraisalPayload,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.post<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}/self-appraisal`,
      payload,
    );
    return response.data;
  },

  submitManagerReview: async (
    cycleId: string,
    employeeId: string,
    payload: PerformanceManagerReviewPayload,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.post<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}/manager-review`,
      payload,
    );
    return response.data;
  },

  calibrateAppraisal: async (
    cycleId: string,
    employeeId: string,
    payload: PerformanceCalibrationPayload,
  ): Promise<EmployeePerformanceDetail> => {
    const response = await api.post<EmployeePerformanceDetail>(
      `/hris/performance/cycles/${cycleId}/employees/${employeeId}/calibration`,
      payload,
    );
    return response.data;
  },
};
