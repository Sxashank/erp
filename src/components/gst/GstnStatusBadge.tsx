import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TaxBadgeProps {
  status?: string | null;
  className?: string;
}

const filingStatusClasses: Record<string, string> = {
  NOT_GENERATED: 'border-slate-300 bg-slate-100 text-slate-700',
  DRAFT: 'border-slate-300 bg-slate-100 text-slate-700',
  GENERATED: 'border-blue-300 bg-blue-100 text-blue-700',
  VALIDATED: 'border-amber-300 bg-amber-100 text-amber-700',
  SUBMITTED: 'border-purple-300 bg-purple-100 text-purple-700',
  FILED: 'border-green-300 bg-green-100 text-green-700',
  ERROR: 'border-red-300 bg-red-100 text-red-700',
};

const mismatchTypeClasses: Record<string, string> = {
  MATCHED: 'border-green-300 bg-green-100 text-green-700',
  MISSING_IN_2B: 'border-red-300 bg-red-100 text-red-700',
  MISSING_IN_BOOKS: 'border-amber-300 bg-amber-100 text-amber-700',
  AMOUNT_MISMATCH: 'border-purple-300 bg-purple-100 text-purple-700',
  GSTIN_MISMATCH: 'border-orange-300 bg-orange-100 text-orange-700',
};

const resolutionStatusClasses: Record<string, string> = {
  PENDING: 'border-slate-300 bg-slate-100 text-slate-700',
  ACCEPTED: 'border-green-300 bg-green-100 text-green-700',
  REJECTED: 'border-red-300 bg-red-100 text-red-700',
  UNDER_REVIEW: 'border-blue-300 bg-blue-100 text-blue-700',
  FOLLOW_UP: 'border-amber-300 bg-amber-100 text-amber-700',
};

function formatLabel(status?: string | null) {
  if (!status) {
    return 'Unknown';
  }

  return status
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace('Gstr', 'GSTR')
    .replace('Itc', 'ITC')
    .replace('Gstin', 'GSTIN');
}

function TaxBadge({
  status,
  classes,
  className,
}: TaxBadgeProps & { classes: Record<string, string> }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'border font-medium',
        classes[status ?? ''] ?? 'border-slate-300 bg-slate-100 text-slate-700',
        className,
      )}
    >
      {formatLabel(status)}
    </Badge>
  );
}

export function GstnFilingStatusBadge({ status, className }: TaxBadgeProps) {
  return <TaxBadge status={status} classes={filingStatusClasses} className={className} />;
}

export function ItcMismatchTypeBadge({ status, className }: TaxBadgeProps) {
  return <TaxBadge status={status} classes={mismatchTypeClasses} className={className} />;
}

export function ItcResolutionStatusBadge({ status, className }: TaxBadgeProps) {
  return <TaxBadge status={status} classes={resolutionStatusClasses} className={className} />;
}
