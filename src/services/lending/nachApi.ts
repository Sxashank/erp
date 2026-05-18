/**
 * NACH API Service
 *
 * Thin typed axios wrappers for NACH batch / transaction endpoints exposed
 * under /api/v1/lending/nach/*. Pages do not call this directly — react-query
 * hooks in `src/hooks/lending/useNachBatches.ts` / `useNachRetryDue.ts` are
 * the only callers. See CLAUDE.md §3.3, §5.4.
 *
 * Read and write paths use camelCase via Pydantic CamelSchema. Query-string
 * names are translated only at the hook/service boundary.
 * Monetary fields cross the wire as Decimal-as-string per CLAUDE.md §6.2.
 */

import api from '../api';

const BASE_URL = '/lending/nach';

// ============== Batch — generate from due EMIs ==============

/**
 * Body for POST /lending/nach/batches/generate. Field names mirror the
 * backend `NachBatchGenerateRequest` (camelCase). `organizationId` and
 * `debitDate` are required; everything else is optional.
 */
export interface GenerateNachBatchRequest {
  organizationId: string;
  debitDate: string; // ISO yyyy-MM-dd
  integrationConfigId?: string | undefined;
  includeOverdue?: boolean | undefined;
  maxDpd?: number | undefined;
  loanAccountIds?: string[] | undefined;
  productIds?: string[] | undefined;
}

/**
 * Shape of POST /lending/nach/batches/generate response (NachBatchResponse).
 * Monetary fields are Decimal-as-string on the wire (CLAUDE.md §6.2).
 */
export interface GenerateNachBatchResponse {
  id: string;
  organizationId: string;
  batchReference: string;
  integrationConfigId: string | null;
  batchDate: string;
  debitDate: string;
  fileFormat: string;
  totalTransactions: number;
  totalAmount: string;
  successCount: number;
  successAmount: string;
  failureCount: number;
  failureAmount: string;
  pendingCount: number;
  fileName: string | null;
  fileGeneratedAt: string | null;
  submittedAt: string | null;
  submissionReference: string | null;
  responseReceivedAt: string | null;
  status: string;
  errorMessage: string | null;
  remarks: string | null;
  createdAt: string;
}

export async function generateNachBatch(
  body: GenerateNachBatchRequest,
  idempotencyKey: string,
): Promise<GenerateNachBatchResponse> {
  const response = await api.post<GenerateNachBatchResponse>(`${BASE_URL}/batches/generate`, body, {
    headers: {
      // NACH batch initiates auto-debits — financial mutation per
      // CLAUDE.md §6.3.
      'Idempotency-Key': idempotencyKey,
    },
  });
  return response.data;
}

// ============== Retry batch — create from selected failed transactions ==============

/**
 * Body for POST /lending/nach/retry-batch. Field names mirror the backend
 * `RetryBatchRequest` (camelCase via Pydantic CamelSchema).
 */
export interface CreateRetryBatchRequest {
  transactionIds: string[];
  newDebitDate: string; // ISO yyyy-MM-dd
}

export async function createRetryBatch(
  body: CreateRetryBatchRequest,
  idempotencyKey: string,
): Promise<GenerateNachBatchResponse> {
  const response = await api.post<GenerateNachBatchResponse>(`${BASE_URL}/retry-batch`, body, {
    headers: {
      // Re-presenting bounced auto-debits is a financial mutation
      // (CLAUDE.md §6.3, allowlist: `lending/nach`).
      'Idempotency-Key': idempotencyKey,
    },
  });
  return response.data;
}

export const nachApi = {
  generateNachBatch,
  createRetryBatch,
};

export default nachApi;
