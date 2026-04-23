/**
 * Loan Account API Service
 * API calls for Loan Account management (LMS)
 */

import api from '../api';
import type {
  LoanAccount,
  RepaymentSchedule,
  LoanAccountFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/accounts';

// ============== Loan Account CRUD ==============

export async function getLoanAccounts(filters?: LoanAccountFilters): Promise<PaginatedResponse<LoanAccount>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.product_id) params.append('product_id', filters.product_id);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.asset_classification) params.append('asset_classification', filters.asset_classification);
  if (filters?.branch_id) params.append('branch_id', filters.branch_id);
  if (filters?.dpd_from !== undefined) params.append('dpd_from', filters.dpd_from.toString());
  if (filters?.dpd_to !== undefined) params.append('dpd_to', filters.dpd_to.toString());
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<LoanAccount>>(`${BASE_URL}?${params.toString()}`);
  return response.data;
}

export async function getLoanAccount(accountId: string): Promise<LoanAccount> {
  const response = await api.get<LoanAccount>(`${BASE_URL}/${accountId}`);
  return response.data;
}

export async function createLoanAccount(sanctionId: string): Promise<LoanAccount> {
  const response = await api.post<LoanAccount>(BASE_URL, { sanction_id: sanctionId });
  return response.data;
}

export async function updateLoanAccount(accountId: string, data: Partial<LoanAccount>): Promise<LoanAccount> {
  const response = await api.put<LoanAccount>(`${BASE_URL}/${accountId}`, data);
  return response.data;
}

// ============== Repayment Schedule ==============

export async function getRepaymentSchedule(accountId: string): Promise<RepaymentSchedule[]> {
  const response = await api.get<RepaymentSchedule[]>(`${BASE_URL}/${accountId}/schedule`);
  return response.data;
}

export async function regenerateSchedule(
  accountId: string,
  data?: { effective_date?: string; reason?: string }
): Promise<RepaymentSchedule[]> {
  const response = await api.post<RepaymentSchedule[]>(`${BASE_URL}/${accountId}/schedule/regenerate`, data);
  return response.data;
}

export async function updateScheduleEntry(
  accountId: string,
  scheduleId: string,
  data: Partial<RepaymentSchedule>
): Promise<RepaymentSchedule> {
  const response = await api.put<RepaymentSchedule>(
    `${BASE_URL}/${accountId}/schedule/${scheduleId}`,
    data
  );
  return response.data;
}

// ============== Rate Reset ==============

export async function processRateReset(
  accountId: string,
  data: { new_rate: number; effective_date: string; remarks?: string }
): Promise<LoanAccount> {
  const response = await api.post<LoanAccount>(`${BASE_URL}/${accountId}/rate-reset`, data);
  return response.data;
}

export async function getRateResetHistory(accountId: string): Promise<Array<{
  reset_id: string;
  old_rate: number;
  new_rate: number;
  effective_date: string;
  created_at: string;
}>> {
  const response = await api.get(`${BASE_URL}/${accountId}/rate-reset/history`);
  return response.data;
}

// ============== Balance & Position ==============

export async function getLoanBalance(accountId: string, asOfDate?: string): Promise<{
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

export async function runAccrual(accountId: string, data?: { accrual_date?: string }): Promise<{
  accrual_id: string;
  accrued_amount: number;
  accrual_date: string;
}> {
  const response = await api.post(`${BASE_URL}/${accountId}/accrual`, data);
  return response.data;
}

export async function getAccrualHistory(accountId: string): Promise<Array<{
  accrual_id: string;
  accrual_date: string;
  principal_balance: number;
  days: number;
  rate: number;
  accrued_amount: number;
}>> {
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

export async function getDemandHistory(accountId: string): Promise<Array<{
  demand_id: string;
  due_date: string;
  principal_demand: number;
  interest_demand: number;
  total_demand: number;
  paid_amount: number;
  status: string;
}>> {
  const response = await api.get(`${BASE_URL}/${accountId}/demand/history`);
  return response.data;
}

// ============== Statement of Account ==============

export async function getStatementOfAccount(
  accountId: string,
  dateFrom: string,
  dateTo: string
): Promise<{
  account_details: LoanAccount;
  opening_balance: number;
  transactions: Array<{
    date: string;
    particulars: string;
    debit: number;
    credit: number;
    balance: number;
  }>;
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
  format: 'pdf' | 'excel' = 'pdf'
): Promise<Blob> {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo, format });
  const response = await api.get<Blob>(`${BASE_URL}/${accountId}/statement/download?${params.toString()}`, {
    responseType: 'blob',
  });
  return response.data;
}

// ============== Closure ==============

export async function getClosureQuote(accountId: string, closureDate?: string): Promise<{
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
  data: { closure_type: 'REGULAR' | 'FORECLOSURE'; remarks?: string }
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
