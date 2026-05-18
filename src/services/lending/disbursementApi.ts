/**
 * Disbursement API Service
 *
 * The list endpoint emits camelCase via Pydantic CamelSchema on the
 * backend (`response_model_by_alias=True`) — no client-side mapping.
 *
 * Monetary fields are JSON strings on the wire (Pydantic Decimal —
 * CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
 *
 * Mutation endpoints require an `Idempotency-Key` header (CLAUDE.md §6.3 —
 * the BE idempotency middleware lists `lending/disbursements` as a financial
 * mutation resource).
 */

import api from '../api';

import type { DisbursementFilters, PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/disbursements';

// ============== List item (matches DisbursementListResponse) ==============

export type DisbursementStatusValue =
  | 'PENDING'
  | 'APPROVED'
  | 'PROCESSED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'FAILED'
  | 'REVERSED';

export interface DisbursementListItem {
  id: string;
  disbursementReference: string;
  disbursementNumber: number;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  requestedAmount: string;
  approvedAmount: string | null;
  disbursedAmount: string | null;
  requestDate: string;
  disbursementDate: string | null;
  status: DisbursementStatusValue;
  beneficiaryName: string;
  utrNumber: string | null;
}

// ============== Mutation request / response shapes ==============

/**
 * Body for `POST /lending/disbursements/` — matches the BE
 * `DisbursementCreateRequest` Pydantic model.
 *
 * Decimal fields are sent as strings (CLAUDE.md §6.2).
 */
export interface DisbursementCreateBody {
  loanAccountId: string;
  requestedAmount: string;
  beneficiaryName: string;
  beneficiaryAccountNumber: string;
  beneficiaryIfsc: string;
  disbursementMode: string;
  scheduledDate?: string;
  purpose?: string;
  beneficiaryBank?: string;
  bankAccountId?: string;
  milestoneId?: string;
}

/** Matches BE `DisbursementResponse`. */
export interface DisbursementCreateResponse {
  id: string;
  disbursementReference: string;
  loanAccountId: string;
  disbursementNumber: number;
  requestedAmount: string;
  approvedAmount: string | null;
  disbursedAmount: string | null;
  status: string;
  disbursementMode: string;
  beneficiaryName: string;
  requestDate: string;
  scheduledDate: string | null;
  disbursementDate: string | null;
  conditionsVerified: boolean;
}

/** Body for `POST /lending/disbursements/approve`. */
export interface ApprovalBody {
  disbursementId: string;
  approvedAmount?: string;
  remarks?: string;
}

/** Body for `POST /lending/disbursements/verify-conditions`. */
export interface VerifyConditionsBody {
  disbursementId: string;
  verificationNotes?: string;
}

export interface VerifyConditionsResponse {
  disbursementId: string;
  conditionsVerified: boolean;
  verifiedAt: string | null;
  message: string;
}

/** Body for `POST /lending/disbursements/reject`. */
export interface RejectBody {
  disbursementId: string;
  rejectionReason: string;
}

/** Body for `POST /lending/disbursements/process`. */
export interface ProcessBody {
  disbursementId: string;
  disbursedAmount: string;
  sourceAccountId?: string;
  disbursementDate?: string;
  valueDate?: string;
  utrNumber?: string;
  chequeNumber?: string;
  disbursementCharges?: string;
}

/**
 * Shape of the generic action ack envelope used by approve / reject /
 * process / cancel / reverse. Extra fields beyond `disbursementId` and
 * `status` vary by action — keep this loose.
 */
export interface DisbursementActionResponse {
  disbursementId: string;
  status: string;
  message: string;
  approvedAmount?: string | null;
  approvalDate?: string | null;
  disbursedAmount?: string | null;
  netDisbursement?: string | null;
  utrNumber?: string | null;
  loanAccount?: {
    id: string;
    totalDisbursed: string;
    undisbursed?: string;
    principalOutstanding: string;
    status: string;
  };
}

// ============== Real BE endpoints ==============

/**
 * Build an `Idempotency-Key` header. The BE idempotency middleware
 * requires it on every POST to `/lending/disbursements/*` (CLAUDE.md §6.3).
 */
function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

/**
 * `POST /lending/disbursements/` — create a new disbursement request.
 * Maps to `DisbursementService.create_disbursement_request`.
 */
export async function createDisbursement(
  body: DisbursementCreateBody,
): Promise<DisbursementCreateResponse> {
  const response = await api.post<DisbursementCreateResponse>(`${BASE_URL}/`, body, {
    headers: idempotencyHeaders(),
  });
  return response.data;
}

/**
 * `POST /lending/disbursements/approve` — approve a disbursement request.
 * Maps to `DisbursementService.approve_disbursement`.
 */
export async function approveDisbursementRequest(
  body: ApprovalBody,
): Promise<DisbursementActionResponse> {
  const response = await api.post<DisbursementActionResponse>(`${BASE_URL}/approve`, body, {
    headers: idempotencyHeaders(),
  });
  return response.data;
}

/**
 * `POST /lending/disbursements/verify-conditions` — record manual
 * verification of pre-disbursement conditions before approval.
 */
export async function verifyDisbursementConditions(
  body: VerifyConditionsBody,
): Promise<VerifyConditionsResponse> {
  const response = await api.post<VerifyConditionsResponse>(`${BASE_URL}/verify-conditions`, body, {
    headers: idempotencyHeaders(),
  });
  return response.data;
}

/**
 * `POST /lending/disbursements/reject` — reject a disbursement request.
 * Maps to `DisbursementService.reject_disbursement`.
 */
export async function rejectDisbursementRequest(
  body: RejectBody,
): Promise<DisbursementActionResponse> {
  const response = await api.post<DisbursementActionResponse>(`${BASE_URL}/reject`, body, {
    headers: idempotencyHeaders(),
  });
  return response.data;
}

/**
 * `POST /lending/disbursements/process` — release funds for an approved
 * disbursement. Maps to `DisbursementService.process_disbursement`.
 */
export async function processDisbursementRequest(
  body: ProcessBody,
): Promise<DisbursementActionResponse> {
  const response = await api.post<DisbursementActionResponse>(`${BASE_URL}/process`, body, {
    headers: idempotencyHeaders(),
  });
  return response.data;
}

// ============== Disbursement Request Queries ==============

export async function getDisbursements(
  filters?: DisbursementFilters,
): Promise<PaginatedResponse<DisbursementListItem>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('page_size', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<DisbursementListItem>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return response.data;
}

// ============== Export all functions ==============

export const disbursementApi = {
  // Real BE endpoints (use these)
  createDisbursement,
  verifyDisbursementConditions,
  approveDisbursementRequest,
  rejectDisbursementRequest,
  processDisbursementRequest,

  // CRUD
  getDisbursements,
};

export default disbursementApi;
