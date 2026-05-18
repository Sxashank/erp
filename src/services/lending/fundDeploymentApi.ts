import api from '../api';

import type { PaginatedResponse } from '@/types/lending';

export interface FundDeploymentSummary {
  mappedDeployments: number;
  deployedAmount: string;
  activeDrawnBorrowings: string;
  unmappedDrawnBorrowings: string;
  weightedCostRate: string;
  weightedLendingRate: string;
  weightedSpreadBps: string;
}

export interface FundDeployment {
  id: string;
  organizationId: string;
  deploymentReference: string;
  borrowingId: string;
  borrowingTrancheId: string | null;
  loanAccountId: string;
  disbursementId: string | null;
  allocationDate: string;
  allocatedAmount: string;
  costRate: string;
  lendingRate: string;
  spreadBps: string;
  allocationBasis: Record<string, unknown> | null;
  status: string;
  remarks: string | null;
  createdAt: string;
}

export interface FundProfitabilityRow {
  loanAccountId: string;
  loanAccountNumber: string;
  entityName: string | null;
  deploymentCount: number;
  deployedAmount: string;
  weightedCostRate: string;
  weightedLendingRate: string;
  spreadBps: string;
  estimatedAnnualInterestIncome: string;
  estimatedAnnualInterestExpense: string;
  estimatedAnnualNii: string;
}

export interface FundProfitabilitySummary {
  mappedLoans: number;
  deployedAmount: string;
  weightedCostRate: string;
  weightedLendingRate: string;
  weightedSpreadBps: string;
  estimatedAnnualInterestIncome: string;
  estimatedAnnualInterestExpense: string;
  estimatedAnnualNii: string;
}

export interface FundProfitabilityResponse {
  summary: FundProfitabilitySummary;
  rows: FundProfitabilityRow[];
}

export interface FundDeploymentCreateBody {
  borrowingId: string;
  loanAccountId: string;
  allocatedAmount: number;
  allocationDate: string;
  remarks?: string;
}

export interface FundDeploymentFilters {
  borrowingId?: string;
  loanAccountId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

const BASE_URL = '/lending/treasury/fund-deployments';

export async function getFundDeploymentSummary(): Promise<FundDeploymentSummary> {
  const { data } = await api.get<FundDeploymentSummary>(`${BASE_URL}/summary`);
  return data;
}

export async function getFundDeploymentProfitability(
  limit = 50,
): Promise<FundProfitabilityResponse> {
  const { data } = await api.get<FundProfitabilityResponse>(`${BASE_URL}/profitability`, {
    params: { limit },
  });
  return data;
}

export async function getFundDeployments(
  filters: FundDeploymentFilters = {},
): Promise<PaginatedResponse<FundDeployment>> {
  const params = new URLSearchParams();
  if (filters.borrowingId) params.append('borrowing_id', filters.borrowingId);
  if (filters.loanAccountId) params.append('loan_account_id', filters.loanAccountId);
  if (filters.status) params.append('status', filters.status);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.pageSize) params.append('page_size', String(filters.pageSize));

  const { data } = await api.get<PaginatedResponse<FundDeployment>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return data;
}

export async function createFundDeployment(
  body: FundDeploymentCreateBody,
): Promise<FundDeployment> {
  const { data } = await api.post<FundDeployment>(BASE_URL, body, {
    headers: {
      'Idempotency-Key': crypto.randomUUID(),
    },
  });
  return data;
}
