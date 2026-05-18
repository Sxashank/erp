/**
 * Collateral API Service
 *
 * Wraps `/lending/collaterals/*` endpoints (see
 * `backend/app/api/v1/lending/collaterals.py`). Wire format is camelCase via
 * CamelSchema; query-string names stay snake_case only where FastAPI expects
 * query aliases.
 *
 * Monetary fields are sent as strings (Decimal on the wire — see
 * CLAUDE.md §6.2). Inputs accept `string | number` for ergonomics; the
 * functions stringify on the way out.
 */

import api from '../api';

const BASE_URL = '/lending/collaterals';

// ============== Shared sub-shapes ==============

export interface CollateralPropertyDetails {
  address?: string;
  areaSqft?: string;
  surveyNumber?: string;
  type?: string;
  detailedDescription?: string;
}

export interface CollateralOwnerDetails {
  name?: string;
  relationship?: string;
  isThirdParty?: boolean;
  entityId?: string;
}

export interface CollateralValuationDetails {
  declaredValue?: string;
  marketValue?: string;
  forcedSaleValue?: string;
  valuationDate?: string;
  valuerName?: string;
  valuerFirm?: string;
  reportPath?: string;
}

// ============== Create ==============

export type SecurityCategory = 'PRIMARY' | 'COLLATERAL' | 'GUARANTEE';
export type ChargeType = 'FIRST' | 'SECOND' | 'PARI_PASSU' | 'SUBSERVIENT';

export interface CreateCollateralRequest {
  sanctionId: string;
  securityCategory: SecurityCategory;
  securityType: string;
  description: string;
  acceptableValue: string;
  marginPercentage?: string;
  chargeType?: ChargeType;
  propertyDetails?: CollateralPropertyDetails;
  ownerDetails?: CollateralOwnerDetails;
  valuationDetails?: CollateralValuationDetails;
}

export interface CollateralResponse {
  id: string;
  sanctionId: string;
  securityNumber: number;
  securityCategory: string;
  securityType: string;
  description: string;
  acceptableValue: string;
  marginPercentage: string;
  netValue: string;
  status: string;
}

export async function createCollateral(
  data: CreateCollateralRequest,
  idempotencyKey: string,
): Promise<CollateralResponse> {
  const response = await api.post<CollateralResponse>(`${BASE_URL}/`, data, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return response.data;
}

// ============== Valuation update ==============

export interface UpdateValuationRequest {
  securityId: string;
  marketValue: string;
  forcedSaleValue?: string;
  acceptableValue?: string;
  valuationDate?: string;
  valuerName?: string;
  valuerFirm?: string;
  reportPath?: string;
  nextValuationDate?: string;
}

export interface UpdateValuationResponse {
  securityId: string;
  marketValue: string;
  acceptableValue: string;
  netValue: string;
  valuationDate: string | null;
  nextValuationDate: string | null;
  message: string;
}

export async function updateValuation(
  data: UpdateValuationRequest,
  idempotencyKey: string,
): Promise<UpdateValuationResponse> {
  const response = await api.put<UpdateValuationResponse>(`${BASE_URL}/valuation`, data, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return response.data;
}

// ============== List by loan ==============

export interface CollateralByLoanItem {
  id: string;
  securityNumber: number;
  securityCategory: string;
  securityType: string;
  description: string;
  acceptableValue: string;
  marginPercentage: string;
  netValue: string;
  marketValue: string | null;
  valuationDate: string | null;
  nextValuationDate: string | null;
}

export interface CollateralsByLoanResponse {
  loanAccountId: string;
  count: number;
  securities: CollateralByLoanItem[];
}

export async function getCollateralsByLoan(
  loanAccountId: string,
): Promise<CollateralsByLoanResponse> {
  const response = await api.get<CollateralsByLoanResponse>(`${BASE_URL}/loan/${loanAccountId}`);
  return response.data;
}

// ============== Coverage ==============

export interface CoverageResponse {
  sanctionId: string;
  loanAmount: string;
  totalAcceptableValue: string;
  totalNetValue: string;
  coverageRatio: string;
  isFullySecured: boolean;
}

export async function getCoverage(
  sanctionId: string,
  includeReleased = false,
): Promise<CoverageResponse> {
  const response = await api.get<CoverageResponse>(`${BASE_URL}/coverage/${sanctionId}`, {
    params: { include_released: includeReleased },
  });
  return response.data;
}

export const collateralApi = {
  createCollateral,
  updateValuation,
  getCollateralsByLoan,
  getCoverage,
};

export default collateralApi;
