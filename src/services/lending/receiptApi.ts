/**
 * Receipt API Service
 * API calls for Receipt/Collection management
 */

import api from '../api';
import type {
  Receipt,
  ReceiptFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/receipts';

// ============== Receipt CRUD ==============

export async function getReceipts(filters?: ReceiptFilters): Promise<PaginatedResponse<Receipt>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.loan_account_id) params.append('loan_account_id', filters.loan_account_id);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.receipt_mode) params.append('receipt_mode', filters.receipt_mode);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<Receipt>>(`${BASE_URL}?${params.toString()}`);
  return response.data;
}

export async function getReceipt(receiptId: string): Promise<Receipt> {
  const response = await api.get<Receipt>(`${BASE_URL}/${receiptId}`);
  return response.data;
}

export interface CreateReceiptRequest {
  loan_account_id: string;
  receipt_date: string;
  amount: number;
  receipt_mode: 'CASH' | 'CHEQUE' | 'NEFT' | 'RTGS' | 'UPI' | 'AUTO_DEBIT' | 'OTHER';
  reference_number?: string;
  instrument_number?: string;
  instrument_date?: string;
  bank_name?: string;
  remarks?: string;
}

export async function createReceipt(data: CreateReceiptRequest): Promise<Receipt> {
  const response = await api.post<Receipt>(BASE_URL, data);
  return response.data;
}

export async function updateReceipt(receiptId: string, data: Partial<CreateReceiptRequest>): Promise<Receipt> {
  const response = await api.put<Receipt>(`${BASE_URL}/${receiptId}`, data);
  return response.data;
}

export async function deleteReceipt(receiptId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${receiptId}`);
}

// ============== Receipt Allocation ==============

export interface AllocationBreakdown {
  component: 'PENAL_INTEREST' | 'CHARGES' | 'OVERDUE_INTEREST' | 'CURRENT_INTEREST' | 'OVERDUE_PRINCIPAL' | 'CURRENT_PRINCIPAL' | 'PREPAYMENT' | 'ON_ACCOUNT';
  demand_id?: string;
  amount: number;
  remarks?: string;
}

export async function getProposedAllocation(
  loanAccountId: string,
  amount: number
): Promise<{
  total_amount: number;
  allocations: AllocationBreakdown[];
  unallocated: number;
}> {
  const params = new URLSearchParams({ amount: amount.toString() });
  const response = await api.get(`${BASE_URL}/allocation/propose/${loanAccountId}?${params.toString()}`);
  return response.data;
}

export async function allocateReceipt(
  receiptId: string,
  allocations?: AllocationBreakdown[]
): Promise<Receipt> {
  const response = await api.post<Receipt>(`${BASE_URL}/${receiptId}/allocate`, { allocations });
  return response.data;
}

export async function getAllocationDetails(receiptId: string): Promise<{
  receipt: Receipt;
  allocations: Array<{
    allocation_id: string;
    component: string;
    demand_id?: string;
    due_date?: string;
    allocated_amount: number;
    created_at: string;
  }>;
}> {
  const response = await api.get(`${BASE_URL}/${receiptId}/allocation`);
  return response.data;
}

// ============== Receipt Reversal ==============

export async function reverseReceipt(
  receiptId: string,
  data: { reason: string; reversal_date?: string }
): Promise<Receipt> {
  const response = await api.post<Receipt>(`${BASE_URL}/${receiptId}/reverse`, data);
  return response.data;
}

export async function getReversalHistory(receiptId: string): Promise<Array<{
  reversal_id: string;
  original_receipt_id: string;
  reversal_date: string;
  reason: string;
  reversed_by: string;
  created_at: string;
}>> {
  const response = await api.get(`${BASE_URL}/${receiptId}/reversal/history`);
  return response.data;
}

// ============== Cheque Management ==============

export async function recordChequeDeposit(
  receiptId: string,
  data: { deposit_date: string; bank_account_id: string }
): Promise<Receipt> {
  const response = await api.post<Receipt>(`${BASE_URL}/${receiptId}/cheque/deposit`, data);
  return response.data;
}

export async function recordChequeRealization(
  receiptId: string,
  data: { realization_date: string }
): Promise<Receipt> {
  const response = await api.post<Receipt>(`${BASE_URL}/${receiptId}/cheque/realize`, data);
  return response.data;
}

export async function recordChequeBounce(
  receiptId: string,
  data: { bounce_date: string; bounce_reason: string; bounce_charges?: number }
): Promise<Receipt> {
  const response = await api.post<Receipt>(`${BASE_URL}/${receiptId}/cheque/bounce`, data);
  return response.data;
}

export async function getPendingCheques(): Promise<Array<{
  receipt_id: string;
  loan_account_number: string;
  entity_name: string;
  amount: number;
  instrument_number: string;
  instrument_date: string;
  deposit_date?: string;
  days_pending: number;
}>> {
  const response = await api.get(`${BASE_URL}/cheques/pending`);
  return response.data;
}

// ============== Bulk Receipts ==============

export async function uploadBulkReceipts(formData: FormData): Promise<{
  total_records: number;
  successful: number;
  failed: number;
  errors: Array<{ row: number; error: string }>;
}> {
  const response = await api.post(`${BASE_URL}/bulk/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function downloadReceiptTemplate(): Promise<Blob> {
  const response = await api.get<Blob>(`${BASE_URL}/bulk/template`, {
    responseType: 'blob',
  });
  return response.data;
}

// ============== Receipt Reports ==============

export async function getReceiptsByAccount(loanAccountId: string): Promise<Receipt[]> {
  const response = await api.get<Receipt[]>(`${BASE_URL}/account/${loanAccountId}`);
  return response.data;
}

export async function getDailyCollection(date: string): Promise<{
  date: string;
  total_collection: number;
  receipt_count: number;
  by_mode: Array<{ mode: string; amount: number; count: number }>;
  by_branch: Array<{ branch: string; amount: number; count: number }>;
}> {
  const response = await api.get(`${BASE_URL}/reports/daily?date=${date}`);
  return response.data;
}

export async function getCollectionEfficiency(
  month: number,
  year: number
): Promise<{
  month: number;
  year: number;
  total_demand: number;
  total_collection: number;
  efficiency_percent: number;
  by_product: Array<{ product: string; demand: number; collection: number; efficiency: number }>;
}> {
  const response = await api.get(`${BASE_URL}/reports/efficiency?month=${month}&year=${year}`);
  return response.data;
}

// ============== Export all functions ==============

export const receiptApi = {
  // CRUD
  getReceipts,
  getReceipt,
  createReceipt,
  updateReceipt,
  deleteReceipt,

  // Allocation
  getProposedAllocation,
  allocateReceipt,
  getAllocationDetails,

  // Reversal
  reverseReceipt,
  getReversalHistory,

  // Cheque
  recordChequeDeposit,
  recordChequeRealization,
  recordChequeBounce,
  getPendingCheques,

  // Bulk
  uploadBulkReceipts,
  downloadReceiptTemplate,

  // Reports
  getReceiptsByAccount,
  getDailyCollection,
  getCollectionEfficiency,
};

export default receiptApi;
