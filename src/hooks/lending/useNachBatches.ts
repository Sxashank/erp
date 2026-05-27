/**
 * useNachBatches — list + mutation hooks for /lending/nach/batches.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * Mutations send `Idempotency-Key` per
 * CLAUDE.md §6.3 (NACH batch initiates auto-debits = financial mutation).
 *
 * See CLAUDE.md §5.4, §6.3, §7.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '@/services/api';
import {
  createRetryBatch,
  generateNachBatch,
  type CreateRetryBatchRequest,
  type GenerateNachBatchRequest,
  type GenerateNachBatchResponse,
} from '@/services/lending/nachApi';
import type { PaginatedResponse } from '@/types/lending';

export type NachBatchStatusValue =
  | 'CREATED'
  | 'VALIDATED'
  | 'FILE_GENERATED'
  | 'SUBMITTED'
  | 'PROCESSING'
  | 'RESPONSE_RECEIVED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface NachBatchListItem {
  id: string;
  batchReference: string;
  batchDate: string;
  debitDate: string;
  integrationConfigId: string | null;
  totalTransactions: number;
  // Monetary fields are JSON strings on the wire (Pydantic Decimal — CLAUDE.md §6.2).
  totalAmount: string;
  successCount: number;
  failureCount: number;
  pendingCount: number;
  fileName: string | null;
  fileGeneratedAt: string | null;
  submittedAt: string | null;
  responseReceivedAt: string | null;
  status: NachBatchStatusValue;
  createdAt: string;
}

export interface NachBatchFilters {
  status?: NachBatchStatusValue;
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
}

export const nachBatchesQueryKey = (filters?: NachBatchFilters) =>
  ['lending', 'nach', 'batches', filters ?? {}] as const;

async function fetchNachBatches(filters?: NachBatchFilters) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.startDate) params.append('startDate', filters.startDate);
  if (filters?.endDate) params.append('endDate', filters.endDate);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<NachBatchListItem>>(
    `/lending/nach/batches?${params.toString()}`,
  );
  return data;
}

export function useNachBatches(filters?: NachBatchFilters) {
  return useQuery<PaginatedResponse<NachBatchListItem>>({
    queryKey: nachBatchesQueryKey(filters),
    queryFn: () => fetchNachBatches(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/**
 * Shape of an error envelope returned by the FastAPI app
 * (CLAUDE.md §7). Currently the NACH endpoints raise `HTTPException`, so
 * `detail` may be a plain string; the `AppException` hierarchy produces the
 * full envelope. We accept either and surface a single human message.
 */
interface ApiErrorEnvelope {
  error_code?: string;
  message?: string;
  detail?: string;
  correlation_id?: string;
}

interface AxiosLikeError {
  response?: { data?: ApiErrorEnvelope | string };
  message?: string;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  const e = err as AxiosLikeError;
  const data = e?.response?.data;
  if (typeof data === 'string') return data;
  if (data && typeof data === 'object') {
    if (typeof data.message === 'string' && data.message) return data.message;
    if (typeof data.detail === 'string' && data.detail) return data.detail;
  }
  if (typeof e?.message === 'string' && e.message) return e.message;
  return fallback;
}

/**
 * useCreateNachBatch — POST /lending/nach/batches/generate.
 *
 * Generates a NACH batch from due EMIs. NACH batches initiate auto-debits
 * against borrower accounts, so this is a financial mutation: an
 * `Idempotency-Key` is sent per request (CLAUDE.md §6.3) and both the
 * batches list and the retry-due list are invalidated on success.
 */
export function useCreateNachBatch() {
  const queryClient = useQueryClient();
  return useMutation<GenerateNachBatchResponse, unknown, GenerateNachBatchRequest>({
    mutationFn: async (body) => {
      const idempotencyKey = crypto.randomUUID();
      return generateNachBatch(body, idempotencyKey);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'nach', 'batches'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'nach', 'retry-due'] });
    },
  });
}

/**
 * useCreateNachRetryBatch — POST /lending/nach/retry-batch.
 *
 * Creates a NACH batch by re-presenting selected bounced transactions on a
 * new debit date. Re-presents are auto-debits against borrower accounts, so
 * this is a financial mutation: an `Idempotency-Key` is sent per request
 * (CLAUDE.md §6.3) and both the batches list and the retry-due list are
 * invalidated on success.
 */
export function useCreateNachRetryBatch() {
  const queryClient = useQueryClient();
  return useMutation<GenerateNachBatchResponse, unknown, CreateRetryBatchRequest>({
    mutationFn: async (body) => {
      const idempotencyKey = crypto.randomUUID();
      return createRetryBatch(body, idempotencyKey);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'nach', 'batches'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'nach', 'retry-due'] });
    },
  });
}

export { extractErrorMessage as extractNachErrorMessage };
