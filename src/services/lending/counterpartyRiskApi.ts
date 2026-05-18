/**
 * Counterparty Risk API service — thin axios wrappers (CLAUDE.md §5.4).
 *
 * Wire format is camelCase (BE uses CamelSchema). Money/percent fields are
 * JSON strings (Pydantic Decimal — CLAUDE.md §6.2). The page coerces with
 * `Number(...)` when arithmetic / formatting is needed.
 */

import api from '../api';

export type CounterpartyType = 'ENTITY' | 'LENDER' | 'ISSUER';
export type LimitStatus = 'WITHIN_LIMIT' | 'NEAR_LIMIT' | 'BREACHED';
export type BreachSeverity = 'WARNING' | 'BREACH' | 'CRITICAL';

export interface CounterpartyExposureItem {
  counterpartyId: string;
  counterpartyName: string;
  counterpartyType: CounterpartyType;
  loanExposure: string;
  investmentExposure: string;
  borrowingExposure: string;
  totalExposure: string;
  tier1Capital: string;
  limitAmount: string;
  utilizationPercent: string;
  status: LimitStatus;
  rating: string | null;
  sector: string | null;
  isInfrastructure: boolean;
}

export interface CounterpartyExposureResponse {
  items: CounterpartyExposureItem[];
  totalCounterparties: number;
  totalExposure: string;
  nearLimitCount: number;
  breachedCount: number;
  tier1Capital: string;
  singleBorrowerLimitPercent: string;
  infraLimitPercent: string;
}

export interface SectorConcentrationItem {
  sector: string;
  exposure: string;
  count: number;
  percentOfPortfolio: string;
}

export interface SectorConcentrationResponse {
  items: SectorConcentrationItem[];
  totalExposure: string;
}

export interface RatingDistributionItem {
  rating: string;
  exposure: string;
  count: number;
  percentOfPortfolio: string;
}

export interface RatingDistributionResponse {
  items: RatingDistributionItem[];
  totalExposure: string;
}

export interface LimitBreachItem {
  counterpartyId: string;
  counterpartyName: string;
  counterpartyType: CounterpartyType;
  totalExposure: string;
  limitAmount: string;
  utilizationPercent: string;
  status: LimitStatus;
  severity: BreachSeverity;
  isInfrastructure: boolean;
}

export interface LimitBreachResponse {
  items: LimitBreachItem[];
  nearLimitCount: number;
  breachedCount: number;
}

const BASE = '/lending/counterparty-risk';

export async function getCounterpartyExposures(topN = 50): Promise<CounterpartyExposureResponse> {
  const { data } = await api.get<CounterpartyExposureResponse>(`${BASE}/exposures`, {
    params: { top_n: topN },
  });
  return data;
}

export async function getSectorConcentration(): Promise<SectorConcentrationResponse> {
  const { data } = await api.get<SectorConcentrationResponse>(`${BASE}/sectors`);
  return data;
}

export async function getRatingDistribution(): Promise<RatingDistributionResponse> {
  const { data } = await api.get<RatingDistributionResponse>(`${BASE}/ratings`);
  return data;
}

export async function getLimitBreaches(): Promise<LimitBreachResponse> {
  const { data } = await api.get<LimitBreachResponse>(`${BASE}/breaches`);
  return data;
}
