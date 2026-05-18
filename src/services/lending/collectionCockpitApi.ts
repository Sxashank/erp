import { api } from '@/services/api';

export interface CollectionCockpitSummary {
  periodFrom: string;
  periodTo: string;
  demandAmount: string;
  receiptAmount: string;
  allocatedAmount: string;
  unallocatedReceipts: string;
  collectionEfficiencyPercent: string;
  overdueAmount: string;
  overdueAccounts: number;
  unmatchedBankCreditCount: number;
  unmatchedBankCreditAmount: string;
  matchedBankCreditCount: number;
  matchedBankCreditAmount: string;
}

export interface CollectionBucketMetric {
  bucket: string;
  label: string;
  installmentCount: number;
  amountDue: string;
  portfolioPercent: string;
}

export interface UpcomingCollectionItem {
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  dueDate: string;
  installmentNumber: number;
  status: string;
  daysPastDue: number;
  principalDue: string;
  interestDue: string;
  penalDue: string;
  amountDue: string;
}

export interface UnmatchedBankCreditItem {
  statementId: string;
  transactionDate: string;
  valueDate: string;
  referenceNumber: string | null;
  utrNumber: string | null;
  description: string | null;
  creditAmount: string;
  reconciledAmount: string;
  unreconciledAmount: string;
}

export interface CollectionCockpitResponse {
  summary: CollectionCockpitSummary;
  ageingBuckets: CollectionBucketMetric[];
  upcomingCollections: UpcomingCollectionItem[];
  unmatchedBankCredits: UnmatchedBankCreditItem[];
}

export interface CollectionCockpitFilters {
  periodFrom?: string;
  periodTo?: string;
  limit?: number;
}

export async function getCollectionCockpit(
  filters: CollectionCockpitFilters = {},
): Promise<CollectionCockpitResponse> {
  const { data } = await api.get<CollectionCockpitResponse>('/lending/collection-cockpit', {
    params: {
      period_from: filters.periodFrom,
      period_to: filters.periodTo,
      limit: filters.limit,
    },
  });
  return data;
}
