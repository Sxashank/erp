import { api } from '@/services/api';

export interface RiskCockpitSummary {
  totalAccounts: number;
  totalOutstanding: string;
  overdueAccounts: number;
  overdueAmount: string;
  smaAccounts: number;
  smaAmount: string;
  npaAccounts: number;
  npaAmount: string;
  grossNpaPercent: string;
  provisionRequired: string;
  provisionHeld: string;
  provisionGap: string;
  provisionCoveragePercent: string;
}

export interface RiskBucketMetric {
  classification: string;
  label: string;
  accountCount: number;
  outstanding: string;
  portfolioPercent: string;
  provisionRequired: string;
  provisionHeld: string;
  provisionGap: string;
  provisionCoveragePercent: string;
}

export interface OverdueBandMetric {
  band: string;
  label: string;
  accountCount: number;
  outstanding: string;
  portfolioPercent: string;
}

export interface TopRiskExposure {
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  assetClassification: string;
  daysPastDue: number;
  totalOutstanding: string;
  overdueAmount: string;
  provisionRequired: string;
  provisionHeld: string;
  provisionCoveragePercent: string;
  npaDate: string | null;
  oldestDueDate: string | null;
}

export interface RiskCockpitResponse {
  summary: RiskCockpitSummary;
  assetClassification: RiskBucketMetric[];
  overdueBands: OverdueBandMetric[];
  topExposures: TopRiskExposure[];
}

export async function getRiskCockpit(topN = 10): Promise<RiskCockpitResponse> {
  const { data } = await api.get<RiskCockpitResponse>('/lending/risk-cockpit', {
    params: { top_n: topN },
  });
  return data;
}
