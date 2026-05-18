import api from '../api';

export type NumericValue = number | string;

export interface MISMetric {
  code: string;
  label: string;
  value: NumericValue;
  valueType: 'AMOUNT' | 'PERCENTAGE' | 'NUMBER' | string;
  unit?: string | null;
  status: string;
  description?: string | null;
}

export interface ReportFilterDefinition {
  code: string;
  label: string;
  type: string;
  required: boolean;
}

export interface ReportCatalogItem {
  reportCode: string;
  reportName: string;
  category: string;
  module: string;
  description: string;
  route: string;
  supportedFilters: ReportFilterDefinition[];
  exportFormats: string[];
  scheduleEligible: boolean;
  permission: string;
  manualFirstNote?: string | null;
}

export interface ReportCatalogGroup {
  category: string;
  title: string;
  description: string;
  reports: ReportCatalogItem[];
}

export interface ReportCatalogResponse {
  generatedAt: string;
  groups: ReportCatalogGroup[];
}

export interface ReportPeriod {
  fromDate: string;
  toDate: string;
}

export interface ReportRun {
  id: string;
  reportCode: string;
  reportName: string;
  category: string;
  parameters: Record<string, unknown>;
  generatedBy?: string | null;
  generatedAt: string;
  status: string;
  rowCount: number;
  exportFormat: string;
  fileReference?: string | null;
  errorMessage?: string | null;
  durationMs?: number | null;
}

export interface ReportSchedule {
  id: string;
  reportCode: string;
  reportName: string;
  category: string;
  frequency: string;
  scheduleTime: string;
  outputFormat: string;
  parameters: Record<string, unknown>;
  recipients: string[];
  isActive: boolean;
  lastRunAt?: string | null;
  nextRunAt?: string | null;
  lastStatus?: string | null;
  deliveryMode: string;
  ownerUserId?: string | null;
  description?: string | null;
}

export interface DashboardSummary {
  asOfDate: string;
  generatedAt: string;
  executiveMetrics: MISMetric[];
  moduleMetrics: MISMetric[];
  exceptionMetrics: MISMetric[];
  recentRuns: ReportRun[];
  activeSchedules: ReportSchedule[];
}

export interface PortfolioSummary {
  totalAccounts: number;
  activeAccounts: number;
  closedAccounts: number;
  writtenOffAccounts: number;
  totalSanctioned: NumericValue;
  totalDisbursed: NumericValue;
  principalOutstanding: NumericValue;
  interestOutstanding: NumericValue;
  totalOutstanding: NumericValue;
  principalOverdue: NumericValue;
  interestOverdue: NumericValue;
  totalOverdue: NumericValue;
  averageTicketSize: NumericValue;
  weightedAverageYield: NumericValue;
}

export interface PortfolioBreakdownItem {
  name: string;
  count: number;
  amount: NumericValue;
  sharePercent: NumericValue;
  averageYield?: NumericValue | null;
}

export interface PortfolioSummaryReport {
  reportType: string;
  asOfDate: string;
  generatedAt: string;
  summary: PortfolioSummary;
  productBreakdown: PortfolioBreakdownItem[];
  assetQualityBreakdown: PortfolioBreakdownItem[];
  topExposures: Record<string, unknown>[];
}

export interface PeriodSummary {
  totalCount: number;
  totalAmount: NumericValue;
  averageTicketSize: NumericValue;
}

export interface DisbursementBreakdownItem {
  name: string;
  count: number;
  amount: NumericValue;
  averageTicketSize: NumericValue;
  sharePercent: NumericValue;
}

export interface DailyTrendItem {
  date: string;
  count: number;
  amount: NumericValue;
}

export interface DisbursementReport {
  reportType: string;
  period: ReportPeriod;
  generatedAt: string;
  summary: PeriodSummary;
  breakdown: DisbursementBreakdownItem[];
  dailyTrend: DailyTrendItem[];
}

export interface CollectionSummary {
  totalDemand: NumericValue;
  totalCollected: NumericValue;
  collectionEfficiency: NumericValue;
  principalCollected: NumericValue;
  interestCollected: NumericValue;
  penalCollected: NumericValue;
  chargesCollected: NumericValue;
  shortfall: NumericValue;
}

export interface CollectionModeItem {
  mode: string;
  amount: NumericValue;
  sharePercent: NumericValue;
}

export interface CollectionBucketItem {
  bucket: string;
  demand: NumericValue;
  collected: NumericValue;
  shortfall: NumericValue;
  efficiency: NumericValue;
}

export interface CollectionReport {
  reportType: string;
  period: ReportPeriod;
  generatedAt: string;
  summary: CollectionSummary;
  modeWise: CollectionModeItem[];
  bucketWise: CollectionBucketItem[];
}

export interface DelinquencyBucketItem {
  bucket: string;
  accounts: number;
  amount: NumericValue;
  sharePercent: NumericValue;
  classification: string;
}

export interface TopDelinquentAccount {
  loanAccountNumber: string;
  borrowerName: string;
  productName: string;
  outstandingAmount: NumericValue;
  daysPastDue: number;
  classification: string;
}

export interface DelinquencyReport {
  reportType: string;
  asOfDate: string;
  generatedAt: string;
  summary: {
    totalOutstanding: NumericValue;
    totalDelinquent: NumericValue;
    delinquencyRate: NumericValue;
    overdueAccounts: number;
  };
  buckets: DelinquencyBucketItem[];
  topDelinquentAccounts: TopDelinquentAccount[];
}

export interface ProfitabilityReport {
  reportType: string;
  period: ReportPeriod;
  generatedAt: string;
  summary: {
    interestIncome: NumericValue;
    feeIncome: NumericValue;
    totalIncome: NumericValue;
    interestExpense: NumericValue;
    provisionExpense: NumericValue;
    operatingExpense: NumericValue;
    totalExpense: NumericValue;
    profitBeforeTax: NumericValue;
    netInterestMargin: NumericValue;
    netMargin: NumericValue;
    loanYield: NumericValue;
    costOfFunds: NumericValue;
    spread: NumericValue;
  };
  productWise: {
    name: string;
    income: NumericValue;
    expense: NumericValue;
    profit: NumericValue;
    margin: NumericValue;
  }[];
}

export interface BranchPerformanceReport {
  reportType: string;
  period: ReportPeriod;
  generatedAt: string;
  branches: {
    branchId?: string | null;
    branchName: string;
    aum: NumericValue;
    disbursement: NumericValue;
    collection: NumericValue;
    collectionEfficiency: NumericValue;
    npaPercentage: NumericValue;
    applications: number;
    sanctionedAmount: NumericValue;
  }[];
  summary: Record<string, unknown>;
}

export interface ModuleReportRow {
  label: string;
  values: Record<string, unknown>;
  status: string;
  route?: string | null;
}

export interface ModuleReportSection {
  moduleCode: string;
  moduleName: string;
  category: string;
  route: string;
  metrics: MISMetric[];
  rows: ModuleReportRow[];
  exceptions: MISMetric[];
}

export interface AllModulesReport {
  reportType: string;
  period: ReportPeriod;
  asOfDate: string;
  generatedAt: string;
  modules: ModuleReportSection[];
}

export interface DateRangeParams {
  fromDate?: string;
  toDate?: string;
}

export interface AsOfParams {
  asOfDate?: string;
}

export const misApi = {
  getCatalog: async (): Promise<ReportCatalogResponse> => {
    const response = await api.get<ReportCatalogResponse>('/reports/mis/catalog');
    return response.data;
  },
  getDashboard: async (params?: AsOfParams): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>('/reports/mis/dashboard', { params });
    return response.data;
  },
  getPortfolioSummary: async (
    params?: AsOfParams & { unitId?: string },
  ): Promise<PortfolioSummaryReport> => {
    const response = await api.get<PortfolioSummaryReport>('/reports/mis/portfolio-summary', {
      params,
    });
    return response.data;
  },
  getDisbursement: async (
    params?: DateRangeParams & { groupBy?: 'PRODUCT' | 'BRANCH' | 'CHANNEL' },
  ): Promise<DisbursementReport> => {
    const response = await api.get<DisbursementReport>('/reports/mis/disbursement', { params });
    return response.data;
  },
  getCollection: async (params?: DateRangeParams): Promise<CollectionReport> => {
    const response = await api.get<CollectionReport>('/reports/mis/collection', { params });
    return response.data;
  },
  getDelinquency: async (params?: AsOfParams): Promise<DelinquencyReport> => {
    const response = await api.get<DelinquencyReport>('/reports/mis/delinquency', { params });
    return response.data;
  },
  getProfitability: async (params?: DateRangeParams): Promise<ProfitabilityReport> => {
    const response = await api.get<ProfitabilityReport>('/reports/mis/profitability', { params });
    return response.data;
  },
  getBranchPerformance: async (params?: DateRangeParams): Promise<BranchPerformanceReport> => {
    const response = await api.get<BranchPerformanceReport>('/reports/mis/branch-performance', {
      params,
    });
    return response.data;
  },
  getAllModules: async (params?: DateRangeParams & AsOfParams): Promise<AllModulesReport> => {
    const response = await api.get<AllModulesReport>('/reports/mis/all-modules', { params });
    return response.data;
  },
  listRuns: async (limit = 50): Promise<ReportRun[]> => {
    const response = await api.get<ReportRun[]>('/reports/mis/runs', { params: { limit } });
    return response.data;
  },
  createRun: async (payload: {
    reportCode: string;
    exportFormat: string;
    parameters?: Record<string, unknown>;
  }): Promise<ReportRun> => {
    const response = await api.post<ReportRun>('/reports/mis/runs', {
      reportCode: payload.reportCode,
      exportFormat: payload.exportFormat,
      parameters: payload.parameters ?? {},
    });
    return response.data;
  },
  listSchedules: async (activeOnly = false): Promise<ReportSchedule[]> => {
    const response = await api.get<ReportSchedule[]>('/reports/mis/schedules', {
      params: { activeOnly },
    });
    return response.data;
  },
  createSchedule: async (payload: {
    reportCode: string;
    frequency: string;
    scheduleTime: string;
    outputFormat: string;
    parameters?: Record<string, unknown>;
    recipients?: string[];
    isActive?: boolean;
    description?: string | null;
  }): Promise<ReportSchedule> => {
    const response = await api.post<ReportSchedule>('/reports/mis/schedules', {
      ...payload,
      parameters: payload.parameters ?? {},
      recipients: payload.recipients ?? [],
      isActive: payload.isActive ?? true,
    });
    return response.data;
  },
  runScheduleNow: async (scheduleId: string): Promise<ReportRun> => {
    const response = await api.post<ReportRun>(`/reports/mis/schedules/${scheduleId}/run-now`);
    return response.data;
  },
};
