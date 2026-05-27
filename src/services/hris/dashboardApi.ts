import { api } from '@/services/api';

export interface HRDashboardStats {
  totalEmployees: number;
  activeEmployees: number;
  newJoineesThisMonth: number;
  separationsThisMonth: number;
  pendingLeaveApprovals: number;
  pendingRegularizations: number;
  todayPresent: number;
  todayAbsent: number;
  todayOnLeave: number;
  attendancePercentage: number;
  upcomingTrainings: number;
  activeCycles: number;
  pendingGoals: number;
  pendingAppraisals: number;
  payrollReadyBatches: number;
  payrollPendingBatches: number;
}

export interface HRDashboardPendingAction {
  id: string;
  type: string;
  title: string;
  employee: string;
  requestDate: string;
  status: string;
}

export interface HRDashboardUpcomingEvent {
  id: string;
  type: string;
  title: string;
  date: string;
  count?: number | null;
}

export interface HRDistributionItem {
  label: string;
  count: number;
}

export interface HRDashboardPayrollStatus {
  latestBatchId?: string | null;
  latestBatchNumber?: string | null;
  latestBatchStatus?: string | null;
  processedBatchesThisYear: number;
  approvedBatchesThisYear: number;
  paidBatchesThisYear: number;
}

export interface HRDashboardResponse {
  stats: HRDashboardStats;
  pendingActions: HRDashboardPendingAction[];
  upcomingEvents: HRDashboardUpcomingEvent[];
  departmentDistribution: HRDistributionItem[];
  unitDistribution: HRDistributionItem[];
  trainingCompletion: HRDistributionItem[];
  separationPipeline: HRDistributionItem[];
  payroll: HRDashboardPayrollStatus;
}

export const hrDashboardApi = {
  getDashboard: async (): Promise<HRDashboardResponse> => {
    const response = await api.get<HRDashboardResponse>('/hris/dashboard');
    return response.data;
  },
};
