import { api } from '@/services/api';

export interface ClosureCockpitSummary {
  closureReadyCount: number;
  closureReadyOutstanding: string;
  closedPendingReleaseCount: number;
  unreleasedSecurityCount: number;
  unreleasedSecurityValue: string;
  recentClosureReceiptCount: number;
  recentClosureReceiptAmount: string;
  blockedByOutstandingCount: number;
  blockedByOutstandingAmount: string;
}

export interface ClosureCandidateItem {
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  status: string;
  totalOutstanding: string;
  principalOutstanding: string;
  interestOutstanding: string;
  chargesOutstanding: string;
  maturityDate: string | null;
  closureDate: string | null;
  closureStatus: string;
  unreleasedSecurityCount: number;
  unreleasedSecurityValue: string;
  originalDocumentsHeld: number;
}

export interface SecurityReleaseItem {
  securityId: string;
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  securityType: string;
  securityCategory: string;
  description: string;
  acceptableValue: string;
  netValue: string;
  status: string;
  originalDocumentsReceived: boolean;
  documentLocation: string | null;
  releaseDate: string | null;
}

export interface RecentClosureReceiptItem {
  receiptId: string;
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  receiptNumber: string;
  receiptDate: string;
  receiptType: string;
  receiptAmount: string;
  allocatedAmount: string;
  unallocatedAmount: string;
  status: string;
  instrumentNumber: string | null;
}

export interface ClosureCockpitResponse {
  summary: ClosureCockpitSummary;
  closureCandidates: ClosureCandidateItem[];
  pendingSecurityReleases: SecurityReleaseItem[];
  recentClosureReceipts: RecentClosureReceiptItem[];
}

export interface ClosureCockpitFilters {
  limit?: number;
  recentDays?: number;
}

export async function getClosureCockpit(
  filters: ClosureCockpitFilters = {},
): Promise<ClosureCockpitResponse> {
  const { data } = await api.get<ClosureCockpitResponse>('/lending/closure-cockpit', {
    params: {
      limit: filters.limit,
      recent_days: filters.recentDays,
    },
  });
  return data;
}
