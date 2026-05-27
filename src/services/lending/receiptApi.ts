import api from '../api';

import type { PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/receipts';

export type ReceiptStatusValue = 'PENDING' | 'ALLOCATED' | 'REVERSED' | 'BOUNCED';

export interface ReceiptListItem {
  id: string;
  receiptNumber: string;
  loanAccountId: string;
  loanAccountNumber: string | null;
  entityId: string | null;
  entityName: string | null;
  receiptDate: string;
  valueDate: string;
  receiptAmount: string;
  allocatedAmount: string;
  unallocatedAmount: string;
  receiptType: string;
  receiptMode: string;
  instrumentNumber: string | null;
  status: ReceiptStatusValue;
  bounced: boolean;
}

export interface ReceiptFilters {
  search?: string;
  status?: ReceiptStatusValue;
  page?: number;
  pageSize?: number;
}

export interface CreateReceiptRequest {
  loanAccountId: string;
  receiptAmount: number;
  receiptDate: string;
  valueDate?: string;
  receiptType?: string;
  receiptMode: string;
  instrumentNumber?: string;
  instrumentDate?: string;
  instrumentBank?: string;
  mandateId?: string;
  receiptAccountId?: string;
  receiptSuspenseAccountId?: string;
  remarks?: string;
}

export interface ReceiptResponse {
  id: string;
  receiptNumber: string;
  loanAccountId: string;
  receiptAmount: string;
  receiptDate: string;
  valueDate: string;
  receiptType: string;
  receiptMode: string;
  status: string;
  allocatedAmount: string;
  unallocatedAmount: string;
  principalAllocated: string;
  interestAllocated: string;
  penalInterestAllocated: string;
  chargesAllocated: string;
}

export type AllocationMethod = 'fifo' | 'proportional' | 'specific';

export interface SpecificAllocation {
  installmentId?: string;
  scheduleId?: string;
  component:
    | 'PENAL_INTEREST'
    | 'CHARGES'
    | 'OVERDUE_INTEREST'
    | 'CURRENT_INTEREST'
    | 'OVERDUE_PRINCIPAL'
    | 'CURRENT_PRINCIPAL'
    | 'PREPAYMENT'
    | 'ON_ACCOUNT';
  amount: number;
}

export interface AllocateReceiptRequest {
  receiptId: string;
  allocationMethod?: AllocationMethod;
  specificAllocations?: SpecificAllocation[];
}

export interface AllocateReceiptResponse {
  receiptId: string;
  allocationCount: number;
  allocations: {
    id: string;
    receiptId: string;
    installmentId: string | null;
    component: string;
    amount: string;
    sequence: number;
  }[];
}

export interface ReverseReceiptRequest {
  receiptId: string;
  reversalReason: string;
  reversalDate?: string;
}

export interface ReverseReceiptResponse {
  receiptId: string;
  receiptNumber: string;
  status: string;
  message: string;
}

export interface BulkReceiptItem {
  loanAccountNumber: string;
  receiptAmount: number;
  receiptDate: string;
  receiptMode: string;
  instrumentNumber?: string;
  remarks?: string;
}

export interface BulkReceiptRequest {
  receipts: BulkReceiptItem[];
  autoAllocate?: boolean;
}

export interface BulkReceiptResponse {
  totalCount: number;
  successCount: number;
  failedCount: number;
  totalAmount: string;
  failures: { row?: number; loanAccountNumber?: string; error?: string }[];
}

function buildReceiptParams(filters?: ReceiptFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('pageSize', filters.pageSize.toString());
  return params;
}

export async function getReceipts(
  filters?: ReceiptFilters,
): Promise<PaginatedResponse<ReceiptListItem>> {
  const params = buildReceiptParams(filters);
  const response = await api.get<PaginatedResponse<ReceiptListItem>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return response.data;
}

export async function getReceipt(receiptId: string): Promise<ReceiptResponse> {
  const response = await api.get<ReceiptResponse>(`${BASE_URL}/${receiptId}`);
  return response.data;
}

export async function createReceipt(data: CreateReceiptRequest): Promise<ReceiptResponse> {
  const response = await api.post<ReceiptResponse>(BASE_URL, data);
  return response.data;
}

export async function allocateReceipt(
  data: AllocateReceiptRequest,
): Promise<AllocateReceiptResponse> {
  const response = await api.post<AllocateReceiptResponse>(`${BASE_URL}/allocate`, data);
  return response.data;
}

export async function reverseReceipt(data: ReverseReceiptRequest): Promise<ReverseReceiptResponse> {
  const response = await api.post<ReverseReceiptResponse>(`${BASE_URL}/reverse`, data);
  return response.data;
}

export async function importBulkReceipts(data: BulkReceiptRequest): Promise<BulkReceiptResponse> {
  const response = await api.post<BulkReceiptResponse>(`${BASE_URL}/bulk`, data);
  return response.data;
}

export const receiptApi = {
  getReceipts,
  getReceipt,
  createReceipt,
  allocateReceipt,
  reverseReceipt,
  importBulkReceipts,
};

export default receiptApi;
