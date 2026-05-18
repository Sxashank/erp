import api from '../api';

export interface RepaymentMatchCandidate {
  statementId: string;
  transactionDate: string;
  valueDate: string;
  referenceNumber: string | null;
  utrNumber: string | null;
  description: string | null;
  creditAmount: string;
  suggestedLoanAccountId: string | null;
  loanAccountNumber: string | null;
  entityName: string | null;
  suggestedReceiptId: string | null;
  suggestedInstallmentId: string | null;
  dueDate: string | null;
  dueAmount: string | null;
  confidence: string;
  matchBasis: string[];
  suggestedAction: 'CREATE_RECEIPT' | 'LINK_RECEIPT' | 'REVIEW';
}

export interface RepaymentMatchingSummary {
  unmatchedCreditCount: number;
  unmatchedCreditAmount: string;
  highConfidenceCount: number;
  reviewRequiredCount: number;
}

export interface RepaymentMatchingResponse {
  summary: RepaymentMatchingSummary;
  candidates: RepaymentMatchCandidate[];
}

export interface CreateMatchedReceiptBody {
  loanAccountId?: string;
  autoAllocate?: boolean;
}

export interface CreateMatchedReceiptResponse {
  statementId: string;
  matchId: string;
  receiptId: string;
  receiptNumber: string;
  loanAccountId: string;
  receiptAmount: string;
  allocatedAmount: string;
  unallocatedAmount: string;
  statementStatus: string;
  matchConfidence: string;
  matchType: 'AUTO' | 'MANUAL';
  matchBasis: Record<string, unknown>;
}

export interface RepaymentMatchingFilters {
  bankAccountId?: string;
  fromDate?: string;
  toDate?: string;
  minConfidence?: string;
  limit?: number;
}

export async function getRepaymentMatchingSummary(
  filters: RepaymentMatchingFilters = {},
): Promise<RepaymentMatchingSummary> {
  const { data } = await api.get<RepaymentMatchingSummary>('/lending/repayment-matching/summary', {
    params: filters,
  });
  return data;
}

export async function getRepaymentMatchCandidates(
  filters: RepaymentMatchingFilters = {},
): Promise<RepaymentMatchingResponse> {
  const { data } = await api.get<RepaymentMatchingResponse>(
    '/lending/repayment-matching/candidates',
    { params: filters },
  );
  return data;
}

export async function createMatchedReceipt(
  statementId: string,
  body: CreateMatchedReceiptBody = {},
): Promise<CreateMatchedReceiptResponse> {
  const { data } = await api.post<CreateMatchedReceiptResponse>(
    `/lending/repayment-matching/statements/${statementId}/create-receipt`,
    body,
    {
      headers: {
        'Idempotency-Key': crypto.randomUUID(),
      },
    },
  );
  return data;
}
