/**
 * Lending dashboard API — aggregator endpoint.
 *
 * Wire format is camelCase (backend uses Pydantic's `CamelSchema` with
 * `alias_generator=to_camel` + `response_model_by_alias=True`). Monetary +
 * rate fields are JSON strings on the wire (Pydantic Decimal — CLAUDE.md
 * §6.2 "Float is banned for money"). Pass them straight to
 * `<AmountDisplay>` / `<PercentageDisplay>` (both accept `string`), or
 * coerce via `Number(...)` for display-only arithmetic.
 */

import api from '../api';

export interface PortfolioKPIs {
  totalAum: string;
  aumGrowthMom: string;
  activeAccounts: number;
  sanctionedPipeline: string;
  pendingDisbursements: string;
  collectionEfficiency: string;
  overdueAmount: string;
  grossNpa: string;
  netNpa: string;
  provisionCoverage: string;
}

export interface LifecycleStageMetric {
  stage: string;
  count: number;
  amount: string;
}

export interface TreasuryFundingSummary {
  activeBorrowings: number;
  sanctionedBorrowings: string;
  drawnBorrowings: string;
  availableBorrowings: string;
  borrowingOutstanding: string;
  weightedCostOfFunds: string;
}

export interface SourceOfFundsSummary {
  mappedDeployments: number;
  deployedAmount: string;
  activeDrawnBorrowings: string;
  unmappedDrawnBorrowings: string;
  weightedCostRate: string;
  weightedLendingRate: string;
  weightedSpreadBps: string;
}

export interface MarginSummary {
  lendingYield: string;
  costOfFunds: string;
  grossSpreadBps: string;
  interestReceivable: string;
  interestPayable: string;
  netInterestPosition: string;
}

export interface CollectionSummary {
  dueThisMonth: string;
  collectedThisMonth: string;
  collectionEfficiency: string;
  overdueAmount: string;
  unallocatedReceipts: string;
  unmatchedBankCreditCount: number;
  unmatchedBankCreditAmount: string;
  autoMatchCandidateCount: number;
  matchReviewRequiredCount: number;
}

export interface CashflowBucket {
  bucket: string;
  borrowerInflows: string;
  lenderOutflows: string;
  netGap: string;
}

export interface MonthlyDisbursement {
  month: string;
  amount: string;
}

export interface ProductSlice {
  name: string;
  value: string;
  color: string;
}

export interface AssetClassRow {
  category: string;
  amount: string;
  percentage: string;
  color: string;
}

export interface PendingApprovalItem {
  id: string;
  type: string;
  reference: string;
  entity: string | null;
  amount: string;
  stage: string | null;
  dueDate: string | null;
}

export interface UpcomingMaturityItem {
  id: string;
  accountNumber: string;
  entity: string | null;
  maturityDate: string;
  outstanding: string;
}

export interface LendingDashboardResponse {
  portfolioKpis: PortfolioKPIs;
  lifecyclePipeline: LifecycleStageMetric[];
  treasuryFunding: TreasuryFundingSummary;
  sourceOfFunds: SourceOfFundsSummary;
  marginSummary: MarginSummary;
  collectionSummary: CollectionSummary;
  cashflowBuckets: CashflowBucket[];
  monthlyDisbursements: MonthlyDisbursement[];
  portfolioByProduct: ProductSlice[];
  assetClassification: AssetClassRow[];
  pendingApprovals: PendingApprovalItem[];
  upcomingMaturities: UpcomingMaturityItem[];
}

export async function getLendingDashboard(): Promise<LendingDashboardResponse> {
  const { data } = await api.get<LendingDashboardResponse>('/lending/dashboard');
  return data;
}
