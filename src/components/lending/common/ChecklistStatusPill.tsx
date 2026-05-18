/**
 * ChecklistStatusPill — status badge for per-loan approval checklist items.
 *
 * Five canonical states: PENDING (grey), IN_PROGRESS (blue), MET (green),
 * WAIVED (amber), NOT_APPLICABLE (slate). See CLAUDE.md §5.1.
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type ChecklistItemStatus = 'PENDING' | 'IN_PROGRESS' | 'MET' | 'WAIVED' | 'NOT_APPLICABLE';

const statusColors: Record<ChecklistItemStatus, string> = {
  PENDING: 'bg-gray-100 text-gray-700 border-gray-300',
  IN_PROGRESS: 'bg-blue-100 text-blue-700 border-blue-300',
  MET: 'bg-green-100 text-green-700 border-green-300',
  WAIVED: 'bg-amber-100 text-amber-700 border-amber-300',
  NOT_APPLICABLE: 'bg-slate-100 text-slate-600 border-slate-300',
};

const statusLabels: Record<ChecklistItemStatus, string> = {
  PENDING: 'Pending',
  IN_PROGRESS: 'In Progress',
  MET: 'Met',
  WAIVED: 'Waived',
  NOT_APPLICABLE: 'Not Applicable',
};

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-sm px-3 py-1',
};

export interface ChecklistStatusPillProps {
  status: ChecklistItemStatus | string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ChecklistStatusPill({
  status,
  className,
  size = 'md',
}: ChecklistStatusPillProps): JSX.Element | null {
  if (!status) return null;
  const colorClass = statusColors[status as ChecklistItemStatus] ?? 'bg-gray-100 text-gray-700';
  const label = statusLabels[status as ChecklistItemStatus] ?? String(status);

  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', colorClass, sizeClasses[size], className)}
    >
      {label}
    </Badge>
  );
}
