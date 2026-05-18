/**
 * Account Aggregator (AA) API Service
 *
 * Thin typed axios wrappers for /api/v1/lending/aa/* endpoints. Pages do not
 * call this directly — react-query hooks in
 * `src/hooks/lending/aa/*` are the only callers. See CLAUDE.md §3.3, §5.4.
 *
 * Wire format is camelCase via Pydantic CamelSchema. Mutations that trigger
 * an externally billed AA bureau call (fetch / revoke / data pull) carry an
 * `Idempotency-Key` per CLAUDE.md §6.3.
 */

import api from '../api';

import type { PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/aa';

// ============== Shared shapes ==============

export type AAConsentStatusValue =
  | 'PENDING'
  | 'APPROVED'
  | 'ACTIVE'
  | 'REJECTED'
  | 'PAUSED'
  | 'REVOKED'
  | 'EXPIRED'
  | 'FAILED';

export type AAFetchSessionStatusValue =
  | 'INITIATED'
  | 'PENDING'
  | 'READY'
  | 'COMPLETED'
  | 'PARTIAL'
  | 'FAILED'
  | 'EXPIRED';

export interface FetchSession {
  id: string;
  sessionId: string;
  status: AAFetchSessionStatusValue | string;
  fiTypesRequested: string[];
  accountsCount: number;
  transactionsCount: number;
  dataFrom: string;
  dataTo: string;
  initiatedAt: string;
  completedAt: string | null;
  errorMessage: string | null;
}

export interface ConsentLog {
  id: string;
  eventType: string;
  oldStatus: string | null;
  newStatus: string | null;
  message: string | null;
  rawPayload: Record<string, unknown>;
  createdAt: string;
  createdByName: string | null;
}

export interface ConsentDetail {
  id: string;
  organizationId: string;
  entityId: string | null;
  entityName: string | null;
  customerId: string;
  provider: string;
  consentHandle: string;
  consentId: string | null;
  status: AAConsentStatusValue | string;
  purpose: string;
  fiTypes: string[];
  consentMode: string;
  fetchType: string;
  frequencyType: string;
  frequencyValue: number;
  dateRangeFrom: string;
  dateRangeTo: string;
  consentExpiry: string;
  redirectUrl: string | null;
  createdAt: string;
  updatedAt: string;
  createdByName: string | null;
  fetchSessions: FetchSession[];
  logs: ConsentLog[];
}

// Partial consent payload as returned by check-status and revoke endpoints.
export type ConsentMutationResponse = Partial<ConsentDetail> &
  Pick<ConsentDetail, 'id' | 'status'>;

export interface BankAccount {
  id: string;
  fetchSessionId: string;
  consentId: string;
  entityId: string | null;
  entityName: string | null;
  fiType: string;
  fipId: string;
  fipName: string;
  linkRefNumber: string;
  maskedAccountNumber: string;
  accountType: string;
  ifscCode: string;
  bankName: string;
  branch: string | null;
  holderName: string;
  nominee: string | null;
  currentBalance: number;
  availableBalance: number | null;
  currency: string;
  balanceAsOn: string;
  transactionsCount: number;
  fetchedAt: string;
}

export interface FetchedBankAccountSummary {
  id: string;
  fiType: string;
  fipName: string;
  maskedAccountNumber: string;
  accountType: string;
  bankName: string;
  holderName: string;
  currentBalance: number;
  currency: string;
  transactionsCount: number;
}

export interface FetchSessionDetail {
  id: string;
  consentId: string;
  sessionId: string;
  status: AAFetchSessionStatusValue | string;
  fiTypesRequested: string[];
  accountsCount: number;
  transactionsCount: number;
  dataFrom: string;
  dataTo: string;
  initiatedAt: string;
  completedAt: string | null;
  errorMessage: string | null;
  bankAccounts: FetchedBankAccountSummary[];
}

export interface BankTransaction {
  id: string;
  txnId: string;
  txnType: string;
  mode: string;
  amount: number;
  currentBalance: number | null;
  txnDate: string;
  valueDate: string | null;
  narration: string;
  reference: string | null;
  category: string | null;
}

// ============== Create consent ==============

export interface CreateConsentRequest {
  organizationId: string;
  entityId: string | null;
  customerId: string;
  provider: string;
  purpose: string;
  fiTypes: string[];
  consentMode: string;
  fetchType: string;
  frequencyType: string;
  frequencyValue: number;
  dateRangeFrom: string;
  dateRangeTo: string;
  consentExpiry: string;
}

export interface CreateConsentResponse {
  id: string;
  consentHandle: string;
  redirectUrl: string;
  status: AAConsentStatusValue | string;
}

export async function createConsent(
  body: CreateConsentRequest,
  idempotencyKey: string,
): Promise<CreateConsentResponse> {
  const { data } = await api.post<CreateConsentResponse>(`${BASE_URL}/consents`, body, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return data;
}

// ============== Read consent ==============

export async function getConsent(consentId: string): Promise<ConsentDetail> {
  const { data } = await api.get<ConsentDetail>(`${BASE_URL}/consents/${consentId}`);
  return data;
}

// ============== Mutations on a consent ==============

export async function checkConsentStatus(
  consentId: string,
  idempotencyKey: string,
): Promise<ConsentMutationResponse> {
  const { data } = await api.post<ConsentMutationResponse>(
    `${BASE_URL}/consents/${consentId}/check-status`,
    null,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return data;
}

export interface RevokeConsentRequest {
  reason: string;
}

export async function revokeConsent(
  consentId: string,
  body: RevokeConsentRequest,
  idempotencyKey: string,
): Promise<ConsentMutationResponse> {
  const { data } = await api.post<ConsentMutationResponse>(
    `${BASE_URL}/consents/${consentId}/revoke`,
    body,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return data;
}

export interface InitiateFetchRequest {
  consentId: string;
  fiTypes: string[];
  dateFrom: string;
  dateTo: string;
}

export interface InitiateFetchResponse {
  sessionId: string;
  status: AAFetchSessionStatusValue | string;
}

export async function initiateFetch(
  consentId: string,
  body: InitiateFetchRequest,
  idempotencyKey: string,
): Promise<InitiateFetchResponse> {
  const { data } = await api.post<InitiateFetchResponse>(
    `${BASE_URL}/consents/${consentId}/fetch`,
    body,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return data;
}

// ============== Sessions ==============

export async function getFetchSession(sessionId: string): Promise<FetchSessionDetail> {
  const { data } = await api.get<FetchSessionDetail>(`${BASE_URL}/sessions/${sessionId}`);
  return data;
}

export async function fetchSessionData(
  sessionId: string,
  idempotencyKey: string,
): Promise<FetchSessionDetail> {
  const { data } = await api.post<FetchSessionDetail>(
    `${BASE_URL}/sessions/${sessionId}/fetch-data`,
    null,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return data;
}

// ============== Bank accounts / transactions ==============

export interface BankAccountFilters {
  organizationId?: string;
  entityId?: string;
  fiType?: string;
  page?: number;
  pageSize?: number;
}

export async function listBankAccounts(
  filters?: BankAccountFilters,
): Promise<PaginatedResponse<BankAccount>> {
  const params = new URLSearchParams();
  if (filters?.organizationId) params.append('organization_id', filters.organizationId);
  if (filters?.entityId) params.append('entity_id', filters.entityId);
  if (filters?.fiType) params.append('fi_type', filters.fiType);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<BankAccount>>(
    `${BASE_URL}/bank-accounts?${params.toString()}`,
  );
  return data;
}

export interface AccountTransactionFilters {
  startDate?: string;
  endDate?: string;
  txnType?: string;
  page?: number;
  pageSize?: number;
}

export async function listAccountTransactions(
  accountId: string,
  filters?: AccountTransactionFilters,
): Promise<PaginatedResponse<BankTransaction>> {
  const params = new URLSearchParams();
  if (filters?.startDate) params.append('start_date', filters.startDate);
  if (filters?.endDate) params.append('end_date', filters.endDate);
  if (filters?.txnType) params.append('txn_type', filters.txnType);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<BankTransaction>>(
    `${BASE_URL}/bank-accounts/${accountId}/transactions?${params.toString()}`,
  );
  return data;
}

// ============== Providers ==============

export interface AAProviderInfo {
  name: string;
  code: string;
  sandboxAvailable: boolean;
  fiTypesSupported: string[];
}

export interface ListProvidersResponse {
  providers: AAProviderInfo[];
  schemas?: Record<string, unknown>;
}

export async function listProviders(): Promise<ListProvidersResponse> {
  const { data } = await api.get<ListProvidersResponse>(`${BASE_URL}/providers`);
  return data;
}

export const aaApi = {
  createConsent,
  getConsent,
  checkConsentStatus,
  revokeConsent,
  initiateFetch,
  getFetchSession,
  fetchSessionData,
  listBankAccounts,
  listAccountTransactions,
  listProviders,
};

export default aaApi;
