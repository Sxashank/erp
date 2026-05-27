/**
 * Treasury Investment API service.
 *
 * Thin axios wrapper for `/lending/treasury/investments/*`. Wire format is
 * camelCase (Pydantic CamelSchema on the BE). Money fields are JSON strings
 * on the wire — Pydantic v2 serialises `Decimal` as `string` so we never
 * lose precision (CLAUDE.md §6.2).
 *
 * Mutating endpoints inject a fresh `Idempotency-Key` per call
 * (CLAUDE.md §6.3). See `src/lib/errorToast.ts` for surfacing the
 * `{error_code, message, correlation_id}` envelope on failure.
 */

import api from '../api';

const BASE_URL = '/lending/treasury/investments';

// --------------------------------------------------------------------------
// Enums (mirror BE — keep them as string literals so dropdowns can iterate)
// --------------------------------------------------------------------------

export type InvestmentType =
  | 'GSEC'
  | 'SDL'
  | 'TBILL'
  | 'CORP_BOND'
  | 'NCD'
  | 'CP'
  | 'CD'
  | 'MUTUAL_FUND';

export type InvestmentCategory = 'HTM' | 'AFS' | 'HFT';

export type CouponFrequency = 'ANNUAL' | 'SEMI_ANNUAL' | 'QUARTERLY' | 'MONTHLY' | 'ZERO';

export type InvestmentStatus = 'ACTIVE' | 'MATURED' | 'SOLD';

// --------------------------------------------------------------------------
// Wire shapes
// --------------------------------------------------------------------------

/** Investment record as it appears on the wire (Decimal-as-string). */
export interface InvestmentResponse {
  id: string;
  organizationId: string;
  investmentNumber: string;

  type: InvestmentType;
  category: InvestmentCategory;

  issuer: string;
  description: string;
  isin: string | null;

  faceValue: string;
  purchasePrice: string;
  units: string;

  couponRate: string;
  ytm: string;
  couponFrequency: CouponFrequency;

  purchaseDate: string; // ISO yyyy-MM-dd
  maturityDate: string | null;

  broker: string | null;
  remarks: string | null;

  status: InvestmentStatus;
  currentValue: string | null;
  accruedInterest: string;

  saleValue: string | null;
  saleDate: string | null;
  realizedGainLoss: string | null;

  createdAt: string;
  updatedAt: string | null;
  version: number;
}

export interface InvestmentListResponse {
  items: InvestmentResponse[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface CategoryBreakdown {
  key: string;
  count: number;
  faceValue: string;
  purchaseValue: string;
  currentValue: string;
}

export interface PortfolioSummaryResponse {
  totalCount: number;
  activeCount: number;
  totalFaceValue: string;
  totalPurchaseValue: string;
  totalCurrentValue: string;
  unrealizedGainLoss: string;
  weightedAvgYtm: string | null;
  byCategory: CategoryBreakdown[];
  byType: CategoryBreakdown[];
}

export interface MaturityBucketItem {
  id: string;
  investmentNumber: string;
  issuer: string;
  description: string;
  type: InvestmentType;
  faceValue: string;
  units: string;
  couponRate: string;
  maturityDate: string;
}

export interface MaturityBucket {
  label: string;
  periodStart: string;
  periodEnd: string;
  totalFaceValue: string;
  investmentCount: number;
  investments: MaturityBucketItem[];
}

export interface InvestmentMaturityResponse {
  monthsAhead: number;
  asOfDate: string;
  upcoming30D: MaturityBucketItem[];
  totalMaturing30D: string;
  totalMaturing90D: string;
  totalMaturingPeriod: string;
  buckets: MaturityBucket[];
}

// --------------------------------------------------------------------------
// Request shapes
// --------------------------------------------------------------------------

export interface InvestmentFilters {
  status?: InvestmentStatus;
  category?: InvestmentCategory;
  page?: number;
  pageSize?: number;
}

/**
 * Create request — camelCase per BE CamelSchema. Decimal-typed fields can be
 * `number` or `string`; we send strings so we never lose precision on the
 * wire (CLAUDE.md §6.2). The form layer formats user input before calling.
 */
export interface InvestmentCreateRequest {
  type: InvestmentType;
  category: InvestmentCategory;
  issuer: string;
  description: string;
  isin?: string;

  faceValue: string;
  purchasePrice: string;
  units: string;

  couponRate: string;
  ytm: string;
  couponFrequency: CouponFrequency;

  purchaseDate: string; // yyyy-MM-dd
  maturityDate?: string;

  broker?: string;
  remarks?: string;
}

export interface InvestmentMatureRequest {
  saleValue?: string;
  saleDate?: string;
  remarks?: string;
}

// --------------------------------------------------------------------------
// Calls
// --------------------------------------------------------------------------

export async function listInvestments(
  filters?: InvestmentFilters,
): Promise<InvestmentListResponse> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.category) params.append('category', filters.category);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<InvestmentListResponse>(`${BASE_URL}?${params.toString()}`);
  return data;
}

export async function getInvestment(id: string): Promise<InvestmentResponse> {
  const { data } = await api.get<InvestmentResponse>(`${BASE_URL}/${id}`);
  return data;
}

export async function getPortfolioSummary(): Promise<PortfolioSummaryResponse> {
  const { data } = await api.get<PortfolioSummaryResponse>(`${BASE_URL}/portfolio/summary`);
  return data;
}

export async function getMaturitySchedule(months = 12): Promise<InvestmentMaturityResponse> {
  const { data } = await api.get<InvestmentMaturityResponse>(
    `${BASE_URL}/maturity?months=${months}`,
  );
  return data;
}

/**
 * POST /treasury/investments — financial mutation, requires Idempotency-Key
 * (CLAUDE.md §6.3). A fresh UUID is generated per call so retries dedupe.
 */
export async function createInvestment(
  payload: InvestmentCreateRequest,
): Promise<InvestmentResponse> {
  const { data } = await api.post<InvestmentResponse>(BASE_URL, payload, {
    headers: { 'Idempotency-Key': crypto.randomUUID() },
  });
  return data;
}

/**
 * POST /treasury/investments/{id}/mature — financial mutation, requires
 * Idempotency-Key (CLAUDE.md §6.3).
 */
export async function markMatured(
  id: string,
  payload: InvestmentMatureRequest = {},
): Promise<InvestmentResponse> {
  const { data } = await api.post<InvestmentResponse>(`${BASE_URL}/${id}/mature`, payload, {
    headers: { 'Idempotency-Key': crypto.randomUUID() },
  });
  return data;
}

export const treasuryInvestmentApi = {
  listInvestments,
  getInvestment,
  getPortfolioSummary,
  getMaturitySchedule,
  createInvestment,
  markMatured,
};

export default treasuryInvestmentApi;
