/**
 * Loan Account API Service
 * API calls for Loan Account management (LMS).
 *
 * The list endpoint emits camelCase via Pydantic CamelSchema on the
 * backend (`response_model_by_alias=True`) — no client-side mapping.
 */

import api from '../api';

import type {
  LoanAccount,
  RepaymentSchedule,
  LoanAccountFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/loan-accounts';

function idempotencyHeaders(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

// ============== List item (matches LoanAccountListResponse) ==============

export type LoanAccountStatus =
  | 'CREATED'
  | 'ACTIVE'
  | 'DORMANT'
  | 'FROZEN'
  | 'CLOSED'
  | 'WRITTEN_OFF'
  | 'RECALLED';
export type AssetClassification =
  | 'STANDARD'
  | 'SMA_0'
  | 'SMA_1'
  | 'SMA_2'
  | 'NPA'
  | 'SUBSTANDARD'
  | 'SUB_STANDARD'
  | 'DOUBTFUL'
  | 'DOUBTFUL_1'
  | 'DOUBTFUL_2'
  | 'DOUBTFUL_3'
  | 'LOSS';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal
// preserves precision — CLAUDE.md §6.2). Pass them straight to
// <AmountDisplay> / <PercentageDisplay> (both accept `string`), or coerce
// once via `Number(...)` for display-only aggregations.
export interface LoanAccountListItem {
  id: string;
  loanAccountNumber: string;
  entityId: string;
  entityName: string | null;
  productId: string;
  productName: string | null;
  sanctionedAmount: string;
  totalDisbursedAmount: string;
  principalOutstanding: string;
  totalOutstanding: string;
  currentInterestRate: string;
  daysPastDue: number;
  assetClassification: AssetClassification;
  status: LoanAccountStatus;
  accountOpenDate: string;
  maturityDate: string | null;
}

export interface HistoricalLoanOnboardingResult {
  loanAccountId: string | null;
  loanAccountNumber: string | null;
  applicationId: string | null;
  sanctionId: string | null;
  scheduleId: string | null;
  importedInstallments: number;
  importedReceipts: number;
  dryRun: boolean;
  warnings: string[];
  errors: string[];
}

export interface HistoricalLoanOnboardingBatchResponse {
  dryRun: boolean;
  totalLoans: number;
  importedLoans: number;
  totalInstallments: number;
  importedReceipts: number;
  results: HistoricalLoanOnboardingResult[];
}

export interface HistoricalInstallmentPayload {
  installmentNumber: number;
  dueDate: string;
  openingBalance: string;
  principalAmount?: string;
  interestAmount?: string;
  emiAmount: string;
  closingBalance: string;
  principalPaid?: string;
  interestPaid?: string;
  penalInterestDue?: string;
  penalInterestPaid?: string;
  status?: string;
  paidDate?: string;
  receiptReference?: string;
  receiptMode?: string;
  remarks?: string;
}

export interface HistoricalLoanOnboardingPayload {
  entityId?: string;
  entityCode?: string;
  productId?: string;
  productCode?: string;
  legacyLoanNumber?: string;
  loanAccountNumber?: string;
  loanReferenceNumber?: string;
  applicationDate: string;
  sanctionDate: string;
  accountOpenDate: string;
  firstDisbursementDate?: string;
  lastDisbursementDate?: string;
  repaymentStartDate?: string;
  maturityDate?: string;
  cutoverDate: string;
  sanctionedAmount: string;
  totalDisbursedAmount: string;
  principalOutstanding: string;
  interestOutstanding?: string;
  interestOverdue?: string;
  principalOverdue?: string;
  penalInterestOutstanding?: string;
  chargesOutstanding?: string;
  totalOutstanding?: string;
  tenureMonths: number;
  moratoriumMonths?: number;
  interestType: string;
  currentInterestRate: string;
  penalInterestRate?: string;
  repaymentFrequency: string;
  repaymentMode: string;
  dayCountConvention: string;
  currentEmiAmount?: string;
  daysPastDue?: number;
  assetClassification?: string;
  npaDate?: string;
  purpose?: string;
  projectName?: string;
  remarks?: string;
  createHistoricalReceipts?: boolean;
  postHistoricalAccounting?: boolean;
  installments?: HistoricalInstallmentPayload[];
}

// ============== Loan Account CRUD ==============

export async function getLoanAccounts(
  filters?: LoanAccountFilters,
): Promise<PaginatedResponse<LoanAccountListItem>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityId) params.append('entityId', filters.entityId);
  if (filters?.productId) params.append('productId', filters.productId);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.assetClassification) {
    params.append('assetClassification', filters.assetClassification);
  }
  if (filters?.dpdFrom !== undefined) params.append('minDpd', filters.dpdFrom.toString());
  if (filters?.dpdTo !== undefined) params.append('maxDpd', filters.dpdTo.toString());
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('pageSize', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<LoanAccountListItem>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return response.data;
}

export async function getLoanAccount(accountId: string): Promise<LoanAccount> {
  const response = await api.get<LoanAccount>(`${BASE_URL}/${accountId}`);
  return response.data;
}

export async function createLoanAccount(sanctionId: string): Promise<LoanAccount> {
  const response = await api.post<LoanAccount>(BASE_URL, { sanctionId });
  return response.data;
}

export async function updateLoanAccount(
  accountId: string,
  data: Partial<LoanAccount>,
): Promise<LoanAccount> {
  const response = await api.put<LoanAccount>(`${BASE_URL}/${accountId}`, data);
  return response.data;
}

export async function downloadHistoricalLoanTemplate(): Promise<Blob> {
  const response = await api.get<Blob>(`${BASE_URL}/historical-onboarding/template.csv`, {
    responseType: 'blob',
  });
  return response.data;
}

export async function importHistoricalLoans(
  file: File,
  dryRun = true,
): Promise<HistoricalLoanOnboardingBatchResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<HistoricalLoanOnboardingBatchResponse>(
    `${BASE_URL}/historical-onboarding/import?dryRun=${dryRun ? 'true' : 'false'}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...idempotencyHeaders(),
      },
    },
  );
  return response.data;
}

export async function onboardHistoricalLoan(
  payload: HistoricalLoanOnboardingPayload,
  dryRun = true,
): Promise<HistoricalLoanOnboardingResult> {
  const response = await api.post<HistoricalLoanOnboardingResult>(
    `${BASE_URL}/historical-onboarding?dryRun=${dryRun ? 'true' : 'false'}`,
    payload,
    { headers: idempotencyHeaders() },
  );
  return response.data;
}

// ============== Repayment Schedule ==============

export async function getRepaymentSchedule(accountId: string): Promise<RepaymentSchedule[]> {
  const response = await api.get<RepaymentSchedule[]>(`${BASE_URL}/${accountId}/schedule`);
  return response.data;
}

export async function regenerateSchedule(
  accountId: string,
  data?: { effective_date?: string; reason?: string },
): Promise<RepaymentSchedule[]> {
  const response = await api.post<RepaymentSchedule[]>(
    `${BASE_URL}/${accountId}/schedule/regenerate`,
    data,
  );
  return response.data;
}

export async function updateScheduleEntry(
  accountId: string,
  scheduleId: string,
  data: Partial<RepaymentSchedule>,
): Promise<RepaymentSchedule> {
  const response = await api.put<RepaymentSchedule>(
    `${BASE_URL}/${accountId}/schedule/${scheduleId}`,
    data,
  );
  return response.data;
}

// ============== Rate Reset ==============

export async function processRateReset(
  accountId: string,
  data: { new_rate: number; effective_date: string; remarks?: string },
): Promise<LoanAccount> {
  const response = await api.post<LoanAccount>(`${BASE_URL}/${accountId}/rate-reset`, data);
  return response.data;
}

export async function getRateResetHistory(accountId: string): Promise<
  {
    reset_id: string;
    old_rate: number;
    new_rate: number;
    effective_date: string;
    created_at: string;
  }[]
> {
  const response = await api.get(`${BASE_URL}/${accountId}/rate-reset/history`);
  return response.data;
}

// ============== Balance & Position ==============

export async function getLoanBalance(
  accountId: string,
  asOfDate?: string,
): Promise<{
  principal_outstanding: number;
  interest_outstanding: number;
  penal_outstanding: number;
  charges_outstanding: number;
  total_outstanding: number;
  as_of_date: string;
}> {
  const params = asOfDate ? `?as_of_date=${asOfDate}` : '';
  const response = await api.get(`${BASE_URL}/${accountId}/balance${params}`);
  return response.data;
}

export async function getLoanSummary(accountId: string): Promise<{
  sanctioned_amount: number;
  disbursed_amount: number;
  principal_repaid: number;
  interest_paid: number;
  total_outstanding: number;
  next_due_date: string;
  next_due_amount: number;
  overdue_amount: number;
  dpd: number;
}> {
  const response = await api.get(`${BASE_URL}/${accountId}/summary`);
  return response.data;
}

// ============== Interest Accrual ==============

export async function runAccrual(
  accountId: string,
  data?: { accrual_date?: string },
): Promise<{
  accrual_id: string;
  accrued_amount: number;
  accrual_date: string;
}> {
  const response = await api.post(`${BASE_URL}/${accountId}/accrual`, data);
  return response.data;
}

export async function getAccrualHistory(accountId: string): Promise<
  {
    accrual_id: string;
    accrual_date: string;
    principal_balance: number;
    days: number;
    rate: number;
    accrued_amount: number;
  }[]
> {
  const response = await api.get(`${BASE_URL}/${accountId}/accrual/history`);
  return response.data;
}

// ============== Demands ==============

export async function generateDemand(accountId: string): Promise<{
  demand_id: string;
  due_date: string;
  principal_demand: number;
  interest_demand: number;
  total_demand: number;
}> {
  const response = await api.post(`${BASE_URL}/${accountId}/demand/generate`);
  return response.data;
}

export async function getDemandHistory(accountId: string): Promise<
  {
    demand_id: string;
    due_date: string;
    principal_demand: number;
    interest_demand: number;
    total_demand: number;
    paid_amount: number;
    status: string;
  }[]
> {
  const response = await api.get(`${BASE_URL}/${accountId}/demand/history`);
  return response.data;
}

// ============== Statement of Account ==============

export async function getStatementOfAccount(
  accountId: string,
  dateFrom: string,
  dateTo: string,
): Promise<{
  account_details: LoanAccount;
  opening_balance: number;
  transactions: {
    date: string;
    particulars: string;
    debit: number;
    credit: number;
    balance: number;
  }[];
  closing_balance: number;
}> {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  const response = await api.get(`${BASE_URL}/${accountId}/statement?${params.toString()}`);
  return response.data;
}

export async function downloadStatement(
  accountId: string,
  dateFrom: string,
  dateTo: string,
  format: 'pdf' | 'excel' = 'pdf',
): Promise<Blob> {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo, format });
  const response = await api.get<Blob>(
    `${BASE_URL}/${accountId}/statement/download?${params.toString()}`,
    {
      responseType: 'blob',
    },
  );
  return response.data;
}

// ============== Closure ==============

export async function getClosureQuote(
  accountId: string,
  closureDate?: string,
): Promise<{
  principal_outstanding: number;
  interest_till_date: number;
  penal_outstanding: number;
  charges: number;
  prepayment_penalty: number;
  total_closure_amount: number;
  valid_till: string;
}> {
  const params = closureDate ? `?closure_date=${closureDate}` : '';
  const response = await api.get(`${BASE_URL}/${accountId}/closure/quote${params}`);
  return response.data;
}

export async function initiateClosure(
  accountId: string,
  data: { closure_type: 'REGULAR' | 'FORECLOSURE'; remarks?: string },
): Promise<{ closure_request_id: string }> {
  const response = await api.post(`${BASE_URL}/${accountId}/closure/initiate`, data);
  return response.data;
}

// ============== Export all functions ==============

export const loanAccountApi = {
  // CRUD
  getLoanAccounts,
  getLoanAccount,
  createLoanAccount,
  updateLoanAccount,
  downloadHistoricalLoanTemplate,
  importHistoricalLoans,
  onboardHistoricalLoan,

  // Schedule
  getRepaymentSchedule,
  regenerateSchedule,
  updateScheduleEntry,

  // Rate Reset
  processRateReset,
  getRateResetHistory,

  // Balance
  getLoanBalance,
  getLoanSummary,

  // Accrual
  runAccrual,
  getAccrualHistory,

  // Demands
  generateDemand,
  getDemandHistory,

  // Statement
  getStatementOfAccount,
  downloadStatement,

  // Closure
  getClosureQuote,
  initiateClosure,
};

export default loanAccountApi;
