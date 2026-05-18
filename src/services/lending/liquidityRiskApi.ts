/**
 * Liquidity Risk API service — thin axios wrappers (CLAUDE.md §5.4).
 *
 * Backend: /api/v1/lending/liquidity-risk/{lcr,nsfr,cashflow-ladder,funding-concentration}.
 * Wire format is camelCase via Pydantic CamelSchema. Money + percent + weight
 * fields are Decimal-as-string (CLAUDE.md §6.2); the page coerces with
 * Number(...) when arithmetic or display formatting is needed.
 */

import api from '../api';

export type LiquidityStatus = 'ADEQUATE' | 'WATCH' | 'BREACH' | 'NO_DATA';
export type ConcentrationRiskFlag = 'HIGH' | 'MEDIUM' | 'LOW';

// =============================================================================
// LCR
// =============================================================================

export interface LCRComponent {
  label: string;
  amount: string;
  weight: string;
  weightedAmount: string;
}

export interface LCRSnapshot {
  asOfDate: string;
  hqlaLevel1: LCRComponent[];
  hqlaLevel2A: LCRComponent[];
  hqlaLevel2B: LCRComponent[];
  totalHqla: string;
  outflows: LCRComponent[];
  totalWeightedOutflows: string;
  inflows: LCRComponent[];
  totalWeightedInflows: string;
  inflowCapApplied: boolean;
  netCashOutflows: string;
  lcrPercent: string;
  minimumRequiredPercent: string;
  status: LiquidityStatus;
}

// =============================================================================
// NSFR
// =============================================================================

export interface NSFRComponent {
  label: string;
  amount: string;
  weight: string;
  weightedAmount: string;
}

export interface NSFRSnapshot {
  asOfDate: string;
  asfComponents: NSFRComponent[];
  totalAsf: string;
  rsfComponents: NSFRComponent[];
  totalRsf: string;
  nsfrPercent: string;
  minimumRequiredPercent: string;
  status: LiquidityStatus;
}

// =============================================================================
// Cash-flow ladder
// =============================================================================

export interface CashflowBucket {
  bucketLabel: string;
  daysFrom: number;
  daysTo: number | null;
  inflows: string;
  outflows: string;
  gap: string;
  cumulativeGap: string;
}

export interface CashflowLadderSnapshot {
  asOfDate: string;
  buckets: CashflowBucket[];
  totalInflows: string;
  totalOutflows: string;
  netPosition: string;
}

// =============================================================================
// Funding concentration
// =============================================================================

export interface FundingConcentrationItem {
  lenderId: string;
  lenderName: string;
  lenderType: string | null;
  outstanding: string;
  percentOfTotal: string;
  riskFlag: ConcentrationRiskFlag;
}

export interface FundingConcentrationSnapshot {
  asOfDate: string;
  items: FundingConcentrationItem[];
  totalOutstanding: string;
  totalLenders: number;
  highConcentrationCount: number;
}

const BASE = '/lending/liquidity-risk';

export async function getLcrSnapshot(asOfDate?: string): Promise<LCRSnapshot> {
  const { data } = await api.get<LCRSnapshot>(`${BASE}/lcr`, {
    params: asOfDate ? { as_of_date: asOfDate } : undefined,
  });
  return data;
}

export async function getNsfrSnapshot(asOfDate?: string): Promise<NSFRSnapshot> {
  const { data } = await api.get<NSFRSnapshot>(`${BASE}/nsfr`, {
    params: asOfDate ? { as_of_date: asOfDate } : undefined,
  });
  return data;
}

export async function getCashflowLadder(asOfDate?: string): Promise<CashflowLadderSnapshot> {
  const { data } = await api.get<CashflowLadderSnapshot>(`${BASE}/cashflow-ladder`, {
    params: asOfDate ? { as_of_date: asOfDate } : undefined,
  });
  return data;
}

export async function getFundingConcentration(
  topN = 10,
  asOfDate?: string,
): Promise<FundingConcentrationSnapshot> {
  const params: Record<string, string | number> = { top_n: topN };
  if (asOfDate) params.as_of_date = asOfDate;
  const { data } = await api.get<FundingConcentrationSnapshot>(`${BASE}/funding-concentration`, {
    params,
  });
  return data;
}
