/**
 * StatusBadge Component
 * Enterprise-grade status badges for lending module
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type {
  EntityStatus,
  ApplicationStage,
  ApplicationStatus,
  AssetClassification,
  LoanAccountStatus,
  DisbursementStatus,
  ReceiptStatus,
  OTSStatus,
  LegalCaseStatus,
} from '@/types/lending';

// ============== COLOR CONFIGURATIONS ==============

const entityStatusColors: Record<EntityStatus, string> = {
  PROSPECT: 'bg-slate-100 text-slate-700 border-slate-300',
  ACTIVE: 'bg-green-100 text-green-700 border-green-300',
  INACTIVE: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  BLACKLISTED: 'bg-red-100 text-red-700 border-red-300',
};

const applicationStageColors: Record<ApplicationStage, string> = {
  LEAD: 'bg-slate-100 text-slate-700 border-slate-300',
  APPLICATION: 'bg-blue-100 text-blue-700 border-blue-300',
  APPRAISAL: 'bg-amber-100 text-amber-700 border-amber-300',
  SANCTION: 'bg-purple-100 text-purple-700 border-purple-300',
  POST_SANCTION: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  DISBURSED: 'bg-green-100 text-green-700 border-green-300',
  CLOSED: 'bg-slate-100 text-slate-600 border-slate-300',
};

const applicationStatusColors: Record<ApplicationStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  SUBMITTED: 'bg-blue-100 text-blue-700 border-blue-300',
  UNDER_REVIEW: 'bg-amber-100 text-amber-700 border-amber-300',
  SANCTIONED: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  WITHDRAWN: 'bg-slate-100 text-slate-600 border-slate-300',
};

const assetClassificationColors: Record<AssetClassification, string> = {
  STANDARD: 'bg-green-100 text-green-700 border-green-300',
  SMA_0: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  SMA_1: 'bg-amber-100 text-amber-700 border-amber-300',
  SMA_2: 'bg-orange-100 text-orange-700 border-orange-300',
  NPA: 'bg-red-100 text-red-700 border-red-300',
  SUBSTANDARD: 'bg-red-200 text-red-800 border-red-400',
  SUB_STANDARD: 'bg-red-200 text-red-800 border-red-400',
  DOUBTFUL: 'bg-red-300 text-red-900 border-red-500',
  DOUBTFUL_1: 'bg-red-300 text-red-900 border-red-500',
  DOUBTFUL_2: 'bg-red-400 text-white border-red-600',
  DOUBTFUL_3: 'bg-red-500 text-white border-red-700',
  LOSS: 'bg-red-600 text-white border-red-800',
};

const loanAccountStatusColors: Record<LoanAccountStatus, string> = {
  CREATED: 'bg-blue-100 text-blue-700 border-blue-300',
  ACTIVE: 'bg-green-100 text-green-700 border-green-300',
  DORMANT: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  FROZEN: 'bg-orange-100 text-orange-700 border-orange-300',
  CLOSED: 'bg-slate-100 text-slate-600 border-slate-300',
  WRITTEN_OFF: 'bg-slate-200 text-slate-700 border-slate-400',
  RECALLED: 'bg-red-100 text-red-700 border-red-300',
};

const disbursementStatusColors: Record<DisbursementStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  APPROVED: 'bg-blue-100 text-blue-700 border-blue-300',
  PROCESSED: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
};

const receiptStatusColors: Record<ReceiptStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  ALLOCATED: 'bg-green-100 text-green-700 border-green-300',
  PARTIAL: 'bg-blue-100 text-blue-700 border-blue-300',
  REVERSED: 'bg-red-100 text-red-700 border-red-300',
};

const otsStatusColors: Record<OTSStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  SUBMITTED: 'bg-blue-100 text-blue-700 border-blue-300',
  APPROVED: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  SETTLED: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  CANCELLED: 'bg-slate-200 text-slate-600 border-slate-400',
};

const legalCaseStatusColors: Record<LegalCaseStatus, string> = {
  FILED: 'bg-blue-100 text-blue-700 border-blue-300',
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  HEARING: 'bg-purple-100 text-purple-700 border-purple-300',
  DISPOSED: 'bg-green-100 text-green-700 border-green-300',
  APPEALED: 'bg-orange-100 text-orange-700 border-orange-300',
  CLOSED: 'bg-slate-100 text-slate-600 border-slate-300',
};

// NACH Batch Status
type NachBatchStatus =
  | 'CREATED'
  | 'VALIDATED'
  | 'FILE_GENERATED'
  | 'SUBMITTED'
  | 'PROCESSING'
  | 'RESPONSE_RECEIVED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

const nachBatchStatusColors: Record<NachBatchStatus, string> = {
  CREATED: 'bg-slate-100 text-slate-700 border-slate-300',
  VALIDATED: 'bg-blue-100 text-blue-700 border-blue-300',
  FILE_GENERATED: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  SUBMITTED: 'bg-purple-100 text-purple-700 border-purple-300',
  PROCESSING: 'bg-amber-100 text-amber-700 border-amber-300',
  RESPONSE_RECEIVED: 'bg-cyan-100 text-cyan-700 border-cyan-300',
  COMPLETED: 'bg-green-100 text-green-700 border-green-300',
  FAILED: 'bg-red-100 text-red-700 border-red-300',
  CANCELLED: 'bg-gray-100 text-gray-600 border-gray-300',
};

// NACH Transaction Status
type NachTransactionStatus =
  | 'PENDING'
  | 'INCLUDED'
  | 'SUBMITTED'
  | 'SUCCESS'
  | 'BOUNCED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'RETRY_SCHEDULED';

const nachTransactionStatusColors: Record<NachTransactionStatus, string> = {
  PENDING: 'bg-slate-100 text-slate-700 border-slate-300',
  INCLUDED: 'bg-blue-100 text-blue-700 border-blue-300',
  SUBMITTED: 'bg-purple-100 text-purple-700 border-purple-300',
  SUCCESS: 'bg-green-100 text-green-700 border-green-300',
  BOUNCED: 'bg-red-100 text-red-700 border-red-300',
  REJECTED: 'bg-red-200 text-red-800 border-red-400',
  CANCELLED: 'bg-gray-100 text-gray-600 border-gray-300',
  RETRY_SCHEDULED: 'bg-amber-100 text-amber-700 border-amber-300',
};

// ============== LABEL FORMATTERS ==============

const formatLabel = (status: string): string => {
  if (!status) return '';
  return status
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Sma/g, 'SMA')
    .replace(/Npa/g, 'NPA')
    .replace(/Ots/g, 'OTS');
};

// ============== COMPONENTS ==============

interface StatusBadgeProps {
  status: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-sm px-3 py-1',
};

export function EntityStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass = entityStatusColors[status as EntityStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

// Risk Category Badge
const riskCategoryColors: Record<string, string> = {
  LOW: 'bg-green-100 text-green-700 border-green-300',
  MEDIUM: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  HIGH: 'bg-red-100 text-red-700 border-red-300',
};

export function RiskCategoryBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass = riskCategoryColors[status] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)} Risk
    </Badge>
  );
}

export function ApplicationStageBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    applicationStageColors[status as ApplicationStage] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function ApplicationStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    applicationStatusColors[status as ApplicationStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function AssetClassificationBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    assetClassificationColors[status as AssetClassification] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-semibold', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function LoanAccountStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    loanAccountStatusColors[status as LoanAccountStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function DisbursementStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    disbursementStatusColors[status as DisbursementStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function ReceiptStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass = receiptStatusColors[status as ReceiptStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function OTSStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass = otsStatusColors[status as OTSStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function LegalCaseStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    legalCaseStatusColors[status as LegalCaseStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function NachBatchStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    nachBatchStatusColors[status as NachBatchStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function NachTransactionStatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  if (!status) return null;
  const colorClass =
    nachTransactionStatusColors[status as NachTransactionStatus] || 'bg-gray-100 text-gray-700';

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {formatLabel(status)}
    </Badge>
  );
}

/**
 * Generic status badge that auto-detects the type
 */
export function StatusBadge({
  type,
  status,
  className,
  size = 'md',
}: {
  type:
    | 'entity'
    | 'stage'
    | 'application'
    | 'classification'
    | 'loan'
    | 'disbursement'
    | 'receipt'
    | 'ots'
    | 'legal'
    | 'nach_batch'
    | 'nach_transaction'
    | 'sanction'
    | 'loanAccount'
    | 'product';
  status: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}) {
  if (!status) return null;
  switch (type) {
    case 'entity':
      return <EntityStatusBadge status={status} className={className} size={size} />;
    case 'stage':
      return <ApplicationStageBadge status={status} className={className} size={size} />;
    case 'application':
      return <ApplicationStatusBadge status={status} className={className} size={size} />;
    case 'classification':
      return <AssetClassificationBadge status={status} className={className} size={size} />;
    case 'loan':
      return <LoanAccountStatusBadge status={status} className={className} size={size} />;
    case 'disbursement':
      return <DisbursementStatusBadge status={status} className={className} size={size} />;
    case 'receipt':
      return <ReceiptStatusBadge status={status} className={className} size={size} />;
    case 'ots':
      return <OTSStatusBadge status={status} className={className} size={size} />;
    case 'legal':
      return <LegalCaseStatusBadge status={status} className={className} size={size} />;
    case 'sanction':
      return <ApplicationStatusBadge status={status} className={className} size={size} />;
    case 'loanAccount':
      return <LoanAccountStatusBadge status={status} className={className} size={size} />;
    case 'nach_batch':
      return <NachBatchStatusBadge status={status} className={className} size={size} />;
    case 'nach_transaction':
      return <NachTransactionStatusBadge status={status} className={className} size={size} />;
    default:
      return (
        <Badge variant="outline" className={cn('font-medium', sizeClasses[size], className)}>
          {formatLabel(status)}
        </Badge>
      );
  }
}
