/**
 * useNachRetryDue — query for /lending/nach/retry-due.
 *
 * Returns the (un-paginated) list of bounced transactions eligible for retry,
 * plus aggregate totals. Wire format is camelCase per Pydantic CamelSchema.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface NachRetryDueItem {
  id: string;
  transactionReference: string;
  loanAccountNumber: string;
  borrowerName: string;
  originalDebitDate: string;
  retryCount: number;
  nextRetryDate: string;
  // Monetary fields are JSON strings on the wire (Pydantic Decimal — CLAUDE.md §6.2).
  debitAmount: string;
  lastFailureReason: string | null;
  umrn: string | null;
  bankName: string | null;
  returnCode: string | null;
  mandateStatus: string | null;
  maxRetries: number;
}

export interface NachRetryDueResponse {
  items: NachRetryDueItem[];
  total: number;
  totalAmount: string;
}

export const nachRetryDueQueryKey = (asOfDate?: string) =>
  ['lending', 'nach', 'retry-due', asOfDate ?? ''] as const;

async function fetchRetryDue(asOfDate?: string): Promise<NachRetryDueResponse> {
  const params = new URLSearchParams();
  if (asOfDate) params.append('as_of_date', asOfDate);
  const { data } = await api.get<NachRetryDueResponse>(
    `/lending/nach/retry-due${params.toString() ? `?${params.toString()}` : ''}`,
  );
  return data;
}

export function useNachRetryDue(asOfDate?: string) {
  return useQuery<NachRetryDueResponse>({
    queryKey: nachRetryDueQueryKey(asOfDate),
    queryFn: () => fetchRetryDue(asOfDate),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
