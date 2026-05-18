import { api } from '@/services/api';

export interface DisbursementReadinessSummary {
  sanctionedNotDisbursedCount: number;
  sanctionedNotDisbursedAmount: string;
  readyCount: number;
  readyAmount: string;
  conditionBlockedCount: number;
  conditionBlockedAmount: string;
  expiredCount: number;
  expiredAmount: string;
  pendingDisbursementCount: number;
  pendingDisbursementAmount: string;
  approvedPendingProcessingCount: number;
  approvedPendingProcessingAmount: string;
  processedThisMonthAmount: string;
}

export interface ReadinessBucketMetric {
  bucket: string;
  label: string;
  count: number;
  amount: string;
}

export interface ReadinessBlockerItem {
  sanctionId: string;
  sanctionNumber: string;
  applicationId: string;
  applicationNumber: string;
  borrowerName: string;
  projectName: string | null;
  sanctionedAmount: string;
  undisbursedAmount: string;
  validityDate: string | null;
  firstDisbursementDeadline: string | null;
  status: string;
  readinessStatus: string;
  mandatoryPending: number;
  mandatoryOverdue: number;
  pendingDisbursementAmount: string;
}

export interface PendingDisbursementItem {
  disbursementId: string;
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  reference: string;
  requestedAmount: string;
  approvedAmount: string | null;
  scheduledDate: string | null;
  requestDate: string;
  status: string;
  conditionsVerified: boolean;
  utrNumber: string | null;
}

export interface DisbursementReadinessResponse {
  summary: DisbursementReadinessSummary;
  readinessBuckets: ReadinessBucketMetric[];
  blockers: ReadinessBlockerItem[];
  pendingDisbursements: PendingDisbursementItem[];
}

export interface DisbursementReadinessFilters {
  limit?: number;
}

export async function getDisbursementReadiness(
  filters: DisbursementReadinessFilters = {},
): Promise<DisbursementReadinessResponse> {
  const { data } = await api.get<DisbursementReadinessResponse>('/lending/disbursement-readiness', {
    params: {
      limit: filters.limit,
    },
  });
  return data;
}
