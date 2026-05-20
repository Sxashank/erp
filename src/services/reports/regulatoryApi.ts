/**
 * Regulatory reports API — thin axios wrappers around
 * `GET /api/v1/reports/regulatory/*` (see
 * `backend/app/api/v1/reports/regulatory.py` and
 * `backend/app/services/reports/regulatory_report_service.py`).
 *
 * All endpoints are read-only GETs (no `Idempotency-Key` needed). The
 * backend serialises numeric amounts via `float(Decimal(...))` for now —
 * we accept `number | string` on the response types so future
 * Decimal-string switches (CLAUDE.md §6.2) don't break the types.
 *
 * See CLAUDE.md §5.4 (services are thin, typed, no business logic).
 */

import api from '../api';

/** Common scalar field type for monetary amounts and ratios. Backend
 *  currently emits `float`; tolerate `string` so we can flip to decimal
 *  strings later without an FE migration. */
export type NumericValue = number | string;

/* ──────────────────────── ALM ──────────────────────── */

export interface ALMBucket {
  bucket: string;
  assets: NumericValue;
  liabilities: NumericValue;
  gap: NumericValue;
  cumulative_gap: NumericValue;
  gap_percentage: NumericValue;
}

export interface ALMReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  buckets: ALMBucket[];
  summary: {
    total_assets: NumericValue;
    total_liabilities: NumericValue;
    net_gap: NumericValue;
  };
}

export interface ALMParams {
  as_of_date?: string;
  report_type?: 'STRUCTURAL' | 'DYNAMIC';
}

export async function getAlm(params?: ALMParams): Promise<ALMReport> {
  const res = await api.get<ALMReport>('/reports/regulatory/alm', { params });
  return res.data;
}

/* ──────────────────────── NPA ──────────────────────── */

export interface NPACategory {
  category_code: string;
  category_name: string;
  account_count: number;
  outstanding_amount: NumericValue;
  provision_rate: NumericValue;
  provision_amount: NumericValue;
}

export interface NPAReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  categories: NPACategory[];
  summary: {
    total_advances: NumericValue;
    gross_npa: NumericValue;
    gross_npa_ratio: NumericValue;
    total_provision: NumericValue;
    net_npa: NumericValue;
    net_npa_ratio: NumericValue;
  };
}

export interface NPAParams {
  as_of_date?: string;
  detailed?: boolean;
}

export async function getNpa(params?: NPAParams): Promise<NPAReport> {
  const res = await api.get<NPAReport>('/reports/regulatory/npa', { params });
  return res.data;
}

/* ──────────────────────── CRAR ──────────────────────── */

export interface CRARReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  capital: {
    tier1_capital: NumericValue;
    tier2_capital: NumericValue;
    total_capital: NumericValue;
  };
  risk_weighted_assets: {
    credit_risk_rwa: NumericValue;
    market_risk_rwa: NumericValue;
    operational_risk_rwa: NumericValue;
    total_rwa: NumericValue;
  };
  ratios: {
    crar: NumericValue;
    tier1_ratio: NumericValue;
    minimum_crar_required: NumericValue;
    surplus_deficit: NumericValue;
  };
}

export interface CRARParams {
  as_of_date?: string;
}

export async function getCrar(params?: CRARParams): Promise<CRARReport> {
  const res = await api.get<CRARReport>('/reports/regulatory/crar', { params });
  return res.data;
}

/* ──────────────────────── Liquidity (LCR) ──────────────────────── */

export interface LiquidityReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  hqla: {
    level1_assets: NumericValue;
    level2a_assets: NumericValue;
    level2b_assets: NumericValue;
    total_hqla: NumericValue;
  };
  cash_flows: {
    total_outflows: NumericValue;
    total_inflows: NumericValue;
    net_outflows: NumericValue;
  };
  ratios: {
    lcr: NumericValue;
    minimum_lcr_required: NumericValue;
    surplus_deficit: NumericValue;
  };
}

export interface LiquidityParams {
  as_of_date?: string;
}

export async function getLiquidity(params?: LiquidityParams): Promise<LiquidityReport> {
  const res = await api.get<LiquidityReport>('/reports/regulatory/liquidity', {
    params,
  });
  return res.data;
}

/* ──────────────────── Large Exposure ──────────────────── */

export interface LargeExposureItem {
  borrower_name: string;
  exposure_amount: NumericValue;
}

export interface LargeExposureReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  tier1_capital: NumericValue;
  threshold_percentage: NumericValue;
  threshold_amount: NumericValue;
  exposures: LargeExposureItem[];
  summary: {
    count: number;
    total_exposure: NumericValue;
  };
}

export interface LargeExposureParams {
  as_of_date?: string;
  threshold_percentage?: number;
}

export async function getLargeExposure(params?: LargeExposureParams): Promise<LargeExposureReport> {
  const res = await api.get<LargeExposureReport>('/reports/regulatory/large-exposure', { params });
  return res.data;
}

/* ──────────────────── CRAR sub-sections ──────────────────── */

/** Capital-composition line item — one row of the Tier-1 / Tier-2 ladder. */
export interface CapitalCompositionLine {
  label: string;
  amount: NumericValue;
  isSubtotal: boolean;
  tier: 'TIER_1' | 'TIER_2';
}

export interface CapitalCompositionResponse {
  asOfDate: string;
  generatedAt: string;
  organizationId: string;
  tier1Lines: CapitalCompositionLine[];
  tier1Total: NumericValue;
  tier2Lines: CapitalCompositionLine[];
  tier2Total: NumericValue;
  totalCapital: NumericValue;
}

export interface CrarCompositionParams {
  as_of_date?: string;
}

export async function getCrarComposition(
  params?: CrarCompositionParams,
): Promise<CapitalCompositionResponse> {
  const res = await api.get<CapitalCompositionResponse>('/reports/regulatory/crar/composition', {
    params,
  });
  return res.data;
}

export interface CapitalSnapshotItem {
  snapshotDate: string;
  tier1Capital: NumericValue;
  tier2Capital: NumericValue;
  totalCapital: NumericValue;
  creditRiskRwa: NumericValue;
  marketRiskRwa: NumericValue;
  operationalRiskRwa: NumericValue;
  totalRwa: NumericValue;
  crar: NumericValue;
  tier1Ratio: NumericValue;
}

export interface CrarTrendResponse {
  organizationId: string;
  months: number;
  generatedAt: string;
  snapshots: CapitalSnapshotItem[];
}

export interface CrarTrendParams {
  months?: number;
}

export async function getCrarTrend(params?: CrarTrendParams): Promise<CrarTrendResponse> {
  const res = await api.get<CrarTrendResponse>('/reports/regulatory/crar/trend', { params });
  return res.data;
}

export type InfrastructureRatioStatus = 'QUALIFIED' | 'AT_RISK' | 'NOT_QUALIFIED';

export interface InfrastructureRatioResponse {
  asOfDate: string;
  generatedAt: string;
  organizationId: string;
  infrastructureLoansAmount: NumericValue;
  totalLoansAmount: NumericValue;
  infrastructureRatioPercent: NumericValue;
  minimumRequiredPercent: NumericValue;
  status: InfrastructureRatioStatus;
}

export interface InfrastructureRatioParams {
  as_of_date?: string;
}

export async function getInfrastructureRatio(
  params?: InfrastructureRatioParams,
): Promise<InfrastructureRatioResponse> {
  const res = await api.get<InfrastructureRatioResponse>(
    '/reports/regulatory/crar/infrastructure-ratio',
    { params },
  );
  return res.data;
}

/* ──────────────────── Sector Exposure ──────────────────── */

export interface SectorExposureItem {
  sector: string;
  exposure_amount: NumericValue;
  percentage: NumericValue;
}

export interface SectorExposureReport {
  report_type: string;
  as_of_date: string;
  generated_at: string;
  sectors: SectorExposureItem[];
  total_advances: NumericValue;
}

export interface SectorExposureParams {
  as_of_date?: string;
}

export async function getSectorExposure(
  params?: SectorExposureParams,
): Promise<SectorExposureReport> {
  const res = await api.get<SectorExposureReport>('/reports/regulatory/sector-exposure', {
    params,
  });
  return res.data;
}
