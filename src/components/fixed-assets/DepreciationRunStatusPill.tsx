import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { DepreciationRunStatus } from '@/types/fixed-assets';

const statusClasses: Record<DepreciationRunStatus, string> = {
  RUNNING: 'bg-amber-100 text-amber-700 border-amber-300',
  COMPLETED: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  POSTED: 'bg-blue-100 text-blue-700 border-blue-300',
  FAILED: 'bg-red-100 text-red-700 border-red-300',
};

export function DepreciationRunStatusPill({
  status,
  className,
}: {
  status: DepreciationRunStatus;
  className?: string;
}): JSX.Element {
  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', statusClasses[status], className)}
    >
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}
