/**
 * useReceipts — list + mutation hooks for /lending/receipts.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Python internals keep
 * snake_case; frontend DTOs stay camelCase at every API boundary.
 *
 * See CLAUDE.md §5.4, §6.3 (Idempotency-Key on financial mutations),
 * §7 (error envelope).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type ReceiptStatusValue = 'PENDING' | 'ALLOCATED' | 'REVERSED' | 'BOUNCED';
export type ReceiptModeValue =
  | 'CASH'
  | 'CHEQUE'
  | 'DD'
  | 'RTGS'
  | 'NEFT'
  | 'IMPS'
  | 'UPI'
  | 'NACH'
  | 'AUTO_DEBIT'
  | 'ADJUSTMENT';
export type ReceiptTypeValue =
  | 'REGULAR'
  | 'PREPAYMENT'
  | 'FORECLOSURE'
  | 'SUBVENTION'
  | 'INSURANCE_CLAIM'
  | 'LEGAL_RECOVERY'
  | 'OTS_SETTLEMENT'
  | 'WRITE_BACK';

// Monetary fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
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
  receiptType: ReceiptTypeValue;
  receiptMode: ReceiptModeValue;
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

export const receiptsQueryKey = (filters?: ReceiptFilters) =>
  ['lending', 'receipts', filters ?? {}] as const;

async function fetchReceipts(filters?: ReceiptFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<ReceiptListItem>>(
    `/lending/receipts?${params.toString()}`,
  );
  return data;
}

export function useReceipts(filters?: ReceiptFilters) {
  return useQuery<PaginatedResponse<ReceiptListItem>>({
    queryKey: receiptsQueryKey(filters),
    queryFn: () => fetchReceipts(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export interface CreateReceiptBody {
  loanAccountId: string;
  receiptAmount: number;
  receiptDate: string;
  valueDate?: string | undefined;
  receiptType?: string | undefined;
  receiptMode: string;
  instrumentNumber?: string | undefined;
  instrumentDate?: string | undefined;
  instrumentBank?: string | undefined;
  mandateId?: string | undefined;
  receiptAccountId?: string | undefined;
  receiptSuspenseAccountId?: string | undefined;
  remarks?: string | undefined;
}

export interface CreateReceiptResponse {
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

export function useCreateReceipt() {
  const queryClient = useQueryClient();
  return useMutation<CreateReceiptResponse, unknown, CreateReceiptBody>({
    mutationFn: async (body) => {
      const { data } = await api.post<CreateReceiptResponse>('/lending/receipts/', body, {
        headers: {
          // Financial mutation — Idempotency-Key required (CLAUDE.md §6.3).
          'Idempotency-Key': crypto.randomUUID(),
        },
      });
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'receipts'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'repayment-matching'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Allocation
// ---------------------------------------------------------------------------

export type AllocationMethod = 'fifo' | 'proportional' | 'specific';

/** Per-component breakdown when method = "specific". */
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

export interface AllocateReceiptBody {
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

export function useAllocateReceipt() {
  const queryClient = useQueryClient();
  return useMutation<AllocateReceiptResponse, unknown, AllocateReceiptBody>({
    mutationFn: async (body) => {
      const { data } = await api.post<AllocateReceiptResponse>('/lending/receipts/allocate', body, {
        headers: {
          // Financial mutation (CLAUDE.md §6.3).
          'Idempotency-Key': crypto.randomUUID(),
        },
      });
      return data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'receipts'] });
      void queryClient.invalidateQueries({
        queryKey: ['lending', 'receipt', vars.receiptId],
      });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'repayment-matching'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Bulk
// ---------------------------------------------------------------------------

export interface BulkReceiptItem {
  loanAccountNumber: string;
  receiptAmount: number;
  receiptDate: string;
  receiptMode: string;
  instrumentNumber?: string | undefined;
  remarks?: string | undefined;
}

export interface BulkReceiptBody {
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

/**
 * The backend currently exposes a single POST /lending/receipts/bulk that
 * validates + creates in one call (see receipts.py:233). There is no
 * separate "validate" endpoint yet. We expose this as the import hook;
 * client-side validation should happen before invoking it.
 */
export function useImportBulkReceipts() {
  const queryClient = useQueryClient();
  return useMutation<BulkReceiptResponse, unknown, BulkReceiptBody>({
    mutationFn: async (body) => {
      const { data } = await api.post<BulkReceiptResponse>('/lending/receipts/bulk', body, {
        headers: {
          // Financial mutation (CLAUDE.md §6.3).
          'Idempotency-Key': crypto.randomUUID(),
        },
      });
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'receipts'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'repayment-matching'] });
    },
  });
}
